import uuid
from sqlalchemy import Column, String, Enum, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from backend.db.base import Base
from backend.models.user import UserRole

class Subtype(Base):
    __tablename__ = "subtypes"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    role = Column(Enum(UserRole), nullable=False)
    fields_schema = Column(JSON, nullable=False)  # {"field_name": {"type": "...", "required": bool}, ...}
    users = relationship("User", back_populates="subtype")
