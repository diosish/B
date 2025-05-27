import httpx
import asyncio
from typing import Optional
import os


class TelegramBot:
    def __init__(self, token: str):
        self.token = token
        self.base_url = f"https://api.telegram.org/bot{token}"

    async def send_message(self, chat_id: int, text: str):
        """Отправка сообщения"""
        try:
            async with httpx.AsyncClient() as client:
                url = f"{self.base_url}/sendMessage"
                data = {
                    "chat_id": chat_id,
                    "text": text,
                    "parse_mode": "HTML"
                }
                await client.post(url, json=data)
        except Exception as e:
            print(f"Error sending message: {e}")

    async def send_webapp_button(self, chat_id: int, text: str, webapp_url: str):
        """Отправка кнопки с WebApp"""
        keyboard = {
            "inline_keyboard": [[{
                "text": "🚀 Открыть приложение",
                "web_app": {"url": webapp_url}
            }]]
        }

        try:
            async with httpx.AsyncClient() as client:
                url = f"{self.base_url}/sendMessage"
                data = {
                    "chat_id": chat_id,
                    "text": text,
                    "reply_markup": keyboard,
                    "parse_mode": "HTML"
                }
                await client.post(url, json=data)
        except Exception as e:
            print(f"Error sending webapp button: {e}")


# Глобальный экземпляр
bot = TelegramBot(os.getenv("BOT_TOKEN"))


# Функции уведомлений
async def notify_application_status(user_telegram_id: int, event_title: str, status: str):
    """Уведомление об изменении статуса заявки"""
    messages = {
        "approved": f"✅ <b>Отличные новости!</b>\n\nВаша заявка на мероприятие <b>'{event_title}'</b> одобрена!\n\n🎉 Ожидайте дополнительную информацию от организатора.",
        "rejected": f"❌ <b>Заявка отклонена</b>\n\nК сожалению, ваша заявка на мероприятие <b>'{event_title}'</b> не была принята.\n\n💪 Не расстраивайтесь, попробуйте подать заявку на другие мероприятия!"
    }

    message = messages.get(status, f"📋 Статус вашей заявки на '{event_title}' изменён на: {status}")
    await bot.send_message(user_telegram_id, message)


async def notify_new_event(user_telegram_id: int, event_title: str, city: str, payment: float = 0):
    """Уведомление о новом мероприятии в городе"""
    text = f"""
🆕 <b>Новое мероприятие!</b>

📅 <b>{event_title}</b>
📍 Город: {city}
💰 Оплата: {payment} ₽

Откройте приложение, чтобы подать заявку!
    """
    await bot.send_message(user_telegram_id, text)


async def notify_new_application(organizer_telegram_id: int, event_title: str, volunteer_name: str):
    """Уведомление организатору о новой заявке"""
    text = f"""
📋 <b>Новая заявка!</b>

Волонтёр <b>{volunteer_name}</b> подал заявку на ваше мероприятие <b>'{event_title}'</b>

Откройте приложение, чтобы рассмотреть заявку.
    """
    await bot.send_message(organizer_telegram_id, text)


async def notify_new_application(organizer_telegram_id: int, event_title: str, volunteer_name: str):
    """Уведомление организатору о новой заявке"""
    text = f"""
📋 <b>Новая заявка!</b>

Волонтёр <b>{volunteer_name}</b> подал заявку на ваше мероприятие:
📅 <b>"{event_title}"</b>

🔍 Откройте приложение, чтобы рассмотреть заявку.
    """
    await bot.send_message(organizer_telegram_id, text.strip())


async def notify_event_status_change(telegram_id: int, event_title: str, old_status: str, new_status: str):
    """Уведомление об изменении статуса мероприятия"""
    status_messages = {
        "completed": f"✅ <b>Мероприятие завершено!</b>\n\nВаше мероприятие <b>'{event_title}'</b> успешно завершено.\n\n⭐ Не забудьте оставить отзывы о волонтёрах!",
        "cancelled": f"❌ <b>Мероприятие отменено</b>\n\nМероприятие <b>'{event_title}'</b> было отменено.\n\n💔 Приносим извинения за неудобства."
    }

    message = status_messages.get(new_status, f"📋 Статус мероприятия '{event_title}' изменён на: {new_status}")
    await bot.send_message(telegram_id, message)


async def notify_review_received(volunteer_telegram_id: int, event_title: str, rating: int, organizer_name: str):
    """Уведомление волонтёру о получении отзыва"""
    stars = "⭐" * rating
    text = f"""
⭐ <b>Новый отзыв!</b>

Организатор <b>{organizer_name}</b> оставил отзыв о вашей работе на мероприятии:
📅 <b>"{event_title}"</b>

🌟 Оценка: {stars} ({rating}/5)

👏 Отличная работа! Ваш рейтинг обновлён.
    """
    await bot.send_message(volunteer_telegram_id, text.strip())


async def notify_city_subscribers(city: str, event_title: str, payment: float, work_type: str):
    """Уведомление подписчикам города о новом мероприятии"""
    # В будущем здесь будет система подписок на уведомления по городам
    # Пока что это заглушка
    text = f"""
🆕 <b>Новое мероприятие в городе {city}!</b>

📅 <b>{event_title}</b>
💰 Оплата: {payment} ₽
🏷️ Тип работы: {work_type}

🚀 Откройте приложение, чтобы подать заявку!
    """

    # В будущем здесь будет рассылка подписчикам
    print(f"📢 Broadcasting to {city} subscribers: {event_title}")


async def send_welcome_message(chat_id: int, user_name: str):
    """Приветственное сообщение для новых пользователей"""
    text = f"""
👋 <b>Добро пожаловать, {user_name}!</b>

Это система поиска <b>оплачиваемой волонтёрской работы</b>.

<b>🎯 Что вы можете сделать:</b>
👥 Зарегистрироваться как волонтёр
🏢 Стать организатором мероприятий  
📅 Найти подходящие мероприятия
💰 Получать оплату за участие
⭐ Получать отзывы и строить репутацию

<b>🚀 Начать работу очень просто:</b>
1. Нажмите кнопку ниже
2. Заполните свой профиль
3. Начните искать мероприятия или создавать их!

💡 <i>Все взаимодействие происходит через удобное веб-приложение.</i>
    """

    await bot.send_webapp_button(chat_id, text.strip(), os.getenv("WEBAPP_URL"))