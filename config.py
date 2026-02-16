import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv('BOT_TOKEN')
API_ID = int(os.getenv('API_ID', 0))
API_HASH = os.getenv('API_HASH')

admin_ids_str = os.getenv('ADMIN_ID', '0')
ADMIN_IDS = [int(id.strip()) for id in admin_ids_str.split(',') if id.strip()]
ADMIN_ID = ADMIN_IDS[0] if ADMIN_IDS else 0

DB_PATH = 'usernames.db'
SESSION_NAME = 'checker_session'

# Оптимальные настройки для избежания FloodWait
# Рекомендуемые значения для стабильной работы:
# - MAX_CONCURRENT_CHECKS: 3-5 (безопасно), 5-10 (умеренно), 10-20 (агрессивно)
# - CHECK_INTERVAL: 2-5 секунд между батчами
# - CHECK_BATCH_SIZE: 20-50 username в батче
# - CYCLE_DELAY: 10-30 секунд между полными циклами

CHECK_BATCH_SIZE = 30  # Уменьшено с 50 для более плавной работы
CHECK_INTERVAL = 3  # Увеличено с 1 до 3 секунд между батчами
MAX_CONCURRENT_CHECKS = 5  # Уменьшено с 20 до 5 для избежания FloodWait
CYCLE_DELAY = 15  # Увеличено с 5 до 15 секунд между полными циклами

LOG_FILE = 'logs/bot.log'
