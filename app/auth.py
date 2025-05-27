import hashlib
import hmac
import json
from urllib.parse import parse_qsl, unquote
from fastapi import HTTPException, Header
from typing import Optional
import os


def extract_telegram_user_from_init_data(init_data: str) -> Optional[dict]:
    """Извлечение данных пользователя из init_data без проверки подписи"""
    try:
        if not init_data or init_data == 'test_data':
            return None

        parsed_data = dict(parse_qsl(init_data))
        user_data = parsed_data.get('user')

        if not user_data:
            return None

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
        print(f"Error extracting user data: {e}")
        return None


def verify_telegram_auth(init_data: str) -> dict:
    """Проверка подлинности данных Telegram WebApp"""
    try:
        # В режиме разработки упрощаем проверку
        if os.getenv("ENVIRONMENT") == "development":
            print("🔧 Development mode: simplified auth")

            # Пытаемся извлечь реальные данные
            user_data = extract_telegram_user_from_init_data(init_data)
            if user_data:
                print(f"✅ Real user data extracted: {user_data['id']}")
                return user_data

            # Fallback на тестовые данные
            print("⚠️ Using test user data")
            return {
                'id': 123456789,
                'first_name': 'Test',
                'last_name': 'User',
                'username': 'testuser',
                'language_code': 'ru',
                'is_premium': False
            }

        # Продакшн режим - полная проверка
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

        # В режиме разработки всегда возвращаем пользователя
        if os.getenv("ENVIRONMENT") == "development":
            print("🔄 Fallback to test user")
            return {
                'id': 123456789,
                'first_name': 'Test',
                'last_name': 'User',
                'username': 'testuser',
                'language_code': 'ru',
                'is_premium': False
            }

        raise HTTPException(status_code=401, detail=f"Invalid auth data: {str(e)}")


def get_telegram_user(authorization: Optional[str] = Header(None)):
    """Получение данных пользователя из заголовка"""

    # Логируем для отладки
    print(f"🔍 Authorization header: {authorization is not None}")

    # В режиме разработки всегда возвращаем пользователя
    if os.getenv("ENVIRONMENT") == "development":
        if authorization and authorization != 'test_data':
            try:
                user = verify_telegram_auth(authorization)
                print(f"✅ Authenticated user: {user['id']} ({user['first_name']})")
                return user
            except Exception as e:
                print(f"⚠️ Auth failed, using test user: {e}")

        # Возвращаем тестового пользователя
        test_user = {
            'id': 123456789,
            'first_name': 'Test',
            'last_name': 'User',
            'username': 'testuser',
            'language_code': 'ru',
            'is_premium': False
        }
        print(f"🧪 Using test user: {test_user['id']}")
        return test_user

    # Продакшн режим - требуем заголовок
    if not authorization:
        raise HTTPException(status_code=401, detail="Authorization header required")

    return verify_telegram_auth(authorization)


def get_telegram_user_flexible(authorization: Optional[str] = Header(None)):
    """Более гибкая версия получения пользователя - всегда возвращает результат"""
    try:
        return get_telegram_user(authorization)
    except HTTPException:
        # Если авторизация не удалась, возвращаем тестового пользователя
        print("🔄 Auth failed, using fallback test user")
        return {
            'id': 123456789,
            'first_name': 'Test',
            'last_name': 'User',
            'username': 'testuser',
            'language_code': 'ru',
            'is_premium': False
        }