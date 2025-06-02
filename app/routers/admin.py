# app/routers/admin.py - ИСПРАВЛЕННЫЙ РОУТЕР
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from typing import List
from datetime import datetime, timedelta
from fastapi.responses import Response

from .. import crud, models, schemas
from ..database import get_db
from ..admin_auth import require_admin_auth  # Изменено: используем админ авторизацию

router = APIRouter()


@router.get("/stats")
def get_system_stats(
        db: Session = Depends(get_db),
        admin_session: dict = Depends(require_admin_auth)  # Изменено
):
    """Получение статистики системы"""
    print(f"📊 Getting system stats for admin session: {admin_session['session_id'][:8]}...")

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
        admin_session: dict = Depends(require_admin_auth)  # Изменено
):
    """Список всех пользователей"""
    print(f"👥 Getting users list for admin session: {admin_session['session_id'][:8]}...")

    return db.query(models.User).order_by(models.User.created_at.desc()).offset(skip).limit(limit).all()


@router.get("/events", response_model=List[schemas.EventResponse])
def list_all_events(
        skip: int = 0,
        limit: int = 100,
        db: Session = Depends(get_db),
        admin_session: dict = Depends(require_admin_auth)  # Изменено
):
    """Список всех мероприятий"""
    print(f"📅 Getting events list for admin session: {admin_session['session_id'][:8]}...")

    return db.query(models.Event).order_by(models.Event.created_at.desc()).offset(skip).limit(limit).all()


@router.put("/users/{user_id}/status")
def update_user_status(
        user_id: int,
        status_data: dict,
        db: Session = Depends(get_db),
        admin_session: dict = Depends(require_admin_auth)  # Изменено
):
    """Обновление статуса пользователя"""
    print(f"🔄 Updating user {user_id} status by admin: {admin_session['session_id'][:8]}...")

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
        admin_session: dict = Depends(require_admin_auth)  # Изменено
):
    """Удаление мероприятия"""
    print(f"🗑️ Deleting event {event_id} by admin: {admin_session['session_id'][:8]}...")

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
        admin_session: dict = Depends(require_admin_auth)  # Изменено
):
    """Экспорт пользователей в CSV"""
    print(f"📊 Exporting users by admin: {admin_session['session_id'][:8]}...")

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
        admin_session: dict = Depends(require_admin_auth)  # Изменено
):
    """Очистка старых завершенных мероприятий"""
    print(f"🧹 Cleaning up old events by admin: {admin_session['session_id'][:8]}...")

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
def update_application_status(
        application_id: int,
        status: str,
        db: Session = Depends(get_db),
        admin_session: dict = Depends(require_admin_auth)  # Изменено
):
    """Обновление статуса заявки администратором"""
    print(f"🔄 Updating application {application_id} status by admin: {admin_session['session_id'][:8]}...")

    if status not in ["pending", "approved", "rejected"]:
        raise HTTPException(status_code=400, detail="Invalid status")

    application = crud.update_application_status(db, application_id, status)
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")

    return {"message": "Status updated successfully"}


# Новый endpoint для проверки прав администратора (совместимость со старым кодом)
@router.get("/check")
def check_admin_access(admin_session: dict = Depends(require_admin_auth)):
    """Проверка прав администратора"""
    return {
        "message": "Admin access granted",
        "session_id": admin_session["session_id"][:8] + "...",
        "role": admin_session["role"]
    }


# Endpoint для получения информации о системе
@router.get("/system-info")
def get_system_info(admin_session: dict = Depends(require_admin_auth)):
    """Получение информации о системе"""
    import psutil
    import os

    return {
        "system": {
            "cpu_percent": psutil.cpu_percent(),
            "memory_percent": psutil.virtual_memory().percent,
            "disk_percent": psutil.disk_usage('/').percent,
        },
        "environment": {
            "environment": os.getenv("ENVIRONMENT", "development"),
            "database_url": os.getenv("DATABASE_URL", "").split("@")[-1] if "@" in os.getenv("DATABASE_URL",
                                                                                             "") else "local",
            "webapp_url": os.getenv("WEBAPP_URL", ""),
        },
        "admin_session": {
            "session_id": admin_session["session_id"][:8] + "...",
            "role": admin_session["role"]
        }
    }