import uuid
from datetime import datetime
from sqlalchemy import Column, String, JSON, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from backend.db.base import Base

class AdminToken(Base):
    __tablename__ = "admin_tokens"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    token = Column(String, unique=True, nullable=False)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    permissions = Column(JSON, default={})
    used_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    used_at = Column(DateTime, nullable=True)
    creator = relationship("User", foreign_keys=[created_by])
    user = relationship("User", foreign_keys=[used_by])
