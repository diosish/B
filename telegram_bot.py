# ===== telegram_bot.py (новый файл в корне проекта) =====
import asyncio
import httpx
import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
WEBAPP_URL = os.getenv("WEBAPP_URL")


class TelegramBot:
    def __init__(self, token: str):
        self.token = token
        self.base_url = f"https://api.telegram.org/bot{token}"

    async def send_message(self, chat_id: int, text: str, reply_markup=None):
        """Отправка сообщения"""
        async with httpx.AsyncClient() as client:
            url = f"{self.base_url}/sendMessage"
            data = {
                "chat_id": chat_id,
                "text": text,
                "parse_mode": "HTML"
            }
            if reply_markup:
                data["reply_markup"] = reply_markup

            response = await client.post(url, json=data)
            return response.json()

    async def send_webapp_button(self, chat_id: int, text: str, webapp_url: str):
        """Отправка кнопки с WebApp"""
        keyboard = {
            "inline_keyboard": [[{
                "text": "🚀 Открыть приложение",
                "web_app": {"url": webapp_url}
            }]]
        }

        return await self.send_message(chat_id, text, keyboard)

    async def set_webhook(self, webhook_url: str):
        """Установка webhook"""
        async with httpx.AsyncClient() as client:
            url = f"{self.base_url}/setWebhook"
            data = {"url": webhook_url}
            response = await client.post(url, json=data)
            return response.json()

    async def get_updates(self, offset=None):
        """Получение обновлений (для polling)"""
        async with httpx.AsyncClient() as client:
            url = f"{self.base_url}/getUpdates"
            params = {"timeout": 10}
            if offset:
                params["offset"] = offset

            response = await client.get(url, params=params)
            return response.json()


# Обработчик команд
async def handle_start_command(chat_id: int, first_name: str = ""):
    bot = TelegramBot(BOT_TOKEN)

    welcome_text = f"""
🎉 <b>Добро пожаловать, {first_name}!</b>

Это система регистрации оплачиваемых волонтёров.

<b>Что вы можете делать:</b>
• 👥 Зарегистрироваться как волонтёр 
• 🏢 Стать организатором мероприятий
• 📅 Найти подходящие мероприятия
• 💰 Получать оплату за участие

Нажмите кнопку ниже, чтобы начать!
    """

    await bot.send_webapp_button(chat_id, welcome_text, WEBAPP_URL)


async def handle_volunteer_profile_command(chat_id: int):
    """Обработка команды /volunteer_profile"""
    bot = TelegramBot(BOT_TOKEN)
    await bot.send_webapp_button(chat_id, "👥 Профиль волонтёра", f"{WEBAPP_URL}/volunteer/profile")


async def handle_organizer_profile_command(chat_id: int):
    """Обработка команды /organizer_profile"""
    bot = TelegramBot(BOT_TOKEN)
    await bot.send_webapp_button(chat_id, "🏢 Профиль организатора", f"{WEBAPP_URL}/organizer/profile")


# Простой polling бот
async def start_polling():
    bot = TelegramBot(BOT_TOKEN)
    offset = None

    print(f"🤖 Бот запущен! WebApp URL: {WEBAPP_URL}")

    while True:
        try:
            updates = await bot.get_updates(offset)

            if updates.get("ok") and updates.get("result"):
                for update in updates["result"]:
                    offset = update["update_id"] + 1

                    # Обработка команд
                    if "message" in update and "text" in update["message"]:
                        message = update["message"]
                        chat_id = message["chat"]["id"]
                        text = message["text"]
                        first_name = message["from"].get("first_name", "")

                        if text.startswith("/start"):
                            await handle_start_command(chat_id, first_name)
                        elif text == "/help":
                            help_text = """
🆘 <b>Помощь</b>

Доступные команды:
/start - Запустить приложение
/help - Показать эту справку
/volunteer_profile - Открыть профиль волонтёра
/organizer_profile - Открыть профиль организатора

Для работы с системой используйте кнопку "Открыть приложение"
                            """
                            await bot.send_message(chat_id, help_text)
                        elif text == "/volunteer_profile":
                            await handle_volunteer_profile_command(chat_id)
                        elif text == "/organizer_profile":
                            await handle_organizer_profile_command(chat_id)

        except Exception as e:
            print(f"Ошибка в боте: {e}")
            await asyncio.sleep(5)


if __name__ == "__main__":
    asyncio.run(start_polling())

# ===== app/auth.py (обновленный) =====
import hashlib
import hmac
import json
from urllib.parse import parse_qsl, unquote
from fastapi import HTTPException, Header
from typing import Optional
import os


def verify_telegram_auth(init_data: str) -> dict:
    """Проверка подлинности данных Telegram WebApp"""
    try:
        # Парсинг init_data
        parsed_data = dict(parse_qsl(init_data))

        # Извлечение hash
        hash_value = parsed_data.pop('hash', None)
        if not hash_value:
            raise ValueError("Hash not found")

        # Создание строки для проверки
        data_check_string = '\n'.join([f"{k}={v}" for k, v in sorted(parsed_data.items())])

        # Создание secret key
        bot_token = os.getenv("BOT_TOKEN")
        if not bot_token:
            raise ValueError("BOT_TOKEN not set")

        secret_key = hmac.new(
            "WebAppData".encode(),
            bot_token.encode(),
            hashlib.sha256
        ).digest()

        # Проверка подписи
        calculated_hash = hmac.new(
            secret_key,
            data_check_string.encode(),
            hashlib.sha256
        ).hexdigest()

        # В разработке можем упростить проверку
        if os.getenv("ENVIRONMENT") == "development":
            print("⚠️ Режим разработки: пропуск проверки подписи")
        elif calculated_hash != hash_value:
            raise ValueError("Invalid signature")

        # Извлечение данных пользователя
        user_data = parsed_data.get('user')
        if not user_data:
            raise ValueError("User data not found")

        user_info = json.loads(unquote(user_data))

        return {
            'id': user_info.get('id'),
            'first_name': user_info.get('first_name', ''),
            'last_name': user_info.get('last_name', ''),
            'username': user_info.get('username', ''),
            'language_code': user_info.get('language_code', 'ru'),
            'is_premium': user_info.get('is_premium', False)
        }

    except Exception as e:
        print(f"Auth error: {e}")
        # В разработке возвращаем тестовые данные
        if os.getenv("ENVIRONMENT") == "development":
            return {
                'id': 123456789,
                'first_name': 'Test',
                'last_name': 'User',
                'username': 'testuser',
                'language_code': 'ru',
                'is_premium': False
            }
        raise HTTPException(status_code=401, detail="Invalid auth data")


def get_telegram_user(authorization: Optional[str] = Header(None)):
    """Получение данных пользователя из заголовка"""
    if not authorization:
        raise HTTPException(status_code=401, detail="Authorization header required")

    return verify_telegram_auth(authorization)

