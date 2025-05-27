from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class UserCreate(BaseModel):
    telegram_id: int
    full_name: str
    city: Optional[str] = None
    role: str = "volunteer"
    volunteer_type: Optional[str] = None
    skills: Optional[str] = None
    org_type: Optional[str] = None
    org_name: Optional[str] = None
    inn: Optional[str] = None


class UserResponse(BaseModel):
    id: int
    telegram_id: int
    full_name: str
    city: Optional[str]
    role: str
    rating: Optional[float]
    created_at: datetime

    class Config:
        from_attributes = True


class EventCreate(BaseModel):
    title: str
    description: Optional[str] = None
    city: Optional[str] = None
    date: Optional[datetime] = None
    duration: Optional[int] = None
    payment: Optional[float] = None
    work_type: Optional[str] = None


class EventResponse(BaseModel):
    id: int
    title: str
    description: Optional[str]
    city: Optional[str]
    date: Optional[datetime]
    duration: Optional[int]
    payment: Optional[float]
    work_type: Optional[str]
    status: str
    organizer_id: int
    created_at: datetime

    class Config:
        from_attributes = True


class ApplicationCreate(BaseModel):
    event_id: int
    volunteer_id: int


class ApplicationResponse(BaseModel):
    id: int
    event_id: int
    volunteer_id: int
    status: str
    applied_at: datetime

    class Config:
        from_attributes = True