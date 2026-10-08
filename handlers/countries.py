from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, CallbackQuery

from database import (
    get_countries_by_region, search_countries, get_country_full,
    get_visa_info, get_country_advice,
    is_favorite, add_favorite, remove_favorite
)
from keyboards import (
    countries_kb, country_card_kb, back_to_country_kb,
    advice_categories_kb, cancel_kb
)
from utils import (
    format_country_info, format_visa_info,
    send_long_message,   # ← новая функция
)

router = Router()


class SearchSG(StatesGroup):
    waiting_query = State()


# ---------- Выбор региона ----------
@router.callback_query(F.data.startswith("region:"))
async def show_region_countries(call: CallbackQuery):
    region_id = int(call.data.split(":")[1])
    countries = get_countries_by_region(region_id)
    if not countries:
        await call.message.edit_text("⚠️ В этом регионе пока нет стран.", reply_markup=countries_kb([]))
        return
    await call.message.edit_text(
        f"🌍 Найдено стран: <b>{len(countries)}</b>\nВыберите страну:",
        reply_markup=countries_kb(countries, back_cb="menu:countries"),
    )
    await call.answer()


# ---------- Поиск ----------
@router.callback_query(F.data == "search:start")
async def search_start(call: CallbackQuery, state: FSMContext):
    await state.set_state(SearchSG.waiting_query)
    await call.message.edit_text(
        "🔍 Введите название страны (или его часть):",
        reply_markup=cancel_kb("menu:countries"),
    )
    await call.answer()


@router.message(SearchSG.waiting_query)
async def search_process(message: Message, state: FSMContext):
    query = message.text.strip()
    if len(query) < 2:
        await message.answer("⚠️ Введите минимум 2 символа.")
        return
    results = search_countries(query)
    await state.clear()
    if not results:
        await message.answer(
            f"😔 По запросу «{query}» ничего не найдено.\nПопробуйте другое название.",
        )
        return
    await message.answer(
        f"🔍 Найдено: <b>{len(results)}</b>. Выберите страну:",
        reply_markup=countries_kb(results, back_cb="menu:countries"),
    )


# ---------- Карточка страны ----------
@router.callback_query(F.data.startswith("country:"))
async def show_country(call: CallbackQuery):
    country_id = int(call.data.split(":")[1])
    c = get_country_full(country_id)
    if not c:
        await call.answer("Страна не найдена", show_alert=True)
        return
    fav = is_favorite(call.from_user.id, country_id)
    text = (
        f"🌍 <b>{c['name']}</b>\n\n"
        f"🏛 Столица: {c.get('capital', '—')}\n"
        f"💰 Валюта: {c.get('currency', '—')}\n"
        f"🗣 Язык: {c.get('language', '—')}\n\n"
        f"Выберите раздел:"
    )
    await call.message.edit_text(text, reply_markup=country_card_kb(country_id, fav))
    await call.answer()


# ---------- Избранное ----------
@router.callback_query(F.data.startswith("favadd:"))
async def fav_add(call: CallbackQuery):
    country_id = int(call.data.split(":")[1])
    add_favorite(call.from_user.id, country_id)
    await call.answer("⭐ Добавлено в избранное")
    c = get_country_full(country_id)
    await call.message.edit_reply_markup(
        reply_markup=country_card_kb(country_id, True)
    )


@router.callback_query(F.data.startswith("favdel:"))
async def fav_del(call: CallbackQuery):
    country_id = int(call.data.split(":")[1])
    remove_favorite(call.from_user.id, country_id)
    await call.answer("💔 Удалено из избранного")
    await call.message.edit_reply_markup(
        reply_markup=country_card_kb(country_id, False)
    )


# ---------- Информация о стране ----------
@router.callback_query(F.data.startswith("cinfo:"))
async def country_info(call: CallbackQuery):
    cid = int(call.data.split(":")[1])
    c = get_country_full(cid)
    if not c:
        await call.answer("Нет данных", show_alert=True)
        return

    text = format_country_info(c)
    await send_long_message(call, text, reply_markup=back_to_country_kb(cid))
    await call.answer()


@router.callback_query(F.data.startswith("cvisa:"))
async def country_visa(call: CallbackQuery):
    cid = int(call.data.split(":")[1])
    v = get_visa_info(cid)
    if not v:
        await call.answer("Визовые требования не заполнены", show_alert=True)
        return

    text = (
        format_visa_info(v)
        + "\n\n<i>⚠️ Информация носит справочный характер. "
          "Проверяйте данные на сайтах посольств.</i>"
    )
    await send_long_message(call, text, reply_markup=back_to_country_kb(cid))
    await call.answer()


@router.callback_query(F.data.startswith("cadvice:"))
async def country_advice(call: CallbackQuery):
    cid = int(call.data.split(":")[1])
    items = get_country_advice(cid)
    if not items:
        await call.answer("Советов пока нет", show_alert=True)
        return
    categories = sorted({i["category"] for i in items})
    await call.message.edit_text(
        "💡 <b>Советы путешественникам</b>\n\nВыберите категорию:",
        reply_markup=advice_categories_kb(cid, categories),
    )
    await call.answer()


@router.callback_query(F.data.startswith("advcat:"))
async def advice_category(call: CallbackQuery):
    _, cid, cat = call.data.split(":", 2)
    items = [i for i in get_country_advice(int(cid)) if i["category"] == cat]

    text = f"💡 <b>{cat}</b>\n\n" + "\n\n".join(f"• {i['text']}" for i in items)
    await send_long_message(call, text, reply_markup=back_to_country_kb(int(cid)))
    await call.answer()