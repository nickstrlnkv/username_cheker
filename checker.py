import asyncio
import logging
import os
from typing import List, Dict, Optional
from telethon import TelegramClient
from telethon.errors import UsernameInvalidError, UsernameNotOccupiedError, FloodWaitError
from telethon.tl.functions.contacts import ResolveUsernameRequest
import config

logger = logging.getLogger(__name__)

class UsernameChecker:
    def __init__(self, api_id: int, api_hash: str, session_name: str):
        self.api_id = api_id
        self.api_hash = api_hash
        self.session_name = session_name
        self.client = TelegramClient(session_name, api_id, api_hash)
        self.is_running = False
        self._check_task = None
        self.auth_callbacks = {
            'phone': None,
            'code': None,
            'password': None
        }
        
    async def start(self, phone_callback=None, code_callback=None, password_callback=None):
        self.auth_callbacks['phone'] = phone_callback
        self.auth_callbacks['code'] = code_callback
        self.auth_callbacks['password'] = password_callback
        
        await self.client.start(
            phone=phone_callback,
            code_callback=code_callback,
            password=password_callback
        )
        logger.info("Telethon client started")
    
    def is_authorized(self) -> bool:
        return self.client.is_connected() and self.client.is_user_authorized()
    
    async def stop(self):
        self.is_running = False
        if self._check_task:
            self._check_task.cancel()
        await self.client.disconnect()
        logger.info("Telethon client stopped")

    async def reset_session(self):
        await self.stop()

        session_file = f"{self.session_name}.session"
        session_journal = f"{self.session_name}.session-journal"

        for path in (session_file, session_journal):
            try:
                if os.path.exists(path):
                    os.remove(path)
            except OSError as e:
                logger.warning(f"Failed to remove session file {path}: {e}")

        self.client = TelegramClient(self.session_name, self.api_id, self.api_hash)
    
    async def check_username(self, username: str) -> str:
        username = username.lstrip('@').lower()
        
        try:
            await self.client(ResolveUsernameRequest(username))
            return 'occupied'
        except UsernameNotOccupiedError:
            return 'free'
        except UsernameInvalidError:
            return 'free'
        except FloodWaitError as e:
            logger.warning(f"FloodWait: need to wait {e.seconds} seconds")
            await asyncio.sleep(e.seconds)
            return 'error'
        except Exception as e:
            logger.error(f"Error checking @{username}: {e}")
            return 'error'
    
    async def check_usernames_batch(self, usernames: List[str]) -> Dict[str, str]:
        results = {}
        
        semaphore = asyncio.Semaphore(config.MAX_CONCURRENT_CHECKS)
        
        async def check_with_semaphore(username: str):
            async with semaphore:
                status = await self.check_username(username)
                results[username] = status
                await asyncio.sleep(0.1)
        
        tasks = [check_with_semaphore(username) for username in usernames]
        await asyncio.gather(*tasks, return_exceptions=True)
        
        return results
    
    async def start_monitoring(self, db, notification_callback):
        self.is_running = True
        logger.info("Monitoring started - entering main loop")
        
        while self.is_running:
            try:
                usernames = await db.get_usernames_for_check()
                
                if not usernames:
                    logger.info("No usernames to check, waiting...")
                    await asyncio.sleep(10)
                    continue
                
                logger.info(f"Starting check cycle for {len(usernames)} usernames")
                
                for i in range(0, len(usernames), config.CHECK_BATCH_SIZE):
                    if not self.is_running:
                        break
                    
                    batch = usernames[i:i + config.CHECK_BATCH_SIZE]
                    results = await self.check_usernames_batch(batch)
                    
                    for username, status in results.items():
                        old_status = await db.update_username_status(username, status)
                        
                        if old_status == 'occupied' and status == 'free':
                            logger.info(f"USERNAME FREED: @{username}")
                            await notification_callback(username)
                        elif old_status == 'unknown' and status == 'free':
                            logger.info(f"FREE USERNAME FOUND: @{username}")
                            await notification_callback(username)
                    
                    logger.info(f"Checked batch {i//config.CHECK_BATCH_SIZE + 1}/{(len(usernames)-1)//config.CHECK_BATCH_SIZE + 1}")
                    await asyncio.sleep(config.CHECK_INTERVAL)
                
                logger.info(f"Cycle completed. Waiting {config.CYCLE_DELAY} seconds before next cycle...")
                await asyncio.sleep(config.CYCLE_DELAY)
                
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}", exc_info=True)
                await asyncio.sleep(5)
        
        logger.info("Monitoring stopped")
    
    def stop_monitoring(self):
        self.is_running = False
        if self._check_task and not self._check_task.done():
            self._check_task.cancel()
            logger.info("Monitoring task cancelled")
