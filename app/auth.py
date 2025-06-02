# app/auth.py - ОБНОВЛЕННАЯ ВЕРСИЯ с проверкой активности пользователей
import hashlib
import hmac
import json
from urllib.parse import parse_qsl, unquote
from fastapi import HTTPException, Header, Request
from typing import Optional
import os
from datetime import datetime, timedelta

from .database import SessionLocal
from . import crud


def extract_real_telegram_id(init_data: str) -> Optional[int]:
    """Извлечение реального telegram_id из init_data, даже в режиме разработки"""
    try:
        parsed_data = dict(parse_qsl(init_data))
        user_data = parsed_data.get('user')

        if user_data:
            user_info = json.loads(unquote(user_data))
            telegram_id = user_info.get('id')
            if telegram_id and isinstance(telegram_id, int):
                return telegram_id
    except Exception as e:
        print(f"⚠️ Could not extract real telegram_id: {e}")

    return None


def verify_telegram_auth(init_data: str, allow_test_mode: bool = True, check_active: bool = True) -> dict:
    """Проверка подлинности данных Telegram WebApp с проверкой активности пользователя"""

    # Пытаемся извлечь реальный telegram_id
    real_telegram_id = extract_real_telegram_id(init_data)

    # Режим разработки - но используем реальный ID если он есть
    if allow_test_mode and (
            os.getenv("ENVIRONMENT") == "development" or
            init_data == "test_data" or
            not os.getenv("BOT_TOKEN")
    ):
        print("⚠️ Development mode: simplified auth validation")

        # Если удалось извлечь реальный ID, используем его
        if real_telegram_id:
            print(f"🔍 Using real telegram_id in dev mode: {real_telegram_id}")
            user_data = {
                'id': real_telegram_id,
                'first_name': 'Dev',
                'last_name': 'User',
                'username': f'devuser_{real_telegram_id}',
                'language_code': 'ru',
                'is_premium': False
            }
        else:
            # Фоллбек к тестовому пользователю только если не удалось извлечь реальный ID
            print("🧪 Using fallback test user")
            user_data = {
                'id': 123456789,
                'first_name': 'Test',
                'last_name': 'User',
                'username': 'testuser',
                'language_code': 'ru',
                'is_premium': False
            }

        # Проверяем активность пользователя
        if check_active:
            check_user_active_status(user_data['id'])

        return user_data

    try:
        # Полная проверка для продакшена
        parsed_data = dict(parse_qsl(init_data))

        # Извлечение hash
        hash_value = parsed_data.pop('hash', None)
        if not hash_value:
            raise ValueError("Hash not found in init_data")

        # Проверяем временную метку (auth_date не должен быть старше 24 часов)
        auth_date = parsed_data.get('auth_date')
        if auth_date:
            auth_timestamp = int(auth_date)
            current_timestamp = int(datetime.utcnow().timestamp())
            if current_timestamp - auth_timestamp > 86400:  # 24 часа
                raise ValueError("Auth data is too old")

        # Создание строки для проверки
        data_check_string = '\n'.join([f"{k}={v}" for k, v in sorted(parsed_data.items())])

        # Создание secret key
        bot_token = os.getenv("BOT_TOKEN")
        if not bot_token:
            raise ValueError("BOT_TOKEN not configured")

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
            raise ValueError("Invalid signature - authentication failed")

        # Извлечение данных пользователя
        user_data = parsed_data.get('user')
        if not user_data:
            raise ValueError("User data not found in init_data")

        user_info = json.loads(unquote(user_data))

        # Валидация обязательных полей
        if not user_info.get('id'):
            raise ValueError("User ID not found")

        if not isinstance(user_info['id'], int):
            raise ValueError("Invalid user ID format")

        telegram_user = {
            'id': user_info.get('id'),
            'first_name': user_info.get('first_name', ''),
            'last_name': user_info.get('last_name', ''),
            'username': user_info.get('username', ''),
            'language_code': user_info.get('language_code', 'ru'),
            'is_premium': user_info.get('is_premium', False),
            'auth_date': auth_date
        }

        # Проверяем активность пользователя
        if check_active:
            check_user_active_status(telegram_user['id'])

        return telegram_user

    except Exception as e:
        print(f"❌ Telegram auth error: {e}")

        # В режиме разработки возвращаем данные с реальным ID если возможно
        if allow_test_mode and os.getenv("ENVIRONMENT") == "development":
            print("⚠️ Auth failed, but using fallback in development mode")

            if real_telegram_id:
                print(f"🔍 Using real telegram_id as fallback: {real_telegram_id}")
                user_data = {
                    'id': real_telegram_id,
                    'first_name': 'Dev',
                    'last_name': 'User',
                    'username': f'devuser_{real_telegram_id}',
                    'language_code': 'ru',
                    'is_premium': False
                }
            else:
                user_data = {
                    'id': 123456789,
                    'first_name': 'Test',
                    'last_name': 'User',
                    'username': 'testuser',
                    'language_code': 'ru',
                    'is_premium': False
                }

            # Проверяем активность пользователя даже в режиме разработки
            if check_active:
                check_user_active_status(user_data['id'])

            return user_data

        raise HTTPException(
            status_code=401,
            detail=f"Telegram authentication failed: {str(e)}"
        )


