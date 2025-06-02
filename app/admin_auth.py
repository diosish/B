# app/admin_auth.py - Исправленная система авторизации администратора
import os
import secrets
import hashlib
from datetime import datetime, timedelta
from typing import Optional, Dict
from fastapi import HTTPException, Request, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

# Временное хранилище сессий и токенов (в продакшене используйте Redis)
admin_sessions: Dict[str, dict] = {}
admin_bot_tokens: Dict[str, dict] = {}

security = HTTPBearer(auto_error=False)


class AdminAuthManager:
    def __init__(self):
        self.admin_login = os.getenv("ADMIN_LOGIN", "admin")
        self.admin_password = os.getenv("ADMIN_PASSWORD", "admin123")
        self.session_duration = timedelta(hours=8)  # Сессия действует 8 часов
        self.token_duration = timedelta(hours=2)    # Токен из бота действует 2 часа

    def hash_password(self, password: str) -> str:
        """Хеширование пароля"""
        return hashlib.sha256(password.encode()).hexdigest()

    def verify_credentials(self, login: str, password: str) -> bool:
        """Проверка логина и пароля"""
        return (login == self.admin_login and
                self.hash_password(password) == self.hash_password(self.admin_password))

    def generate_bot_token(self) -> str:
        """Генерация токена для доступа из бота"""
        token = secrets.token_urlsafe(32)
        expires_at = datetime.utcnow() + self.token_duration

        admin_bot_tokens[token] = {
            'created_at': datetime.utcnow(),
            'expires_at': expires_at
        }

        self.cleanup_expired_tokens()
        return token

    def validate_bot_token(self, token: str) -> bool:
        """Проверка токена из бота"""
        if token not in admin_bot_tokens:
            return False

        if admin_bot_tokens[token]['expires_at'] < datetime.utcnow():
            admin_bot_tokens.pop(token, None)
            return False

        return True

    def create_session(self) -> str:
        """Создание новой админ сессии"""
        session_id = secrets.token_urlsafe(32)
        expires_at = datetime.utcnow() + self.session_duration

        admin_sessions[session_id] = {
            'created_at': datetime.utcnow(),
            'expires_at': expires_at,
            'last_activity': datetime.utcnow()
        }

        self.cleanup_expired_sessions()
        return session_id

    def validate_session(self, session_id: str) -> bool:
        """Проверка валидности сессии"""
        if session_id not in admin_sessions:
            return False

        session = admin_sessions[session_id]

        # Проверяем, не истекла ли сессия
        if session['expires_at'] < datetime.utcnow():
            self.invalidate_session(session_id)
            return False

        # Обновляем последнюю активность
        session['last_activity'] = datetime.utcnow()
        return True

    def invalidate_session(self, session_id: str):
        """Инвалидация сессии"""
        admin_sessions.pop(session_id, None)

    def cleanup_expired_sessions(self):
        """Очистка просроченных сессий"""
        now = datetime.utcnow()
        expired_sessions = [
            session_id for session_id, session_data in admin_sessions.items()
            if session_data['expires_at'] < now
        ]

        for session_id in expired_sessions:
            admin_sessions.pop(session_id, None)

    def cleanup_expired_tokens(self):
        """Очистка просроченных токенов"""
        now = datetime.utcnow()
        expired_tokens = [
            token for token, data in admin_bot_tokens.items()
            if data['expires_at'] < now
        ]

        for token in expired_tokens:
            admin_bot_tokens.pop(token, None)

    def extend_session(self, session_id: str):
        """Продление сессии"""
        if session_id in admin_sessions:
            admin_sessions[session_id]['expires_at'] = datetime.utcnow() + self.session_duration

    def is_admin_user(self, telegram_id: int) -> bool:
        """Проверка, является ли пользователь администратором"""
        admin_ids_str = os.getenv("ADMIN_TELEGRAM_IDS", "123456789")
        admin_ids = [int(id_str.strip()) for id_str in admin_ids_str.split(",") if id_str.strip()]
        return telegram_id in admin_ids


# Глобальный экземпляр менеджера
admin_auth = AdminAuthManager()


def get_session_from_request(request: Request) -> Optional[str]:
    """Получение session_id из запроса"""
    # Сначала проверяем заголовок Authorization
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        return auth_header.split(" ")[1]

    # Затем проверяем cookies
    return request.cookies.get("admin_session")


def require_admin_auth(request: Request) -> dict:
    """Dependency для проверки админ авторизации"""
    session_id = get_session_from_request(request)

    if not session_id:
        raise HTTPException(
            status_code=401,
            detail="Admin authentication required",
            headers={"WWW-Authenticate": "Bearer"}
        )

    if not admin_auth.validate_session(session_id):
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired admin session",
            headers={"WWW-Authenticate": "Bearer"}
        )

    # Продлеваем сессию при активности
    admin_auth.extend_session(session_id)

    return {"session_id": session_id, "role": "admin"}


def optional_admin_auth(request: Request) -> Optional[dict]:
    """Опциональная админ авторизация"""
    try:
        return require_admin_auth(request)
    except HTTPException:
        return None


# Middleware для логирования админ активности
class AdminActivityMiddleware:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] == "http":
            request = Request(scope, receive)

            # Проверяем админ активность
            if request.url.path.startswith("/admin"):
                session_id = get_session_from_request(request)
                if session_id and admin_auth.validate_session(session_id):
                    print(f"🔐 Admin activity: {request.method} {request.url.path}")

        await self.app(scope, receive, send)


def get_admin_stats() -> dict:
    """Получение статистики админ сессий"""
    active_sessions = len([
        s for s in admin_sessions.values()
        if s['expires_at'] > datetime.utcnow()
    ])

    return {
        "active_sessions": active_sessions,
        "total_sessions": len(admin_sessions),
        "active_tokens": len(admin_bot_tokens),
        "last_cleanup": datetime.utcnow().isoformat()
    }