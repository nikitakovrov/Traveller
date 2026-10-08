from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, CallbackQuery

from database import add_document, get_documents, delete_document, get_document
from keyboards import documents_menu_kb, doc_types_kb, doc_delete_kb, cancel_kb, main_menu_kb
from utils import days_until, humanize_doc_type
from config import DEFAULT_REMINDER_DAYS

router = Router()


class DocSG(StatesGroup):
    choosing_type = State()
    waiting_date = State()
    waiting_number = State()


@router.callback_query(F.data == "menu:documents")
async def doc_menu(call: CallbackQuery):
    await call.message.edit_text(
        "📄 <b>Мои документы</b>\n\n"
        "Здесь можно вести учёт загранпаспорта, визы и страховки. "
        "Бот напомнит о сроках действия.",
        reply_markup=documents_menu_kb(),
    )
    await call.answer()


@router.callback_query(F.data == "doc:add")
async def doc_add(call: CallbackQuery, state: FSMContext):
    await state.set_state(DocSG.choosing_type)
    await call.message.edit_text("Выберите тип документа:", reply_markup=doc_types_kb())
    await call.answer()


@router.callback_query(F.data.startswith("doctype:"))
async def doc_type(call: CallbackQuery, state: FSMContext):
    dtype = call.data.split(":")[1]
    await state.update_data(doc_type=dtype)
    await state.set_state(DocSG.waiting_date)
    await call.message.edit_text(
        "Введите дату окончания в формате <b>ГГГГ-ММ-ДД</b> (например, 2026-12-31):",
        reply_markup=cancel_kb("menu:documents"),
    )
    await call.answer()


@router.message(DocSG.waiting_date)
async def doc_date(message: Message, state: FSMContext):
    from datetime import datetime
    text = message.text.strip()
    try:
        datetime.strptime(text, "%Y-%m-%d")
    except ValueError:
        await message.answer("⚠️ Неверный формат. Введите как 2026-12-31.")
        return
    if days_until(text) < 0:
        await message.answer("⚠️ Дата уже в прошлом. Введите будущую дату.")
        return
    await state.update_data(expire_date=text)
    await state.set_state(DocSG.waiting_number)
    await message.answer(
        "Введите номер документа или отправьте «-», чтобы пропустить:",
        reply_markup=cancel_kb("menu:documents"),
    )


@router.message(DocSG.waiting_number)
async def doc_number(message: Message, state: FSMContext):
    number = None if message.text.strip() in ("-", "нет", "skip") else message.text.strip()
    data = await state.get_data()
    dtype = data["doc_type"]
    reminder_days = DEFAULT_REMINDER_DAYS.get(dtype, 7)
    doc = add_document(
        message.from_user.id, dtype, data["expire_date"], number, reminder_days
    )
    await state.clear()
    await message.answer(
        f"✅ Документ добавлен!\n\n"
        f"Тип: <b>{humanize_doc_type(dtype)}</b>\n"
        f"Действует до: <b>{data['expire_date']}</b>\n"
        f"Напоминание: за <b>{reminder_days}</b> дн.\n\n"
        f"Номер: {number or '—'}",
        reply_markup=documents_menu_kb(),
    )


@router.callback_query(F.data == "doc:list")
async def doc_list(call: CallbackQuery):
    docs = get_documents(call.from_user.id)
    if not docs:
        await call.message.edit_text(
            "📋 У вас пока нет добавленных документов.",
            reply_markup=documents_menu_kb(),
        )
        await call.answer()
        return
    lines = ["📋 <b>Ваши документы:</b>\n"]
    for d in docs:
        days = days_until(d["expire_date"])
        marker = "🔴" if days <= d.get("reminder_days", 7) else "🟢"
        lines.append(
            f"{marker} <b>{humanize_doc_type(d['doc_type'])}</b>\n"
            f"   до {d['expire_date']} (осталось {days} дн.)\n"
            f"   № {d.get('number') or '—'}\n"
        )
    await call.message.edit_text(
        "\n".join(lines),
        reply_markup=doc_delete_kb(docs),
    )
    await call.answer()


@router.callback_query(F.data.startswith("docdel:"))
async def doc_delete(call: CallbackQuery):
    doc_id = int(call.data.split(":")[1])
    doc = get_document(doc_id)
    if not doc or doc["telegram_id"] != call.from_user.id:
        await call.answer("Документ не найден", show_alert=True)
        return
    delete_document(doc_id, call.from_user.id)
    await call.answer("Удалено")
    await doc_list(call)