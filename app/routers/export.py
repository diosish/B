from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from sqlalchemy.orm import Session
import json
from datetime import datetime

from .. import crud, models
from ..database import get_db
from ..auth import get_telegram_user_flexible

router = APIRouter()


@router.get("/volunteers/{event_id}")
async def export_volunteers_csv(
        event_id: int,
        db: Session = Depends(get_db),
        telegram_user: dict = Depends(get_telegram_user_flexible)
):
    """Экспорт списка волонтёров мероприятия в CSV"""

    # Проверяем права организатора
    organizer = crud.get_user_by_telegram_id(db, telegram_user['id'])
    if not organizer or organizer.role != "organizer":
        raise HTTPException(status_code=403, detail="Access denied")

    # Получаем мероприятие
    event = crud.get_event_by_id(db, event_id)
    if not event or event.organizer_id != organizer.id:
        raise HTTPException(status_code=404, detail="Event not found")

    # Получаем одобренных волонтёров
    approved_applications = db.query(models.Application).filter(
        models.Application.event_id == event_id,
        models.Application.status == "approved"
    ).all()

    # Создаем CSV контент
    csv_content = "№,Имя,Город,Тип,Рейтинг,Навыки,Дата заявки\n"

    for i, app in enumerate(approved_applications, 1):
        volunteer = crud.get_user_by_id(db, app.volunteer_id)
        if volunteer:
            csv_content += f"{i},"
            csv_content += f'"{volunteer.full_name}",'
            csv_content += f'"{volunteer.city or ""}",'
            csv_content += f'"{volunteer.volunteer_type or ""}",'
            csv_content += f"{volunteer.rating or 0:.1f},"
            csv_content += f'"{(volunteer.skills or "").replace(chr(34), chr(39))}",'
            csv_content += f'"{app.applied_at.strftime("%d.%m.%Y")}"\n'

    return Response(
        content=csv_content,
        media_type="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename=volunteers_{event.title}_{event_id}.csv"
        }
    )


@router.get("/volunteers/{event_id}/json")
async def export_volunteers_json(
        event_id: int,
        db: Session = Depends(get_db),
        telegram_user: dict = Depends(get_telegram_user_flexible)
):
    """Экспорт списка волонтёров мероприятия в JSON"""

    # Проверяем права организатора
    organizer = crud.get_user_by_telegram_id(db, telegram_user['id'])
    if not organizer or organizer.role != "organizer":
        raise HTTPException(status_code=403, detail="Access denied")

    # Получаем мероприятие
    event = crud.get_event_by_id(db, event_id)
    if not event or event.organizer_id != organizer.id:
        raise HTTPException(status_code=404, detail="Event not found")

    # Получаем одобренных волонтёров
    approved_applications = db.query(models.Application).filter(
        models.Application.event_id == event_id,
        models.Application.status == "approved"
    ).all()

    volunteers_data = []
    for app in approved_applications:
        volunteer = crud.get_user_by_id(db, app.volunteer_id)
        if volunteer:
            volunteers_data.append({
                "name": volunteer.full_name,
                "city": volunteer.city,
                "type": volunteer.volunteer_type,
                "rating": volunteer.rating or 0,
                "skills": volunteer.skills,
                "applied_at": app.applied_at.isoformat()
            })

    export_data = {
        "event": {
            "id": event.id,
            "title": event.title,
            "date": event.date.isoformat() if event.date else None,
            "city": event.city
        },
        "exported_at": datetime.utcnow().isoformat(),
        "volunteers": volunteers_data,
        "total_count": len(volunteers_data)
    }

    return Response(
        content=json.dumps(export_data, ensure_ascii=False, indent=2),
        media_type="application/json",
        headers={
            "Content-Disposition": f"attachment; filename=volunteers_{event.title}_{event_id}.json"
        }
    )