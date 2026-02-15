import asyncio
import logging
from aiogram import Bot, Dispatcher, Router, F
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.types import Message

import config
from database import Database
from checker import UsernameChecker
from handlers import router
from utils import setup_logging
from auth_handler import TelethonAuthHandler

logger = logging.getLogger(__name__)
auth_handler = None

async def authorize_telethon(bot, checker, auth_handler):
    """Отдельная задача для авторизации Telethon"""
    await asyncio.sleep(2)
    
    try:
        await checker.client.connect()
        is_authorized = await checker.client.is_user_authorized()
        
        if not is_authorized:
            logger.info("Telethon not authorized, will request auth via bot")
            for admin_id in config.ADMIN_IDS:
                await bot.send_message(
                    admin_id,
                    "⚠️ <b>Требуется авторизация Telethon</b>\n\n"
                    "Сейчас начнется процесс авторизации.\n"
                    "Следуйте инструкциям бота.",
                    parse_mode="HTML"
                )
            await checker.start(
                phone_callback=auth_handler.phone_callback,
                code_callback=auth_handler.code_callback,
                password_callback=auth_handler.password_callback
            )
            for admin_id in config.ADMIN_IDS:
                await bot.send_message(
                    admin_id,
                    "✅ <b>Авторизация успешна!</b>\n\n"
                    "Telethon клиент подключен и готов к работе.",
                    parse_mode="HTML"
                )
        else:
            logger.info("Telethon already authorized")
            await checker.start(
                phone_callback=auth_handler.phone_callback,
                code_callback=auth_handler.code_callback,
                password_callback=auth_handler.password_callback
            )
            for admin_id in config.ADMIN_IDS:
                await bot.send_message(
                    admin_id,
                    "✅ <b>Бот запущен!</b>\n\n"
                    "Telethon клиент уже авторизован и готов к работе.",
                    parse_mode="HTML"
                )
    except Exception as e:
        logger.error(f"Error starting Telethon: {e}", exc_info=True)
        for admin_id in config.ADMIN_IDS:
            await bot.send_message(
                admin_id,
                f"❌ <b>Ошибка запуска Telethon</b>\n\n"
                f"<code>{str(e)}</code>",
                parse_mode="HTML"
            )

async def main():
    setup_logging()
    logger.info("Starting Telegram Username Monitor Bot...")
    
    if not config.BOT_TOKEN:
        logger.error("BOT_TOKEN not found in .env file!")
        return
    
    if not config.API_ID or not config.API_HASH:
        logger.error("API_ID or API_HASH not found in .env file!")
        return
    
    db = Database()
    await db.init_db()
    logger.info("Database initialized")
    
    bot = Bot(
        token=config.BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
    
    global auth_handler
    auth_handler = TelethonAuthHandler(bot, config.ADMIN_ID)
    
    checker = UsernameChecker(
        api_id=config.API_ID,
        api_hash=config.API_HASH,
        session_name=config.SESSION_NAME
    )
    
    dp = Dispatcher()
    
    auth_router = Router()
    
    @auth_router.message(F.from_user.id.in_(config.ADMIN_IDS))
    async def handle_auth_messages(message: Message):
        if auth_handler.is_waiting_phone():
            auth_handler.set_phone(message.text)
            await message.answer("✅ Номер телефона получен")
        elif auth_handler.is_waiting_code():
            auth_handler.set_code(message.text)
            await message.answer("✅ Код получен")
        elif auth_handler.is_waiting_password():
            auth_handler.set_password(message.text)
            await message.delete()
            await message.answer("✅ Пароль получен и удален из истории")
    
    dp.include_router(router)
    dp.include_router(auth_router)
    
    @router.message.middleware()
    async def inject_dependencies(handler, event, data):
        data['db'] = db
        data['checker'] = checker
        data['bot'] = bot
        data['auth_handler'] = auth_handler
        return await handler(event, data)
    
    @router.callback_query.middleware()
    async def inject_dependencies_callback(handler, event, data):
        data['db'] = db
        data['checker'] = checker
        data['bot'] = bot
        data['auth_handler'] = auth_handler
        return await handler(event, data)
    
    auth_task = asyncio.create_task(authorize_telethon(bot, checker, auth_handler))
    
    try:
        logger.info("Bot started successfully!")
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    except Exception as e:
        logger.error(f"Error in main loop: {e}", exc_info=True)
    finally:
        auth_task.cancel()
        await checker.stop()
        await bot.session.close()
        logger.info("Bot stopped")

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
