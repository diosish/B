import asyncio
import logging
from datetime import datetime, timedelta
from typing import List, Dict
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os

logger = logging.getLogger(__name__)


class SystemMonitor:
    """Класс для мониторинга системы и отправки уведомлений"""

    def __init__(self):
        self.alerts = []
        self.last_check = datetime.utcnow()
        self.check_interval = 300  # 5 минут

    async def start_monitoring(self):
        """Запуск мониторинга в фоновом режиме"""
        while True:
            try:
                await self.perform_health_checks()
                await asyncio.sleep(self.check_interval)
            except Exception as e:
                logger.error(f"Monitoring error: {e}")
                await asyncio.sleep(60)  # Повтор через минуту при ошибке

    async def perform_health_checks(self):
        """Выполнение проверок здоровья системы"""
        from .database import SessionLocal
        from . import models

        db = SessionLocal()
        try:
            # Проверка активности пользователей
            recent_registrations = db.query(models.User).filter(
                models.User.created_at > datetime.utcnow() - timedelta(hours=24)
            ).count()

            # Проверка застрявших заявок
            old_pending_applications = db.query(models.Application).filter(
                models.Application.status == "pending",
                models.Application.applied_at < datetime.utcnow() - timedelta(days=7)
            ).count()

            # Проверка системных ресурсов
            import psutil
            cpu_percent = psutil.cpu_percent()
            memory_percent = psutil.virtual_memory().percent
            disk_percent = psutil.disk_usage('/').percent

            # Создание алертов при необходимости
            alerts = []

            if cpu_percent > 85:
                alerts.append(f"High CPU usage: {cpu_percent}%")

            if memory_percent > 90:
                alerts.append(f"High memory usage: {memory_percent}%")

            if disk_percent > 90:
                alerts.append(f"High disk usage: {disk_percent}%")

            if old_pending_applications > 10:
                alerts.append(f"Too many old pending applications: {old_pending_applications}")

            # Отправка уведомлений
            if alerts and self.should_send_alert():
                await self.send_alert_notification(alerts)

            logger.info(
                f"Health check completed. CPU: {cpu_percent}%, Memory: {memory_percent}%, Disk: {disk_percent}%")

        except Exception as e:
            logger.error(f"Health check failed: {e}")
        finally:
            db.close()

    def should_send_alert(self) -> bool:
        """Проверка, нужно ли отправлять уведомление (throttling)"""
        # Отправляем не чаще раза в час
        if not self.alerts or datetime.utcnow() - self.last_check > timedelta(hours=1):
            self.last_check = datetime.utcnow()
            return True
        return False

    async def send_alert_notification(self, alerts: List[str]):
        """Отправка уведомления об алертах"""
        try:
            # Отправка в Telegram админам
            await self.send_telegram_alert(alerts)

            # Отправка по email (если настроено)
            await self.send_email_alert(alerts)

        except Exception as e:
            logger.error(f"Failed to send alert: {e}")

    async def send_telegram_alert(self, alerts: List[str]):
        """Отправка алерта в Telegram"""
        try:
            from .bot import bot
            admin_ids = os.getenv("ADMIN_TELEGRAM_IDS", "123456789").split(",")

            alert_text = "🚨 SYSTEM ALERT 🚨\n\n" + "\n".join(f"• {alert}" for alert in alerts)
            alert_text += f"\n\n⏰ Time: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC"

            for admin_id in admin_ids:
                try:
                    await bot.send_message(int(admin_id.strip()), alert_text)
                except Exception as e:
                    logger.error(f"Failed to send Telegram alert to {admin_id}: {e}")

        except Exception as e:
            logger.error(f"Telegram alert failed: {e}")

    async def send_email_alert(self, alerts: List[str]):
        """Отправка алерта по email"""
        smtp_host = os.getenv("SMTP_HOST")
        smtp_user = os.getenv("SMTP_USER")
        smtp_password = os.getenv("SMTP_PASSWORD")

        if not all([smtp_host, smtp_user, smtp_password]):
            return  # Email не настроен

        try:
            msg = MIMEMultipart()
            msg['From'] = smtp_user
            msg['To'] = smtp_user  # Отправляем себе
            msg['Subject'] = "Volunteer System Alert"

            body = "System Alert:\n\n" + "\n".join(f"- {alert}" for alert in alerts)
            body += f"\n\nTime: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC"

            msg.attach(MIMEText(body, 'plain'))

            server = smtplib.SMTP(smtp_host, int(os.getenv("SMTP_PORT", 587)))
            server.starttls()
            server.login(smtp_user, smtp_password)
            text = msg.as_string()
            server.sendmail(smtp_user, smtp_user, text)
            server.quit()

            logger.info("Email alert sent successfully")

        except Exception as e:
            logger.error(f"Email alert failed: {e}")


# Глобальный экземпляр монитора
system_monitor = SystemMonitor()


# Функция для запуска мониторинга
async def start_background_monitoring():
    """Запуск фонового мониторинга"""
    asyncio.create_task(system_monitor.start_monitoring())
