from fastapi import APIRouter, BackgroundTasks
from backend.core.config import settings
from bot.notify import send_message

router = APIRouter(prefix="/notify", tags=["notify"])

@router.post("/test")
def test_notify(chat_id: int, text: str, bg: BackgroundTasks):
    bg.add_task(send_message, chat_id, text)
    return {"status": "scheduled"}
