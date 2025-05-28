from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from typing import List
from datetime import datetime, timedelta
from fastapi.responses import Response

from .. import crud, models, schemas
from ..database import get_db
from ..auth import get_telegram_user_flexible

router = APIRouter()


@router.get("/check")
def check_admin_access(telegram_user: dict = Depends(get_telegram_user_flexible)):
    """Проверка прав администратора"""
    # Простая проверка - можно расширить логикой проверки админов
    admin_ids = [123456789]  # Добавьте сюда telegram_id администраторов

    if telegram_user['id'] not in admin_ids:
        raise HTTPException(status_code=403, detail="Admin access required")

    return {"message": "Admin access granted"}


@router.get("/stats")
def get_system_stats(
        db: Session = Depends(get_db),
        telegram_user: dict = Depends(get_telegram_user_flexible)
):
    """Получение статистики системы"""

    # Проверка прав (упрощенная)
    admin_ids = [123456789]
    if telegram_user['id'] not in admin_ids:
        raise HTTPException(status_code=403, detail="Admin access required")

    stats = {
        "total_users": db.query(models.User).count(),
        "total_volunteers": db.query(models.User).filter(models.User.role == "volunteer").count(),
        "total_organizers": db.query(models.User).filter(models.User.role == "organizer").count(),
        "total_events": db.query(models.Event).count(),
        "active_events": db.query(models.Event).filter(models.Event.status == "active").count(),
        "completed_events": db.query(models.Event).filter(models.Event.status == "completed").count(),
        "total_applications": db.query(models.Application).count(),
        "pending_applications": db.query(models.Application).filter(models.Application.status == "pending").count(),
        "approved_applications": db.query(models.Application).filter(models.Application.status == "approved").count(),
    }

    return stats


@router.get("/users", response_model=List[schemas.UserResponse])
def list_all_users(
        skip: int = 0,
        limit: int = 100,
        db: Session = Depends(get_db),
        telegram_user: dict = Depends(get_telegram_user_flexible)
):
    """Список всех пользователей"""

    admin_ids = [123456789]
    if telegram_user['id'] not in admin_ids:
        raise HTTPException(status_code=403, detail="Admin access required")

    return db.query(models.User).order_by(models.User.created_at.desc()).offset(skip).limit(limit).all()


@router.get("/events", response_model=List[schemas.EventResponse])
def list_all_events(
        skip: int = 0,
        limit: int = 100,
        db: Session = Depends(get_db),
        telegram_user: dict = Depends(get_telegram_user_flexible)
):
    """Список всех мероприятий"""

    admin_ids = [123456789]
    if telegram_user['id'] not in admin_ids:
        raise HTTPException(status_code=403, detail="Admin access required")

    return db.query(models.Event).order_by(models.Event.created_at.desc()).offset(skip).limit(limit).all()


@router.put("/users/{user_id}/status")
def update_user_status(
        user_id: int,
        status_data: dict,
        db: Session = Depends(get_db),
        telegram_user: dict = Depends(get_telegram_user_flexible)
):
    """Обновление статуса пользователя"""

    admin_ids = [123456789]
    if telegram_user['id'] not in admin_ids:
        raise HTTPException(status_code=403, detail="Admin access required")

    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.is_active = status_data.get('is_active', user.is_active)
    db.commit()
    db.refresh(user)

    return {"message": "User status updated", "user": user}


@router.delete("/events/{event_id}")
def delete_event(
        event_id: int,
        db: Session = Depends(get_db),
        telegram_user: dict = Depends(get_telegram_user_flexible)
):
    """Удаление мероприятия"""

    admin_ids = [123456789]
    if telegram_user['id'] not in admin_ids:
        raise HTTPException(status_code=403, detail="Admin access required")

    event = db.query(models.Event).filter(models.Event.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")

    # Удаляем связанные заявки и отзывы
    db.query(models.Application).filter(models.Application.event_id == event_id).delete()
    db.query(models.Review).filter(models.Review.event_id == event_id).delete()
    db.delete(event)
    db.commit()

    return {"message": "Event deleted successfully"}


@router.get("/export/users")
def export_users_csv(
        db: Session = Depends(get_db),
        telegram_user: dict = Depends(get_telegram_user_flexible)
):
    """Экспорт пользователей в CSV"""

    admin_ids = [123456789]
    if telegram_user['id'] not in admin_ids:
        raise HTTPException(status_code=403, detail="Admin access required")

    users = db.query(models.User).all()

    csv_content = "ID,Telegram ID,Имя,Город,Роль,Статус,Дата регистрации,Тип волонтёра,Рейтинг\n"

    for user in users:
        csv_content += f"{user.id},"
        csv_content += f"{user.telegram_id},"
        csv_content += f'"{user.full_name}",'
        csv_content += f'"{user.city or ""}",'
        csv_content += f"{user.role},"
        csv_content += f"{'Активен' if user.is_active else 'Неактивен'},"
        csv_content += f'"{user.created_at.strftime("%d.%m.%Y")}",'
        csv_content += f'"{user.volunteer_type or ""}",'
        csv_content += f"{user.rating or 0}\n"

    return Response(
        content=csv_content,
        media_type="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename=users_export_{datetime.now().strftime('%Y%m%d')}.csv"
        }
    )


@router.post("/cleanup/events")
def cleanup_old_events(
        db: Session = Depends(get_db),
        telegram_user: dict = Depends(get_telegram_user_flexible)
):
    """Очистка старых завершенных мероприятий"""

    admin_ids = [123456789]
    if telegram_user['id'] not in admin_ids:
        raise HTTPException(status_code=403, detail="Admin access required")

    # Удаляем завершенные мероприятия старше 30 дней
    cutoff_date = datetime.utcnow() - timedelta(days=30)

    old_events = db.query(models.Event).filter(
        and_(
            models.Event.status == "completed",
            models.Event.updated_at < cutoff_date
        )
    ).all()

    deleted_count = 0
    for event in old_events:
        # Удаляем связанные данные
        db.query(models.Application).filter(models.Application.event_id == event.id).delete()
        db.query(models.Review).filter(models.Review.event_id == event.id).delete()
        db.delete(event)
        deleted_count += 1

    db.commit()

    return {"message": f"Deleted {deleted_count} old events", "deleted_count": deleted_count}


@router.put("/applications/{application_id}/status")
def update_application_status(application_id: int, status: str, db: Session = Depends(get_db)):
    if status not in ["pending", "approved", "rejected"]:
        raise HTTPException(status_code=400, detail="Invalid status")

    application = crud.update_application_status(db, application_id, status)
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")

    return {"message": "Status updated successfully"}