from fastapi import FastAPI, Request, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
import os
from dotenv import load_dotenv

from .database import engine, SessionLocal
from .models import Base
from .routers import volunteers, organizers, events, admin, applications, auth

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

# ===== ОСНОВНЫЕ СТРАНИЦЫ =====
@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    """Главная страница - проверка авторизации и выбор роли"""
    return templates.TemplateResponse("index.html", {"request": request})

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

@app.get("/organizer/events", response_class=HTMLResponse)
async def organizer_events_page(request: Request):
    """Мои мероприятия организатора"""
    return templates.TemplateResponse("organizer_events.html", {"request": request})

@app.get("/organizer/applications", response_class=HTMLResponse)
async def organizer_applications_page(request: Request):
    """Заявки на мероприятие"""
    return templates.TemplateResponse("organizer_applications.html", {"request": request})

# Старые маршруты для совместимости
@app.get("/volunteer", response_class=HTMLResponse)
async def volunteer_redirect(request: Request):
    return templates.TemplateResponse("volunteer_redirect.html", {"request": request})

@app.get("/organizer", response_class=HTMLResponse)
async def organizer_redirect(request: Request):
    return templates.TemplateResponse("organizer_redirect.html", {"request": request})

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)