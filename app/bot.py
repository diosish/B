import httpx
import asyncio
from typing import Optional
import os


class TelegramBot:
    def __init__(self, token: str):
        self.token = token
        self.base_url = f"https://api.telegram.org/bot{token}"

    async def send_message(self, chat_id: int, text: str):
        """Отправка сообщения"""
        async with httpx.AsyncClient() as client:
            url = f"{self.base_url}/sendMessage"
            data = {"chat_id": chat_id, "text": text}
            await client.post(url, json=data)

    async def send_webapp_button(self, chat_id: int, text: str, webapp_url: str):
        """Отправка кнопки с WebApp"""
        keyboard = {
            "inline_keyboard": [[{
                "text": "Открыть приложение",
                "web_app": {"url": webapp_url}
            }]]
        }

        async with httpx.AsyncClient() as client:
            url = f"{self.base_url}/sendMessage"
            data = {
                "chat_id": chat_id,
                "text": text,
                "reply_markup": keyboard
            }
            await client.post(url, json=data)


# Глобальный экземпляр
bot = TelegramBot(os.getenv("BOT_TOKEN"))


# Функции уведомлений
async def notify_application_status(user_telegram_id: int, event_title: str, status: str):
    """Уведомление об изменении статуса заявки"""
    messages = {
        "approved": f"✅ Ваша заявка на мероприятие '{event_title}' одобрена!",
        "rejected": f"❌ Ваша заявка на мероприятие '{event_title}' отклонена."
    }
    await bot.send_message(user_telegram_id, messages.get(status, "Статус заявки изменён"))


async def notify_new_event(user_telegram_id: int, event_title: str, city: str):
    """Уведомление о новом мероприятии в городе"""
    text = f"🆕 Новое мероприятие в городе {city}: {event_title}"
    await bot.send_message(user_telegram_id, text)