from fastapi import FastAPI, Request, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
import os
from dotenv import load_dotenv

from .database import engine, SessionLocal
from .models import Base
from .routers import volunteers, organizers, events, admin

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

@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    return templates.TemplateResponse("base.html", {"request": request})

@app.get("/volunteer", response_class=HTMLResponse)
async def volunteer_page(request: Request):
    return templates.TemplateResponse("volunteer.html", {"request": request})

@app.get("/organizer", response_class=HTMLResponse)
async def organizer_page(request: Request):
    return templates.TemplateResponse("organizer.html", {"request": request})

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)