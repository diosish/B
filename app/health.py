# app/health.py - НОВЫЙ ФАЙЛ
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from datetime import datetime
import psutil
import os
from typing import Dict, Any

from .database import get_db

router = APIRouter()


@router.get("/health")
async def health_check(db: Session = Depends(get_db)):
    """Базовая проверка здоровья системы"""
    try:
        # Проверка подключения к БД
        db.execute(text("SELECT 1"))

        return {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "version": "1.0.0"
        }
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"System unhealthy: {str(e)}")


@router.get("/health/detailed")
async def detailed_health_check(db: Session = Depends(get_db)):
    """Детальная проверка здоровья системы"""
    health_status = {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "checks": {}
    }

    # Проверка базы данных
    try:
        db.execute(text("SELECT 1"))
        # Проверяем время отклика БД
        start_time = datetime.utcnow()
        db.execute(text("SELECT COUNT(*) FROM users LIMIT 1"))
        db_response_time = (datetime.utcnow() - start_time).total_seconds()

        health_status["checks"]["database"] = {
            "status": "healthy",
            "response_time_seconds": db_response_time
        }
    except Exception as e:
        health_status["status"] = "unhealthy"
        health_status["checks"]["database"] = {
            "status": "unhealthy",
            "error": str(e)
        }

    # Проверка системных ресурсов
    try:
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')

        health_status["checks"]["system"] = {
            "status": "healthy",
            "cpu_percent": cpu_percent,
            "memory_percent": memory.percent,
            "disk_percent": disk.percent,
            "available_memory_mb": round(memory.available / 1024 / 1024, 2)
        }

        # Предупреждения о высокой нагрузке
        if cpu_percent > 80 or memory.percent > 90 or disk.percent > 90:
            health_status["checks"]["system"]["status"] = "warning"
            health_status["status"] = "degraded"

    except Exception as e:
        health_status["checks"]["system"] = {
            "status": "unhealthy",
            "error": str(e)
        }

    # Проверка переменных окружения
    required_env_vars = ["DATABASE_URL", "BOT_TOKEN", "SECRET_KEY"]
    missing_vars = [var for var in required_env_vars if not os.getenv(var)]

    if missing_vars:
        health_status["status"] = "unhealthy"
        health_status["checks"]["environment"] = {
            "status": "unhealthy",
            "missing_variables": missing_vars
        }
    else:
        health_status["checks"]["environment"] = {
            "status": "healthy",
            "all_required_vars_present": True
        }

    # Проверка Telegram Bot API (опционально)
    try:
        import httpx
        bot_token = os.getenv("BOT_TOKEN")
        if bot_token:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"https://api.telegram.org/bot{bot_token}/getMe",
                    timeout=5.0
                )
                if response.status_code == 200:
                    health_status["checks"]["telegram_bot"] = {
                        "status": "healthy",
                        "bot_info": response.json().get("result", {}).get("username", "unknown")
                    }
                else:
                    health_status["checks"]["telegram_bot"] = {
                        "status": "unhealthy",
                        "error": f"HTTP {response.status_code}"
                    }
    except Exception as e:
        health_status["checks"]["telegram_bot"] = {
            "status": "unhealthy",
            "error": str(e)
        }

    return health_status


@router.get("/metrics")
async def get_metrics(db: Session = Depends(get_db)):
    """Метрики для мониторинга (Prometheus формат)"""
    try:
        # Получаем метрики из БД
        from . import models

        total_users = db.query(models.User).count()
        active_users = db.query(models.User).filter(models.User.is_active == True).count()
        total_events = db.query(models.Event).count()
        active_events = db.query(models.Event).filter(models.Event.status == "active").count()
        total_applications = db.query(models.Application).count()
        pending_applications = db.query(models.Application).filter(models.Application.status == "pending").count()

        # Системные метрики
        cpu_percent = psutil.cpu_percent()
        memory = psutil.virtual_memory()

        metrics_text = f"""# HELP volunteer_users_total Total number of users
# TYPE volunteer_users_total counter
volunteer_users_total {total_users}

# HELP volunteer_users_active Number of active users  
# TYPE volunteer_users_active gauge
volunteer_users_active {active_users}

# HELP volunteer_events_total Total number of events
# TYPE volunteer_events_total counter
volunteer_events_total {total_events}

# HELP volunteer_events_active Number of active events
# TYPE volunteer_events_active gauge
volunteer_events_active {active_events}

# HELP volunteer_applications_total Total number of applications
# TYPE volunteer_applications_total counter
volunteer_applications_total {total_applications}

# HELP volunteer_applications_pending Number of pending applications
# TYPE volunteer_applications_pending gauge
volunteer_applications_pending {pending_applications}

# HELP volunteer_system_cpu_percent CPU usage percentage
# TYPE volunteer_system_cpu_percent gauge
volunteer_system_cpu_percent {cpu_percent}

# HELP volunteer_system_memory_percent Memory usage percentage
# TYPE volunteer_system_memory_percent gauge
volunteer_system_memory_percent {memory.percent}
"""

        return metrics_text

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate metrics: {str(e)}")


@router.get("/status")
async def system_status():
    """Простой статус для load balancer'ов"""
    return {"status": "ok", "timestamp": datetime.utcnow().isoformat()}

