from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel

from .. import crud, models, schemas
from ..database import get_db
from ..auth import get_telegram_user_flexible

router = APIRouter()


class EventStatusUpdate(BaseModel):
    status: str


@router.get("/", response_model=List[schemas.EventResponse])
def list_events(
        skip: int = 0,
        limit: int = 100,
        city: Optional[str] = Query(None),
        organizer_id: Optional[int] = Query(None),
        db: Session = Depends(get_db)
):
    """Получение списка мероприятий с фильтрацией"""
    query = db.query(models.Event)

    # Фильтр по городу
    if city:
        query = query.filter(models.Event.city.ilike(f"%{city}%"))

    # Фильтр по организатору (для получения своих мероприятий)
    if organizer_id:
        # Находим пользователя по telegram_id (если передан как organizer_id)
        if organizer_id > 1000000000:  # Это telegram_id
            db_user = crud.get_user_by_telegram_id(db, organizer_id)
            if db_user:
                organizer_id = db_user.id

        query = query.filter(models.Event.organizer_id == organizer_id)

    # Показываем только активные мероприятия для общего списка
    if not organizer_id:
        query = query.filter(models.Event.status == "active")

    return query.offset(skip).limit(limit).all()


@router.post("/", response_model=schemas.EventResponse)
def create_event(
        event: schemas.EventCreate,
        organizer_id: Optional[int] = Query(None),
        db: Session = Depends(get_db),
        telegram_user: dict = Depends(get_telegram_user_flexible)
):
    """Создание мероприятия"""
    print(f"🎯 Creating event for user: {telegram_user}")

    # Находим организатора в БД
    db_user = crud.get_user_by_telegram_id(db, telegram_user['id'])
    if not db_user:
        raise HTTPException(status_code=404, detail="User not registered")

    if db_user.role != "organizer":
        raise HTTPException(status_code=403, detail="Only organizers can create events")

    return crud.create_event(db, event, db_user.id)


@router.get("/{event_id}", response_model=schemas.EventResponse)
def get_event(event_id: int, db: Session = Depends(get_db)):
    """Получение конкретного мероприятия"""
    db_event = db.query(models.Event).filter(models.Event.id == event_id).first()
    if not db_event:
        raise HTTPException(status_code=404, detail="Event not found")
    return db_event


@router.put("/{event_id}/status")
def update_event_status(
        event_id: int,
        status_update: EventStatusUpdate,
        db: Session = Depends(get_db),
        telegram_user: dict = Depends(get_telegram_user_flexible)
):
    """Обновление статуса мероприятия"""
    print(f"🔄 Updating event {event_id} status to {status_update.status}")

    # Проверяем, что пользователь - организатор этого мероприятия
    db_user = crud.get_user_by_telegram_id(db, telegram_user['id'])
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")

    event = db.query(models.Event).filter(models.Event.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")

    if event.organizer_id != db_user.id:
        raise HTTPException(status_code=403, detail="Access denied")

    # Проверяем валидность статуса
    valid_statuses = ["active", "completed", "cancelled"]
    if status_update.status not in valid_statuses:
        raise HTTPException(status_code=400, detail=f"Invalid status. Must be one of: {valid_statuses}")

    # Обновляем статус
    old_status = event.status
    event.status = status_update.status
    db.commit()
    db.refresh(event)

    print(f"✅ Event {event_id} status updated from {old_status} to {status_update.status}")

    return {
        "message": f"Event status updated to {status_update.status}",
        "event": event
    }


@router.get("/{event_id}/applications")
def get_event_applications(
        event_id: int,
        db: Session = Depends(get_db),
        telegram_user: dict = Depends(get_telegram_user_flexible)
):
    """Получение заявок на мероприятие (только для организатора)"""
    # Проверяем, что пользователь - организатор этого мероприятия
    db_user = crud.get_user_by_telegram_id(db, telegram_user['id'])
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")

    event = db.query(models.Event).filter(models.Event.id == event_id).first()
    if not event or event.organizer_id != db_user.id:
        raise HTTPException(status_code=403, detail="Access denied")

    applications = db.query(models.Application).filter(
        models.Application.event_id == event_id
    ).all()

    return applications


@router.delete("/{event_id}")
def delete_event(
        event_id: int,
        db: Session = Depends(get_db),
        telegram_user: dict = Depends(get_telegram_user_flexible)
):
    """Удаление мероприятия (только для организатора)"""
    print(f"🗑️ Deleting event {event_id}")

    # Проверяем, что пользователь - организатор этого мероприятия
    db_user = crud.get_user_by_telegram_id(db, telegram_user['id'])
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")

    event = db.query(models.Event).filter(models.Event.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")

    if event.organizer_id != db_user.id:
        raise HTTPException(status_code=403, detail="Access denied")

    try:
        # Удаляем связанные данные в правильном порядке
        # Сначала отзывы
        db.query(models.Review).filter(models.Review.event_id == event_id).delete()

        # Затем заявки
        db.query(models.Application).filter(models.Application.event_id == event_id).delete()

        # И наконец само мероприятие
        db.delete(event)
        db.commit()

        print(f"✅ Event {event_id} deleted successfully")
        return {"message": "Event deleted successfully", "event_id": event_id}

    except Exception as e:
        print(f"❌ Error deleting event: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to delete event: {str(e)}")