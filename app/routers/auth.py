from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional

from .. import crud, models, schemas
from ..database import get_db

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

    user = crud.get_user_by_telegram_id(db, telegram_id)

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


@router.put("/profile")
def update_user_profile(
        telegram_id: int = Query(...),
        profile_data: ProfileUpdateRequest = ...,
        db: Session = Depends(get_db)
):
    """Обновление профиля пользователя"""

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

    return {"message": "Profile updated successfully", "user": user}