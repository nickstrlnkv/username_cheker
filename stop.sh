#!/bin/bash

echo "Stopping Telegram Username Monitor Bot..."

PID=$(pgrep -f "python bot.py")

if [ -z "$PID" ]; then
    echo "Bot is not running"
else
    kill $PID
    echo "Bot stopped (PID: $PID)"
fi
