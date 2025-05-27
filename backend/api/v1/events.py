from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from backend.db.session import get_db
from backend.models.event import Event
from backend.schemas.event import EventCreate, EventRead

router = APIRouter(prefix="/events", tags=["events"])

@router.post("/", response_model=EventRead)
def create_event(data: EventCreate, db: Session = Depends(get_db)):
    ev = Event(**data.dict())
    db.add(ev); db.commit(); db.refresh(ev)
    return ev

@router.get("/", response_model=list[EventRead])
def list_events(db: Session = Depends(get_db)):
    return db.query(Event).all()
