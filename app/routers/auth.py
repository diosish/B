from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional

from .. import crud, models, schemas
from ..database import get_db
from ..auth import get_telegram_user_flexible

router = APIRouter()


class ProfileUpdateRequest(BaseModel):
    full_name: Optional[str] = None
    city: Optional[str] = None
    volunteer_type: Optional[str] = None
    skills: Optional[str] = None
    org_type: Optional[str] = None
    org_name: Optional[str] = None
    inn: Optional[str] = None
    description: Optional[str] = None


@router.get("/check")
def check_user_registration(
        telegram_id: int = Query(...),
        db: Session = Depends(get_db)
):
    """Проверка регистрации пользователя по Telegram ID"""

    print(f"🔍 Checking registration for user: {telegram_id}")

    user = crud.get_user_by_telegram_id(db, telegram_id)

    if not user:
        print(f"❌ User {telegram_id} not found")
        return {
            "registered": False,
            "user": None
        }

    print(f"✅ User {telegram_id} found: {user.role}")
    return {
        "registered": True,
        "user": {
            "id": user.id,
            "telegram_id": user.telegram_id,
            "full_name": user.full_name,
            "role": user.role,
            "city": user.city,
            "created_at": user.created_at,
            "volunteer_type": user.volunteer_type if user.role == "volunteer" else None,
            "skills": user.skills if user.role == "volunteer" else None,
            "rating": user.rating if user.role == "volunteer" else None,
            "org_type": user.org_type if user.role == "organizer" else None,
            "org_name": user.org_name if user.role == "organizer" else None,
            "inn": user.inn if user.role == "organizer" else None,
            "description": user.description if user.role == "organizer" else None
        }
    }


@router.get("/my-profile")
def get_my_profile(
        db: Session = Depends(get_db),
        telegram_user: dict = Depends(get_telegram_user_flexible)
):
    """Получение профиля текущего пользователя"""

    user = crud.get_user_by_telegram_id(db, telegram_user['id'])
    if not user:
        return {
            "registered": False,
            "user": None
        }

    return {
        "registered": True,
        "user": {
            "id": user.id,
            "telegram_id": user.telegram_id,
            "full_name": user.full_name,
            "role": user.role,
            "city": user.city,
            "created_at": user.created_at,
            "volunteer_type": user.volunteer_type if user.role == "volunteer" else None,
            "skills": user.skills if user.role == "volunteer" else None,
            "rating": user.rating if user.role == "volunteer" else None,
            "org_type": user.org_type if user.role == "organizer" else None,
            "org_name": user.org_name if user.role == "organizer" else None,
            "inn": user.inn if user.role == "organizer" else None,
            "description": user.description if user.role == "organizer" else None
        }
    }


@router.delete("/profile")
def delete_user_profile(
        telegram_id: int = Query(...),
        db: Session = Depends(get_db)
):
    """Удаление профиля пользователя"""

    print(f"🗑️ Deleting profile for user: {telegram_id}")

    user = crud.get_user_by_telegram_id(db, telegram_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    try:
        # Удаляем связанные данные
        # Заявки пользователя
        db.query(models.Application).filter(models.Application.volunteer_id == user.id).delete()

        # Отзывы о пользователе (если волонтер)
        db.query(models.Review).filter(models.Review.volunteer_id == user.id).delete()

        # Отзывы, оставленные пользователем (если организатор)
        db.query(models.Review).filter(models.Review.organizer_id == user.id).delete()

        # Мероприятия пользователя (если организатор)
        if user.role == "organizer":
            user_events = db.query(models.Event).filter(models.Event.organizer_id == user.id).all()
            for event in user_events:
                # Удаляем заявки на мероприятия
                db.query(models.Application).filter(models.Application.event_id == event.id).delete()
                # Удаляем отзывы к мероприятиям
                db.query(models.Review).filter(models.Review.event_id == event.id).delete()

            # Удаляем сами мероприятия
            db.query(models.Event).filter(models.Event.organizer_id == user.id).delete()

        # Удаляем самого пользователя
        db.delete(user)
        db.commit()

        print(f"✅ Profile deleted successfully for user: {telegram_id}")
        return {"message": "Profile deleted successfully"}

    except Exception as e:
        print(f"❌ Error deleting profile: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to delete profile")


@router.delete("/my-profile")
def delete_my_profile(
        db: Session = Depends(get_db),
        telegram_user: dict = Depends(get_telegram_user_flexible)
):
    """Удаление профиля текущего пользователя"""
    return delete_user_profile(telegram_user['id'], db)

@router.put("/profile")
def update_user_profile(
        telegram_id: int = Query(...),
        profile_data: ProfileUpdateRequest = ...,
        db: Session = Depends(get_db)
):
    """Обновление профиля пользователя"""

    print(f"🔄 Updating profile for user: {telegram_id}")

    user = crud.get_user_by_telegram_id(db, telegram_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Обновляем только переданные поля
    update_data = profile_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        if hasattr(user, field) and value is not None:
            setattr(user, field, value)

    db.commit()
    db.refresh(user)

    print(f"✅ Profile updated for user: {telegram_id}")
    return {"message": "Profile updated successfully", "user": user}


@router.put("/my-profile")
def update_my_profile(
        profile_data: ProfileUpdateRequest,
        db: Session = Depends(get_db),
        telegram_user: dict = Depends(get_telegram_user_flexible)
):
    """Обновление профиля текущего пользователя"""

    print(f"🔄 Updating profile for current user: {telegram_user['id']}")

    user = crud.get_user_by_telegram_id(db, telegram_user['id'])
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Обновляем только переданные поля
    update_data = profile_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        if hasattr(user, field) and value is not None:
            setattr(user, field, value)

    db.commit()
    db.refresh(user)

    print(f"✅ Profile updated for current user: {telegram_user['id']}")
    return {"message": "Profile updated successfully", "user": user}