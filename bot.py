import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

import config
from database import Database
from checker import UsernameChecker
from handlers import router
from utils import setup_logging

logger = logging.getLogger(__name__)

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
    
    checker = UsernameChecker(
        api_id=config.API_ID,
        api_hash=config.API_HASH,
        session_name=config.SESSION_NAME
    )
    await checker.start()
    
    bot = Bot(
        token=config.BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
    
    dp = Dispatcher()
    dp.include_router(router)
    
    @router.message.middleware()
    async def inject_dependencies(handler, event, data):
        data['db'] = db
        data['checker'] = checker
        data['bot'] = bot
        return await handler(event, data)
    
    @router.callback_query.middleware()
    async def inject_dependencies_callback(handler, event, data):
        data['db'] = db
        data['checker'] = checker
        data['bot'] = bot
        return await handler(event, data)
    
    try:
        logger.info("Bot started successfully!")
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    except Exception as e:
        logger.error(f"Error in main loop: {e}", exc_info=True)
    finally:
        await checker.stop()
        await bot.session.close()
        logger.info("Bot stopped")

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
