from sqlalchemy.orm import Session
from . import models, schemas
from typing import List, Optional

def get_user_by_telegram_id(db: Session, telegram_id: int):
    """Получение пользователя по Telegram ID"""
    try:
        print(f"Looking for user with telegram_id: {telegram_id}")
        user = db.query(models.User).filter(models.User.telegram_id == telegram_id).first()
        if user:
            print(f"User found: {user.id}")
        else:
            print("User not found")
        return user
    except Exception as e:
        print(f"Error getting user: {str(e)}")
        raise

def create_user(db: Session, user: schemas.UserCreate):
    """Создание нового пользователя"""
    try:
        print(f"Creating user with data: {user.dict()}")
        db_user = models.User(
            telegram_id=user.telegram_id,
            full_name=user.full_name,
            city=user.city,
            role=user.role,
            volunteer_type=user.volunteer_type,
            skills=user.skills,
            org_type=user.org_type,
            org_name=user.org_name,
            inn=user.inn,
            description=user.description
        )
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        print(f"User created successfully: {db_user.id}")
        return db_user
    except Exception as e:
        print(f"Error creating user: {str(e)}")
        db.rollback()
        raise

def get_events(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Event).offset(skip).limit(limit).all()

def create_event(db: Session, event: schemas.EventCreate, organizer_id: int):
    db_event = models.Event(**event.dict(), organizer_id=organizer_id)
    db.add(db_event)
    db.commit()
    db.refresh(db_event)
    return db_event

def get_applications_by_volunteer(db: Session, volunteer_id: int):
    return db.query(models.Application).filter(models.Application.volunteer_id == volunteer_id).all()

def create_application(db: Session, application: schemas.ApplicationCreate):
    db_application = models.Application(**application.dict())
    db.add(db_application)
    db.commit()
    db.refresh(db_application)
    return db_application

def update_application_status(db: Session, application_id: int, status: str):
    db_application = db.query(models.Application).filter(models.Application.id == application_id).first()
    if db_application:
        db_application.status = status
        db.commit()
        db.refresh(db_application)
    return db_application

def get_user_by_id(db: Session, user_id: int):
    return db.query(models.User).filter(models.User.id == user_id).first()

def get_event_by_id(db: Session, event_id: int):
    return db.query(models.Event).filter(models.Event.id == event_id).first()

def get_events_by_organizer(db: Session, organizer_id: int):
    return db.query(models.Event).filter(models.Event.organizer_id == organizer_id).all()