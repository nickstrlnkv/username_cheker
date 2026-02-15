import asyncio
import logging
from aiogram import Bot
from aiogram.fsm.context import FSMContext

logger = logging.getLogger(__name__)

class TelethonAuthHandler:
    def __init__(self, bot: Bot, admin_id: int):
        self.bot = bot
        self.admin_id = admin_id
        self.phone_future = None
        self.code_future = None
        self.password_future = None

    def set_admin_id(self, admin_id: int):
        self.admin_id = admin_id
        
    async def phone_callback(self):
        self.phone_future = asyncio.Future()
        
        await self.bot.send_message(
            self.admin_id,
            "📱 <b>Авторизация Telethon</b>\n\n"
            "Отправьте ваш номер телефона в международном формате.\n"
            "Пример: +79991234567",
            parse_mode="HTML"
        )
        
        phone = await self.phone_future
        logger.info(f"Phone received: {phone[:5]}***")
        return phone
    
    async def code_callback(self):
        self.code_future = asyncio.Future()
        
        await self.bot.send_message(
            self.admin_id,
            "🔐 <b>Код подтверждения</b>\n\n"
            "Отправьте код, который пришел вам в Telegram.",
            parse_mode="HTML"
        )
        
        code = await self.code_future
        logger.info("Code received")
        return code
    
    async def password_callback(self):
        self.password_future = asyncio.Future()
        
        await self.bot.send_message(
            self.admin_id,
            "🔒 <b>Двухфакторная аутентификация</b>\n\n"
            "Отправьте ваш пароль 2FA.\n\n"
            "⚠️ Сообщение с паролем будет автоматически удалено!",
            parse_mode="HTML"
        )
        
        password = await self.password_future
        logger.info("Password received")
        return password
    
    def set_phone(self, phone: str):
        if self.phone_future and not self.phone_future.done():
            self.phone_future.set_result(phone)
    
    def set_code(self, code: str):
        if self.code_future and not self.code_future.done():
            self.code_future.set_result(code)
    
    def set_password(self, password: str):
        if self.password_future and not self.password_future.done():
            self.password_future.set_result(password)
    
    def is_waiting_phone(self) -> bool:
        return self.phone_future is not None and not self.phone_future.done()
    
    def is_waiting_code(self) -> bool:
        return self.code_future is not None and not self.code_future.done()
    
    def is_waiting_password(self) -> bool:
        return self.password_future is not None and not self.password_future.done()
