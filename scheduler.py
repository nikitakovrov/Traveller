import asyncio
from datetime import datetime, date, timedelta

from aiogram import Bot
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from database import get_documents, notification_already_sent, log_notification
from utils import days_until, humanize_doc_type


async def check_reminders(bot: Bot):
    """Раз в сутки проверяет документы и рассылает напоминания."""
    # Здесь под капотом — простой перебор всех документов.
    # В реальном проекте лучше добавить выборку через SQL-фильтр.
    from database import supabase
    res = supabase.table("documents").select("*").execute()
    today = date.today()
    for doc in res.data:
        expire = datetime.strptime(doc["expire_date"], "%Y-%m-%d").date()
        days_left = (expire - today).days
        reminder_days = doc.get("reminder_days", 7)
        if days_left != reminder_days:
            continue
        if notification_already_sent(doc["id"]):
            continue
        text = (
            f"⏰ <b>Напоминание о документе</b>\n\n"
            f"Тип: <b>{humanize_doc_type(doc['doc_type'])}</b>\n"
            f"Срок действия истекает <b>{doc['expire_date']}</b> "
            f"(через {days_left} дн.)\n\n"
            f"Пожалуйста, позаботьтесь о продлении или замене заранее."
        )
        try:
            await bot.send_message(doc["telegram_id"], text)
            log_notification(doc["id"], doc["telegram_id"], text)
        except Exception as e:
            print(f"Не удалось отправить напоминание {doc['id']}: {e}")


def setup_scheduler(bot: Bot) -> AsyncIOScheduler:
    scheduler = AsyncIOScheduler(timezone="Europe/Minsk")
    scheduler.add_job(check_reminders, "cron", hour=9, minute=0, args=[bot])
    scheduler.start()
    return scheduler