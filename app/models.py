# app/models.py - ИСПРАВЛЕННАЯ ВЕРСИЯ
from sqlalchemy import Column, Integer, String, DateTime, Float, Boolean, Text, ForeignKey, BigInteger, CheckConstraint, UniqueConstraint
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, validates
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
    telegram_id = Column(BigInteger, unique=True, nullable=False, index=True)
    full_name = Column(String(255), nullable=False)
    city = Column(String(100))
    role = Column(String(20), default="volunteer", nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = Column(Boolean, default=True)

    # Поля волонтёра
    volunteer_type = Column(String(50))  # студент, фрилансер, профи
    skills = Column(Text)
    resume = Column(Text)
    rating = Column(Float, default=0.0)

    # Поля организатора
    org_type = Column(String(50))  # ООО, ИП, физлицо, НКО
    org_name = Column(String(255))
    inn = Column(String(20))
    description = Column(Text)

    # Ограничения для валидации
    __table_args__ = (
        CheckConstraint("role IN ('volunteer', 'organizer', 'admin')", name='valid_role'),
        CheckConstraint("rating >= 0 AND rating <= 5", name='valid_rating'),
    )

    @validates('role')
    def validate_role(self, key, role):
        valid_roles = ['volunteer', 'organizer', 'admin']
        if role not in valid_roles:
            raise ValueError(f"Invalid role: {role}. Must be one of {valid_roles}")
        return role

    @validates('rating')
    def validate_rating(self, key, rating):
        if rating is not None and (rating < 0 or rating > 5):
            raise ValueError("Rating must be between 0 and 5")
        return rating

    @validates('volunteer_type')
    def validate_volunteer_type(self, key, volunteer_type):
        if volunteer_type:
            valid_types = ['студент', 'фрилансер', 'профи']
            if volunteer_type not in valid_types:
                raise ValueError(f"Invalid volunteer type: {volunteer_type}")
        return volunteer_type

    @validates('org_type')
    def validate_org_type(self, key, org_type):
        if org_type:
            valid_types = ['ООО', 'ИП', 'физлицо', 'НКО']
            if org_type not in valid_types:
                raise ValueError(f"Invalid organization type: {org_type}")
        return org_type


class Event(Base):
    __tablename__ = "events"

    id = Column(Integer, primary_key=True)
    title = Column(String(255), nullable=False)
    description = Column(Text)
    treb = Column(Text)  # Добавлено поле для требований
    contact = Column(Text)  # Добавлено поле для контактной информации
    city = Column(String(100))
    date = Column(DateTime)
    duration = Column(Integer)  # часы
    payment = Column(Float, default=0.0)
    work_type = Column(String(50))
    status = Column(String(20), default="active", nullable=False)
    organizer_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Связи
    organizer = relationship("User", backref="events", foreign_keys=[organizer_id])

    # Ограничения для валидации
    __table_args__ = (
        CheckConstraint("status IN ('active', 'completed', 'cancelled')", name='valid_status'),
        CheckConstraint("payment >= 0", name='non_negative_payment'),
    )

    @validates('status')
    def validate_status(self, key, status):
        valid_statuses = ['active', 'completed', 'cancelled']
        if status not in valid_statuses:
            raise ValueError(f"Invalid status: {status}. Must be one of {valid_statuses}")
        return status

    @validates('payment')
    def validate_payment(self, key, payment):
        if payment is not None and payment < 0:
            raise ValueError("Payment cannot be negative")
        return payment

    @validates('work_type')
    def validate_work_type(self, key, work_type):
        if work_type:
            valid_types = ['регистрация', 'логистика', 'техническое', 'информационное', 'промо', 'обслуживание', 'другое']
            if work_type not in valid_types:
                raise ValueError(f"Invalid work type: {work_type}")
        return work_type


class Application(Base):
    __tablename__ = "applications"

    id = Column(Integer, primary_key=True)
    event_id = Column(Integer, ForeignKey("events.id"), nullable=False)
    volunteer_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    status = Column(String(20), default="pending", nullable=False)
    applied_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Связи
    event = relationship("Event", backref="applications")
    volunteer = relationship("User", backref="volunteer_applications", foreign_keys=[volunteer_id])

    # Ограничения
    __table_args__ = (
        CheckConstraint("status IN ('pending', 'approved', 'rejected')", name='valid_application_status'),
        # Уникальная заявка от одного волонтёра на одно мероприятие
        UniqueConstraint('event_id', 'volunteer_id', name='unique_volunteer_application'),
    )

    @validates('status')
    def validate_status(self, key, status):
        valid_statuses = ['pending', 'approved', 'rejected']
        if status not in valid_statuses:
            raise ValueError(f"Invalid application status: {status}")
        return status


class Review(Base):
    __tablename__ = "reviews"

    id = Column(Integer, primary_key=True)
    event_id = Column(Integer, ForeignKey("events.id"), nullable=False)
    volunteer_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    organizer_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    rating = Column(Integer, nullable=False)
    comment = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Связи
    event = relationship("Event", backref="reviews")
    volunteer = relationship("User", foreign_keys=[volunteer_id], backref="received_reviews")
    organizer = relationship("User", foreign_keys=[organizer_id], backref="given_reviews")

    # Ограничения
    __table_args__ = (
        CheckConstraint("rating >= 1 AND rating <= 5", name='valid_rating_range'),
        # Один отзыв от организатора на волонтёра за одно мероприятие
        UniqueConstraint('event_id', 'volunteer_id', 'organizer_id', name='unique_review'),
    )

    @validates('rating')
    def validate_rating(self, key, rating):
        if rating < 1 or rating > 5:
            raise ValueError("Rating must be between 1 and 5")
        return rating

    @validates('comment')
    def validate_comment(self, key, comment):
        if not comment or len(comment.strip()) < 10:
            raise ValueError("Comment must be at least 10 characters long")
        return comment.strip()