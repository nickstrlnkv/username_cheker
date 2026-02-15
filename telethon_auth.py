import asyncio
import logging
from typing import Iterable, Optional

logger = logging.getLogger(__name__)

async def authorize_telethon(
    bot,
    checker,
    auth_handler,
    admin_ids: Iterable[int],
    prompt_admin_id: Optional[int] = None,
    delay: float = 2.0
):
    """Authorize Telethon via bot messages."""
    auth_handler.set_auth_in_progress(True)
    try:
        if delay:
            await asyncio.sleep(delay)

        target_admin_ids = list(admin_ids)
        if prompt_admin_id is not None:
            auth_handler.set_admin_id(prompt_admin_id)
            target_admin_ids = [prompt_admin_id]
        elif target_admin_ids:
            auth_handler.set_admin_id(target_admin_ids[0])

        await checker.client.connect()
        is_authorized = await checker.client.is_user_authorized()

        if not is_authorized:
            logger.info("Telethon not authorized, will request auth via bot")
            for admin_id in target_admin_ids:
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
            for admin_id in target_admin_ids:
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
            for admin_id in target_admin_ids:
                await bot.send_message(
                    admin_id,
                    "✅ <b>Бот запущен!</b>\n\n"
                    "Telethon клиент уже авторизован и готов к работе.",
                    parse_mode="HTML"
                )
    except Exception as e:
        logger.error(f"Error starting Telethon: {e}", exc_info=True)
        for admin_id in target_admin_ids:
            await bot.send_message(
                admin_id,
                f"❌ <b>Ошибка запуска Telethon</b>\n\n"
                f"<code>{str(e)}</code>",
                parse_mode="HTML"
            )
    finally:
        auth_handler.set_auth_in_progress(False)

async def ensure_authorized(
    bot,
    checker,
    auth_handler,
    admin_ids: Iterable[int],
    prompt_admin_id: Optional[int] = None
) -> bool:
    if auth_handler.is_auth_in_progress():
        return False

    await checker.client.connect()
    is_authorized = await checker.client.is_user_authorized()

    if is_authorized:
        return True

    auth_handler.set_auth_in_progress(True)
    asyncio.create_task(
        authorize_telethon(
            bot,
            checker,
            auth_handler,
            admin_ids,
            prompt_admin_id=prompt_admin_id,
            delay=0
        )
    )
    return False
