# app/main.py - ОБНОВЛЕННАЯ ВЕРСИЯ с админ авторизацией
from fastapi import FastAPI, Request, Depends, HTTPException, status
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from starlette.middleware.gzip import GZipMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
import os
import time
import logging
from contextlib import asynccontextmanager
from dotenv import load_dotenv

from .database import engine, SessionLocal
from .models import Base
from .routers import volunteers, organizers, events, admin, applications, auth, reviews, export
from .routers import admin_auth  # НОВЫЙ ИМПОРТ
from .health import router as health_router
from .auth import get_telegram_user_flexible
from .admin_auth import AdminActivityMiddleware, require_admin_auth, optional_admin_auth  # НОВЫЙ ИМПОРТ
from .monitoring import start_background_monitoring
from . import crud

# Загрузка переменных окружения
load_dotenv()

# Настройка логирования
logging.basicConfig(
    level=getattr(logging, os.getenv("LOG_LEVEL", "INFO")),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(os.getenv("LOG_FILE", "app.log")),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


# Контекстный менеджер для startup/shutdown
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Управление жизненным циклом приложения"""
    logger.info("🚀 Starting Volunteer Management System...")

    # Создание таблиц при старте
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("✅ Database tables created/verified")
    except Exception as e:
        logger.error(f"❌ Database initialization failed: {e}")
        raise

    # Запуск фонового мониторинга
    try:
        await start_background_monitoring()
        logger.info("✅ Background monitoring started")
    except Exception as e:
        logger.warning(f"⚠️ Background monitoring failed to start: {e}")

    logger.info("✅ Application startup completed")

    yield

    # Cleanup при shutdown
    logger.info("🛑 Shutting down Volunteer Management System...")
    logger.info("✅ Application shutdown completed")


# Создание приложения
app = FastAPI(
    title="Volunteer Management System",
    description="Система управления оплачиваемыми волонтёрами",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs" if os.getenv("ENVIRONMENT") == "development" else None,
    redoc_url="/redoc" if os.getenv("ENVIRONMENT") == "development" else None,
)


# ==============================================
# MIDDLEWARE
# ==============================================

# Middleware для логирования запросов
class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()

        # Логируем входящий запрос
        logger.info(
            f"📨 {request.method} {request.url.path} from {request.client.host if request.client else 'unknown'}")

        response = await call_next(request)

        # Логируем время обработки
        process_time = time.time() - start_time
        logger.info(
            f"⏱️ {request.method} {request.url.path} completed in {process_time:.3f}s with status {response.status_code}")

        # Добавляем заголовок с временем обработки
        response.headers["X-Process-Time"] = str(process_time)

        return response


# Middleware для обработки ошибок
class ErrorHandlingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        try:
            response = await call_next(request)
            return response
        except Exception as e:
            logger.error(f"❌ Unhandled error in {request.method} {request.url.path}: {str(e)}")

            # В development режиме показываем детали ошибки
            if os.getenv("ENVIRONMENT") == "development":
                return JSONResponse(
                    status_code=500,
                    content={
                        "detail": f"Internal server error: {str(e)}",
                        "path": str(request.url.path),
                        "method": request.method
                    }
                )
            else:
                return JSONResponse(
                    status_code=500,
                    content={"detail": "Internal server error"}
                )


# Добавление middleware
app.add_middleware(GZipMiddleware, minimum_size=1000)
app.add_middleware(AdminActivityMiddleware)  # НОВЫЙ MIDDLEWARE
app.add_middleware(RequestLoggingMiddleware)
app.add_middleware(ErrorHandlingMiddleware)

# CORS настройки
allowed_origins = os.getenv("CORS_ORIGINS", "").split(",") if os.getenv("CORS_ORIGINS") else ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Доверенные хосты (только в production)
if os.getenv("ENVIRONMENT") == "production":
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=["*.ngrok-free.app", "localhost", "127.0.0.1"]
    )

# ==============================================
# СТАТИЧЕСКИЕ ФАЙЛЫ И ШАБЛОНЫ
# ==============================================

app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")

# ==============================================
# РОУТЕРЫ API
# ==============================================

# Health checks (должны быть первыми для мониторинга)
app.include_router(health_router, tags=["health"])

# Основные API роутеры
app.include_router(volunteers.router, prefix="/api/volunteers", tags=["volunteers"])
app.include_router(organizers.router, prefix="/api/organizers", tags=["organizers"])
app.include_router(events.router, prefix="/api/events", tags=["events"])
app.include_router(applications.router, prefix="/api/applications", tags=["applications"])
app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(reviews.router, prefix="/api/reviews", tags=["reviews"])
app.include_router(export.router, prefix="/api/export", tags=["export"])
app.include_router(admin.router, prefix="/api/admin", tags=["admin"])

# НОВЫЙ РОУТЕР для админ авторизации
app.include_router(admin_auth.router, prefix="/admin", tags=["admin-auth"])


# ==============================================
# ФУНКЦИИ ПРОВЕРКИ РОЛЕЙ
# ==============================================

async def check_user_role(request: Request, required_role: str):
    """Проверка роли пользователя для страниц"""
    try:
        auth_header = request.headers.get('authorization')
        if not auth_header:
            return False

        telegram_user = get_telegram_user_flexible(auth_header)
        db = SessionLocal()
        try:
            user = crud.get_user_by_telegram_id(db, telegram_user['id'])
            return user and user.role == required_role and user.is_active
        finally:
            db.close()
    except Exception as e:
        logger.error(f"Role check failed: {e}")
        return False


# ==============================================
# ОСНОВНЫЕ СТРАНИЦЫ
# ==============================================

@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    """Главная страница - проверка авторизации и выбор роли"""
    return templates.TemplateResponse("index.html", {"request": request})


# ==============================================
# АДМИН ПАНЕЛЬ (ОБНОВЛЕННАЯ)
# ==============================================

@app.get("/admin/login", response_class=HTMLResponse)
async def admin_login_redirect(request: Request):
    """Редирект на страницу входа админа"""
    return RedirectResponse(url="/admin/login", status_code=302)


@app.get("/admin/dashboard", response_class=HTMLResponse)
async def admin_dashboard(
    request: Request,
    admin_session: dict = Depends(require_admin_auth)
):
    """Админ панель - только для авторизованных администраторов"""
    return templates.TemplateResponse(
        "admin_dashboard_secure.html",
        {"request": request, "admin_session": admin_session}
    )


@app.get("/admin", response_class=HTMLResponse)
async def admin_root(request: Request):
    """Корень админ панели - перенаправление"""
    # Проверяем, авторизован ли админ
    admin_session = optional_admin_auth(request)
    if admin_session:
        return RedirectResponse(url="/admin/dashboard", status_code=302)
    else:
        return RedirectResponse(url="/admin/login", status_code=302)


# ==============================================
# СТРАНИЦЫ ВОЛОНТЁРА
# ==============================================

@app.get("/volunteer/profile", response_class=HTMLResponse)
async def volunteer_profile_page(request: Request):
    """Профиль волонтёра"""
    return templates.TemplateResponse("volunteer_profile.html", {"request": request})


@app.get("/volunteer/events", response_class=HTMLResponse)
async def volunteer_events_page(request: Request):
    """Список мероприятий для волонтёра"""
    return templates.TemplateResponse("volunteer_events.html", {"request": request})


@app.get("/volunteer/applications", response_class=HTMLResponse)
async def volunteer_applications_page(request: Request):
    """Мои заявки волонтёра"""
    return templates.TemplateResponse("volunteer_applications.html", {"request": request})


@app.get("/volunteer/reviews", response_class=HTMLResponse)
async def volunteer_reviews_page(request: Request):
    """Отзывы волонтёра"""
    return templates.TemplateResponse("volunteer_reviews.html", {"request": request})


# ==============================================
# СТРАНИЦЫ ОРГАНИЗАТОРА
# ==============================================

@app.get("/organizer/profile", response_class=HTMLResponse)
async def organizer_profile_page(request: Request):
    """Профиль организатора"""
    return templates.TemplateResponse("organizer_profile.html", {"request": request})


@app.get("/organizer/create-event", response_class=HTMLResponse)
async def create_event_page(request: Request):
    """Создание мероприятия"""
    return templates.TemplateResponse("create_event.html", {"request": request})


@app.get("/organizer/events", response_class=HTMLResponse)
async def organizer_events_page(request: Request):
    """Мои мероприятия организатора"""
    return templates.TemplateResponse("organizer_events.html", {"request": request})


@app.get("/organizer/applications", response_class=HTMLResponse)
async def organizer_applications_page(request: Request):
    """Заявки на мероприятие"""
    return templates.TemplateResponse("organizer_applications.html", {"request": request})


@app.get("/organizer/reviews", response_class=HTMLResponse)
async def organizer_reviews_page(request: Request):
    """Отзывы о волонтёрах"""
    return templates.TemplateResponse("event_reviews.html", {"request": request})


@app.get("/organizer/manage", response_class=HTMLResponse)
async def event_management_page(request: Request):
    """Управление мероприятием"""
    return templates.TemplateResponse("event_management.html", {"request": request})


@app.get("/organizer/edit", response_class=HTMLResponse)
async def edit_event_page(request: Request):
    """Редактирование мероприятия"""
    return templates.TemplateResponse("edit_event_page.html", {"request": request})


# ==============================================
# СТРАНИЦЫ РЕГИСТРАЦИИ
# ==============================================

@app.get("/register/volunteer", response_class=HTMLResponse)
async def volunteer_registration_page(request: Request):
    """Страница регистрации волонтёра"""
    return templates.TemplateResponse("register_volunteer.html", {"request": request})


@app.get("/register/organizer", response_class=HTMLResponse)
async def organizer_registration_page(request: Request):
    """Страница регистрации организатора"""
    return templates.TemplateResponse("register_organizer.html", {"request": request})


# ==============================================
# СТРАНИЦЫ МЕРОПРИЯТИЙ
# ==============================================

@app.get("/event/{event_id}", response_class=HTMLResponse)
async def event_details_page(event_id: int, request: Request):
    """Страница мероприятия"""
    return templates.TemplateResponse(
        "event_details.html",
        {"request": request, "event_id": event_id}
    )


# ==============================================
# СОВМЕСТИМОСТЬ И РЕДИРЕКТЫ
# ==============================================

@app.get("/volunteer", response_class=HTMLResponse)
async def volunteer_redirect(request: Request):
    """Редирект для совместимости"""
    return templates.TemplateResponse("volunteer_redirect.html", {"request": request})


@app.get("/organizer", response_class=HTMLResponse)
async def organizer_redirect(request: Request):
    """Редирект для совместимости"""
    return templates.TemplateResponse("organizer_redirect.html", {"request": request})


# ==============================================
# ОБРАБОТКА ОШИБОК
# ==============================================

@app.exception_handler(404)
async def not_found_handler(request: Request, exc: HTTPException):
    """Обработчик 404 ошибок"""
    return templates.TemplateResponse(
        "error_404.html",
        {"request": request},
        status_code=404
    )


@app.exception_handler(500)
async def internal_error_handler(request: Request, exc: HTTPException):
    """Обработчик 500 ошибок"""
    logger.error(f"Internal server error: {exc}")
    return templates.TemplateResponse(
        "error_500.html",
        {"request": request},
        status_code=500
    )


@app.exception_handler(403)
async def forbidden_handler(request: Request, exc: HTTPException):
    """Обработчик 403 ошибок"""
    return templates.TemplateResponse(
        "error_403.html",
        {"request": request},
        status_code=403
    )


# ==============================================
# ДОПОЛНИТЕЛЬНЫЕ ENDPOINTS
# ==============================================

@app.get("/api/version")
async def get_version():
    """Получение версии приложения"""
    return {
        "version": "1.0.0",
        "environment": os.getenv("ENVIRONMENT", "development"),
        "build_time": "2024-01-01T00:00:00Z",
        "admin_auth": "enabled"  # НОВОЕ ПОЛЕ
    }


@app.get("/robots.txt", response_class=HTMLResponse)
async def robots_txt():
    """Robots.txt для поисковых роботов"""
    return """User-agent: *
Disallow: /admin
Disallow: /api
Allow: /
"""


@app.get("/sitemap.xml", response_class=HTMLResponse)
async def sitemap_xml(request: Request):
    """Sitemap для поисковых систем"""
    base_url = str(request.base_url).rstrip('/')

    return f"""<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
    <url>
        <loc>{base_url}/</loc>
        <changefreq>daily</changefreq>
        <priority>1.0</priority>
    </url>
    <url>
        <loc>{base_url}/register/volunteer</loc>
        <changefreq>weekly</changefreq>
        <priority>0.8</priority>
    </url>
    <url>
        <loc>{base_url}/register/organizer</loc>
        <changefreq>weekly</changefreq>
        <priority>0.8</priority>
    </url>
</urlset>
"""


# ==============================================
# ЗАПУСК ПРИЛОЖЕНИЯ
# ==============================================

if __name__ == "__main__":
    import uvicorn

    # Конфигурация для запуска
    config = {
        "app": "app.main:app",
        "host": "0.0.0.0",
        "port": int(os.getenv("PORT", 8000)),
        "reload": os.getenv("ENVIRONMENT") == "development",
        "workers": int(os.getenv("WORKERS", 1)) if os.getenv("ENVIRONMENT") != "development" else 1,
        "access_log": True,
        "log_level": os.getenv("LOG_LEVEL", "info").lower(),
    }

    logger.info(f"🚀 Starting server with config: {config}")
    uvicorn.run(**config)