import enum, uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Enum, JSON, BigInteger, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from backend.db.base import Base

class UserRole(str, enum.Enum):
    volunteer = "volunteer"
    organizer = "organizer"
    admin = "admin"

class User(Base):
    __tablename__ = "users"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tg_id = Column(BigInteger, unique=True, nullable=False)
    full_name = Column(String, nullable=False)
    city = Column(String, nullable=True)
    role = Column(Enum(UserRole), nullable=False)
    subtype_id = Column(UUID(as_uuid=True), ForeignKey("subtypes.id"), nullable=True)
    profile_data = Column(JSON, default={})
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    subtype = relationship("Subtype", back_populates="users")
