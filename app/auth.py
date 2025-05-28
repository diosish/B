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
        parsed_data = dict(parse_qsl(init_data))
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

        if calculated_hash != hash_value:
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
        print(f"❌ Auth error: {e}")
        raise HTTPException(status_code=401, detail=f"Authentication failed")


def get_telegram_user_flexible(authorization: Optional[str] = Header(None)):
    """Получение данных пользователя из заголовка авторизации"""
    if not authorization:
        raise HTTPException(status_code=401, detail="Authorization header required")

    return verify_telegram_auth(authorization)