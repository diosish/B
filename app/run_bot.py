#!/usr/bin/env python3
"""
Скрипт для запуска Telegram бота
"""

import asyncio
import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from telegram_bot import start_polling

if __name__ == "__main__":
    print("🤖 Запуск Telegram бота...")
    print("Нажмите Ctrl+C для остановки")

    try:
        asyncio.run(start_polling())
    except KeyboardInterrupt:
        print("\n👋 Бот остановлен")