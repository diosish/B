# app/crud.py - УЛУЧШЕННАЯ ВЕРСИЯ
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, func, desc
from . import models, schemas
from typing import List, Optional
from datetime import datetime, timedelta


def get_user_by_telegram_id(db: Session, telegram_id: int):
    """Получение пользователя по Telegram ID с подробным логированием"""
    print(f"🔍 Looking for user with telegram_id: {telegram_id}")
    user = db.query(models.User).filter(models.User.telegram_id == telegram_id).first()
    if user:
        print(f"✅ User found: ID={user.id}, Role={user.role}")
    else:
        print(f"❌ User not found for telegram_id: {telegram_id}")
    return user


def create_user(db: Session, user: schemas.UserCreate):
    """Создание нового пользователя с валидацией"""
    try:
        print(f"📝 Creating user with telegram_id={user.telegram_id}, role={user.role}")

        # Проверяем, что пользователь с таким telegram_id не существует
        existing_user = get_user_by_telegram_id(db, user.telegram_id)
        if existing_user:
            raise ValueError(f"User with telegram_id {user.telegram_id} already exists")

        # Создаем пользователя
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
            description=user.description,
            rating=0.0 if user.role == "volunteer" else None
        )

        db.add(db_user)
        db.commit()
        db.refresh(db_user)

        print(f"✅ User created successfully: ID={db_user.id}")
        return db_user

    except Exception as e:
        print(f"❌ Error creating user: {str(e)}")
        db.rollback()
        raise


def get_events(db: Session, skip: int = 0, limit: int = 100, city: Optional[str] = None,
               status: Optional[str] = None, organizer_id: Optional[int] = None):
    """Получение списка мероприятий с фильтрацией и оптимизированными запросами"""
    query = db.query(models.Event).options(joinedload(models.Event.organizer))

    # Применяем фильтры
    if city:
        query = query.filter(models.Event.city.ilike(f"%{city}%"))

    if status:
        query = query.filter(models.Event.status == status)

    if organizer_id:
        query = query.filter(models.Event.organizer_id == organizer_id)

    return query.order_by(desc(models.Event.created_at)).offset(skip).limit(limit).all()


def create_event(db: Session, event: schemas.EventCreate, organizer_id: int):
    """Создание мероприятия с проверками"""
    try:
        # Проверяем существование организатора
        organizer = get_user_by_id(db, organizer_id)
        if not organizer:
            raise ValueError(f"Organizer with ID {organizer_id} not found")

        if organizer.role != "organizer":
            raise ValueError(f"User {organizer_id} is not an organizer")

        # Создаем мероприятие
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

        print(f"✅ Event created: ID={db_event.id}, Title='{db_event.title}'")
        return db_event

    except Exception as e:
        print(f"❌ Error creating event: {str(e)}")
        db.rollback()
        raise


def create_application(db: Session, application: schemas.ApplicationCreate):
    """Создание заявки с проверками на дубликаты и валидность"""
    try:
        # Проверяем существование мероприятия
        event = get_event_by_id(db, application.event_id)
        if not event:
            raise ValueError(f"Event with ID {application.event_id} not found")

        if event.status != "active":
            raise ValueError(f"Cannot apply to event with status '{event.status}'")

        # Проверяем существование волонтёра
        volunteer = get_user_by_id(db, application.volunteer_id)
        if not volunteer:
            raise ValueError(f"Volunteer with ID {application.volunteer_id} not found")

        if volunteer.role != "volunteer":
            raise ValueError(f"User {application.volunteer_id} is not a volunteer")

        # Проверяем, что волонтёр не подавал заявку на это мероприятие
        existing_app = db.query(models.Application).filter(
            and_(
                models.Application.event_id == application.event_id,
                models.Application.volunteer_id == application.volunteer_id
            )
        ).first()

        if existing_app:
            raise ValueError("Application already exists for this event and volunteer")

        # Проверяем пересечение по времени с другими одобренными заявками
        if event.date:
            time_conflicts = check_time_conflicts(db, application.volunteer_id, event.date, event.duration or 8)
            if time_conflicts:
                raise ValueError("Time conflict with another approved event")

        # Создаем заявку
        db_application = models.Application(
            event_id=application.event_id,
            volunteer_id=application.volunteer_id
        )

        db.add(db_application)
        db.commit()
        db.refresh(db_application)

        print(f"✅ Application created: ID={db_application.id}")
        return db_application

    except Exception as e:
        print(f"❌ Error creating application: {str(e)}")
        db.rollback()
        raise


