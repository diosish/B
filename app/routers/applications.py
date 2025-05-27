from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from .. import crud, models, schemas
from ..database import get_db
from ..bot import notify_application_status

router = APIRouter()


@router.get("/event/{event_id}", response_model=List[schemas.ApplicationWithVolunteer])
def get_event_applications(
        event_id: int,
        organizer_telegram_id: int = Query(...),
        db: Session = Depends(get_db)
):
    """Получение заявок на мероприятие (для организатора)"""

    # Проверяем, что пользователь - организатор этого мероприятия
    organizer = crud.get_user_by_telegram_id(db, organizer_telegram_id)
    if not organizer:
        raise HTTPException(status_code=404, detail="Organizer not found")

    event = crud.get_event_by_id(db, event_id)
    if not event or event.organizer_id != organizer.id:
        raise HTTPException(status_code=403, detail="Access denied")

    # Получаем заявки с информацией о волонтёрах
    applications = db.query(models.Application).filter(
        models.Application.event_id == event_id
    ).all()

    # Добавляем информацию о волонтёрах
    result = []
    for app in applications:
        volunteer = crud.get_user_by_id(db, app.volunteer_id)
        app_data = {
            "id": app.id,
            "event_id": app.event_id,
            "volunteer_id": app.volunteer_id,
            "status": app.status,
            "applied_at": app.applied_at,
            "volunteer": volunteer
        }
        result.append(app_data)

    return result


@router.put("/{application_id}/status")
async def update_application_status(
        application_id: int,
        status: str = Query(..., regex="^(approved|rejected|pending)$"),
        organizer_telegram_id: int = Query(...),
        db: Session = Depends(get_db)
):
    """Обновление статуса заявки"""

    # Проверяем права организатора
    organizer = crud.get_user_by_telegram_id(db, organizer_telegram_id)
    if not organizer:
        raise HTTPException(status_code=404, detail="Organizer not found")

    application = db.query(models.Application).filter(
        models.Application.id == application_id
    ).first()

    if not application:
        raise HTTPException(status_code=404, detail="Application not found")

    # Проверяем, что организатор имеет право изменять эту заявку
    event = crud.get_event_by_id(db, application.event_id)
    if event.organizer_id != organizer.id:
        raise HTTPException(status_code=403, detail="Access denied")

    # Обновляем статус
    old_status = application.status
    application.status = status
    db.commit()

    # Отправляем уведомление волонтёру
    if old_status != status and status in ["approved", "rejected"]:
        volunteer = crud.get_user_by_id(db, application.volunteer_id)
        if volunteer:
            await notify_application_status(
                volunteer.telegram_id,
                event.title,
                status
            )

    return {"message": f"Application status updated to {status}"}


@router.get("/volunteer/{telegram_id}", response_model=List[schemas.ApplicationWithEvent])
def get_volunteer_applications(
        telegram_id: int,
        db: Session = Depends(get_db)
):
    """Получение заявок волонтёра с информацией о мероприятиях"""

    volunteer = crud.get_user_by_telegram_id(db, telegram_id)
    if not volunteer:
        raise HTTPException(status_code=404, detail="Volunteer not found")

    applications = crud.get_applications_by_volunteer(db, volunteer.id)

    # Добавляем информацию о мероприятиях
    result = []
    for app in applications:
        event = crud.get_event_by_id(db, app.event_id)
        app_data = {
            "id": app.id,
            "event_id": app.event_id,
            "volunteer_id": app.volunteer_id,
            "status": app.status,
            "applied_at": app.applied_at,
            "event": event
        }
        result.append(app_data)

    return result