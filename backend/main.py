# backend/main.py

from fastapi import FastAPI

# Ипортируем модели, чтобы они автоматически зарегистрировались в MetaData
import backend.models   # <- вот эта строка

from backend.db.base import Base
from backend.db.session import engine
from backend.api.v1 import auth, users, events, notifications

# Создание всех таблиц на основании уже загруженных моделей
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Volunteer WebApp")
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(events.router)
app.include_router(notifications.router)
