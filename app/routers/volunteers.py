from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from .. import crud, models, schemas
from ..database import get_db
from ..auth import get_telegram_user_flexible

router = APIRouter()


@router.post("/register", response_model=schemas.UserResponse)
def register_volunteer(
        user: schemas.UserCreate,
        db: Session = Depends(get_db),
        telegram_user: dict = Depends(get_telegram_user_flexible)
):
    """Регистрация волонтёра через Telegram"""

    print(f"👥 Registering volunteer: {telegram_user}")

    # Используем данные из Telegram авторизации
    user.telegram_id = telegram_user['id']

    if not user.full_name:
        user.full_name = f"{telegram_user['first_name']} {telegram_user['last_name'] or ''}".strip()

    user.role = "volunteer"

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
    print(f"➕ Creating new volunteer user")
    return crud.create_user(db, user)


@router.get("/profile", response_model=schemas.UserResponse)
def get_my_profile(
        db: Session = Depends(get_db),
        telegram_user: dict = Depends(get_telegram_user_flexible)
):
    """Получение профиля текущего пользователя"""
    db_user = crud.get_user_by_telegram_id(db, telegram_user['id'])
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user


@router.get("/applications", response_model=List[schemas.ApplicationResponse])
def get_my_applications(
        db: Session = Depends(get_db),
        telegram_user: dict = Depends(get_telegram_user_flexible)
):
    """Получение заявок текущего пользователя"""
    db_user = crud.get_user_by_telegram_id(db, telegram_user['id'])
    if not db_user:
        return []

    return crud.get_applications_by_volunteer(db, db_user.id)


@router.post("/apply", response_model=schemas.ApplicationResponse)
def apply_to_event(
        application: schemas.ApplicationCreate,
        db: Session = Depends(get_db),
        telegram_user: dict = Depends(get_telegram_user_flexible)
):
    """Подача заявки на мероприятие"""
    db_user = crud.get_user_by_telegram_id(db, telegram_user['id'])
    if not db_user:
        raise HTTPException(status_code=404, detail="User not registered")

    # Проверим, не подавал ли уже заявку
    existing_application = db.query(models.Application).filter(
        models.Application.event_id == application.event_id,
        models.Application.volunteer_id == db_user.id
    ).first()

    if existing_application:
        raise HTTPException(status_code=400, detail="Application already exists")

    # Создаем заявку
    application.volunteer_id = db_user.id
    return crud.create_application(db, application)


@router.get("/test")
def test_volunteers():
    return {"message": "Volunteers API is working", "status": "ok"}