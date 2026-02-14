#!/bin/bash

echo "=== Telegram Username Monitor Bot - Status Check ==="
echo ""

# Проверка процесса
if pgrep -f "python bot.py" > /dev/null; then
    PID=$(pgrep -f "python bot.py")
    echo "✅ Bot is running (PID: $PID)"
    
    # Использование ресурсов
    echo ""
    echo "Resource usage:"
    ps -p $PID -o %cpu,%mem,etime,cmd
else
    echo "❌ Bot is NOT running"
fi

echo ""

# Проверка файлов
if [ -f ".env" ]; then
    echo "✅ .env file exists"
else
    echo "❌ .env file missing"
fi

if [ -d "venv" ]; then
    echo "✅ Virtual environment exists"
else
    echo "❌ Virtual environment missing"
fi

if [ -f "usernames.db" ]; then
    DB_SIZE=$(du -h usernames.db | cut -f1)
    echo "✅ Database exists (size: $DB_SIZE)"
else
    echo "⚠️  Database not created yet"
fi

echo ""

# Последние логи
if [ -d "logs" ]; then
    LATEST_LOG=$(ls -t logs/bot_*.log 2>/dev/null | head -1)
    if [ -n "$LATEST_LOG" ]; then
        echo "Latest log entries:"
        echo "---"
        tail -5 "$LATEST_LOG"
    fi
else
    echo "⚠️  No logs directory"
fi