def check_time_conflicts(db: Session, volunteer_id: int, event_date: datetime, duration: int) -> bool:
    """Проверка временных конфликтов для волонтёра"""
    event_end = event_date + timedelta(hours=duration)

    # Находим одобренные заявки волонтёра на мероприятия в тот же день
    conflicting_applications = db.query(models.Application).join(models.Event).filter(
        and_(
            models.Application.volunteer_id == volunteer_id,
            models.Application.status == "approved",
            models.Event.date.isnot(None),
            models.Event.date >= event_date - timedelta(hours=12),  # В пределах 12 часов
            models.Event.date <= event_date + timedelta(hours=12)
        )
    ).all()

    for app in conflicting_applications:
        other_event = app.event
        if other_event.date and other_event.duration:
            other_end = other_event.date + timedelta(hours=other_event.duration)

            # Проверяем пересечение времени
            if (event_date < other_end and event_end > other_event.date):
                return True

    return False


def create_review(db: Session, event_id: int, volunteer_id: int, organizer_id: int, rating: int, comment: str):
    """Создание отзыва с полными проверками"""
    try:
        # Проверяем существование всех связанных объектов
        event = get_event_by_id(db, event_id)
        if not event:
            raise ValueError(f"Event with ID {event_id} not found")

        volunteer = get_user_by_id(db, volunteer_id)
        if not volunteer or volunteer.role != "volunteer":
            raise ValueError(f"Volunteer with ID {volunteer_id} not found")

        organizer = get_user_by_id(db, organizer_id)
        if not organizer or organizer.role != "organizer":
            raise ValueError(f"Organizer with ID {organizer_id} not found")

        # Проверяем права организатора на это мероприятие
        if event.organizer_id != organizer_id:
            raise ValueError("Organizer can only review volunteers from their own events")

        # Проверяем, что мероприятие завершено
        if event.status != "completed":
            raise ValueError("Can only review volunteers after event completion")

        # Проверяем, что волонтёр был одобрен на это мероприятие
        application = db.query(models.Application).filter(
            and_(
                models.Application.event_id == event_id,
                models.Application.volunteer_id == volunteer_id,
                models.Application.status == "approved"
            )
        ).first()

        if not application:
            raise ValueError("Volunteer was not approved for this event")

        # Проверяем, нет ли уже отзыва
        existing_review = check_existing_review(db, event_id, volunteer_id, organizer_id)
        if existing_review:
            raise ValueError("Review already exists")

        # Создаем отзыв
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

        print(f"✅ Review created: ID={db_review.id}")
        return db_review

    except Exception as e:
        print(f"❌ Error creating review: {str(e)}")
        db.rollback()
        raise


def update_volunteer_rating(db: Session, volunteer_id: int):
    """Обновление рейтинга волонтёра на основе всех отзывов"""
    try:
        # Вычисляем средний рейтинг
        avg_rating = db.query(func.avg(models.Review.rating)).filter(
            models.Review.volunteer_id == volunteer_id
        ).scalar()

        if avg_rating is not None:
            # Обновляем рейтинг пользователя
            volunteer = get_user_by_id(db, volunteer_id)
            if volunteer:
                volunteer.rating = round(float(avg_rating), 2)
                volunteer.updated_at = datetime.utcnow()
                db.commit()
                print(f"✅ Updated rating for volunteer {volunteer_id}: {volunteer.rating}")

    except Exception as e:
        print(f"❌ Error updating volunteer rating: {str(e)}")
        db.rollback()
        raise


