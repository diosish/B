from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from .. import crud, models, schemas
from ..database import get_db
from ..auth import get_telegram_user_flexible

router = APIRouter()


@router.post("/register", response_model=schemas.UserResponse)
def register_organizer(
        registration_data: schemas.OrganizerRegistration,
        db: Session = Depends(get_db),
        telegram_user: dict = Depends(get_telegram_user_flexible)
):
    """Регистрация организатора через Telegram"""

    print(f"🏢 Registering organizer: {telegram_user['id']}")
    print(f"📊 Received registration data: {registration_data}")

    # Проверяем, не зарегистрирован ли уже пользователь
    db_user = crud.get_user_by_telegram_id(db, telegram_user['id'])

    if db_user:
        print(f"👤 User already exists, updating: {db_user.id}")
        # Обновляем существующего пользователя
        db_user.full_name = registration_data.full_name
        db_user.city = registration_data.city
        db_user.org_type = registration_data.org_type
        db_user.org_name = registration_data.org_name
        db_user.inn = registration_data.inn
        db_user.description = registration_data.description
        db_user.role = "organizer"

        # Обнуляем поля волонтёра
        db_user.volunteer_type = None
        db_user.skills = None

        db.commit()
        db.refresh(db_user)
        return db_user

    # Создаем нового пользователя
    create_data = schemas.UserCreate(
        telegram_id=telegram_user['id'],
        full_name=registration_data.full_name,
        city=registration_data.city,
        role="organizer",
        # Обнуляем поля волонтёра
        volunteer_type=None,
        skills=None,
        # Заполняем поля организатора
        org_type=registration_data.org_type,
        org_name=registration_data.org_name,
        inn=registration_data.inn,
        description=registration_data.description
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