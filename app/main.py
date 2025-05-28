from fastapi import FastAPI, Request, Depends, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
import os
from dotenv import load_dotenv

from .database import engine, SessionLocal
from .models import Base
from .routers import volunteers, organizers, events, admin, applications, auth, reviews, export
from .auth import get_telegram_user_flexible
from . import crud

load_dotenv()

# Создание таблиц
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Volunteer System")

# Статические файлы и шаблоны
app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")

# Подключение роутеров
app.include_router(volunteers.router, prefix="/api/volunteers", tags=["volunteers"])
app.include_router(organizers.router, prefix="/api/organizers", tags=["organizers"])
app.include_router(events.router, prefix="/api/events", tags=["events"])
app.include_router(admin.router, prefix="/api/admin", tags=["admin"])
app.include_router(applications.router, prefix="/api/applications", tags=["applications"])
app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(reviews.router, prefix="/api/reviews", tags=["reviews"])
app.include_router(export.router, prefix="/api/export", tags=["export"])


# Функция проверки роли
async def check_user_role(request: Request, required_role: str):
    """Проверка роли пользователя"""
    try:
        auth_header = request.headers.get('authorization')
        if not auth_header:
            return False

        telegram_user = get_telegram_user_flexible(auth_header)
        db = SessionLocal()
        try:
            user = crud.get_user_by_telegram_id(db, telegram_user['id'])
            return user and user.role == required_role
        finally:
            db.close()
    except:
        return False


# ===== ОСНОВНЫЕ СТРАНИЦЫ =====
@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    """Главная страница - проверка авторизации и выбор роли"""
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/admin", response_class=HTMLResponse)
async def admin_dashboard(request: Request):
    """Админ панель"""
    return templates.TemplateResponse("admin_dashboard.html", {"request": request})

# ===== СТРАНИЦЫ ВОЛОНТЁРА =====
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


# ===== СТРАНИЦЫ ОРГАНИЗАТОРА =====
@app.get("/organizer/profile", response_class=HTMLResponse)
async def organizer_profile_page(request: Request):
    """Профиль организатора"""
    return templates.TemplateResponse("organizer_profile.html", {"request": request})


@app.get("/organizer/create-event", response_class=HTMLResponse)
async def create_event_page(request: Request):
    """Создание мероприятия"""
    return templates.TemplateResponse("create_event.html", {"request": request})

@app.get("/event/{event_id}", response_class=HTMLResponse)
async def event_details_page(event_id: int, request: Request):
    """Страница мероприятия"""
    return templates.TemplateResponse("event_details.html", {"request": request, "event_id": event_id})

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


# ===== СТРАНИЦЫ РЕГИСТРАЦИИ =====
@app.get("/register/volunteer", response_class=HTMLResponse)
async def volunteer_registration_page(request: Request):
    """Страница регистрации волонтёра"""
    return templates.TemplateResponse("register_volunteer.html", {"request": request})


@app.get("/register/organizer", response_class=HTMLResponse)
async def organizer_registration_page(request: Request):
    """Страница регистрации организатора"""
    return templates.TemplateResponse("register_organizer.html", {"request": request})


# ===== СОВМЕСТИМОСТЬ =====
@app.get("/volunteer", response_class=HTMLResponse)
async def volunteer_redirect(request: Request):
    return templates.TemplateResponse("volunteer_redirect.html", {"request": request})


@app.get("/organizer", response_class=HTMLResponse)
async def organizer_redirect(request: Request):
    return templates.TemplateResponse("organizer_redirect.html", {"request": request})


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)