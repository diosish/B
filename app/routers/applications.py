from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from .. import crud, models, schemas
from ..database import get_db
from ..auth import get_telegram_user_flexible
from ..bot import notify_application_status

router = APIRouter()


@router.get("/event/{event_id}", response_model=List[schemas.ApplicationWithVolunteer])
def get_event_applications(
        event_id: int,
        db: Session = Depends(get_db),
        telegram_user: dict = Depends(get_telegram_user_flexible)
):
    """Получение заявок на мероприятие (для организатора)"""

    print(f"📋 Getting applications for event {event_id} by user {telegram_user['id']}")

    # Проверяем, что пользователь - организатор этого мероприятия
    organizer = crud.get_user_by_telegram_id(db, telegram_user['id'])
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
        db: Session = Depends(get_db),
        telegram_user: dict = Depends(get_telegram_user_flexible)
):
    """Обновление статуса заявки"""

    print(f"🔄 Updating application {application_id} status to {status} by user {telegram_user['id']}")

    # Проверяем права организатора
    organizer = crud.get_user_by_telegram_id(db, telegram_user['id'])
    if not organizer:
        raise HTTPException(status_code=404, detail="Organizer not found")

    application = db.query(models.Application).filter(
        models.Application.id == application_id
    ).first()

    if not application:
        raise HTTPException(status_code=404, detail="Application not found")

    # Проверяем, что организатор имеет право изменять эту заявку
    event = crud.get_event_by_id(db, application.event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")

    if event.organizer_id != organizer.id:
        raise HTTPException(status_code=403, detail="Access denied")

    # Обновляем статус
    old_status = application.status
    application.status = status
    db.commit()
    db.refresh(application)

    print(f"✅ Application {application_id} status updated from {old_status} to {status}")

    # Отправляем уведомление волонтёру
    if old_status != status and status in ["approved", "rejected"]:
        volunteer = crud.get_user_by_id(db, application.volunteer_id)
        if volunteer:
            try:
                await notify_application_status(
                    volunteer.telegram_id,
                    event.title,
                    status
                )
                print(f"📱 Notification sent to volunteer {volunteer.telegram_id}")
            except Exception as e:
                print(f"❌ Failed to send notification: {e}")

    return {
        "message": f"Application status updated to {status}",
        "application": application
    }


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


# Альтернативный endpoint для получения заявок текущего пользователя
@router.get("/my", response_model=List[schemas.ApplicationWithEvent])
def get_my_applications(
        db: Session = Depends(get_db),
        telegram_user: dict = Depends(get_telegram_user_flexible)
):
    """Получение заявок текущего пользователя"""
    return get_volunteer_applications(telegram_user['id'], db)

@router.delete("/{application_id}")
async def withdraw_application(
        application_id: int,
        db: Session = Depends(get_db),
        telegram_user: dict = Depends(get_telegram_user_flexible)
):
    """Отзыв заявки волонтером"""

    print(f"🔄 Withdrawing application {application_id} by user {telegram_user['id']}")

    # Получаем волонтёра
    volunteer = crud.get_user_by_telegram_id(db, telegram_user['id'])
    if not volunteer:
        raise HTTPException(status_code=404, detail="Volunteer not found")

    # Получаем заявку
    application = db.query(models.Application).filter(
        models.Application.id == application_id
    ).first()

    if not application:
        raise HTTPException(status_code=404, detail="Application not found")

    # Проверяем, что это заявка текущего пользователя
    if application.volunteer_id != volunteer.id:
        raise HTTPException(status_code=403, detail="Access denied")

    # Проверяем, что заявку можно отозвать (только pending заявки)
    if application.status != "pending":
        raise HTTPException(
            status_code=400,
            detail=f"Cannot withdraw application with status: {application.status}"
        )

    try:
        # Удаляем заявку
        db.delete(application)
        db.commit()

        print(f"✅ Application {application_id} withdrawn successfully")

        return {
            "message": "Application withdrawn successfully",
            "application_id": application_id
        }

    except Exception as e:
        print(f"❌ Error withdrawing application: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to withdraw application")