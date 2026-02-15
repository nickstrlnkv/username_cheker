from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def get_main_menu() -> InlineKeyboardMarkup:
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="▶ Старт", callback_data="start_monitoring"),
            InlineKeyboardButton(text="⏹ Стоп", callback_data="stop_monitoring")
        ],
        [
            InlineKeyboardButton(text="📥 Загрузить базу", callback_data="upload_db"),
            InlineKeyboardButton(text="📤 Выгрузить базу", callback_data="download_db")
        ],
        [
            InlineKeyboardButton(text="➕ Добавить username", callback_data="add_username"),
            InlineKeyboardButton(text="➖ Удалить username", callback_data="remove_username")
        ],
        [
            InlineKeyboardButton(text="📊 Статистика", callback_data="statistics"),
            InlineKeyboardButton(text="⚙ Настройки", callback_data="settings")
        ],
        [
            InlineKeyboardButton(text="🗑 Очистить базу", callback_data="clear_db")
        ]
    ])
    return keyboard

def get_settings_menu() -> InlineKeyboardMarkup:
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="⏱ Интервал проверки", callback_data="set_interval")
        ],
        [
            InlineKeyboardButton(text="📦 Размер батча", callback_data="set_batch_size")
        ],
        [
            InlineKeyboardButton(text="🔐 Перевойти Telethon", callback_data="reset_session")
        ],
        [
            InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_menu")
        ]
    ])
    return keyboard

def get_confirm_keyboard(action: str) -> InlineKeyboardMarkup:
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Да", callback_data=f"confirm_{action}"),
            InlineKeyboardButton(text="❌ Нет", callback_data="back_to_menu")
        ]
    ])
    return keyboard

def get_back_button() -> InlineKeyboardMarkup:
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_menu")]
    ])
    return keyboard