def get_reviewable_volunteers(db: Session, event_id: int, organizer_id: int):
    """Получение списка волонтёров для оставления отзывов с оптимизированным запросом"""
    try:
        # Используем один запрос с join'ами для получения всех данных
        reviewable_volunteers = db.query(models.Application, models.User).join(
            models.User, models.Application.volunteer_id == models.User.id
        ).outerjoin(
            models.Review,
            and_(
                models.Review.event_id == event_id,
                models.Review.volunteer_id == models.User.id,
                models.Review.organizer_id == organizer_id
            )
        ).filter(
            and_(
                models.Application.event_id == event_id,
                models.Application.status == "approved",
                models.Review.id.is_(None)  # Нет отзыва
            )
        ).all()

        result = []
        for application, volunteer in reviewable_volunteers:
            result.append({
                "application_id": application.id,
                "volunteer": volunteer
            })

        return result

    except Exception as e:
        print(f"❌ Error getting reviewable volunteers: {str(e)}")
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


def get_user_by_id(db: Session, user_id: int):
    """Получение пользователя по ID"""
    return db.query(models.User).filter(models.User.id == user_id).first()


def get_event_by_id(db: Session, event_id: int):
    """Получение мероприятия по ID с загрузкой организатора"""
    return db.query(models.Event).options(joinedload(models.Event.organizer)).filter(
        models.Event.id == event_id
    ).first()


def get_applications_by_volunteer(db: Session, volunteer_id: int):
    """Получение заявок волонтёра с загрузкой данных о мероприятиях"""
    return db.query(models.Application).options(joinedload(models.Application.event)).filter(
        models.Application.volunteer_id == volunteer_id
    ).order_by(desc(models.Application.applied_at)).all()


def update_application_status(db: Session, application_id: int, status: str):
    """Обновление статуса заявки с проверками"""
    try:
        application = db.query(models.Application).filter(models.Application.id == application_id).first()
        if not application:
            raise ValueError(f"Application {application_id} not found")

        old_status = application.status
        application.status = status
        application.updated_at = datetime.utcnow()

        db.commit()
        db.refresh(application)

        print(f"✅ Application {application_id} status updated: {old_status} -> {status}")
        return application

    except Exception as e:
        print(f"❌ Error updating application status: {str(e)}")
        db.rollback()
        raise


def get_events_by_organizer(db: Session, organizer_id: int):
    """Получение мероприятий организатора"""
    return db.query(models.Event).filter(
        models.Event.organizer_id == organizer_id
    ).order_by(desc(models.Event.created_at)).all()


def get_volunteer_reviews(db: Session, volunteer_id: int):
    """Получение всех отзывов волонтёра с загрузкой связанных данных"""
    return db.query(models.Review).options(
        joinedload(models.Review.event),
        joinedload(models.Review.organizer)
    ).filter(
        models.Review.volunteer_id == volunteer_id
    ).order_by(desc(models.Review.created_at)).all()


def get_organizer_reviews(db: Session, organizer_id: int):
    """Получение всех отзывов, оставленных организатором"""
    return db.query(models.Review).options(
        joinedload(models.Review.event),
        joinedload(models.Review.volunteer)
    ).filter(
        models.Review.organizer_id == organizer_id
    ).order_by(desc(models.Review.created_at)).all()


def get_event_reviews(db: Session, event_id: int):
    """Получение всех отзывов по мероприятию"""
    return db.query(models.Review).options(
        joinedload(models.Review.volunteer)
    ).filter(
        models.Review.event_id == event_id
    ).order_by(desc(models.Review.created_at)).all()


# Статистические функции для админки
def get_system_stats(db: Session):
    """Получение статистики системы"""
    stats = {
        "total_users": db.query(models.User).count(),
        "active_users": db.query(models.User).filter(models.User.is_active == True).count(),
        "total_volunteers": db.query(models.User).filter(models.User.role == "volunteer").count(),
        "total_organizers": db.query(models.User).filter(models.User.role == "organizer").count(),
        "total_events": db.query(models.Event).count(),
        "active_events": db.query(models.Event).filter(models.Event.status == "active").count(),
        "completed_events": db.query(models.Event).filter(models.Event.status == "completed").count(),
        "total_applications": db.query(models.Application).count(),
        "pending_applications": db.query(models.Application).filter(models.Application.status == "pending").count(),
        "approved_applications": db.query(models.Application).filter(models.Application.status == "approved").count(),
        "total_reviews": db.query(models.Review).count(),
        "average_rating": db.query(func.avg(models.Review.rating)).scalar() or 0,
    }

    return stats