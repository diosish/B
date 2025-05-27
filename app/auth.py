import hashlib
import hmac
from urllib.parse import parse_qsl
from fastapi import HTTPException
import os


def verify_telegram_auth(init_data: str) -> dict:
    """Упрощенная проверка Telegram WebApp InitData"""
    try:
        # Парсинг данных
        data = dict(parse_qsl(init_data))

        # В продакшене здесь должна быть полная проверка подписи
        # Для упрощения просто извлекаем user данные
        user_data = data.get('user', '{}')
        import json
        user = json.loads(user_data)

        return {
            'id': user.get('id'),
            'first_name': user.get('first_name', ''),
            'last_name': user.get('last_name', ''),
            'username': user.get('username', '')
        }
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid auth data")