from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from .. import crud, models, schemas
from ..database import get_db
from ..auth import get_telegram_user_flexible
from ..bot import notify_new_application

router = APIRouter()


@router.post("/register", response_model=schemas.UserResponse)
def register_volunteer(
        registration_data: schemas.VolunteerRegistration,
        db: Session = Depends(get_db),
        telegram_user: dict = Depends(get_telegram_user_flexible)
):
    """Регистрация волонтёра через Telegram"""

    print(f"👥 Registering volunteer: {telegram_user['id']}")

    # Проверяем, не зарегистрирован ли уже пользователь
    db_user = crud.get_user_by_telegram_id(db, telegram_user['id'])

    if db_user:
        # ИСПРАВЛЕНИЕ: Не позволяем менять роль, только обновляем данные той же роли
        if db_user.role != "volunteer":
            raise HTTPException(
                status_code=400,
                detail=f"User already registered as {db_user.role}. Cannot change role to volunteer."
            )

        # Обновляем данные существующего волонтёра
        db_user.full_name = registration_data.full_name
        db_user.city = registration_data.city
        db_user.volunteer_type = registration_data.volunteer_type
        db_user.skills = registration_data.skills

        db.commit()
        db.refresh(db_user)
        return db_user

    # Создаем нового пользователя
    create_data = schemas.UserCreate(
        telegram_id=telegram_user['id'],
        full_name=registration_data.full_name,
        city=registration_data.city,
        role="volunteer",
        volunteer_type=registration_data.volunteer_type,
        skills=registration_data.skills,
        # Поля организатора остаются None
        org_type=None,
        org_name=None,
        inn=None,
        description=None
    )

    return crud.create_user(db, create_data)


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
async def apply_to_event(
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

    # Получаем информацию о мероприятии и организаторе
    event = crud.get_event_by_id(db, application.event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")

    organizer = crud.get_user_by_id(db, event.organizer_id)
    if not organizer:
        raise HTTPException(status_code=404, detail="Organizer not found")

    # Создаем заявку
    application.volunteer_id = db_user.id
    db_application = crud.create_application(db, application)

    # Отправляем уведомление организатору
    try:
        await notify_new_application(
            organizer.telegram_id,
            event.title,
            db_user.full_name
        )
        print(f"📱 Notification sent to organizer {organizer.telegram_id}")
    except Exception as e:
        print(f"❌ Failed to send notification to organizer: {e}")

    return db_application