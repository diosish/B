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

    try:
        # Проверяем права организатора
        organizer = crud.get_user_by_telegram_id(db, telegram_user['id'])
        if not organizer or organizer.role != "organizer":
            raise HTTPException(status_code=403, detail="Access denied")

        # Получаем мероприятие
        event = crud.get_event_by_id(db, event_id)
        if not event:
            raise HTTPException(status_code=404, detail="Event not found")

        if event.organizer_id != organizer.id:
            raise HTTPException(status_code=403, detail="Access denied to this event")

        # Получаем одобренных волонтёров
        approved_applications = db.query(models.Application).filter(
            models.Application.event_id == event_id,
            models.Application.status == "approved"
        ).all()

        # Создаем CSV контент
        csv_lines = []
        csv_lines.append("№,Имя,Город,Тип,Рейтинг,Навыки,Дата заявки")

        if not approved_applications:
            csv_lines.append("Нет одобренных волонтёров")
        else:
            for i, app in enumerate(approved_applications, 1):
                volunteer = crud.get_user_by_id(db, app.volunteer_id)
                if volunteer:
                    # Безопасное экранирование CSV данных
                    name = str(volunteer.full_name or "").replace('"', '""')
                    city = str(volunteer.city or "").replace('"', '""')
                    vol_type = str(volunteer.volunteer_type or "").replace('"', '""')
                    skills = str(volunteer.skills or "").replace('"', '""')[:100]  # Ограничиваем длину
                    rating = volunteer.rating or 0
                    date = app.applied_at.strftime("%d.%m.%Y") if app.applied_at else ""

                    csv_lines.append(f'{i},"{name}","{city}","{vol_type}",{rating:.1f},"{skills}","{date}"')

        csv_content = "\n".join(csv_lines)

        # Безопасное имя файла
        safe_title = "".join(c for c in (event.title or "event") if c.isalnum() or c in (' ', '-', '_')).strip()[:20]

        return Response(
            content=csv_content.encode('utf-8-sig'),  # BOM для правильного отображения в Excel
            media_type="text/csv; charset=utf-8",
            headers={
                "Content-Disposition": f"attachment; filename=volunteers_{safe_title}_{event_id}.csv"
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Export error: {e}")
        raise HTTPException(status_code=500, detail=f"Export failed: {str(e)}")


@router.get("/volunteers/{event_id}/json")
async def export_volunteers_json(
        event_id: int,
        db: Session = Depends(get_db),
        telegram_user: dict = Depends(get_telegram_user_flexible)
):
    """Экспорт списка волонтёров мероприятия в JSON"""

    try:
        # Проверяем права организатора
        organizer = crud.get_user_by_telegram_id(db, telegram_user['id'])
        if not organizer or organizer.role != "organizer":
            raise HTTPException(status_code=403, detail="Access denied")

        # Получаем мероприятие
        event = crud.get_event_by_id(db, event_id)
        if not event:
            raise HTTPException(status_code=404, detail="Event not found")

        if event.organizer_id != organizer.id:
            raise HTTPException(status_code=403, detail="Access denied to this event")

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
                    "applied_at": app.applied_at.isoformat() if app.applied_at else None
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

        # Безопасное имя файла
        safe_title = "".join(c for c in (event.title or "event") if c.isalnum() or c in (' ', '-', '_')).strip()[:20]

        return Response(
            content=json.dumps(export_data, ensure_ascii=False, indent=2),
            media_type="application/json",
            headers={
                "Content-Disposition": f"attachment; filename=volunteers_{safe_title}_{event_id}.json"
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Export error: {e}")
        raise HTTPException(status_code=500, detail=f"Export failed: {str(e)}")