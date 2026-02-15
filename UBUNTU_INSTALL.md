# Установка бота на Ubuntu сервер

Полная инструкция по развертыванию Telegram Username Monitor Bot на Ubuntu 20.04/22.04/24.04.

---

## Требования

- Ubuntu 20.04 или новее
- Доступ по SSH
- Права sudo
- Минимум 512 MB RAM
- Python 3.8+

---

## Шаг 1: Подключение к серверу

```bash
ssh user@your-server-ip
```

---

## Шаг 2: Обновление системы

```bash
sudo apt update
sudo apt upgrade -y
```

---

## Шаг 3: Установка Python и зависимостей

### Проверка версии Python

```bash
python3 --version
```

Должна быть версия 3.8 или выше.

### Установка необходимых пакетов

```bash
sudo apt install -y python3 python3-pip python3-venv git
```

---

## Шаг 4: Клонирование репозитория

```bash
cd ~
git clone https://github.com/nickstrlnkv/username_cheker.git
cd username_cheker
```

Или загрузите через scp:

```bash
# На вашем локальном ПК
scp -r username_cheker/ user@your-server-ip:~/
```

---

## Шаг 5: Создание виртуального окружения

```bash
python3 -m venv venv
source venv/bin/activate
```

Вы увидите `(venv)` в начале строки.

---

## Шаг 6: Установка зависимостей

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

Подождите 1-2 минуты, пока установятся все библиотеки.

---

## Шаг 7: Настройка конфигурации

### Создание .env файла

```bash
cp .env.example .env
nano .env
```

### Заполнение данных

```env
BOT_TOKEN=123456789:ABCdefGHIjklMNOpqrsTUVwxyz
API_ID=12345678
API_HASH=abcdef1234567890abcdef1234567890
ADMIN_ID=123456789
```

