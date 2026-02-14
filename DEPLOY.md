# Развертывание на Linux сервере

## Быстрый старт

### 1. Загрузка проекта на сервер

```bash
# Через git
git clone <repository_url>
cd username_cheker

# Или через scp
scp -r username_cheker/ user@server:/path/to/
```

### 2. Установка зависимостей

```bash
chmod +x setup.sh
./setup.sh
```

### 3. Настройка конфигурации

```bash
cp .env.example .env
nano .env
```

Заполните:
```env
BOT_TOKEN=your_bot_token
API_ID=your_api_id
API_HASH=your_api_hash
ADMIN_ID=your_telegram_id
```

### 4. Первый запуск (авторизация Telethon)

```bash
chmod +x start.sh
./start.sh
```

При первом запуске Telethon попросит:
- Номер телефона
- Код из Telegram
- Пароль 2FA (если включен)

После авторизации остановите бота (Ctrl+C).

---

## Запуск в фоновом режиме

### Вариант 1: Screen (простой)

```bash
# Установка screen
sudo apt install screen

# Запуск в screen
screen -S username_bot
./start.sh

# Отключиться: Ctrl+A, затем D
# Подключиться обратно: screen -r username_bot
```

### Вариант 2: Systemd (рекомендуется)

```bash
# Установка как системный сервис
chmod +x install_service.sh
./install_service.sh

# Запуск
sudo systemctl start username-monitor

# Проверка статуса
sudo systemctl status username-monitor

# Просмотр логов
sudo journalctl -u username-monitor -f
```

---

## Управление ботом

### Через скрипты

```bash
./start.sh    # Запуск
./stop.sh     # Остановка
```

### Через systemd

```bash
sudo systemctl start username-monitor     # Запуск
sudo systemctl stop username-monitor      # Остановка
sudo systemctl restart username-monitor   # Перезапуск
sudo systemctl status username-monitor    # Статус
```

### Просмотр логов

```bash
# Логи бота
tail -f logs/bot_*.log

# Системные логи (если через systemd)
sudo journalctl -u username-monitor -f
```

---

## Обновление бота

```bash
# Остановка
sudo systemctl stop username-monitor
# или
./stop.sh

# Обновление кода
git pull
# или загрузите новые файлы

# Обновление зависимостей
source venv/bin/activate
pip install -r requirements.txt --upgrade

# Запуск
sudo systemctl start username-monitor
# или
./start.sh
```

---

## Требования к серверу

### Минимальные

- **OS**: Ubuntu 20.04+ / Debian 10+ / CentOS 8+
- **RAM**: 512 MB
- **CPU**: 1 core
- **Disk**: 1 GB
- **Python**: 3.8+

### Рекомендуемые

- **RAM**: 1 GB+
- **CPU**: 2 cores
- **Disk**: 2 GB+

### Установка Python 3.10+ (если нужно)

```bash
# Ubuntu/Debian
sudo apt update
sudo apt install python3.10 python3.10-venv python3-pip

# CentOS/RHEL
sudo dnf install python3.10 python3-pip
```

---

## Безопасность

### Firewall

Бот не требует открытых портов (только исходящие соединения).

### Файлы с секретами

```bash
# Права доступа
chmod 600 .env
chmod 600 *.session

# Владелец
chown $USER:$USER .env *.session
```

### Автоматическое обновление системы

```bash
# Ubuntu/Debian
sudo apt install unattended-upgrades
sudo dpkg-reconfigure -plow unattended-upgrades
```

---

## Мониторинг

### Проверка работы бота

```bash
# Процесс запущен?
ps aux | grep bot.py

# Логи без ошибок?
tail -n 50 logs/bot_*.log | grep ERROR

# Systemd статус
sudo systemctl status username-monitor
```

### Автоматический перезапуск при падении

Systemd автоматически перезапускает бот (настроено в service файле).

### Уведомления о проблемах

Добавьте в crontab проверку:

```bash
crontab -e
```

```cron
# Проверка каждые 5 минут
*/5 * * * * /path/to/username_cheker/check_bot.sh
```

Создайте `check_bot.sh`:
```bash
#!/bin/bash
if ! pgrep -f "python bot.py" > /dev/null; then
    echo "Bot is down!" | mail -s "Username Bot Alert" your@email.com
fi
```

---

## Резервное копирование

### База данных

```bash
# Создание backup
cp usernames.db backups/usernames_$(date +%Y%m%d_%H%M%S).db

# Автоматический backup (crontab)
0 2 * * * cp /path/to/username_cheker/usernames.db /path/to/backups/usernames_$(date +\%Y\%m\%d).db
```

### Полный backup

```bash
tar -czf username_bot_backup_$(date +%Y%m%d).tar.gz \
    --exclude='venv' \
    --exclude='logs' \
    --exclude='__pycache__' \
    username_cheker/
```

---

## Устранение проблем

### Бот не запускается

```bash
# Проверка логов
cat logs/bot_*.log

# Проверка .env
cat .env

# Проверка зависимостей
source venv/bin/activate
pip list
```

### Ошибки авторизации Telethon

```bash
# Удалить сессию и авторизоваться заново
rm *.session
./start.sh
```

### Высокое использование CPU/RAM

```bash
# Мониторинг ресурсов
top -p $(pgrep -f bot.py)

# Уменьшите MAX_CONCURRENT_CHECKS в config.py
nano config.py
# MAX_CONCURRENT_CHECKS = 10
```

### База данных заблокирована

```bash
# Остановить бот
./stop.sh

# Проверить процессы
lsof usernames.db

# Перезапустить
./start.sh
```

---

## Производительность

### Оптимизация для больших баз (10000+ username)

В `config.py`:
```python
CHECK_BATCH_SIZE = 100
MAX_CONCURRENT_CHECKS = 30
CHECK_INTERVAL = 2
CYCLE_DELAY = 10
```

### Мониторинг производительности

```bash
# Время выполнения цикла
grep "Cycle completed" logs/bot_*.log | tail -5

# Количество проверок
grep "Checked batch" logs/bot_*.log | wc -l
```

---

## Поддержка

При проблемах соберите информацию:

```bash
# Версия Python
python3 --version

# Версия ОС
cat /etc/os-release

# Логи
tail -100 logs/bot_*.log

# Systemd статус
sudo systemctl status username-monitor
```

И создайте Issue в репозитории.
