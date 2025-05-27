from sqlalchemy import Column, Integer, String, DateTime, Float, Boolean, Text, ForeignKey, Table, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

Base = declarative_base()


class UserRole(enum.Enum):
    VOLUNTEER = "volunteer"
    ORGANIZER = "organizer"
    ADMIN = "admin"


class EventStatus(enum.Enum):
    ACTIVE = "active"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class ApplicationStatus(enum.Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    telegram_id = Column(Integer, unique=True, nullable=False, index=True)
    full_name = Column(String(255), nullable=False)
    city = Column(String(100))
    role = Column(String(20), default=UserRole.VOLUNTEER.value)
    created_at = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)

    # Поля волонтёра (если роль = volunteer)
    volunteer_type = Column(String(50))
    skills = Column(Text)
    resume = Column(Text)
    rating = Column(Float, default=0.0)

    # Поля организатора (если роль = organizer)
    org_type = Column(String(50))
    org_name = Column(String(255))
    inn = Column(String(20))
    description = Column(Text)

    __table_args__ = (
        Index('idx_user_telegram_id', 'telegram_id'),
    )


class Event(Base):
    __tablename__ = "events"

    id = Column(Integer, primary_key=True)
    title = Column(String(255), nullable=False)
    description = Column(Text)
    city = Column(String(100))
    date = Column(DateTime)
    duration = Column(Integer)
    payment = Column(Float)
    work_type = Column(String(50))
    status = Column(String(20), default=EventStatus.ACTIVE.value)
    organizer_id = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    organizer = relationship("User", backref="events")


class Application(Base):
    __tablename__ = "applications"

    id = Column(Integer, primary_key=True)
    event_id = Column(Integer, ForeignKey("events.id"))
    volunteer_id = Column(Integer, ForeignKey("users.id"))
    status = Column(String(20), default=ApplicationStatus.PENDING.value)
    applied_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    event = relationship("Event", backref="applications")
    volunteer = relationship("User", backref="volunteer_applications")

    __table_args__ = (
        Index('idx_application_event_volunteer', 'event_id', 'volunteer_id'),
    )


class Review(Base):
    __tablename__ = "reviews"

    id = Column(Integer, primary_key=True)
    event_id = Column(Integer, ForeignKey("events.id"))
    volunteer_id = Column(Integer, ForeignKey("users.id"))
    organizer_id = Column(Integer, ForeignKey("users.id"))
    rating = Column(Integer)  # 1-5
    comment = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

    event = relationship("Event", backref="reviews")
    volunteer = relationship("User", foreign_keys=[volunteer_id], backref="received_reviews")
    organizer = relationship("User", foreign_keys=[organizer_id], backref="given_reviews")