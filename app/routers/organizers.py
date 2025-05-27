from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from .. import crud, models, schemas
from ..database import get_db
from ..auth import get_telegram_user_flexible

router = APIRouter()


@router.post("/register", response_model=schemas.UserResponse)
def register_organizer(
        user: schemas.UserCreate,
        db: Session = Depends(get_db),
        telegram_user: dict = Depends(get_telegram_user_flexible)
):
    """Регистрация организатора через Telegram"""

    print(f"🏢 Registering organizer: {telegram_user}")

    # Используем данные из Telegram авторизации
    user.telegram_id = telegram_user['id']

    if not user.full_name:
        user.full_name = f"{telegram_user['first_name']} {telegram_user['last_name'] or ''}".strip()

    user.role = "organizer"

    # Проверяем, не зарегистрирован ли уже
    db_user = crud.get_user_by_telegram_id(db, user.telegram_id)
    if db_user:
        print(f"👤 User already exists, updating: {db_user.id}")
        # Обновляем существующего пользователя
        for field, value in user.dict(exclude_unset=True).items():
            if value is not None and hasattr(db_user, field):
                setattr(db_user, field, value)
        db.commit()
        db.refresh(db_user)
        return db_user

    # Создаем нового пользователя
    print(f"➕ Creating new organizer user")
    return crud.create_user(db, user)


@router.get("/profile", response_model=schemas.UserResponse)
def get_my_profile(
        db: Session = Depends(get_db),
        telegram_user: dict = Depends(get_telegram_user_flexible)
):
    """Получение профиля текущего организатора"""
    db_user = crud.get_user_by_telegram_id(db, telegram_user['id'])
    if not db_user or db_user.role != "organizer":
        raise HTTPException(status_code=404, detail="Organizer not found")
    return db_user


@router.get("/events", response_model=List[schemas.EventResponse])
def get_my_events(
        db: Session = Depends(get_db),
        telegram_user: dict = Depends(get_telegram_user_flexible)
):
    """Получение мероприятий текущего организатора"""
    db_user = crud.get_user_by_telegram_id(db, telegram_user['id'])
    if not db_user:
        return []

    return db.query(models.Event).filter(models.Event.organizer_id == db_user.id).all()


@router.get("/test")
def test_organizers():
    return {"message": "Organizers API is working", "status": "ok"}