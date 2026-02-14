import logging
import os
from datetime import datetime

def setup_logging():
    os.makedirs('logs', exist_ok=True)
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(
                f'logs/bot_{datetime.now().strftime("%Y%m%d")}.log',
                encoding='utf-8'
            ),
            logging.StreamHandler()
        ]
    )
    
    logging.getLogger('telethon').setLevel(logging.WARNING)
    logging.getLogger('aiogram').setLevel(logging.INFO)

def parse_username(username: str) -> str:
    return username.lstrip('@').lower().strip()

def format_username(username: str) -> str:
    return f"@{parse_username(username)}"
