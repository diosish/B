from sqlalchemy.orm import Session
from sqlalchemy import and_
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
        print(f"Creating user with data: telegram_id={user.telegram_id}")
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
    db_event = models.Event(
        title=event.title,
        description=event.description,
        city=event.city,
        date=event.date,
        duration=event.duration,
        payment=event.payment,
        work_type=event.work_type,
        organizer_id=organizer_id
    )
    db.add(db_event)
    db.commit()
    db.refresh(db_event)
    return db_event


def get_applications_by_volunteer(db: Session, volunteer_id: int):
    return db.query(models.Application).filter(models.Application.volunteer_id == volunteer_id).all()


def create_application(db: Session, application: schemas.ApplicationCreate):
    db_application = models.Application(
        event_id=application.event_id,
        volunteer_id=application.volunteer_id
    )
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


# ===== НОВЫЕ ФУНКЦИИ ДЛЯ РАБОТЫ С ОТЗЫВАМИ =====

def create_review(db: Session, event_id: int, volunteer_id: int, organizer_id: int, rating: int, comment: str):
    """Создание отзыва"""
    try:
        db_review = models.Review(
            event_id=event_id,
            volunteer_id=volunteer_id,
            organizer_id=organizer_id,
            rating=rating,
            comment=comment
        )
        db.add(db_review)
        db.commit()
        db.refresh(db_review)

        # Обновляем рейтинг волонтёра
        update_volunteer_rating(db, volunteer_id)

        return db_review
    except Exception as e:
        print(f"Error creating review: {str(e)}")
        db.rollback()
        raise


def get_reviewable_volunteers(db: Session, event_id: int, organizer_id: int):
    """Получение списка волонтёров для оставления отзывов"""
    try:
        # Получаем всех одобренных волонтёров мероприятия
        approved_applications = db.query(models.Application).filter(
            and_(
                models.Application.event_id == event_id,
                models.Application.status == "approved"
            )
        ).all()

        result = []
        for app in approved_applications:
            # Проверяем, есть ли уже отзыв
            existing_review = check_existing_review(db, event_id, app.volunteer_id, organizer_id)
            if not existing_review:
                volunteer = get_user_by_id(db, app.volunteer_id)
                if volunteer:
                    result.append({
                        "application_id": app.id,
                        "volunteer": volunteer
                    })

        return result
    except Exception as e:
        print(f"Error getting reviewable volunteers: {str(e)}")
        raise


def check_existing_review(db: Session, event_id: int, volunteer_id: int, organizer_id: int):
    """Проверка существования отзыва"""
    return db.query(models.Review).filter(
        and_(
            models.Review.event_id == event_id,
            models.Review.volunteer_id == volunteer_id,
            models.Review.organizer_id == organizer_id
        )
    ).first()


def update_volunteer_rating(db: Session, volunteer_id: int):
    """Обновление рейтинга волонтёра"""
    try:
        # Получаем все отзывы волонтёра
        reviews = db.query(models.Review).filter(
            models.Review.volunteer_id == volunteer_id
        ).all()

        if reviews:
            # Вычисляем средний рейтинг
            total_rating = sum(review.rating for review in reviews)
            avg_rating = total_rating / len(reviews)

            # Обновляем рейтинг пользователя
            volunteer = get_user_by_id(db, volunteer_id)
            if volunteer:
                volunteer.rating = round(avg_rating, 2)
                db.commit()
                print(f"Updated rating for volunteer {volunteer_id}: {avg_rating}")

    except Exception as e:
        print(f"Error updating volunteer rating: {str(e)}")
        db.rollback()
        raise


def get_event_reviews(db: Session, event_id: int):
    """Получение всех отзывов по мероприятию"""
    return db.query(models.Review).filter(
        models.Review.event_id == event_id
    ).all()


def get_volunteer_reviews(db: Session, volunteer_id: int):
    """Получение всех отзывов волонтёра"""
    return db.query(models.Review).filter(
        models.Review.volunteer_id == volunteer_id
    ).order_by(models.Review.created_at.desc()).all()


def get_organizer_reviews(db: Session, organizer_id: int):
    """Получение всех отзывов, оставленных организатором"""
    return db.query(models.Review).filter(
        models.Review.organizer_id == organizer_id
    ).order_by(models.Review.created_at.desc()).all()