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
            InlineKeyboardButton(text="💬 Настройки спама", callback_data="spam_settings")
        ],
        [
            InlineKeyboardButton(text="🔐 Перевойти Telethon", callback_data="reset_session")
        ],
        [
            InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_menu")
        ]
    ])
    return keyboard

def get_spam_settings_menu() -> InlineKeyboardMarkup:
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="⏱ Задержка между сообщениями", callback_data="set_spam_delay")
        ],
        [
            InlineKeyboardButton(text="🔢 Количество сообщений", callback_data="set_spam_count")
        ],
        [
            InlineKeyboardButton(text="🔄 Режим спама", callback_data="set_spam_mode")
        ],
        [
            InlineKeyboardButton(text="🔙 Назад", callback_data="settings")
        ]
    ])
    return keyboard

def get_spam_mode_keyboard() -> InlineKeyboardMarkup:
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🔢 Указать количество", callback_data="spam_mode_count")
        ],
        [
            InlineKeyboardButton(text="♾ До занятия username", callback_data="spam_mode_until")
        ],
        [
            InlineKeyboardButton(text="🔙 Назад", callback_data="spam_settings")
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