def check_user_active_status(telegram_id: int):
    """Проверка активности пользователя в базе данных"""
    db = SessionLocal()
    try:
        user = crud.get_user_by_telegram_id(db, telegram_id)
        if user and not user.is_active:
            print(f"❌ User {telegram_id} is deactivated")
            raise HTTPException(
                status_code=403,
                detail="USER_DEACTIVATED"  # Специальный код для обработки на фронтенде
            )
        elif user:
            print(f"✅ User {telegram_id} is active")
    except HTTPException:
        raise  # Пропускаем HTTPException дальше
    except Exception as e:
        print(f"⚠️ Error checking user status: {e}")
        # Не блокируем пользователя при ошибке проверки БД
    finally:
        db.close()


def get_telegram_user_flexible(authorization: Optional[str] = Header(None)):
    """Получение данных пользователя из заголовка авторизации с проверкой активности"""
    if not authorization:
        raise HTTPException(
            status_code=401,
            detail="Authorization header required"
        )

    return verify_telegram_auth(authorization, allow_test_mode=True, check_active=True)


def get_telegram_user_strict(authorization: Optional[str] = Header(None)):
    """Строгая проверка Telegram аутентификации (для продакшена) с проверкой активности"""
    if not authorization:
        raise HTTPException(
            status_code=401,
            detail="Authorization header required"
        )

    return verify_telegram_auth(authorization, allow_test_mode=False, check_active=True)


def get_telegram_user_no_active_check(authorization: Optional[str] = Header(None)):
    """Получение данных пользователя БЕЗ проверки активности (для служебных целей)"""
    if not authorization:
        raise HTTPException(
            status_code=401,
            detail="Authorization header required"
        )

    return verify_telegram_auth(authorization, allow_test_mode=True, check_active=False)


def validate_admin_access(telegram_user: dict) -> bool:
    """Проверка прав администратора"""
    admin_ids = [
        123456789,  # Тестовый админ
        # Добавьте сюда реальные telegram_id администраторов
    ]

    # Дополнительно проверяем переменную окружения для админов
    env_admin_ids = os.getenv("ADMIN_TELEGRAM_IDS", "")
    if env_admin_ids:
        try:
            env_ids = [int(id_str.strip()) for id_str in env_admin_ids.split(",") if id_str.strip()]
            admin_ids.extend(env_ids)
        except ValueError:
            print("⚠️ Invalid ADMIN_TELEGRAM_IDS format in environment")

    return telegram_user['id'] in admin_ids


