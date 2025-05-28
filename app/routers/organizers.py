from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from .. import crud, models, schemas
from ..database import get_db
from ..auth import get_telegram_user_flexible

router = APIRouter()


@router.post("/register", response_model=schemas.UserResponse)
def register_organizer(
        user_data: schemas.UserCreate,
        db: Session = Depends(get_db),
        telegram_user: dict = Depends(get_telegram_user_flexible)
):
    """Регистрация организатора через Telegram"""

    print(f"🏢 Registering organizer: {telegram_user}")
    print(f"📊 Received user data: {user_data}")

    # Проверяем, не зарегистрирован ли уже пользователь
    db_user = crud.get_user_by_telegram_id(db, telegram_user['id'])

    if db_user:
        print(f"👤 User already exists, updating: {db_user.id}")
        # Обновляем существующего пользователя
        if user_data.full_name:
            db_user.full_name = user_data.full_name
        if user_data.city:
            db_user.city = user_data.city
        if user_data.org_type:
            db_user.org_type = user_data.org_type
        if user_data.org_name:
            db_user.org_name = user_data.org_name
        if user_data.inn:
            db_user.inn = user_data.inn
        if user_data.description:
            db_user.description = user_data.description

        # Убеждаемся что роль правильная
        db_user.role = "organizer"

        db.commit()
        db.refresh(db_user)
        return db_user

    # Создаем объект UserCreate с правильными данными
    full_name = user_data.full_name
    if not full_name:
        full_name = f"{telegram_user['first_name']} {telegram_user['last_name'] or ''}".strip()

    # Создаем новый объект UserCreate с полными данными
    create_data = schemas.UserCreate(
        telegram_id=telegram_user['id'],  # Берем из Telegram данных
        full_name=full_name,
        city=user_data.city,
        role="organizer",
        # Обнуляем поля волонтёра
        volunteer_type=None,
        skills=None,
        # Заполняем поля организатора
        org_type=user_data.org_type,
        org_name=user_data.org_name,
        inn=user_data.inn,
        description=user_data.description
    )

    print(f"➕ Creating new organizer user with data: {create_data}")
    return crud.create_user(db, create_data)


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