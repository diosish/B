# app/telegram_bot.py - Исправленная версия
import asyncio
import httpx
import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
WEBAPP_URL = os.getenv("WEBAPP_URL")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin123")


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
                "parse_mode": "HTML",
                "disable_web_page_preview": True
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


def is_admin_user(telegram_id: int) -> bool:
    """Проверка, является ли пользователь администратором"""
    admin_ids_str = os.getenv("ADMIN_TELEGRAM_IDS", "123456789")
    admin_ids = [int(id_str.strip()) for id_str in admin_ids_str.split(",") if id_str.strip()]
    return telegram_id in admin_ids


# Обработчики команд
async def handle_start_command(chat_id: int, first_name: str = ""):
    """Обработка команды /start"""
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

    await bot.send_webapp_button(chat_id, welcome_text.strip(), WEBAPP_URL)


async def handle_admin_command(chat_id: int, user_id: int):
    """Обработка команды /admin"""
    bot = TelegramBot(BOT_TOKEN)

    # Проверяем, является ли пользователь администратором
    if not is_admin_user(user_id):
        await bot.send_message(chat_id, "❌ У вас нет прав администратора.")
        return

    # Импортируем admin_auth только здесь, чтобы избежать циклических импортов
    try:
        from .admin_auth import admin_auth
        # Генерируем токен
        admin_token = admin_auth.generate_bot_token()
    except ImportError:
        print("❌ Failed to import admin_auth")
        await bot.send_message(chat_id, "❌ Ошибка системы администрирования.")
        return

    # Создаем ссылку на админ панель
    admin_url = f"{WEBAPP_URL}/admin/login?token={admin_token}"

    admin_text = f"""
🔐 <b>Доступ к админ панели</b>

Ваша ссылка для входа в админ панель:
<a href="{admin_url}">🚀 Войти в админ панель</a>

⚠️ <b>Важно:</b>
• Ссылка действительна 2 часа
• Не передавайте ссылку третьим лицам
• После входа используйте логин и пароль

<b>Логин:</b> <code>admin</code>
<b>Пароль:</b> <code>{ADMIN_PASSWORD}</code>

<i>Если кнопка не работает, скопируйте ссылку:</i>
<code>{admin_url}</code>
    """

    await bot.send_message(chat_id, admin_text.strip())


async def handle_help_command(chat_id: int):
    """Обработка команды /help"""
    bot = TelegramBot(BOT_TOKEN)

    help_text = """
🆘 <b>Помощь</b>

<b>Доступные команды:</b>
/start - Запустить приложение
/help - Показать эту справку
/volunteer - Открыть профиль волонтёра
/organizer - Открыть профиль организатора

<b>Для администраторов:</b>
/admin - Получить доступ к админ панели

Для работы с системой используйте кнопку "Открыть приложение"
    """

    await bot.send_message(chat_id, help_text.strip())


async def handle_volunteer_command(chat_id: int):
    """Обработка команды /volunteer"""
    bot = TelegramBot(BOT_TOKEN)
    await bot.send_webapp_button(
        chat_id,
        "👥 Профиль волонтёра",
        f"{WEBAPP_URL}/volunteer/profile"
    )


async def handle_organizer_command(chat_id: int):
    """Обработка команды /organizer"""
    bot = TelegramBot(BOT_TOKEN)
    await bot.send_webapp_button(
        chat_id,
        "🏢 Профиль организатора",
        f"{WEBAPP_URL}/organizer/profile"
    )


# Основной цикл бота
async def start_polling():
    """Запуск бота в режиме polling"""
    bot = TelegramBot(BOT_TOKEN)
    offset = None

    print(f"🤖 Бот запущен! WebApp URL: {WEBAPP_URL}")
    print(f"🔐 Админ пароль: {ADMIN_PASSWORD}")

    while True:
        try:
            updates = await bot.get_updates(offset)

            if updates.get("ok") and updates.get("result"):
                for update in updates["result"]:
                    offset = update["update_id"] + 1

                    # Обработка сообщений
                    if "message" in update and "text" in update["message"]:
                        message = update["message"]
                        chat_id = message["chat"]["id"]
                        user_id = message["from"]["id"]
                        text = message["text"]
                        first_name = message["from"].get("first_name", "")

                        print(f"📨 Получено сообщение от {user_id}: {text}")

                        # Обработка команд
                        if text.startswith("/start"):
                            await handle_start_command(chat_id, first_name)
                        elif text == "/admin":
                            await handle_admin_command(chat_id, user_id)
                        elif text == "/help":
                            await handle_help_command(chat_id)
                        elif text == "/volunteer":
                            await handle_volunteer_command(chat_id)
                        elif text == "/organizer":
                            await handle_organizer_command(chat_id)
                        else:
                            # Неизвестная команда
                            await bot.send_message(
                                chat_id,
                                "❓ Неизвестная команда. Используйте /help для справки."
                            )

        except Exception as e:
            print(f"❌ Ошибка в боте: {e}")
            await asyncio.sleep(5)


if __name__ == "__main__":
    asyncio.run(start_polling())