from fastapi import FastAPI
import backend.models   # чтобы зарегистрировать все модели

from backend.db.base import Base
from backend.db.session import engine
from backend.api.v1 import auth, users, events, notifications

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Volunteer WebApp")

# Корневой маршрут для проверки
@app.get("/")
async def root():
    return {"status": "ok"}

app.include_router(auth.router)
app.include_router(users.router)
app.include_router(events.router)
app.include_router(notifications.router)
