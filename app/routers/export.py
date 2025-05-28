from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from sqlalchemy.orm import Session
from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import os

from .. import crud, models
from ..database import get_db
from ..auth import get_telegram_user_flexible

router = APIRouter()

# Регистрируем шрифт для русского текста
try:
    pdfmetrics.registerFont(TTFont('DejaVuSans', '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'))
    pdfmetrics.registerFont(TTFont('DejaVuSans-Bold', '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'))
except:
    # Fallback для систем без DejaVu
    pass


@router.get("/volunteers/{event_id}")
async def export_volunteers_pdf(
        event_id: int,
        db: Session = Depends(get_db),
        telegram_user: dict = Depends(get_telegram_user_flexible)
):
    """Экспорт списка волонтёров мероприятия в PDF"""

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

    # Создаем PDF
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)

    # Стили
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontName='DejaVuSans-Bold' if 'DejaVuSans-Bold' in pdfmetrics.getRegisteredFontNames() else 'Helvetica-Bold',
        fontSize=18,
        spaceAfter=30,
        alignment=1  # Центрирование
    )

    normal_style = ParagraphStyle(
        'CustomNormal',
        parent=styles['Normal'],
        fontName='DejaVuSans' if 'DejaVuSans' in pdfmetrics.getRegisteredFontNames() else 'Helvetica',
        fontSize=10
    )

    # Содержимое PDF
    story = []

    # Заголовок
    story.append(Paragraph(f"Список волонтёров", title_style))
    story.append(Paragraph(f"Мероприятие: {event.title}", normal_style))
    story.append(Paragraph(f"Дата создания: {event.created_at.strftime('%d.%m.%Y')}", normal_style))
    story.append(Spacer(1, 20))

    if not approved_applications:
        story.append(Paragraph("Нет одобренных волонтёров", normal_style))
    else:
        # Таблица волонтёров
        data = [['№', 'Имя', 'Город', 'Тип', 'Рейтинг', 'Навыки']]

        for i, app in enumerate(approved_applications, 1):
            volunteer = crud.get_user_by_id(db, app.volunteer_id)
            if volunteer:
                data.append([
                    str(i),
                    volunteer.full_name,
                    volunteer.city or '-',
                    volunteer.volunteer_type or '-',
                    f"{volunteer.rating or 0:.1f}",
                    (volunteer.skills or '-')[:50] + ('...' if len(volunteer.skills or '') > 50 else '')
                ])

        table = Table(data)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0),
             'DejaVuSans-Bold' if 'DejaVuSans-Bold' in pdfmetrics.getRegisteredFontNames() else 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('FONTNAME', (0, 1), (-1, -1),
             'DejaVuSans' if 'DejaVuSans' in pdfmetrics.getRegisteredFontNames() else 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))

        story.append(table)

    # Генерируем PDF
    doc.build(story)

    # Возвращаем PDF
    buffer.seek(0)

    return Response(
        content=buffer.getvalue(),
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"attachment; filename=volunteers_{event.title}_{event_id}.pdf"
        }
    )