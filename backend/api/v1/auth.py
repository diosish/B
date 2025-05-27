from fastapi import APIRouter, Depends, HTTPException, Request
from backend.db.session import get_db
from sqlalchemy.orm import Session
from backend.models.user import User, UserRole
from backend.schemas.user import UserCreate, UserRead
from backend.core.config import settings
import hmac, hashlib, time

router = APIRouter(prefix="/auth", tags=["auth"])

def verify_init_data(init_data: str, token: str):
    data, hash_str = init_data.rsplit("\n", 1)
    secret = hashlib.sha256(token.encode()).digest()
    check = hmac.new(secret, data.encode(), hashlib.sha256).hexdigest()
    return hmac.compare_digest(check, hash_str)

@router.post("/login", response_model=UserRead)
def login(request: Request, db: Session = Depends(get_db)):
    init_data = request.headers.get("X-Telegram-WebApp-Data")
    if not init_data or not verify_init_data(init_data, settings.TELEGRAM_BOT_TOKEN):
        raise HTTPException(400, "Invalid init data")
    payload = dict(pair.split("=") for pair in init_data.split("\n"))
    tg_id = int(payload["id"])
    full_name = payload.get("first_name", "") + " " + payload.get("last_name", "")
    user = db.query(User).filter(User.tg_id == tg_id).first()
    if not user:
        user = User(tg_id=tg_id, full_name=full_name, role=UserRole.volunteer)
        db.add(user); db.commit(); db.refresh(user)
    return user
