import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv('BOT_TOKEN')
API_ID = int(os.getenv('API_ID', 0))
API_HASH = os.getenv('API_HASH')
ADMIN_ID = int(os.getenv('ADMIN_ID', 0))

DB_PATH = 'usernames.db'
SESSION_NAME = 'checker_session'

CHECK_BATCH_SIZE = 50
CHECK_INTERVAL = 1
MAX_CONCURRENT_CHECKS = 20
CYCLE_DELAY = 5

LOG_FILE = 'logs/bot.log'
