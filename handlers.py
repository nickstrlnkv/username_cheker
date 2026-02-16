import logging
import asyncio
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, BufferedInputFile
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from io import BytesIO
import keyboards
import config
from telethon_auth import authorize_telethon

logger = logging.getLogger(__name__)

router = Router()

class UserStates(StatesGroup):
    waiting_for_file = State()
    waiting_for_username = State()
    waiting_for_username_to_remove = State()
    waiting_for_interval = State()
    waiting_for_batch_size = State()
    waiting_for_phone = State()
    waiting_for_code = State()
    waiting_for_password = State()
    waiting_for_spam_delay = State()
    waiting_for_spam_count = State()

@router.message(Command("start"))
async def cmd_start(message: Message, db, checker):
    await message.answer(
        "🤖 <b>Telegram Username Monitor Bot</b>\n\n"
        "Бот для мониторинга освобождения Telegram username.\n\n"
        "Выберите действие:",
        reply_markup=keyboards.get_main_menu(),
        parse_mode="HTML"
    )

@router.callback_query(F.data == "back_to_menu")
async def back_to_menu(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text(
        "🤖 <b>Главное меню</b>\n\nВыберите действие:",
        reply_markup=keyboards.get_main_menu(),
        parse_mode="HTML"
    )
    await callback.answer()

@router.callback_query(F.data == "reset_session")
async def reset_session_confirm(callback: CallbackQuery):
    if callback.from_user.id not in config.ADMIN_IDS:
        await callback.answer("⛔ Недостаточно прав", show_alert=True)
        return

    await callback.message.edit_text(
        "⚠️ <b>Сброс сессии Telethon</b>\n\n"
        "Текущая сессия будет удалена, и потребуется повторная авторизация.\n"
        "Мониторинг будет остановлен.\n\n"
        "Продолжить?",
        reply_markup=keyboards.get_confirm_keyboard("reset_session"),
        parse_mode="HTML"
    )
    await callback.answer()

@router.callback_query(F.data == "confirm_reset_session")
async def reset_session(callback: CallbackQuery, db, checker, bot, auth_handler):
    if callback.from_user.id not in config.ADMIN_IDS:
        await callback.answer("⛔ Недостаточно прав", show_alert=True)
        return

    checker.stop_monitoring()
    await db.set_setting('monitoring_active', '0')

    await callback.message.edit_text(
        "🔄 <b>Сброс сессии...</b>\n\n"
        "Удаляем текущую сессию и запускаем повторную авторизацию.",
        parse_mode="HTML"
    )

    await checker.reset_session()

    asyncio.create_task(
        authorize_telethon(
            bot,
            checker,
            auth_handler,
            config.ADMIN_IDS,
            prompt_admin_id=callback.from_user.id,
            delay=0
        )
    )

    await callback.message.edit_text(
        "✅ <b>Сессия сброшена</b>\n\n"
        "Теперь пройдите авторизацию Telethon в этом чате.",
        reply_markup=keyboards.get_back_button(),
        parse_mode="HTML"
    )
    await callback.answer()

@router.callback_query(F.data == "start_monitoring")
async def start_monitoring(callback: CallbackQuery, db, checker, bot):
    # Проверяем реальное состояние мониторинга, а не только БД
    # Это важно при перезапуске бота, когда в БД может остаться старое значение
    is_running = checker.is_running and checker._check_task is not None and not checker._check_task.done()
    is_active_db = await db.get_setting('monitoring_active')
    
    # Если в БД указано что мониторинг активен, но реально он не запущен - синхронизируем состояние
    if is_active_db == '1' and not is_running:
        logger.warning("Database shows monitoring as active, but task is not running. Resetting DB state.")
        await db.set_setting('monitoring_active', '0')
        is_active_db = '0'
    
    if is_running or is_active_db == '1':
        await callback.answer("⚠️ Мониторинг уже запущен!", show_alert=True)
        return
    
    await db.set_setting('monitoring_active', '1')
    
    # Сохраняем chat_id из чата где запущен мониторинг
    chat_id = callback.message.chat.id
    await db.set_setting('spam_chat_id', str(chat_id))
    
    async def notification_callback(username: str):
        try:
            # Отправка уведомлений админам
            for admin_id in config.ADMIN_IDS:
                await bot.send_message(
                    admin_id,
                    f"🎉 <b>USERNAME ОСВОБОДИЛСЯ!</b>\n\n"
                    f"@{username}\n\n"
                    f"Быстрее регистрируйте!",
                    parse_mode="HTML"
                )
            
            # Получаем настройки спама из БД
            spam_chat_id_str = await db.get_setting('spam_chat_id') or ''
            spam_delay = float(await db.get_setting('spam_delay') or '0.5')
            spam_mode = await db.get_setting('spam_mode') or 'count'
            spam_count = int(await db.get_setting('spam_message_count') or '10')
            
            if not spam_chat_id_str:
                logger.warning("spam_chat_id not set, skipping spam")
                await db.mark_as_notified(username)
                return
            
            spam_chat_id = int(spam_chat_id_str)
            message_text = (
                f"🎉 <b>USERNAME ОСВОБОДИЛСЯ!</b>\n\n"
                f"@{username}\n\n"
                f"Быстрее регистрируйте!"
            )
            
            if spam_mode == 'count':
                # Режим: указать количество сообщений
                for i in range(spam_count):
                    try:
                        await bot.send_message(
                            spam_chat_id,
                            message_text,
                            parse_mode="HTML"
                        )
                        await asyncio.sleep(spam_delay)
                    except Exception as spam_error:
                        logger.error(f"Error spamming chat (message {i+1}/{spam_count}): {spam_error}")
                        continue
            elif spam_mode == 'until_occupied':
                # Режим: спамить до занятия username
                asyncio.create_task(
                    spam_until_occupied(bot, checker, db, spam_chat_id, username, message_text, spam_delay)
                )
            
            await db.mark_as_notified(username)
        except Exception as e:
            logger.error(f"Error sending notification: {e}")
    
    try:
        checker._check_task = asyncio.create_task(
            checker.start_monitoring(db, notification_callback)
        )
        logger.info(f"Monitoring task created and started. Task: {checker._check_task}")
        
        await callback.message.edit_text(
            "✅ <b>Мониторинг запущен!</b>\n\n"
            "Бот начал проверку username в фоновом режиме.",
            reply_markup=keyboards.get_back_button(),
            parse_mode="HTML"
        )
        await callback.answer()
    except Exception as e:
        logger.error(f"Error starting monitoring: {e}", exc_info=True)
        await db.set_setting('monitoring_active', '0')
        await callback.answer("❌ Ошибка при запуске мониторинга!", show_alert=True)

async def spam_until_occupied(bot, checker, db, chat_id, username, message_text, delay):
    """Спамит в чат пока username не займут"""
    username_clean = username.lstrip('@').lower()
    check_interval = 5.0  # Интервал проверки статуса (секунды)
    
    while True:
        try:
            # Отправляем сообщение
            try:
                await bot.send_message(
                    chat_id,
                    message_text,
                    parse_mode="HTML"
                )
            except Exception as e:
                logger.error(f"Error sending spam message: {e}")
                # Продолжаем даже если одно сообщение не отправилось
            
            await asyncio.sleep(delay)
            
            # Периодически проверяем статус username
            # Проверяем каждые N сообщений или каждые check_interval секунд
            status = await checker.check_username(username_clean)
            
            if status != 'free':
                # Username занят, прекращаем спам
                logger.info(f"Username @{username_clean} is now {status}, stopping spam")
                break
            
            # Обновляем статус в БД
            await db.update_username_status(username_clean, status)
            
        except Exception as e:
            logger.error(f"Error in spam_until_occupied: {e}")
            await asyncio.sleep(delay)

@router.callback_query(F.data == "stop_monitoring")
async def stop_monitoring(callback: CallbackQuery, db, checker):
    # Проверяем реальное состояние мониторинга
    is_running = checker.is_running and checker._check_task is not None and not checker._check_task.done()
    is_active_db = await db.get_setting('monitoring_active')
    
    # Если реально не запущен, синхронизируем БД
    if not is_running:
        if is_active_db == '1':
            await db.set_setting('monitoring_active', '0')
        await callback.answer("⚠️ Мониторинг не запущен!", show_alert=True)
        return
    
    checker.stop_monitoring()
    await db.set_setting('monitoring_active', '0')
    
    await callback.message.edit_text(
        "⏹ <b>Мониторинг остановлен</b>\n\n"
        "Проверка username приостановлена.",
        reply_markup=keyboards.get_back_button(),
        parse_mode="HTML"
    )
    await callback.answer()

@router.callback_query(F.data == "statistics")
async def show_statistics(callback: CallbackQuery, db):
    stats = await db.get_statistics()
    is_active = await db.get_setting('monitoring_active')
    
    status_text = "🟢 Активен" if is_active == '1' else "🔴 Остановлен"
    
    text = (
        f"📊 <b>Статистика</b>\n\n"
        f"Статус мониторинга: {status_text}\n\n"
        f"📝 Всего в базе: <b>{stats['total']}</b>\n"
        f"🔴 Занято: <b>{stats['occupied']}</b>\n"
        f"🟢 Свободно: <b>{stats['free']}</b>\n"
        f"⚠️ Ошибки: <b>{stats['error']}</b>\n"
        f"❓ Не проверено: <b>{stats['unknown']}</b>\n"
    )
    
    await callback.message.edit_text(
        text,
        reply_markup=keyboards.get_back_button(),
        parse_mode="HTML"
    )
    await callback.answer()

@router.callback_query(F.data == "upload_db")
async def upload_db(callback: CallbackQuery, state: FSMContext):
    await state.set_state(UserStates.waiting_for_file)
    await callback.message.edit_text(
        "📥 <b>Загрузка базы</b>\n\n"
        "Отправьте файл .txt или .csv со списком username.\n"
        "Формат: один username на строку (с @ или без).\n\n"
        "Отправьте /cancel для отмены.",
        parse_mode="HTML"
    )
    await callback.answer()

@router.message(UserStates.waiting_for_file, F.document)
async def process_file(message: Message, state: FSMContext, db):
    document = message.document
    
    if not (document.file_name.endswith('.txt') or document.file_name.endswith('.csv')):
        await message.answer("⚠️ Поддерживаются только .txt и .csv файлы!")
        return
    
    file = await message.bot.download(document)
    content = file.read().decode('utf-8')
    
    usernames = []
    for line in content.split('\n'):
        line = line.strip()
        if line and not line.startswith('#'):
            if ',' in line:
                username = line.split(',')[0].strip()
            else:
                username = line
            usernames.append(username)
    
    result = await db.add_usernames_bulk(usernames)
    
    await message.answer(
        f"✅ <b>Загрузка завершена!</b>\n\n"
        f"Добавлено: <b>{result['added']}</b>\n"
        f"Пропущено (дубликаты): <b>{result['skipped']}</b>",
        reply_markup=keyboards.get_main_menu(),
        parse_mode="HTML"
    )
    await state.clear()

@router.callback_query(F.data == "download_db")
async def download_db(callback: CallbackQuery, db):
    export_data = await db.export_usernames()
    
    if not export_data:
        await callback.answer("⚠️ База данных пуста!", show_alert=True)
        return
    
    file_bytes = export_data.encode('utf-8')
    
    await callback.message.answer_document(
        document=BufferedInputFile(file_bytes, filename="usernames_export.csv"),
        caption="📤 Экспорт базы данных\nФормат: username,status,last_check"
    )
    await callback.answer()

@router.callback_query(F.data == "add_username")
async def add_username(callback: CallbackQuery, state: FSMContext):
    await state.set_state(UserStates.waiting_for_username)
    await callback.message.edit_text(
        "➕ <b>Добавление username</b>\n\n"
        "Отправьте username для добавления (с @ или без).\n"
        "Можно отправить несколько через пробел или с новой строки.\n\n"
        "Отправьте /cancel для отмены.",
        parse_mode="HTML"
    )
    await callback.answer()

@router.message(UserStates.waiting_for_username)
async def process_add_username(message: Message, state: FSMContext, db):
    text = message.text.strip()
    usernames = text.replace(',', ' ').split()
    
    result = await db.add_usernames_bulk(usernames)
    
    await message.answer(
        f"✅ <b>Добавление завершено!</b>\n\n"
        f"Добавлено: <b>{result['added']}</b>\n"
        f"Пропущено (дубликаты): <b>{result['skipped']}</b>",
        reply_markup=keyboards.get_main_menu(),
        parse_mode="HTML"
    )
    await state.clear()

@router.callback_query(F.data == "remove_username")
async def remove_username(callback: CallbackQuery, state: FSMContext):
    await state.set_state(UserStates.waiting_for_username_to_remove)
    await callback.message.edit_text(
        "➖ <b>Удаление username</b>\n\n"
        "Отправьте username для удаления (с @ или без).\n\n"
        "Отправьте /cancel для отмены.",
        parse_mode="HTML"
    )
    await callback.answer()

@router.message(UserStates.waiting_for_username_to_remove)
async def process_remove_username(message: Message, state: FSMContext, db):
    username = message.text.strip()
    success = await db.remove_username(username)
    
    if success:
        await message.answer(
            f"✅ Username @{username.lstrip('@')} удален из базы!",
            reply_markup=keyboards.get_main_menu()
        )
    else:
        await message.answer(
            f"⚠️ Username @{username.lstrip('@')} не найден в базе!",
            reply_markup=keyboards.get_main_menu()
        )
    await state.clear()

@router.callback_query(F.data == "clear_db")
async def clear_db_confirm(callback: CallbackQuery):
    await callback.message.edit_text(
        "⚠️ <b>Подтверждение</b>\n\n"
        "Вы уверены, что хотите очистить всю базу username?\n"
        "Это действие необратимо!",
        reply_markup=keyboards.get_confirm_keyboard("clear_db"),
        parse_mode="HTML"
    )
    await callback.answer()

@router.callback_query(F.data == "confirm_clear_db")
async def clear_db_confirmed(callback: CallbackQuery, db):
    await db.clear_all_usernames()
    await callback.message.edit_text(
        "✅ <b>База данных очищена!</b>\n\n"
        "Все username удалены из базы.",
        reply_markup=keyboards.get_back_button(),
        parse_mode="HTML"
    )
    await callback.answer()

@router.callback_query(F.data == "settings")
async def show_settings(callback: CallbackQuery, db):
    interval = await db.get_setting('check_interval')
    batch_size = await db.get_setting('batch_size')
    
    await callback.message.edit_text(
        f"⚙ <b>Настройки</b>\n\n"
        f"⏱ Интервал между батчами: <b>{interval}с</b>\n"
        f"📦 Размер батча: <b>{batch_size}</b>\n\n"
        f"Выберите параметр для изменения:",
        reply_markup=keyboards.get_settings_menu(),
        parse_mode="HTML"
    )
    await callback.answer()

@router.callback_query(F.data == "set_interval")
async def set_interval(callback: CallbackQuery, state: FSMContext):
    await state.set_state(UserStates.waiting_for_interval)
    await callback.message.edit_text(
        "⏱ <b>Установка интервала</b>\n\n"
        "Отправьте новый интервал между батчами в секундах (1-60).\n\n"
        "Отправьте /cancel для отмены.",
        parse_mode="HTML"
    )
    await callback.answer()

@router.message(UserStates.waiting_for_interval)
async def process_interval(message: Message, state: FSMContext, db):
    try:
        interval = int(message.text.strip())
        if 1 <= interval <= 60:
            await db.set_setting('check_interval', str(interval))
            await message.answer(
                f"✅ Интервал установлен: {interval}с",
                reply_markup=keyboards.get_settings_menu()
            )
        else:
            await message.answer("⚠️ Интервал должен быть от 1 до 60 секунд!")
            return
    except ValueError:
        await message.answer("⚠️ Введите число!")
        return
    
    await state.clear()

@router.callback_query(F.data == "set_batch_size")
async def set_batch_size(callback: CallbackQuery, state: FSMContext):
    await state.set_state(UserStates.waiting_for_batch_size)
    await callback.message.edit_text(
        "📦 <b>Установка размера батча</b>\n\n"
        "Отправьте новый размер батча (10-200).\n\n"
        "Отправьте /cancel для отмены.",
        parse_mode="HTML"
    )
    await callback.answer()

@router.message(UserStates.waiting_for_batch_size)
async def process_batch_size(message: Message, state: FSMContext, db):
    try:
        batch_size = int(message.text.strip())
        if 10 <= batch_size <= 200:
            await db.set_setting('batch_size', str(batch_size))
            await message.answer(
                f"✅ Размер батча установлен: {batch_size}",
                reply_markup=keyboards.get_settings_menu()
            )
        else:
            await message.answer("⚠️ Размер батча должен быть от 10 до 200!")
            return
    except ValueError:
        await message.answer("⚠️ Введите число!")
        return
    
    await state.clear()

@router.callback_query(F.data == "spam_settings")
async def show_spam_settings(callback: CallbackQuery, db):
    spam_delay = await db.get_setting('spam_delay') or '0.5'
    spam_mode = await db.get_setting('spam_mode') or 'count'
    spam_count = await db.get_setting('spam_message_count') or '10'
    
    mode_text = "🔢 Указать количество" if spam_mode == 'count' else "♾ До занятия username"
    
    await callback.message.edit_text(
        f"💬 <b>Настройки спама</b>\n\n"
        f"⏱ Задержка между сообщениями: <b>{spam_delay}с</b>\n"
        f"🔄 Режим спама: <b>{mode_text}</b>\n"
        f"🔢 Количество сообщений: <b>{spam_count}</b>\n\n"
        f"Выберите параметр для изменения:",
        reply_markup=keyboards.get_spam_settings_menu(),
        parse_mode="HTML"
    )
    await callback.answer()

@router.callback_query(F.data == "set_spam_delay")
async def set_spam_delay(callback: CallbackQuery, state: FSMContext):
    await state.set_state(UserStates.waiting_for_spam_delay)
    await callback.message.edit_text(
        "⏱ <b>Установка задержки между сообщениями</b>\n\n"
        "Отправьте задержку в секундах (0.1-10.0).\n"
        "Например: 0.5 для полсекунды, 1.0 для секунды.\n\n"
        "Отправьте /cancel для отмены.",
        parse_mode="HTML"
    )
    await callback.answer()

@router.message(UserStates.waiting_for_spam_delay)
async def process_spam_delay(message: Message, state: FSMContext, db):
    try:
        delay = float(message.text.strip().replace(',', '.'))
        if 0.1 <= delay <= 10.0:
            await db.set_setting('spam_delay', str(delay))
            await message.answer(
                f"✅ Задержка установлена: {delay}с",
                reply_markup=keyboards.get_spam_settings_menu()
            )
        else:
            await message.answer("⚠️ Задержка должна быть от 0.1 до 10.0 секунд!")
            return
    except ValueError:
        await message.answer("⚠️ Введите число (можно с точкой или запятой)!")
        return
    
    await state.clear()

@router.callback_query(F.data == "set_spam_count")
async def set_spam_count(callback: CallbackQuery, state: FSMContext, db):
    spam_mode = await db.get_setting('spam_mode') or 'count'
    if spam_mode != 'count':
        await callback.answer("⚠️ Сначала установите режим 'Указать количество'!", show_alert=True)
        return
    
    await state.set_state(UserStates.waiting_for_spam_count)
    await callback.message.edit_text(
        "🔢 <b>Установка количества сообщений</b>\n\n"
        "Отправьте количество сообщений для спама (1-100).\n\n"
        "Отправьте /cancel для отмены.",
        parse_mode="HTML"
    )
    await callback.answer()

@router.message(UserStates.waiting_for_spam_count)
async def process_spam_count(message: Message, state: FSMContext, db):
    try:
        count = int(message.text.strip())
        if 1 <= count <= 100:
            await db.set_setting('spam_message_count', str(count))
            await message.answer(
                f"✅ Количество сообщений установлено: {count}",
                reply_markup=keyboards.get_spam_settings_menu()
            )
        else:
            await message.answer("⚠️ Количество должно быть от 1 до 100!")
            return
    except ValueError:
        await message.answer("⚠️ Введите число!")
        return
    
    await state.clear()

@router.callback_query(F.data == "set_spam_mode")
async def set_spam_mode(callback: CallbackQuery):
    await callback.message.edit_text(
        "🔄 <b>Выбор режима спама</b>\n\n"
        "🔢 <b>Указать количество</b> - отправить фиксированное количество сообщений\n"
        "♾ <b>До занятия username</b> - продолжать спамить пока username не займут\n\n"
        "Выберите режим:",
        reply_markup=keyboards.get_spam_mode_keyboard(),
        parse_mode="HTML"
    )
    await callback.answer()

@router.callback_query(F.data == "spam_mode_count")
async def spam_mode_count(callback: CallbackQuery, db):
    await db.set_setting('spam_mode', 'count')
    spam_count = await db.get_setting('spam_message_count') or '10'
    await callback.message.edit_text(
        f"✅ <b>Режим установлен: Указать количество</b>\n\n"
        f"Бот будет отправлять <b>{spam_count}</b> сообщений при освобождении username.",
        reply_markup=keyboards.get_spam_settings_menu(),
        parse_mode="HTML"
    )
    await callback.answer()

@router.callback_query(F.data == "spam_mode_until")
async def spam_mode_until(callback: CallbackQuery, db):
    await db.set_setting('spam_mode', 'until_occupied')
    await callback.message.edit_text(
        "✅ <b>Режим установлен: До занятия username</b>\n\n"
        "Бот будет продолжать спамить пока username не займут.",
        reply_markup=keyboards.get_spam_settings_menu(),
        parse_mode="HTML"
    )
    await callback.answer()

@router.message(Command("cancel"))
async def cmd_cancel(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "❌ Действие отменено.",
        reply_markup=keyboards.get_main_menu()
    )
