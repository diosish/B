import requests
from backend.core.config import settings

API_URL = f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}"

def send_message(chat_id: int, text: str):
    requests.post(f"{API_URL}/sendMessage", json={
        "chat_id": chat_id,
        "text": text,
        "reply_markup": {"inline_keyboard": [
            [{"text": "Открыть приложение", "url": settings.WEBAPP_URL}]
        ]}
    })
