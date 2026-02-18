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
    logger.info("authorize_telethon called (delay=%s, prompt_admin_id=%s)", delay, prompt_admin_id)
    if auth_handler.is_auth_in_progress():
        logger.info("Authorization already in progress, skipping")
        return

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

        logger.info("Authorization target admins: %s", target_admin_ids)

        logger.info("Connecting Telethon client...")
        await checker.client.connect()
        is_authorized = await checker.client.is_user_authorized()
        logger.info("Telethon is_authorized=%s", is_authorized)

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
            auth_handler.set_prompt_admin_ids(target_admin_ids)
            logger.info("Starting Telethon client with auth callbacks...")
            await checker.start(
                phone_callback=auth_handler.phone_callback,
                code_callback=auth_handler.code_callback,
                password_callback=auth_handler.password_callback
            )
            logger.info("Telethon client started after authorization")
            for admin_id in target_admin_ids:
                await bot.send_message(
                    admin_id,
                    "✅ <b>Авторизация успешна!</b>\n\n"
                    "Telethon клиент подключен и готов к работе.",
                    parse_mode="HTML"
                )
        else:
            logger.info("Telethon already authorized")
            logger.info("Starting Telethon client (already authorized)...")
            await checker.start(
                phone_callback=auth_handler.phone_callback,
                code_callback=auth_handler.code_callback,
                password_callback=auth_handler.password_callback
            )
            logger.info("Telethon client started (already authorized)")
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
