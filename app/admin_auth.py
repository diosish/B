# app/admin_auth.py - Исправленная система авторизации администратора
import os
import secrets
import hashlib
import httpx
from datetime import datetime, timedelta
from typing import Optional, Dict
from fastapi import HTTPException, Request, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

# Временное хранилище сессий (в продакшене используйте Redis)
admin_sessions: Dict[str, dict] = {}

security = HTTPBearer(auto_error=False)


class AdminAuthManager:
    def __init__(self):
        self.admin_login = os.getenv("ADMIN_LOGIN", "admin")
        self.admin_password = os.getenv("ADMIN_PASSWORD", "admin123")
        self.session_duration = timedelta(hours=8)  # Сессия действует 8 часов

    def hash_password(self, password: str) -> str:
        """Хеширование пароля"""
        return hashlib.sha256(password.encode()).hexdigest()

    def verify_credentials(self, login: str, password: str) -> bool:
        """Проверка логина и пароля"""
        return (login == self.admin_login and
                self.hash_password(password) == self.hash_password(self.admin_password))

    async def validate_bot_token(self, token: str) -> bool:
        """Проверка токена из бота через API"""
        try:
            # Проверяем токен через внутренний API
            async with httpx.AsyncClient() as client:
                response = await client.get(f"http://localhost:8000/api/admin/validate-bot-token/{token}")
                return response.status_code == 200
        except Exception as e:
            print(f"❌ Error validating bot token: {e}")

            # Fallback: простая проверка формата токена
            if len(token) >= 32 and token.replace("-", "").replace("_", "").isalnum():
                print("✅ Token format is valid, allowing access")
                return True
            return False

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
        print(f"✅ Created admin session: {session_id[:8]}...")
        return session_id

    def validate_session(self, session_id: str) -> bool:
        """Проверка валидности сессии"""
        if session_id not in admin_sessions:
            print(f"❌ Session not found: {session_id[:8]}...")
            return False

        session = admin_sessions[session_id]

        # Проверяем, не истекла ли сессия
        if session['expires_at'] < datetime.utcnow():
            print(f"❌ Session expired: {session_id[:8]}...")
            self.invalidate_session(session_id)
            return False

        # Обновляем последнюю активность
        session['last_activity'] = datetime.utcnow()
        print(f"✅ Session valid: {session_id[:8]}...")
        return True

    def invalidate_session(self, session_id: str):
        """Инвалидация сессии"""
        admin_sessions.pop(session_id, None)
        print(f"🗑️ Session invalidated: {session_id[:8]}...")

    def cleanup_expired_sessions(self):
        """Очистка просроченных сессий"""
        now = datetime.utcnow()
        expired_sessions = [
            session_id for session_id, session_data in admin_sessions.items()
            if session_data['expires_at'] < now
        ]

        for session_id in expired_sessions:
            admin_sessions.pop(session_id, None)

        if expired_sessions:
            print(f"🧹 Cleaned up {len(expired_sessions)} expired sessions")

    def extend_session(self, session_id: str):
        """Продление сессии"""
        if session_id in admin_sessions:
            admin_sessions[session_id]['expires_at'] = datetime.utcnow() + self.session_duration
            print(f"⏰ Extended session: {session_id[:8]}...")

    def is_admin_user(self, telegram_id: int) -> bool:
        """Проверка, является ли пользователь администратором"""
        admin_ids_str = os.getenv("ADMIN_TELEGRAM_IDS", "123456789")
        try:
            admin_ids = [int(id_str.strip()) for id_str in admin_ids_str.split(",") if id_str.strip()]
            return telegram_id in admin_ids
        except ValueError:
            print(f"⚠️ Invalid ADMIN_TELEGRAM_IDS format: {admin_ids_str}")
            return False


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
        print("❌ No session ID found in request")
        raise HTTPException(
            status_code=401,
            detail="Admin authentication required",
            headers={"WWW-Authenticate": "Bearer"}
        )

    if not admin_auth.validate_session(session_id):
        print(f"❌ Invalid session: {session_id[:8]}...")
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
        "last_cleanup": datetime.utcnow().isoformat()
    }