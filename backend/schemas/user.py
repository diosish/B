from pydantic import BaseModel
from uuid import UUID
from backend.models.user import UserRole

class UserCreate(BaseModel):
    tg_id: int
    full_name: str
    city: str
    role: UserRole
    subtype_id: UUID | None = None
    profile_data: dict = {}

class UserRead(BaseModel):
    id: UUID
    tg_id: int
    full_name: str
    city: str
    role: UserRole
    subtype_id: UUID | None
    profile_data: dict
    class Config:
        orm_mode = True
