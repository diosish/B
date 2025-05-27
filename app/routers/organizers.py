from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from .. import crud, models, schemas
from ..database import get_db

router = APIRouter()

@router.post("/register", response_model=schemas.UserResponse)
def register_organizer(user: schemas.UserCreate, db: Session = Depends(get_db)):
    user.role = "organizer"
    db_user = crud.get_user_by_telegram_id(db, user.telegram_id)
    if db_user:
        raise HTTPException(status_code=400, detail="User already registered")
    return crud.create_user(db, user)

@router.get("/profile/{telegram_id}", response_model=schemas.UserResponse)
def get_organizer_profile(telegram_id: int, db: Session = Depends(get_db)):
    db_user = crud.get_user_by_telegram_id(db, telegram_id)
    if not db_user or db_user.role != "organizer":
        raise HTTPException(status_code=404, detail="Organizer not found")
    return db_user