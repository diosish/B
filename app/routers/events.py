from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from .. import crud, models, schemas
from ..database import get_db
from ..auth import get_telegram_user

router = APIRouter()


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
        telegram_user: dict = Depends(get_telegram_user)
):
    """Создание мероприятия"""
    # Находим организатора в БД
    db_user = crud.get_user_by_telegram_id(db, telegram_user['id'])
    if not db_user:
        raise HTTPException(status_code=404, detail="User not registered")

    return crud.create_event(db, event, db_user.id)


@router.get("/{event_id}", response_model=schemas.EventResponse)
def get_event(event_id: int, db: Session = Depends(get_db)):
    """Получение конкретного мероприятия"""
    db_event = db.query(models.Event).filter(models.Event.id == event_id).first()
    if not db_event:
        raise HTTPException(status_code=404, detail="Event not found")
    return db_event


@router.get("/{event_id}/applications")
def get_event_applications(
        event_id: int,
        db: Session = Depends(get_db),
        telegram_user: dict = Depends(get_telegram_user)
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


@router.get("/test")
def test_events():
    return {"message": "Events API is working", "status": "ok"}
