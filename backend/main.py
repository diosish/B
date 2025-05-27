from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from pathlib import Path

import backend.models
from backend.db.base import Base
from backend.db.session import engine
from backend.api.v1 import auth, users, events, notifications

# Создаём таблицы
Base.metadata.create_all(bind=engine)

# Инициализация FastAPI
app = FastAPI(title="Volunteer WebApp")

# Абсолютный путь до папки frontend/dist
dist_dir = Path(__file__).resolve().parent.parent / "frontend" / "dist"

# Подключение статики (в корень, например http://localhost:8000/)
app.mount("/", StaticFiles(directory=dist_dir, html=True), name="webapp")

# Подключение API роутеров
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(events.router)
app.include_router(notifications.router)
