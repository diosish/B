import uuid
from datetime import datetime
from sqlalchemy import Column, String, Text, DateTime, Integer, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from backend.db.base import Base

class Event(Base):
    __tablename__ = "events"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String, nullable=False)
    description = Column(Text)
    city = Column(String)
    date_start = Column(DateTime, nullable=False)
    date_end = Column(DateTime, nullable=False)
    pay = Column(Integer, nullable=False)
    work_class = Column(String, nullable=False)
    organizer_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    organizer = relationship("User")
    created_at = Column(DateTime, default=datetime.utcnow)
