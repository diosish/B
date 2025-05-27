from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List
from pydantic import BaseModel

from .. import crud, models, schemas
from ..database import get_db
from ..auth import get_telegram_user_flexible

router = APIRouter()


class ReviewCreate(BaseModel):
    volunteer_id: int
    event_id: int
    rating: int  # 1-5
    comment: str


class ReviewResponse(BaseModel):
    id: int
    event_id: int
    volunteer_id: int
    organizer_id: int
    rating: int
    comment: str
    created_at: datetime

    class Config:
        from_attributes = True


from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List
from pydantic import BaseModel

from .. import crud, models, schemas
from ..database import get_db
from ..auth import get_telegram_user_flexible
from ..bot import notify_review_received

router = APIRouter()


class ReviewCreate(BaseModel):
    volunteer_id: int
    event_id: int
    rating: int  # 1-5
    comment: str


class ReviewResponse(BaseModel):
    id: int
    event_id: int
    volunteer_id: int
    organizer_id: int
    rating: int
    comment: str
    created_at: str

    class Config:
        from_attributes = True


@router.post("/", response_model=ReviewResponse)
async def create_review(
        review: ReviewCreate,
        db: Session = Depends(get_db),
        telegram_user: dict = Depends(get_telegram_user_flexible)
):
    """Создание отзыва об волонтёре (только для организатора)"""

    print(f"⭐ Creating review for volunteer {review.volunteer_id} by user {telegram_user['id']}")

    # Проверяем, что пользователь - организатор
    organizer = crud.get_user_by_telegram_id(db, telegram_user['id'])
    if not organizer or organizer.role != "organizer":
        raise HTTPException(status_code=403, detail="Only organizers can create reviews")

    # Проверяем, что мероприятие существует и принадлежит организатору
    event = crud.get_event_by_id(db, review.event_id)
    if not event or event.organizer_id != organizer.id:
        raise HTTPException(status_code=403, detail="Event not found or access denied")

    # Проверяем, что мероприятие завершено
    if event.status != "completed":
        raise HTTPException(status_code=400, detail="Can only review completed events")

    # Проверяем, что волонтёр участвовал в мероприятии (заявка была одобрена)
    application = db.query(models.Application).filter(
        models.Application.event_id == review.event_id,
        models.Application.volunteer_id == review.volunteer_id,
        models.Application.status == "approved"
    ).first()

    if not application:
        raise HTTPException(
            status_code=400,
            detail="Can only review volunteers who were approved for this event"
        )

    # Проверяем, не оставлял ли уже отзыв
    existing_review = db.query(models.Review).filter(
        models.Review.event_id == review.event_id,
        models.Review.volunteer_id == review.volunteer_id,
        models.Review.organizer_id == organizer.id
    ).first()

    if existing_review:
        raise HTTPException(status_code=400, detail="Review already exists")

    # Проверяем рейтинг
    if review.rating < 1 or review.rating > 5:
        raise HTTPException(status_code=400, detail="Rating must be between 1 and 5")

    # Получаем данные волонтёра
    volunteer = crud.get_user_by_id(db, review.volunteer_id)
    if not volunteer:
        raise HTTPException(status_code=404, detail="Volunteer not found")

    # Создаём отзыв
    db_review = models.Review(
        event_id=review.event_id,
        volunteer_id=review.volunteer_id,
        organizer_id=organizer.id,
        rating=review.rating,
        comment=review.comment
    )

    db.add(db_review)
    db.commit()
    db.refresh(db_review)

    # Обновляем рейтинг волонтёра
    update_volunteer_rating(db, review.volunteer_id)

    # Отправляем уведомление волонтёру
    try:
        await notify_review_received(
            volunteer.telegram_id,
            event.title,
            review.rating,
            organizer.full_name
        )
        print(f"📱 Review notification sent to volunteer {volunteer.telegram_id}")
    except Exception as e:
        print(f"❌ Failed to send review notification: {e}")

    print(f"✅ Review created: {db_review.id}")
    return db_review


@router.get("/volunteer/{volunteer_id}", response_model=List[ReviewResponse])
def get_volunteer_reviews(
        volunteer_id: int,
        skip: int = Query(0),
        limit: int = Query(10),
        db: Session = Depends(get_db)
):
    """Получение отзывов о волонтёре"""

    reviews = db.query(models.Review).filter(
        models.Review.volunteer_id == volunteer_id
    ).order_by(models.Review.created_at.desc()).offset(skip).limit(limit).all()

    return reviews