def generate_user_token(user_id: int, expires_hours: int = 24) -> str:
    """Генерация временного токена для пользователя (для будущего использования)"""
    import secrets
    import base64

    expire_time = datetime.utcnow() + timedelta(hours=expires_hours)
    token_data = {
        'user_id': user_id,
        'expires': expire_time.timestamp(),
        'nonce': secrets.token_hex(16)
    }

    # Простое кодирование (не для безопасности, только для обфускации)
    token_json = json.dumps(token_data)
    token_bytes = token_json.encode('utf-8')
    token_b64 = base64.b64encode(token_bytes).decode('utf-8')

    return token_b64


def validate_user_token(token: str) -> Optional[dict]:
    """Валидация пользовательского токена (для будущего использования)"""
    try:
        import base64

        token_bytes = base64.b64decode(token.encode('utf-8'))
        token_json = token_bytes.decode('utf-8')
        token_data = json.loads(token_json)

        # Проверяем срок действия
        if datetime.utcnow().timestamp() > token_data['expires']:
            return None

        return token_data

    except Exception as e:
        print(f"❌ Token validation error: {e}")
        return None


# Middleware для проверки деактивированных пользователей
class UserStatusMiddleware:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] == "http":
            request = Request(scope, receive)

            # Проверяем только пути приложения, исключаем статические файлы и API ошибок
            if (request.url.path.startswith(("/volunteer", "/organizer", "/event/")) and
                    not request.url.path.startswith(("/api/", "/static/", "/deactivated"))):

                try:
                    # Проверяем авторизацию и активность
                    auth_header = request.headers.get('authorization') or request.cookies.get('auth_token')
                    if auth_header:
                        verify_telegram_auth(auth_header, allow_test_mode=True, check_active=True)
                except HTTPException as e:
                    if e.detail == "USER_DEACTIVATED":
                        # Перенаправляем на страницу деактивации
                        from fastapi.responses import RedirectResponse
                        response = RedirectResponse(url="/deactivated", status_code=302)
                        await response(scope, receive, send)
                        return

        await self.app(scope, receive, send)


# Декоратор для проверки ролей
def require_role(required_role: str):
    """Декоратор для проверки роли пользователя"""

    def decorator(func):
        async def wrapper(*args, **kwargs):
            # Ищем telegram_user в kwargs
            telegram_user = kwargs.get('telegram_user')
            if not telegram_user:
                raise HTTPException(status_code=401, detail="Authentication required")

            # Здесь можно добавить проверку роли через БД
            # Пока что это заглушка
            return await func(*args, **kwargs)

        return wrapper

    return decorator


# Утилиты для работы с сессиями (для будущего развития)
class SessionManager:
    def __init__(self):
        self.sessions = {}  # В продакшене использовать Redis или БД

    def create_session(self, user_id: int) -> str:
        import secrets
        session_id = secrets.token_urlsafe(32)
        self.sessions[session_id] = {
            'user_id': user_id,
            'created_at': datetime.utcnow(),
            'last_activity': datetime.utcnow()
        }
        return session_id

    def get_session(self, session_id: str) -> Optional[dict]:
        session = self.sessions.get(session_id)
        if session:
            # Обновляем последнюю активность
            session['last_activity'] = datetime.utcnow()

            # Проверяем срок жизни сессии (24 часа)
            if datetime.utcnow() - session['created_at'] > timedelta(hours=24):
                self.sessions.pop(session_id, None)
                return None

        return session

    def invalidate_session(self, session_id: str):
        self.sessions.pop(session_id, None)

    def cleanup_expired_sessions(self):
        """Очистка просроченных сессий"""
        expired_sessions = []
        for session_id, session_data in self.sessions.items():
            if datetime.utcnow() - session_data['created_at'] > timedelta(hours=24):
                expired_sessions.append(session_id)

        for session_id in expired_sessions:
            self.sessions.pop(session_id, None)

        print(f"🧹 Cleaned up {len(expired_sessions)} expired sessions")


# Глобальный менеджер сессий
session_manager = SessionManager()