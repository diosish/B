from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from .. import crud, models, schemas
from ..database import get_db
from ..auth import get_telegram_user_flexible
from ..bot import notify_review_received

router = APIRouter()


@router.post("/", response_model=schemas.ReviewResponse)
async def create_review(
        review_data: schemas.ReviewCreate,
        db: Session = Depends(get_db),
        telegram_user: dict = Depends(get_telegram_user_flexible)
):
    """Создание отзыва о волонтёре"""
    print(f"📝 Creating review from user {telegram_user['id']}")

    # Получаем организатора
    organizer = crud.get_user_by_telegram_id(db, telegram_user['id'])
    if not organizer or organizer.role != "organizer":
        raise HTTPException(status_code=403, detail="Only organizers can leave reviews")

    # Проверяем, что это мероприятие организатора
    event = crud.get_event_by_id(db, review_data.event_id)
    if not event or event.organizer_id != organizer.id:
        raise HTTPException(status_code=403, detail="You can only review volunteers from your events")

    # Проверяем, что мероприятие завершено
    if event.status != "completed":
        raise HTTPException(status_code=400, detail="You can only review volunteers after event completion")

    # Проверяем, что волонтёр был одобрен на это мероприятие
    application = db.query(models.Application).filter(
        models.Application.event_id == review_data.event_id,
        models.Application.volunteer_id == review_data.volunteer_id,
        models.Application.status == "approved"
    ).first()

    if not application:
        raise HTTPException(status_code=400, detail="Volunteer was not approved for this event")

    # Проверяем, нет ли уже отзыва
    existing_review = crud.check_existing_review(
        db, review_data.event_id, review_data.volunteer_id, organizer.id
    )
    if existing_review:
        raise HTTPException(status_code=400, detail="Review already exists")

    # Валидация рейтинга
    if not 1 <= review_data.rating <= 5:
        raise HTTPException(status_code=400, detail="Rating must be between 1 and 5")

    # Создаем отзыв
    try:
        review = crud.create_review(
            db,
            event_id=review_data.event_id,
            volunteer_id=review_data.volunteer_id,
            organizer_id=organizer.id,
            rating=review_data.rating,
            comment=review_data.comment
        )

        # Получаем данные волонтёра
        volunteer = crud.get_user_by_id(db, review_data.volunteer_id)

        # Отправляем уведомление волонтёру
        if volunteer:
            try:
                await notify_review_received(
                    volunteer.telegram_id,
                    event.title,
                    review_data.rating,
                    organizer.full_name
                )
                print(f"📱 Notification sent to volunteer {volunteer.telegram_id}")
            except Exception as e:
                print(f"❌ Failed to send notification: {e}")

        # Формируем ответ
        response = schemas.ReviewResponse(
            id=review.id,
            event_id=review.event_id,
            volunteer_id=review.volunteer_id,
            organizer_id=review.organizer_id,
            rating=review.rating,
            comment=review.comment,
            created_at=review.created_at,
            volunteer_name=volunteer.full_name if volunteer else "Unknown",
            event_title=event.title,
            organizer_name=organizer.full_name
        )

        return response

    except Exception as e:
        print(f"❌ Error creating review: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/event/{event_id}/reviewable")
def get_reviewable_volunteers(
        event_id: int,
        db: Session = Depends(get_db),
        telegram_user: dict = Depends(get_telegram_user_flexible)
):
    """Получение списка волонтёров для оставления отзывов"""
    print(f"📋 Getting reviewable volunteers for event {event_id}")

    # Получаем организатора
    organizer = crud.get_user_by_telegram_id(db, telegram_user['id'])
    if not organizer:
        raise HTTPException(status_code=404, detail="Organizer not found")

    # Проверяем, что это мероприятие организатора
    event = crud.get_event_by_id(db, event_id)
    if not event or event.organizer_id != organizer.id:
        raise HTTPException(status_code=403, detail="Access denied")

    # Проверяем, что мероприятие завершено
    if event.status != "completed":
        raise HTTPException(status_code=400, detail="Event must be completed to leave reviews")

    # Получаем волонтёров без отзывов
    try:
        reviewable = crud.get_reviewable_volunteers(db, event_id, organizer.id)
        return reviewable
    except Exception as e:
        print(f"❌ Error getting reviewable volunteers: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/volunteer/{volunteer_id}", response_model=List[schemas.ReviewResponse])
def get_volunteer_reviews(
        volunteer_id: int,
        db: Session = Depends(get_db)
):
    """Получение всех отзывов о волонтёре"""
    # Находим волонтёра по telegram_id
    if volunteer_id > 1000000000:  # Это telegram_id
        user = crud.get_user_by_telegram_id(db, volunteer_id)
        if user:
            volunteer_id = user.id

    reviews = crud.get_volunteer_reviews(db, volunteer_id)

    # Обогащаем данные
    result = []
    for review in reviews:
        event = crud.get_event_by_id(db, review.event_id)
        organizer = crud.get_user_by_id(db, review.organizer_id)

        result.append(schemas.ReviewResponse(
            id=review.id,
            event_id=review.event_id,
            volunteer_id=review.volunteer_id,
            organizer_id=review.organizer_id,
            rating=review.rating,
            comment=review.comment,
            created_at=review.created_at,
            volunteer_name="",  # Не нужно для отзывов о волонтёре
            event_title=event.title if event else "Unknown event",
            organizer_name=organizer.full_name if organizer else "Unknown"
        ))

    return result


@router.get("/my", response_model=List[schemas.ReviewResponse])
def get_my_reviews(
        db: Session = Depends(get_db),
        telegram_user: dict = Depends(get_telegram_user_flexible)
):
    """Получение отзывов текущего пользователя"""
    user = crud.get_user_by_telegram_id(db, telegram_user['id'])
    if not user:
        return []

    if user.role == "volunteer":
        return get_volunteer_reviews(user.id, db)
    elif user.role == "organizer":
        # Возвращаем отзывы, оставленные организатором
        reviews = crud.get_organizer_reviews(db, user.id)

        result = []
        for review in reviews:
            event = crud.get_event_by_id(db, review.event_id)
            volunteer = crud.get_user_by_id(db, review.volunteer_id)

            result.append(schemas.ReviewResponse(
                id=review.id,
                event_id=review.event_id,
                volunteer_id=review.volunteer_id,
                organizer_id=review.organizer_id,
                rating=review.rating,
                comment=review.comment,
                created_at=review.created_at,
                volunteer_name=volunteer.full_name if volunteer else "Unknown",
                event_title=event.title if event else "Unknown event",
                organizer_name=""  # Не нужно для отзывов организатора
            ))

        return result

    return []


@router.get("/event/{event_id}", response_model=List[schemas.ReviewResponse])
def get_event_reviews(
        event_id: int,
        db: Session = Depends(get_db)
):
    """Получение всех отзывов по мероприятию"""
    reviews = crud.get_event_reviews(db, event_id)

    result = []
    for review in reviews:
        volunteer = crud.get_user_by_id(db, review.volunteer_id)
        event = crud.get_event_by_id(db, review.event_id)

        result.append(schemas.ReviewResponse(
            id=review.id,
            event_id=review.event_id,
            volunteer_id=review.volunteer_id,
            organizer_id=review.organizer_id,
            rating=review.rating,
            comment=review.comment,
            created_at=review.created_at,
            volunteer_name=volunteer.full_name if volunteer else "Unknown",
            event_title=event.title if event else "Unknown event",
            organizer_name=""  # Не указываем для списка по мероприятию
        ))

    return result