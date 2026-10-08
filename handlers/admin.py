from aiogram import Router, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, CallbackQuery

from config import ADMIN_IDS
from database import (
    get_regions, add_region, delete_region,
    get_all_countries, add_country, delete_country,
    update_country_field, get_country,
    get_country_regions, set_country_regions,
    add_country_region, remove_country_region,
    upsert_visa_info, delete_visa_info, get_all_visa_with_countries,
    get_all_advice, add_advice, delete_advice,
)
from keyboards import (
    admin_menu_kb, admin_regions_kb, admin_countries_kb,
    admin_regions_select_kb, admin_countries_select_kb,
    admin_delete_countries_kb, admin_visa_kb, admin_advice_kb,
    admin_advice_delete_kb, admin_visa_delete_kb,
    admin_countries_edit_kb, admin_country_fields_kb,
    admin_country_regions_select_kb, admin_country_regions_add_kb,
    cancel_kb, main_menu_kb,
)

router = Router()


def is_admin(user_id: int) -> bool:
    return user_id in ADMIN_IDS


EDITABLE_FIELDS = {
    "name": "Название",
    "capital": "Столица",
    "currency": "Валюта",
    "language": "Язык",
    "timezone": "Часовой пояс",
    "phone_code": "Телефонный код",
    "domain": "Домен",
    "population": "Население",
}


async def deny(event):
    if isinstance(event, CallbackQuery):
        await event.answer("⛔ Нет доступа", show_alert=True)
    else:
        await event.answer("⛔ У вас нет доступа к админ-панели.")


# ================== FSM ==================

class AdminSG(StatesGroup):
    # Regions
    region_name = State()

    # Countries
    country_name = State()
    country_capital = State()
    country_currency = State()
    country_language = State()
    country_timezone = State()
    country_phone = State()
    country_domain = State()
    country_population = State()

    # Country editing
    country_edit_field_value = State()

    # Visa
    visa_free = State()
    visa_processing = State()
    visa_fee = State()
    visa_documents = State()
    visa_validity = State()
    visa_max_stay = State()

    # Advice
    advice_category = State()
    advice_text = State()


# ================== /admin ==================

@router.message(Command("admin"))
async def admin_cmd(message: Message):
    if not is_admin(message.from_user.id):
        await deny(message)
        return
    await message.answer(
        "🛠 <b>Админ-панель</b>\n\nВыберите раздел:",
        reply_markup=admin_menu_kb(),
    )


@router.callback_query(F.data == "admin:menu")
async def admin_menu(call: CallbackQuery, state: FSMContext):
    if not is_admin(call.from_user.id):
        await deny(call)
        return
    await state.clear()
    await call.message.edit_text("🛠 <b>Админ-панель</b>\n\nВыберите раздел:",
                                 reply_markup=admin_menu_kb())
    await call.answer()


# ================== РЕГИОНЫ ==================

@router.callback_query(F.data == "admin:regions")
async def admin_regions(call: CallbackQuery):
    if not is_admin(call.from_user.id):
        await deny(call)
        return
    regions = get_regions()
    text = "🌍 <b>Регионы</b>\n\n"
    text += "\n".join(f"• {r['name']}" for r in regions) if regions else "Пока нет регионов."
    await call.message.edit_text(text, reply_markup=admin_regions_kb(regions))
    await call.answer()


@router.callback_query(F.data == "admin:region:add")
async def admin_region_add(call: CallbackQuery, state: FSMContext):
    if not is_admin(call.from_user.id):
        await deny(call)
        return
    await state.set_state(AdminSG.region_name)
    await call.message.edit_text(
        "Введите название региона (например, Европа):",
        reply_markup=cancel_kb("admin:regions"),
    )
    await call.answer()


