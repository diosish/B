from pydantic import BaseModel, Field, validator
from typing import Optional, List
from datetime import datetime
from enum import Enum


# Enums
class UserRole(str, Enum):
    volunteer = "volunteer"
    organizer = "organizer"
    admin = "admin"


class EventStatus(str, Enum):
    active = "active"
    completed = "completed"
    cancelled = "cancelled"


class ApplicationStatus(str, Enum):
    pending = "pending"
    approved = "approved"
    rejected = "rejected"


# User schemas для регистрации (без telegram_id)
class VolunteerRegistration(BaseModel):
    full_name: str
    city: Optional[str] = None
    volunteer_type: str
    skills: Optional[str] = None


class OrganizerRegistration(BaseModel):
    full_name: str
    city: Optional[str] = None
    org_type: str
    org_name: Optional[str] = None
    inn: Optional[str] = None
    description: Optional[str] = None


# Внутренние схемы для создания пользователя в БД
class UserCreate(BaseModel):
    telegram_id: int  # Поддерживает большие числа
    full_name: str
    city: Optional[str] = None
    role: str = "volunteer"

    # Поля волонтёра
    volunteer_type: Optional[str] = None
    skills: Optional[str] = None

    # Поля организатора
    org_type: Optional[str] = None
    org_name: Optional[str] = None
    inn: Optional[str] = None
    description: Optional[str] = None


class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    city: Optional[str] = None
    volunteer_type: Optional[str] = None
    skills: Optional[str] = None
    org_type: Optional[str] = None
    org_name: Optional[str] = None
    inn: Optional[str] = None
    description: Optional[str] = None


class UserResponse(BaseModel):
    id: int
    telegram_id: int  # Поддерживает большие числа
    full_name: str
    city: Optional[str] = None
    role: str
    created_at: datetime
    is_active: bool = True

    # Поля волонтёра
    volunteer_type: Optional[str] = None
    skills: Optional[str] = None
    resume: Optional[str] = None
    rating: Optional[float] = None

    # Поля организатора
    org_type: Optional[str] = None
    org_name: Optional[str] = None
    inn: Optional[str] = None
    description: Optional[str] = None

    class Config:
        from_attributes = True  # Заменили orm_mode на from_attributes


# Event schemas
class EventBase(BaseModel):
    title: str
    description: Optional[str] = None
    city: Optional[str] = None
    work_type: Optional[str] = None


class EventCreate(EventBase):
    date: Optional[datetime] = None
    duration: Optional[int] = None
    payment: Optional[float] = None
    treb: Optional[str] = None
    contact: Optional[str] = None


class EventUpdate(EventBase):
    title: Optional[str] = None
    date: Optional[datetime] = None
    duration: Optional[int] = None
    payment: Optional[float] = None
    status: Optional[str] = None


class EventResponse(EventBase):
    id: int
    date: Optional[datetime]
    duration: Optional[int]
    payment: Optional[float]
    status: str
    organizer_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True  # Заменили orm_mode на from_attributes


# Application schemas
class ApplicationBase(BaseModel):
    event_id: int


class ApplicationCreate(ApplicationBase):
    volunteer_id: Optional[int] = None  # Будет заполнено автоматически


class ApplicationResponse(ApplicationBase):
    id: int
    volunteer_id: int
    status: str
    applied_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True  # Заменили orm_mode на from_attributes


class ApplicationWithVolunteer(ApplicationResponse):
    volunteer: UserResponse

    class Config:
        from_attributes = True  # Заменили orm_mode на from_attributes


class ApplicationWithEvent(ApplicationResponse):
    event: EventResponse

    class Config:
        from_attributes = True  # Заменили orm_mode на from_attributes


# Review schemas
class ReviewBase(BaseModel):
    rating: int = Field(..., ge=1, le=5)
    comment: str


class ReviewCreate(ReviewBase):
    volunteer_id: int
    event_id: int


class ReviewResponse(ReviewBase):
    id: int
    event_id: int
    volunteer_id: int
    organizer_id: int
    created_at: datetime

    # Additional fields for display
    volunteer_name: Optional[str] = None
    event_title: Optional[str] = None
    organizer_name: Optional[str] = None

    class Config:
        from_attributes = True  # Заменили orm_mode на from_attributes


class ReviewWithDetails(ReviewResponse):
    volunteer: Optional[UserResponse] = None
    event: Optional[EventResponse] = None
    organizer: Optional[UserResponse] = None

    class Config:
        from_attributes = True  # Заменили orm_mode на from_attributes


# Token schemas (for future auth implementation)
class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    telegram_id: Optional[int] = None


# Statistics schemas (for future dashboard)
class UserStats(BaseModel):
    total_events: int = 0
    completed_events: int = 0
    average_rating: Optional[float] = None
    total_earnings: Optional[float] = None


class EventStats(BaseModel):
    total_applications: int = 0
    approved_volunteers: int = 0
    completion_rate: Optional[float] = None


# Error schemas
class HTTPError(BaseModel):
    detail: str


# Pagination schemas
class PaginationParams(BaseModel):
    skip: int = 0
    limit: int = 100


class PaginatedResponse(BaseModel):
    items: List
    total: int
    skip: int
    limit: int