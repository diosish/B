from pydantic import BaseModel
from uuid import UUID
from backend.models.application import ApplicationStatus

class ApplicationCreate(BaseModel):
    volunteer_id: UUID
    event_id: UUID

class ApplicationRead(BaseModel):
    id: UUID
    volunteer_id: UUID
    event_id: UUID
    status: ApplicationStatus
    class Config:
        orm_mode = True