**Где взять:**
- `BOT_TOKEN`: [@BotFather](https://t.me/BotFather) → `/newbot`
- `API_ID` и `API_HASH`: https://my.telegram.org → API development tools
- `ADMIN_ID`: [@userinfobot](https://t.me/userinfobot)

**Сохранение:**
- Нажмите `Ctrl+O` (сохранить)
- Нажмите `Enter`
- Нажмите `Ctrl+X` (выход)

---

## Шаг 8: Первый запуск и авторизация

```bash
python bot.py
```

### Авторизация через Telegram

1. Бот отправит вам сообщение: **"⚠️ Требуется авторизация Telethon"**
2. Следуйте инструкциям в Telegram:
   - Отправьте номер телефона: `+79991234567`
   - Отправьте код из Telegram
   - Если есть 2FA - отправьте пароль

3. После успешной авторизации увидите:
   ```
   ✅ Авторизация успешна!
   Telethon клиент подключен и готов к работе.
   ```

4. Остановите бота: `Ctrl+C`

---

## Шаг 9: Запуск в фоновом режиме

### Вариант 1: Screen (простой способ)

#### Установка screen

```bash
sudo apt install screen -y
```

#### Запуск бота в screen

```bash
screen -S username_bot
python bot.py
```

#### Отключение от screen

Нажмите `Ctrl+A`, затем `D`

#### Подключение обратно

```bash
screen -r username_bot
```

#### Остановка бота

```bash
screen -r username_bot
# Нажмите Ctrl+C
# Затем exit
```

---

### Вариант 2: Systemd (рекомендуется для 24/7)

#### Создание systemd сервиса

```bash
sudo nano /etc/systemd/system/username-monitor.service
```

#### Содержимое файла

```ini
[Unit]
Description=Telegram Username Monitor Bot
After=network.target

[Service]
Type=simple
User=YOUR_USERNAME
WorkingDirectory=/home/YOUR_USERNAME/username_cheker
Environment="PATH=/home/YOUR_USERNAME/username_cheker/venv/bin"
ExecStart=/home/YOUR_USERNAME/username_cheker/venv/bin/python /home/YOUR_USERNAME/username_cheker/bot.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

**Замените:**
- `YOUR_USERNAME` на ваше имя пользователя (узнать: `whoami`)

**Сохранение:**
- `Ctrl+O` → `Enter` → `Ctrl+X`

#### Активация сервиса

```bash
# Перезагрузка конфигурации systemd
sudo systemctl daemon-reload

# Включение автозапуска
sudo systemctl enable username-monitor

# Запуск бота
sudo systemctl start username-monitor

# Проверка статуса
sudo systemctl status username-monitor
```

#### Управление сервисом

```bash
# Запуск
sudo systemctl start username-monitor

# Остановка
sudo systemctl stop username-monitor

# Перезапуск
sudo systemctl restart username-monitor

# Статус
sudo systemctl status username-monitor

# Просмотр логов
sudo journalctl -u username-monitor -f

# Последние 100 строк логов
sudo journalctl -u username-monitor -n 100
```

---

## Шаг 10: Проверка работы

### Открытие бота в Telegram

1. Найдите вашего бота по username
2. Отправьте `/start`
3. Должно появиться меню с кнопками

### Добавление тестовых username

1. Нажмите **"➕ Добавить username"**
2. Отправьте: `telegram durov username`
3. Нажмите **"📊 Статистика"** - должны увидеть 3 username

### Запуск мониторинга

1. Нажмите **"▶ Старт"**
2. Бот начнет проверку
3. В логах увидите:
   ```
   INFO - Monitoring started
   INFO - Starting check cycle for 3 usernames
   ```

---

## Автоматическое обновление

### Создание скрипта обновления

```bash
nano ~/update_bot.sh
```

```bash
#!/bin/bash
cd ~/username_cheker
git pull
source venv/bin/activate
pip install -r requirements.txt --upgrade
sudo systemctl restart username-monitor
echo "Bot updated and restarted!"
```

```bash
chmod +x ~/update_bot.sh
```

### Использование

```bash
~/update_bot.sh
```

---

## Резервное копирование

### Создание backup базы данных

```bash
# Создание папки для backup
mkdir -p ~/backups

# Копирование базы
cp ~/username_cheker/usernames.db ~/backups/usernames_$(date +%Y%m%d_%H%M%S).db
```

### Автоматический backup (crontab)

```bash
crontab -e
```

Добавьте строку (backup каждый день в 3:00):

```cron
0 3 * * * cp ~/username_cheker/usernames.db ~/backups/usernames_$(date +\%Y\%m\%d).db
```

---

## Мониторинг и логи

### Просмотр логов бота

```bash
# Логи в реальном времени
tail -f ~/username_cheker/logs/bot_*.log

# Последние 50 строк
tail -50 ~/username_cheker/logs/bot_*.log

# Поиск ошибок
grep ERROR ~/username_cheker/logs/bot_*.log
```

### Просмотр системных логов (systemd)

```bash
# В реальном времени
sudo journalctl -u username-monitor -f

# Последние 100 строк
sudo journalctl -u username-monitor -n 100

# Логи за сегодня
sudo journalctl -u username-monitor --since today
```

### Проверка использования ресурсов

```bash
# Процессы Python
ps aux | grep python

# Использование памяти и CPU
top -p $(pgrep -f bot.py)

# Размер базы данных
du -h ~/username_cheker/usernames.db
```

---

## Безопасность

### Настройка firewall (UFW)

```bash
# Установка UFW
sudo apt install ufw -y

# Разрешить SSH
sudo ufw allow 22/tcp

# Включить firewall
sudo ufw enable

# Проверка статуса
sudo ufw status
```

**Примечание:** Бот не требует открытых портов (только исходящие соединения).

### Права доступа к файлам

```bash
# Ограничение доступа к .env
chmod 600 ~/username_cheker/.env

# Ограничение доступа к session файлу
chmod 600 ~/username_cheker/*.session
```

### Автоматические обновления безопасности

```bash
sudo apt install unattended-upgrades -y
sudo dpkg-reconfigure -plow unattended-upgrades
```

---

## Устранение проблем

### Бот не запускается

```bash
# Проверка логов
sudo journalctl -u username-monitor -n 50

# Проверка .env файла
cat ~/username_cheker/.env

# Проверка зависимостей
source ~/username_cheker/venv/bin/activate
pip list
```

### Ошибка авторизации Telethon

```bash
# Удаление старой сессии
rm ~/username_cheker/*.session

# Перезапуск бота
sudo systemctl restart username-monitor

# Проверка логов - бот запросит новую авторизацию
sudo journalctl -u username-monitor -f
```

### База данных заблокирована

```bash
# Остановка бота
sudo systemctl stop username-monitor

# Проверка процессов
lsof ~/username_cheker/usernames.db

# Перезапуск
sudo systemctl start username-monitor
```

### Высокое использование CPU/RAM

Отредактируйте `config.py`:

```bash
nano ~/username_cheker/config.py
```

Уменьшите значения:

```python
CHECK_BATCH_SIZE = 30
MAX_CONCURRENT_CHECKS = 10
```

Перезапустите бота:

```bash
sudo systemctl restart username-monitor
```

---

## Полезные команды

### Проверка статуса бота

```bash
# Статус сервиса
sudo systemctl status username-monitor

# Запущен ли процесс
pgrep -f bot.py

# Использование ресурсов
ps aux | grep bot.py
```

### Остановка и запуск

```bash
# Остановка
sudo systemctl stop username-monitor

# Запуск
sudo systemctl start username-monitor

# Перезапуск
sudo systemctl restart username-monitor
```

### Просмотр файлов

```bash
# Список файлов проекта
ls -lah ~/username_cheker/

# Размер базы данных
du -h ~/username_cheker/usernames.db

# Логи
ls -lah ~/username_cheker/logs/
```

---

## Обновление бота

### Через Git

```bash
cd ~/username_cheker
git pull
source venv/bin/activate
pip install -r requirements.txt --upgrade
sudo systemctl restart username-monitor
```

### Проверка версии

```bash
cd ~/username_cheker
git log -1
```

---

## Удаление бота

```bash
# Остановка и отключение сервиса
sudo systemctl stop username-monitor
sudo systemctl disable username-monitor
sudo rm /etc/systemd/system/username-monitor.service
sudo systemctl daemon-reload

# Удаление файлов
rm -rf ~/username_cheker

# Удаление backups (опционально)
rm -rf ~/backups
```

---

## Дополнительная информация

### Документация

- **README.md** - Общая информация
- **DEPLOY.md** - Подробное развертывание
- **QUICKSTART.md** - Быстрый старт
- **ADMINS.md** - Управление администраторами

### Поддержка

При возникновении проблем:

1. Проверьте логи: `sudo journalctl -u username-monitor -n 100`
2. Проверьте статус: `sudo systemctl status username-monitor`
3. Создайте Issue на GitHub с описанием проблемы и логами

---

## Чек-лист установки

- [ ] Подключение к серверу по SSH
- [ ] Обновление системы
- [ ] Установка Python 3.8+
- [ ] Клонирование репозитория
- [ ] Создание venv
- [ ] Установка зависимостей
- [ ] Создание и настройка .env
- [ ] Первый запуск и авторизация Telethon
- [ ] Настройка systemd сервиса
- [ ] Проверка работы бота
- [ ] Настройка автоматического backup
- [ ] Настройка firewall

---

**Готово!** 🎉 Бот установлен и работает 24/7 на вашем Ubuntu сервере.
