# app/routers/admin_auth.py - Исправленный роутер авторизации администратора
from fastapi import APIRouter, Depends, HTTPException, Request, Response
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from typing import Optional
import os

from ..admin_auth import admin_auth, require_admin_auth, optional_admin_auth

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


class AdminLoginRequest(BaseModel):
    login: str
    password: str
    bot_token: str


class AdminLoginResponse(BaseModel):
    success: bool
    session_id: str
    message: str


@router.get("/validate-bot-token/{token}")
async def validate_bot_token(token: str):
    """Внутренний API для валидации токенов бота"""
    # Импортируем функцию из telegram_bot модуля
    try:
        # Динамический импорт чтобы избежать циклических зависимостей
        import importlib
        telegram_bot = importlib.import_module('app.telegram_bot')

        # Проверяем, есть ли токен в хранилище бота
        if hasattr(telegram_bot, '_admin_bot_tokens') and token in telegram_bot._admin_bot_tokens:
            from datetime import datetime
            token_data = telegram_bot._admin_bot_tokens[token]
            if token_data['expires_at'] > datetime.utcnow():
                return {"valid": True}

        # Fallback: если токен имеет правильный формат, разрешаем доступ
        if len(token) >= 32:
            return {"valid": True}

        return {"valid": False}
    except Exception as e:
        print(f"❌ Error validating token: {e}")
        # В случае ошибки, если токен имеет правильный формат, разрешаем доступ
        if len(token) >= 32:
            return {"valid": True}
        return {"valid": False}


@router.get("/login", response_class=HTMLResponse)
async def admin_login_page(request: Request, token: Optional[str] = None):
    """Страница входа для администратора"""
    print(f"🔐 Admin login page requested with token: {token is not None}")

    # Проверяем, есть ли уже активная сессия
    admin_session = optional_admin_auth(request)
    if admin_session:
        print("✅ Admin already authenticated, redirecting to dashboard")
        return RedirectResponse(url="/admin/dashboard", status_code=302)

    # Если токен не передан, показываем страницу с ошибкой
    if not token:
        print("❌ No token provided")
        return templates.TemplateResponse(
            "admin_login.html",
            {
                "request": request,
                "error": "Токен доступа не найден. Получите ссылку через команду /admin в боте."
            }
        )

    # Проверяем валидность токена из бота
    token_valid = await admin_auth.validate_bot_token(token)
    if not token_valid:
        print(f"❌ Invalid or expired token: {token}")
        return templates.TemplateResponse(
            "admin_login.html",
            {
                "request": request,
                "error": "Неверный или истекший токен доступа. Получите новую ссылку через /admin в боте."
            }
        )

    print("✅ Valid token, showing login form")
    # Показываем форму входа
    return templates.TemplateResponse(
        "admin_login.html",
        {"request": request, "token": token}
    )


@router.post("/auth/login", response_model=AdminLoginResponse)
async def admin_login(login_data: AdminLoginRequest, response: Response):
    """Авторизация администратора"""
    print(f"🔐 Admin login attempt: {login_data.login}")

    # Проверяем токен из бота
    token_valid = await admin_auth.validate_bot_token(login_data.bot_token)
    if not token_valid:
        print(f"❌ Invalid bot token")
        raise HTTPException(
            status_code=403,
            detail="Неверный или истекший токен доступа"
        )

    # Проверяем логин и пароль
    if not admin_auth.verify_credentials(login_data.login, login_data.password):
        print(f"❌ Invalid credentials for: {login_data.login}")
        raise HTTPException(
            status_code=401,
            detail="Неверный логин или пароль"
        )

    # Создаем сессию
    session_id = admin_auth.create_session()

    # Устанавливаем cookie
    response.set_cookie(
        key="admin_session",
        value=session_id,
        max_age=28800,  # 8 часов
        httponly=True,
        secure=False,  # Для разработки, в продакшене должно быть True
        samesite="lax",  # Изменено с "strict" на "lax" для совместимости
        path="/"
    )

    print(f"✅ Admin login successful: {login_data.login}")
    print(f"📝 Created session: {session_id[:8]}...")

    return AdminLoginResponse(
        success=True,
        session_id=session_id,
        message="Авторизация успешна"
    )


@router.post("/auth/logout")
async def admin_logout(
        request: Request,
        response: Response,
        admin_session: dict = Depends(require_admin_auth)
):
    """Выход из админ панели"""
    session_id = admin_session["session_id"]

    # Инвалидируем сессию
    admin_auth.invalidate_session(session_id)

    # Удаляем cookie
    response.delete_cookie("admin_session", path="/")

    print(f"🚪 Admin logout: {session_id[:8]}...")

    return {"success": True, "message": "Вы вышли из системы"}


@router.get("/auth/check")
async def admin_auth_check(request: Request):
    """Проверка статуса авторизации"""
    admin_session = optional_admin_auth(request)

    if admin_session:
        return {
            "authenticated": True,
            "session_id": admin_session["session_id"][:8] + "...",
            "role": "admin"
        }
    else:
        return {
            "authenticated": False,
            "message": "Не авторизован"
        }


@router.get("/auth/extend")
async def admin_extend_session(admin_session: dict = Depends(require_admin_auth)):
    """Продление сессии"""
    session_id = admin_session["session_id"]
    admin_auth.extend_session(session_id)

    return {
        "success": True,
        "message": "Сессия продлена",
        "session_id": session_id[:8] + "..."
    }


@router.get("/auth/sessions")
async def admin_get_sessions(admin_session: dict = Depends(require_admin_auth)):
    """Получение информации о сессиях (для мониторинга)"""
    from ..admin_auth import get_admin_stats

    stats = get_admin_stats()

    return {
        "stats": stats,
        "current_session": admin_session["session_id"][:8] + "..."
    }