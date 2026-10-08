import aiohttp
from datetime import datetime, date
from config import EXCHANGE_API_URL


async def get_exchange_rate(from_cur: str, to_cur: str) -> tuple[float, str] | None:
    """Возвращает (курс, дата) или None при ошибке."""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{EXCHANGE_API_URL}{from_cur.upper()}", timeout=8) as resp:
                if resp.status != 200:
                    return None
                data = await resp.json()
                rate = data.get("rates", {}).get(to_cur.upper())
                if rate is None:
                    return None
                return float(rate), data.get("date", str(date.today()))
    except Exception:
        return None


def format_country_info(c: dict) -> str:
    return (
        f"🌍 <b>{c['name']}</b>\n\n"
        f"🏛 Столица: {c.get('capital', '—')}\n"
        f"👥 Население: {c.get('population', '—')}\n"
        f"🗣 Язык: {c.get('language', '—')}\n"
        f"💰 Валюта: {c.get('currency', '—')}\n"
        f"🕐 Часовой пояс: {c.get('timezone', '—')}\n"
        f"📞 Телефонный код: {c.get('phone_code', '—')}\n"
        f"🌐 Домен: {c.get('domain', '—')}\n\n"
    )


def format_visa_info(v: dict) -> str:
    return (
        f"🛂 <b>Визовые требования</b>\n\n"
        f"✈️ Безвизовый въезд: {v.get('visa_free', '—')}\n"
        f"⏱ Срок оформления: {v.get('processing_time', '—')}\n"
        f"💰 Консульский сбор: {v.get('fee', '—')}\n"
        f"📄 Документы: {v.get('documents', '—')}\n"
        f"📅 Срок действия визы: {v.get('validity', '—')}\n"
        f"🕐 Макс. пребывание: {v.get('max_stay', '—')}\n"
    )


def days_until(date_str: str) -> int:
    try:
        d = datetime.strptime(date_str, "%Y-%m-%d").date()
        return (d - date.today()).days
    except Exception:
        return -9999


def humanize_doc_type(t: str) -> str:
    return {"passport": "Загранпаспорт", "visa": "Виза", "insurance": "Мед. страховка"}.get(t, t)


def split_text(text: str, limit: int = 3900) -> list[str]:
    if len(text) <= limit:
        return [text]

    parts = []
    remaining = text

    while remaining:
        if len(remaining) <= limit:
            parts.append(remaining)
            break

        cut = remaining.rfind("\n", 0, limit)

        if cut == -1:
            cut = remaining.rfind(" ", 0, limit)

        if cut == -1:
            cut = limit

        parts.append(remaining[:cut].rstrip())
        remaining = remaining[cut:].lstrip("\n").lstrip()

    return parts


async def send_long_message(
        event,
        text: str,
        reply_markup=None,
        parse_mode: str = "HTML",
):
    from aiogram.types import Message, CallbackQuery

    parts = split_text(text)

    if len(parts) == 1:
        if isinstance(event, CallbackQuery):
            try:
                await event.message.edit_text(parts[0], reply_markup=reply_markup, parse_mode=parse_mode)
            except Exception:
                await event.message.answer(parts[0], reply_markup=reply_markup, parse_mode=parse_mode)
        else:
            await event.answer(parts[0], reply_markup=reply_markup, parse_mode=parse_mode)
        return

    if isinstance(event, CallbackQuery):
        try:
            await event.message.edit_text(
                f"{parts[0]}\n\n<i>…продолжение следует</i>",
                parse_mode=parse_mode,
            )
        except Exception:
            await event.message.answer(
                f"{parts[0]}\n\n<i>…продолжение следует</i>",
                parse_mode=parse_mode,
            )

        for i, part in enumerate(parts[1:-1], start=2):
            await event.message.answer(
                f"{part}\n\n<i>…часть {i} из {len(parts)}</i>",
                parse_mode=parse_mode,
            )

        await event.message.answer(
            f"{parts[-1]}\n\n<i>(конец, часть {len(parts)} из {len(parts)})</i>",
            reply_markup=reply_markup,
            parse_mode=parse_mode,
        )
    else:
        for i, part in enumerate(parts, start=1):
            is_last = (i == len(parts))
            marker = "" if is_last else f"\n\n<i>…часть {i} из {len(parts)}</i>"
            await event.answer(
                part + marker,
                reply_markup=reply_markup if is_last else None,
                parse_mode=parse_mode,
            )