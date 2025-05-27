from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from .. import crud, models, schemas
from ..database import get_db
from ..auth import verify_telegram_auth

router = APIRouter()

@router.post("/register", response_model=schemas.UserResponse)
def register_volunteer(user: schemas.UserCreate, db: Session = Depends(get_db)):
    db_user = crud.get_user_by_telegram_id(db, user.telegram_id)
    if db_user:
        raise HTTPException(status_code=400, detail="User already registered")
    return crud.create_user(db, user)

@router.get("/profile/{telegram_id}", response_model=schemas.UserResponse)
def get_volunteer_profile(telegram_id: int, db: Session = Depends(get_db)):
    db_user = crud.get_user_by_telegram_id(db, telegram_id)
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user

@router.get("/applications/{volunteer_id}", response_model=List[schemas.ApplicationResponse])
def get_volunteer_applications(volunteer_id: int, db: Session = Depends(get_db)):
    return crud.get_applications_by_volunteer(db, volunteer_id)

@router.post("/apply", response_model=schemas.ApplicationResponse)
def apply_to_event(application: schemas.ApplicationCreate, db: Session = Depends(get_db)):
    return crud.create_application(db, application)