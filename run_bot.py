import asyncio
import sys
import os

# Добавляем текущую директорию в sys.path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from telegram_bot import start_polling
except ImportError:
    print("❌ Error: telegram_bot module not found")
    print("📁 Current directory:", os.getcwd())
    print("📁 Python path:", sys.path)
    sys.exit(1)

if __name__ == "__main__":
    print("🤖 Запуск Telegram бота...")
    print("Нажмите Ctrl+C для остановки")

    try:
        asyncio.run(start_polling())
    except KeyboardInterrupt:
        print("\n👋 Бот остановлен")
    except Exception as e:
        print(f"❌ Ошибка запуска бота: {e}")
        sys.exit(1)