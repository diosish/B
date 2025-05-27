from sqlalchemy import Column, Integer, String, DateTime, Float, Boolean, Text, ForeignKey, Table
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

Base = declarative_base()


class UserRole(enum.Enum):
    VOLUNTEER = "volunteer"
    ORGANIZER = "organizer"
    ADMIN = "admin"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    telegram_id = Column(Integer, unique=True, nullable=False)
    full_name = Column(String(255), nullable=False)
    city = Column(String(100))
    role = Column(String(20), default="volunteer")  # Упрощено: строка вместо enum
    created_at = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)

    # Поля волонтёра (если роль = volunteer)
    volunteer_type = Column(String(50))  # студент, фрилансер, профи
    skills = Column(Text)  # JSON string для простоты
    resume = Column(Text)
    rating = Column(Float, default=0.0)

    # Поля организатора (если роль = organizer)
    org_type = Column(String(50))  # ООО, ИП, физлицо, НКО
    org_name = Column(String(255))
    inn = Column(String(20))
    description = Column(Text)


class Event(Base):
    __tablename__ = "events"

    id = Column(Integer, primary_key=True)
    title = Column(String(255), nullable=False)
    description = Column(Text)
    city = Column(String(100))
    date = Column(DateTime)
    duration = Column(Integer)  # часы
    payment = Column(Float)
    work_type = Column(String(50))
    status = Column(String(20), default="active")
    organizer_id = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)

    organizer = relationship("User", backref="events")


class Application(Base):
    __tablename__ = "applications"

    id = Column(Integer, primary_key=True)
    event_id = Column(Integer, ForeignKey("events.id"))
    volunteer_id = Column(Integer, ForeignKey("users.id"))
    status = Column(String(20), default="pending")  # pending, approved, rejected
    applied_at = Column(DateTime, default=datetime.utcnow)

    event = relationship("Event")
    volunteer = relationship("User")


class Review(Base):
    __tablename__ = "reviews"

    id = Column(Integer, primary_key=True)
    event_id = Column(Integer, ForeignKey("events.id"))
    volunteer_id = Column(Integer, ForeignKey("users.id"))
    organizer_id = Column(Integer, ForeignKey("users.id"))
    rating = Column(Integer)  # 1-5
    comment = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)