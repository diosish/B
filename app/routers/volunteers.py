from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session
from typing import List, Optional

from .. import crud, models, schemas
from ..database import get_db
from ..auth import get_telegram_user

router = APIRouter()


@router.post("/register", response_model=schemas.UserResponse)
def register_volunteer(
        user: schemas.UserCreate,
        db: Session = Depends(get_db),
        telegram_user: dict = Depends(get_telegram_user)
):
    """Регистрация волонтёра через Telegram"""

    # Используем данные из Telegram
    user.telegram_id = telegram_user['id']
    if not user.full_name:
        user.full_name = f"{telegram_user['first_name']} {telegram_user['last_name'] or ''}".strip()

    # Проверяем, не зарегистрирован ли уже
    db_user = crud.get_user_by_telegram_id(db, user.telegram_id)
    if db_user:
        # Обновляем существующего пользователя
        for field, value in user.dict(exclude_unset=True).items():
            if value is not None:
                setattr(db_user, field, value)
        db.commit()
        db.refresh(db_user)
        return db_user

    # Создаем нового пользователя
    user.role = "volunteer"
    return crud.create_user(db, user)


@router.get("/profile", response_model=schemas.UserResponse)
def get_my_profile(
        db: Session = Depends(get_db),
        telegram_user: dict = Depends(get_telegram_user)
):
    """Получение профиля текущего пользователя"""
    db_user = crud.get_user_by_telegram_id(db, telegram_user['id'])
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user


@router.get("/applications", response_model=List[schemas.ApplicationResponse])
def get_my_applications(
        db: Session = Depends(get_db),
        telegram_user: dict = Depends(get_telegram_user)
):
    """Получение заявок текущего пользователя"""
    # Сначала найдем пользователя в БД
    db_user = crud.get_user_by_telegram_id(db, telegram_user['id'])
    if not db_user:
        return []

    return crud.get_applications_by_volunteer(db, db_user.id)


@router.post("/apply", response_model=schemas.ApplicationResponse)
def apply_to_event(
        application: schemas.ApplicationCreate,
        db: Session = Depends(get_db),
        telegram_user: dict = Depends(get_telegram_user)
):
    """Подача заявки на мероприятие"""
    # Найдем пользователя в БД
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

