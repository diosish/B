from pydantic import BaseModel
from uuid import UUID
from datetime import datetime

class EventCreate(BaseModel):
    title: str
    description: str
    city: str
    date_start: datetime
    date_end: datetime
    pay: int
    work_class: str

class EventRead(EventCreate):
    id: UUID
    organizer_id: UUID
    class Config:
        orm_mode = True