@router.message(AdminSG.region_name)
async def admin_region_save(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    name = message.text.strip()
    if not name:
        await message.answer("⚠️ Пустое название, попробуйте ещё раз.")
        return
    try:
        add_region(name)
        await state.clear()
        await message.answer(
            f"✅ Регион «{name}» добавлен.",
            reply_markup=admin_menu_kb(),
        )
    except Exception as e:
        await message.answer(f"❌ Ошибка: {e}")


@router.callback_query(F.data.startswith("admin:region:del:"))
async def admin_region_delete(call: CallbackQuery):
    if not is_admin(call.from_user.id):
        await deny(call)
        return
    rid = int(call.data.split(":")[3])
    try:
        delete_region(rid)
        await call.answer("Удалено")
    except Exception as e:
        await call.answer(f"Ошибка: {e}", show_alert=True)
    regions = get_regions()
    text = "🌍 <b>Регионы</b>\n\n"
    text += "\n".join(f"• {r['name']}" for r in regions) if regions else "Пока нет регионов."
    await call.message.edit_text(text, reply_markup=admin_regions_kb(regions))


# ================== СТРАНЫ ==================

@router.callback_query(F.data == "admin:countries")
async def admin_countries(call: CallbackQuery, state: FSMContext):
    if not is_admin(call.from_user.id):
        await deny(call)
        return
    await state.clear()
    await call.message.edit_text("🏙 <b>Управление странами</b>", reply_markup=admin_countries_kb())
    await call.answer()


@router.callback_query(F.data == "admin:country:list")
async def admin_country_list(call: CallbackQuery):
    if not is_admin(call.from_user.id):
        await deny(call)
        return
    countries = get_all_countries()
    if not countries:
        await call.message.edit_text("Пусто.", reply_markup=admin_countries_kb())
        await call.answer()
        return
    text = "📋 <b>Страны:</b>\n\n" + "\n".join(
        f"<code>{c['id']}</code> — {c['name']}" for c in countries
    )
    if len(text) > 4000:
        text = text[:3900] + "\n…"
    await call.message.edit_text(text, reply_markup=admin_countries_kb())
    await call.answer()


@router.callback_query(F.data == "admin:country:add")
async def admin_country_add_start(call: CallbackQuery, state: FSMContext):
    if not is_admin(call.from_user.id):
        await deny(call)
        return
    await state.clear()
    await state.set_state(AdminSG.country_name)
    await call.message.edit_text(
        "Введите название страны (например, Россия):",
        reply_markup=cancel_kb("admin:countries"),
    )
    await call.answer()


@router.message(AdminSG.country_name)
async def admin_country_name(message: Message, state: FSMContext):
    await state.update_data(name=message.text.strip())
    await state.set_state(AdminSG.country_capital)
    await message.answer("Введите столицу:")


@router.message(AdminSG.country_capital)
async def admin_country_capital(message: Message, state: FSMContext):
    await state.update_data(capital=message.text.strip())
    await state.set_state(AdminSG.country_currency)
    await message.answer("Введите валюту (например, EUR):")


@router.message(AdminSG.country_currency)
async def admin_country_currency(message: Message, state: FSMContext):
    await state.update_data(currency=message.text.strip().upper())
    await state.set_state(AdminSG.country_language)
    await message.answer("Введите государственный язык:")


@router.message(AdminSG.country_language)
async def admin_country_language(message: Message, state: FSMContext):
    await state.update_data(language=message.text.strip())
    await state.set_state(AdminSG.country_timezone)
    await message.answer("Введите часовой пояс (например, UTC+1):")


@router.message(AdminSG.country_timezone)
async def admin_country_timezone(message: Message, state: FSMContext):
    await state.update_data(timezone=message.text.strip())
    await state.set_state(AdminSG.country_phone)
    await message.answer("Введите телефонный код (например, +7):")


@router.message(AdminSG.country_phone)
async def admin_country_phone(message: Message, state: FSMContext):
    await state.update_data(phone_code=message.text.strip())
    await state.set_state(AdminSG.country_domain)
    await message.answer("Введите домен верхнего уровня (например, .ru):")


@router.message(AdminSG.country_domain)
async def admin_country_domain(message: Message, state: FSMContext):
    await state.update_data(domain=message.text.strip())
    await state.set_state(AdminSG.country_population)
    await message.answer(
        "Введите население (например, «144 млн») или отправьте «-», чтобы пропустить:"
    )


@router.message(AdminSG.country_population)
async def admin_country_population(message: Message, state: FSMContext):
    val = message.text.strip()
    population = None if val in ("-", "нет", "skip") else val

    data = await state.get_data()
    payload = {
        "name": data["name"],
        "capital": data["capital"],
        "currency": data["currency"],
        "language": data["language"],
        "timezone": data["timezone"],
        "phone_code": data["phone_code"],
        "domain": data["domain"],
        "population": population,
    }
    try:
        created = add_country(payload)
        await state.clear()
        await message.answer(
            f"✅ Страна «{payload['name']}» добавлена (id={created['id']}).\n\n"
            f"Теперь назначьте ей регионы через ✏️ «Редактировать страну» → «Регионы».",
            reply_markup=admin_menu_kb(),
        )
    except Exception as e:
        await message.answer(f"❌ Ошибка: {e}")


@router.callback_query(F.data == "admin:country:del_list")
async def admin_country_del_list(call: CallbackQuery):
    if not is_admin(call.from_user.id):
        await deny(call)
        return
    countries = get_all_countries()
    if not countries:
        await call.message.edit_text("Пусто.", reply_markup=admin_countries_kb())
        await call.answer()
        return
    await call.message.edit_text(
        "🗑 Выберите страну для удаления:",
        reply_markup=admin_delete_countries_kb(countries),
    )
    await call.answer()


@router.callback_query(F.data.startswith("admin:country:del_confirm:"))
async def admin_country_del_confirm(call: CallbackQuery):
    if not is_admin(call.from_user.id):
        await deny(call)
        return
    cid = int(call.data.split(":")[4])
    try:
        delete_country(cid)
        await call.answer("Страна удалена")
    except Exception as e:
        await call.answer(f"Ошибка: {e}", show_alert=True)
    countries = get_all_countries()
    if not countries:
        await call.message.edit_text("Пусто.", reply_markup=admin_countries_kb())
        return
    await call.message.edit_text(
        "🗑 Выберите страну для удаления:",
        reply_markup=admin_delete_countries_kb(countries),
    )


# ================== РЕДАКТИРОВАНИЕ СТРАНЫ ==================

@router.callback_query(F.data == "admin:country:edit_list")
async def admin_country_edit_list(call: CallbackQuery, state: FSMContext):
    if not is_admin(call.from_user.id):
        await deny(call)
        return
    await state.clear()
    countries = get_all_countries()
    if not countries:
        await call.message.edit_text("Пусто.", reply_markup=admin_countries_kb())
        await call.answer()
        return
    await call.message.edit_text(
        "✏️ Выберите страну для редактирования:",
        reply_markup=admin_countries_edit_kb(countries),
    )
    await call.answer()


@router.callback_query(F.data.startswith("admin:country:edit:"))
async def admin_country_edit(call: CallbackQuery, state: FSMContext):
    if not is_admin(call.from_user.id):
        await deny(call)
        return
    cid = int(call.data.split(":")[3])
    c = get_country(cid)
    if not c:
        await call.answer("Страна не найдена", show_alert=True)
        return

    regions = get_country_regions(cid)
    regions_text = ", ".join(r["name"] for r in regions) if regions else "—"

    await state.clear()
    text = (
        f"✏️ <b>Редактирование: {c['name']}</b>\n\n"
        f"🌍 Регионы: {regions_text}\n"
        f"🏛 Столица: {c.get('capital') or '—'}\n"
        f"💰 Валюта: {c.get('currency') or '—'}\n"
        f"🗣 Язык: {c.get('language') or '—'}\n"
        f"🕐 Часовой пояс: {c.get('timezone') or '—'}\n"
        f"📞 Телефонный код: {c.get('phone_code') or '—'}\n"
        f"🌐 Домен: {c.get('domain') or '—'}\n"
        f"👥 Население: {c.get('population') or '—'}\n\n"
        f"Что изменить?"
    )
    await call.message.edit_text(text, reply_markup=admin_country_fields_kb(cid))
    await call.answer()


@router.callback_query(F.data.startswith("admin:country:setfield:"))
async def admin_country_setfield(call: CallbackQuery, state: FSMContext):
    if not is_admin(call.from_user.id):
        await deny(call)
        return
    _, _, _, cid_str, field = call.data.split(":", 4)
    cid = int(cid_str)

    if field not in EDITABLE_FIELDS:
        await call.answer("Недопустимое поле", show_alert=True)
        return

    if field == "region_id":
        regions = get_regions()
        if not regions:
            await call.answer("Нет регионов", show_alert=True)
            return
        await call.message.edit_text(
            "Выберите новый регион:",
            reply_markup=admin_regions_select_for_country_kb(regions, cid),
        )
        await call.answer()
        return

    await state.update_data(edit_country_id=cid, edit_field=field)
    await state.set_state(AdminSG.country_edit_field_value)

    label = EDITABLE_FIELDS[field]
    await call.message.edit_text(
        f"Введите новое значение для поля <b>{label}</b>:\n\n"
        f"<i>Отправьте «-», чтобы очистить значение.</i>",
        reply_markup=cancel_kb(f"admin:country:edit:{cid}"),
    )
    await call.answer()


@router.callback_query(F.data.startswith("admin:country:setreg:"))
async def admin_country_setreg(call: CallbackQuery):
    if not is_admin(call.from_user.id):
        await deny(call)
        return
    _, _, _, cid_str, rid_str = call.data.split(":", 4)
    cid = int(cid_str)
    rid = int(rid_str)
    try:
        update_country_field(cid, "region_id", rid)
        await call.answer("Регион обновлён")
    except Exception as e:
        await call.answer(f"Ошибка: {e}", show_alert=True)
    await admin_country_edit(call, state=None) if False else None
    c = get_country(cid)
    if not c:
        await call.message.edit_text("Страна не найдена.", reply_markup=admin_countries_kb())
        return
    text = (
        f"✏️ <b>Редактирование: {c['name']}</b>\n\n"
        f"🏛 Столица: {c.get('capital') or '—'}\n"
        f"💰 Валюта: {c.get('currency') or '—'}\n"
        f"🗣 Язык: {c.get('language') or '—'}\n"
        f"🕐 Часовой пояс: {c.get('timezone') or '—'}\n"
        f"📞 Телефонный код: {c.get('phone_code') or '—'}\n"
        f"🌐 Домен: {c.get('domain') or '—'}\n"
        f"👥 Население: {c.get('population') or '—'}\n"
        f"Что изменить?"
    )
    await call.message.edit_text(text, reply_markup=admin_country_fields_kb(cid))


@router.message(AdminSG.country_edit_field_value)
async def admin_country_edit_value(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    data = await state.get_data()
    cid = data["edit_country_id"]
    field = data["edit_field"]

    raw = message.text.strip()
    value = None if raw in ("-", "") else raw

    if field == "currency" and value:
        value = value.upper()
    if field == "phone_code" and value and not value.startswith("+"):
        value = "+" + value
    if field == "domain" and value and not value.startswith("."):
        value = "." + value

    try:
        update_country_field(cid, field, value)
        await state.clear()
        await message.answer(
            f"✅ Поле «{EDITABLE_FIELDS.get(field, field)}» обновлено.",
            reply_markup=admin_countries_kb(),
        )
    except Exception as e:
        await message.answer(f"❌ Ошибка: {e}")


# ---------- УПРАВЛЕНИЕ РЕГИОНАМИ СТРАНЫ ----------

@router.callback_query(F.data.startswith("admin:country:regions:"))
async def admin_country_regions_manage(call: CallbackQuery, state: FSMContext):
    if not is_admin(call.from_user.id):
        await deny(call)
        return
    cid = int(call.data.split(":")[3])
    c = get_country(cid)
    if not c:
        await call.answer("Страна не найдена", show_alert=True)
        return
    await state.clear()

    all_regions = get_regions()
    selected = [r["id"] for r in get_country_regions(cid)]

    if not all_regions:
        await call.message.edit_text(
            "⚠️ В системе нет ни одного региона. Сначала создайте регион.",
            reply_markup=admin_countries_kb(),
        )
        await call.answer()
        return

    await call.message.edit_text(
        f"🌍 <b>Регионы для «{c['name']}»</b>\n\n"
        f"Отметьте регионы, к которым относится страна.\n"
        f"✅ — выбран, ⬜ — не выбран.",
        reply_markup=admin_country_regions_select_kb(all_regions, selected, cid),
    )
    await call.answer()


@router.callback_query(F.data.startswith("admin:cregion:toggle:"))
async def admin_country_region_toggle(call: CallbackQuery):
    if not is_admin(call.from_user.id):
        await deny(call)
        return
    _, _, _, cid_str, rid_str = call.data.split(":")
    cid = int(cid_str)
    rid = int(rid_str)

    selected = [r["id"] for r in get_country_regions(cid)]
    if rid in selected:
        remove_country_region(cid, rid)
        await call.answer("Удалено")
    else:
        add_country_region(cid, rid)
        await call.answer("Добавлено")

    all_regions = get_regions()
    selected = [r["id"] for r in get_country_regions(cid)]
    c = get_country(cid)
    text = (
        f"🌍 <b>Регионы для «{c['name']}»</b>\n\n"
        f"Отметьте регионы, к которым относится страна.\n"
        f"✅ — выбран, ⬜ — не выбран."
    )
    try:
        await call.message.edit_text(
            text,
            reply_markup=admin_country_regions_select_kb(all_regions, selected, cid),
        )
    except Exception:
        pass


@router.callback_query(F.data.startswith("admin:cregion:done:"))
async def admin_country_regions_done(call: CallbackQuery):
    if not is_admin(call.from_user.id):
        await deny(call)
        return
    cid = int(call.data.split(":")[3])
    await call.answer("Сохранено")
    await admin_country_edit(call, state=None)


@router.callback_query(F.data.startswith("admin:cregion:manage:"))
async def admin_country_regions_manage_alias(call: CallbackQuery, state: FSMContext):
    if not is_admin(call.from_user.id):
        await deny(call)
        return
    cid = int(call.data.split(":")[3])
    call.data = f"admin:country:regions:{cid}"
    await admin_country_regions_manage(call, state)


# ================== ВИЗЫ ==================

@router.callback_query(F.data == "admin:visa")
async def admin_visa(call: CallbackQuery, state: FSMContext):
    if not is_admin(call.from_user.id):
        await deny(call)
        return
    await state.clear()
    await call.message.edit_text("🛂 <b>Визовые требования</b>", reply_markup=admin_visa_kb())
    await call.answer()


@router.callback_query(F.data == "admin:visa:add")
async def admin_visa_add(call: CallbackQuery, state: FSMContext):
    if not is_admin(call.from_user.id):
        await deny(call)
        return
    countries = get_all_countries()
    if not countries:
        await call.message.edit_text("⚠️ Сначала добавьте страны.", reply_markup=admin_visa_kb())
        await call.answer()
        return
    await state.clear()
    await call.message.edit_text(
        "Выберите страну для визовых требований:",
        reply_markup=admin_countries_select_kb(countries, "admin:visa:country", back_cb="admin:visa"),
    )
    await call.answer()


@router.callback_query(F.data.startswith("admin:visa:country:"))
async def admin_visa_pick_country(call: CallbackQuery, state: FSMContext):
    if not is_admin(call.from_user.id):
        await deny(call)
        return
    cid = int(call.data.split(":")[3])
    await state.update_data(country_id=cid)
    await state.set_state(AdminSG.visa_free)
    await call.message.edit_text(
        "Введите информацию о безвизовом въезде (например, «Безвиз для граждан Беларуси, до 90 дней»):",
        reply_markup=cancel_kb("admin:visa"),
    )
    await call.answer()


@router.message(AdminSG.visa_free)
async def admin_visa_free(message: Message, state: FSMContext):
    await state.update_data(visa_free=message.text.strip())
    await state.set_state(AdminSG.visa_processing)
    await message.answer("Введите срок оформления (например, 10-15 дней):")


@router.message(AdminSG.visa_processing)
async def admin_visa_processing(message: Message, state: FSMContext):
    await state.update_data(processing_time=message.text.strip())
    await state.set_state(AdminSG.visa_fee)
    await message.answer("Введите стоимость консульского сбора (например, 80 EUR):")


@router.message(AdminSG.visa_fee)
async def admin_visa_fee(message: Message, state: FSMContext):
    await state.update_data(fee=message.text.strip())
    await state.set_state(AdminSG.visa_documents)
    await message.answer("Введите перечень документов (через запятую):")


@router.message(AdminSG.visa_documents)
async def admin_visa_documents(message: Message, state: FSMContext):
    await state.update_data(documents=message.text.strip())
    await state.set_state(AdminSG.visa_validity)
    await message.answer("Введите срок действия визы (например, 90 дней):")


@router.message(AdminSG.visa_validity)
async def admin_visa_validity(message: Message, state: FSMContext):
    await state.update_data(validity=message.text.strip())
    await state.set_state(AdminSG.visa_max_stay)
    await message.answer("Введите максимальный срок пребывания (например, 90 дней):")


@router.message(AdminSG.visa_max_stay)
async def admin_visa_max_stay(message: Message, state: FSMContext):
    data = await state.get_data()
    payload = {
        "visa_free": data["visa_free"],
        "processing_time": data["processing_time"],
        "fee": data["fee"],
        "documents": data["documents"],
        "validity": data["validity"],
        "max_stay": message.text.strip(),
    }
    try:
        upsert_visa_info(data["country_id"], payload)
        await state.clear()
        await message.answer("✅ Визовые требования сохранены.", reply_markup=admin_menu_kb())
    except Exception as e:
        await message.answer(f"❌ Ошибка: {e}")


@router.callback_query(F.data == "admin:visa:del_list")
async def admin_visa_del_list(call: CallbackQuery):
    if not is_admin(call.from_user.id):
        await deny(call)
        return
    items = get_all_visa_with_countries()
    if not items:
        await call.message.edit_text("Пусто.", reply_markup=admin_visa_kb())
        await call.answer()
        return
    await call.message.edit_text(
        "🗑 Выберите визу для удаления:",
        reply_markup=admin_visa_delete_kb(items),
    )
    await call.answer()


@router.callback_query(F.data.startswith("admin:visa:del_confirm:"))
async def admin_visa_del_confirm(call: CallbackQuery):
    if not is_admin(call.from_user.id):
        await deny(call)
        return
    vid = int(call.data.split(":")[3])
    try:
        delete_visa_info(vid)
        await call.answer("Удалено")
    except Exception as e:
        await call.answer(f"Ошибка: {e}", show_alert=True)
    items = get_all_visa_with_countries()
    if not items:
        await call.message.edit_text("Пусто.", reply_markup=admin_visa_kb())
        return
    await call.message.edit_text("🗑 Выберите визу для удаления:", reply_markup=admin_visa_delete_kb(items))


# ================== СОВЕТЫ ==================

@router.callback_query(F.data == "admin:advice")
async def admin_advice(call: CallbackQuery, state: FSMContext):
    if not is_admin(call.from_user.id):
        await deny(call)
        return
    await state.clear()
    await call.message.edit_text("💡 <b>Советы</b>", reply_markup=admin_advice_kb())
    await call.answer()


@router.callback_query(F.data == "admin:advice:add")
async def admin_advice_add(call: CallbackQuery, state: FSMContext):
    if not is_admin(call.from_user.id):
        await deny(call)
        return
    countries = get_all_countries()
    if not countries:
        await call.message.edit_text("⚠️ Сначала добавьте страны.", reply_markup=admin_advice_kb())
        await call.answer()
        return
    await state.clear()
    await call.message.edit_text(
        "Выберите страну:",
        reply_markup=admin_countries_select_kb(countries, "admin:advice:country", back_cb="admin:advice"),
    )
    await call.answer()


@router.callback_query(F.data.startswith("admin:advice:country:"))
async def admin_advice_pick_country(call: CallbackQuery, state: FSMContext):
    if not is_admin(call.from_user.id):
        await deny(call)
        return
    cid = int(call.data.split(":")[3])
    await state.update_data(country_id=cid)
    await state.set_state(AdminSG.advice_category)
    await call.message.edit_text(
        "Введите категорию (например, Безопасность, Транспорт, Кухня):",
        reply_markup=cancel_kb("admin:advice"),
    )
    await call.answer()


@router.message(AdminSG.advice_category)
async def admin_advice_category(message: Message, state: FSMContext):
    await state.update_data(category=message.text.strip())
    await state.set_state(AdminSG.advice_text)
    await message.answer("Введите текст совета:")


@router.message(AdminSG.advice_text)
async def admin_advice_text(message: Message, state: FSMContext):
    data = await state.get_data()
    try:
        add_advice(data["country_id"], data["category"], message.text.strip())
        await state.clear()
        await message.answer("✅ Совет добавлен.", reply_markup=admin_menu_kb())
    except Exception as e:
        await message.answer(f"❌ Ошибка: {e}")


@router.callback_query(F.data == "admin:advice:list")
async def admin_advice_list(call: CallbackQuery):
    if not is_admin(call.from_user.id):
        await deny(call)
        return
    rows = get_all_advice()
    if not rows:
        await call.message.edit_text("Пусто.", reply_markup=admin_advice_kb())
        await call.answer()
        return
    lines = ["📋 <b>Советы:</b>\n"]
    for r in rows:
        c = r.get("countries") or {}
        lines.append(f"<b>{c.get('name','—')}</b> [{r['category']}]: {r['text'][:60]}")
    text = "\n".join(lines)
    if len(text) > 4000:
        text = text[:3900] + "\n…"
    await call.message.edit_text(text, reply_markup=admin_advice_kb())
    await call.answer()


@router.callback_query(F.data == "admin:advice:del_list")
async def admin_advice_del_list(call: CallbackQuery):
    if not is_admin(call.from_user.id):
        await deny(call)
        return
    items = get_all_advice()
    if not items:
        await call.message.edit_text("Пусто.", reply_markup=admin_advice_kb())
        await call.answer()
        return
    await call.message.edit_text("🗑 Выберите совет для удаления:", reply_markup=admin_advice_delete_kb(items))
    await call.answer()


@router.callback_query(F.data.startswith("admin:advice:del_confirm:"))
async def admin_advice_del_confirm(call: CallbackQuery):
    if not is_admin(call.from_user.id):
        await deny(call)
        return
    aid = int(call.data.split(":")[3])
    try:
        delete_advice(aid)
        await call.answer("Удалено")
    except Exception as e:
        await call.answer(f"Ошибка: {e}", show_alert=True)
    items = get_all_advice()
    if not items:
        await call.message.edit_text("Пусто.", reply_markup=admin_advice_kb())
        return
    await call.message.edit_text("🗑 Выберите совет для удаления:", reply_markup=admin_advice_delete_kb(items))