@router.get("/event/{event_id}/reviewable")
def get_reviewable_volunteers(
        event_id: int,
        db: Session = Depends(get_db),
        telegram_user: dict = Depends(get_telegram_user_flexible)
):
    """Получение списка волонтёров, которым можно оставить отзыв"""

    # Проверяем, что пользователь - организатор этого мероприятия
    organizer = crud.get_user_by_telegram_id(db, telegram_user['id'])
    if not organizer:
        raise HTTPException(status_code=404, detail="Organizer not found")

    event = crud.get_event_by_id(db, event_id)
    if not event or event.organizer_id != organizer.id:
        raise HTTPException(status_code=403, detail="Access denied")

    # Проверяем, что мероприятие завершено
    if event.status != "completed":
        raise HTTPException(status_code=400, detail="Event is not completed")

    # Получаем одобренных волонтёров без отзывов
    approved_volunteers = db.query(models.Application).filter(
        models.Application.event_id == event_id,
        models.Application.status == "approved"
    ).all()

    reviewable = []
    for application in approved_volunteers:
        # Проверяем, есть ли уже отзыв
        existing_review = db.query(models.Review).filter(
            models.Review.event_id == event_id,
            models.Review.volunteer_id == application.volunteer_id,
            models.Review.organizer_id == organizer.id
        ).first()

        if not existing_review:
            volunteer = crud.get_user_by_id(db, application.volunteer_id)
            if volunteer:
                reviewable.append({
                    "volunteer": volunteer,
                    "application": application
                })

    return reviewable


@router.get("/stats/{volunteer_id}")
def get_volunteer_rating_stats(volunteer_id: int, db: Session = Depends(get_db)):
    """Получение статистики рейтинга волонтёра"""

    volunteer = crud.get_user_by_id(db, volunteer_id)
    if not volunteer:
        raise HTTPException(status_code=404, detail="Volunteer not found")

    # Общая статистика
    stats = db.query(
        func.count(models.Review.id).label('total_reviews'),
        func.avg(models.Review.rating).label('average_rating'),
        func.max(models.Review.rating).label('max_rating'),
        func.min(models.Review.rating).label('min_rating')
    ).filter(models.Review.volunteer_id == volunteer_id).first()

    # Распределение по рейтингам
    rating_distribution = db.query(
        models.Review.rating,
        func.count(models.Review.id).label('count')
    ).filter(
        models.Review.volunteer_id == volunteer_id
    ).group_by(models.Review.rating).all()

    return {
        "volunteer_id": volunteer_id,
        "total_reviews": stats.total_reviews or 0,
        "average_rating": round(float(stats.average_rating or 0), 2),
        "max_rating": stats.max_rating or 0,
        "min_rating": stats.min_rating or 0,
        "current_rating": volunteer.rating or 0,
        "rating_distribution": {str(rating): count for rating, count in rating_distribution}
    }


def update_volunteer_rating(db: Session, volunteer_id: int):
    """Обновление рейтинга волонтёра на основе отзывов"""

    average_rating = db.query(func.avg(models.Review.rating)).filter(
        models.Review.volunteer_id == volunteer_id
    ).scalar()

    if average_rating:
        volunteer = crud.get_user_by_id(db, volunteer_id)
        if volunteer:
            volunteer.rating = round(float(average_rating), 2)
            db.commit()
            print(f"✅ Updated volunteer {volunteer_id} rating to {volunteer.rating}")


@router.delete("/{review_id}")
def delete_review(
        review_id: int,
        db: Session = Depends(get_db),
        telegram_user: dict = Depends(get_telegram_user_flexible)
):
    """Удаление отзыва (только автор может удалить)"""

    organizer = crud.get_user_by_telegram_id(db, telegram_user['id'])
    if not organizer:
        raise HTTPException(status_code=404, detail="User not found")

    review = db.query(models.Review).filter(models.Review.id == review_id).first()
    if not review:
        raise HTTPException(status_code=404, detail="Review not found")

    if review.organizer_id != organizer.id:
        raise HTTPException(status_code=403, detail="Access denied")

    volunteer_id = review.volunteer_id

    db.delete(review)
    db.commit()

    # Обновляем рейтинг волонтёра
    update_volunteer_rating(db, volunteer_id)

    return {"message": "Review deleted successfully"}