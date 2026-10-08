from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, CallbackQuery

from database import get_or_create_user, set_preferred_currency
from keyboards import currency_kb, currencies_list_kb, cancel_kb, main_menu_kb
from utils import get_exchange_rate

router = Router()


class CurrencySG(StatesGroup):
    waiting_amount = State()
    choosing_from = State()
    choosing_to = State()
    waiting_manual_code = State()
    choosing_default = State()


@router.callback_query(F.data == "menu:currency")
async def currency_menu(call: CallbackQuery):
    user = get_or_create_user(call.from_user.id)
    await call.message.edit_text(
        f"💱 <b>Конвертер валют</b>\n\n"
        f"Ваша валюта по умолчанию: <b>{user.get('preferred_currency', 'BYN')}</b>",
        reply_markup=currency_kb(),
    )
    await call.answer()


@router.callback_query(F.data == "currency:convert")
async def currency_convert_start(call: CallbackQuery, state: FSMContext):
    await state.set_state(CurrencySG.waiting_amount)
    await call.message.edit_text(
        "💱 Введите сумму для конвертации:",
        reply_markup=cancel_kb("menu:currency"),
    )
    await call.answer()


@router.message(CurrencySG.waiting_amount)
async def currency_amount(message: Message, state: FSMContext):
    try:
        amount = float(message.text.replace(",", "."))
        if amount <= 0:
            raise ValueError
    except ValueError:
        await message.answer("⚠️ Введите корректное положительное число.")
        return
    await state.update_data(amount=amount)
    await state.set_state(CurrencySG.choosing_from)
    await message.answer(
        "Выберите исходную валюту:",
        reply_markup=currencies_list_kb("from"),
    )


@router.callback_query(F.data.startswith("from:"))
async def choose_from(call: CallbackQuery, state: FSMContext):
    val = call.data.split(":", 1)[1]
    if val == "manual":
        await state.set_state(CurrencySG.waiting_manual_code)
        await state.update_data(manual_for="from")
        await call.message.edit_text("Введите код валюты (например, USD):",
                                     reply_markup=cancel_kb("menu:currency"))
        await call.answer()
        return
    await state.update_data(from_cur=val)
    await state.set_state(CurrencySG.choosing_to)
    await call.message.edit_text(
        "Выберите целевую валюту:",
        reply_markup=currencies_list_kb("to"),
    )
    await call.answer()


@router.callback_query(F.data.startswith("to:"))
async def choose_to(call: CallbackQuery, state: FSMContext):
    val = call.data.split(":", 1)[1]
    if val == "manual":
        await state.set_state(CurrencySG.waiting_manual_code)
        await state.update_data(manual_for="to")
        await call.message.edit_text("Введите код валюты (например, EUR):",
                                     reply_markup=cancel_kb("menu:currency"))
        await call.answer()
        return
    await state.update_data(to_cur=val)
    await finish_conversion(call, state)


@router.message(CurrencySG.waiting_manual_code)
async def manual_code(message: Message, state: FSMContext):
    code = message.text.strip().upper()
    if len(code) < 3 or not code.isalpha():
        await message.answer("⚠️ Код валюты — 3 латинские буквы, например USD.")
        return
    data = await state.get_data()
    if data.get("manual_for") == "from":
        await state.update_data(from_cur=code)
        await state.set_state(CurrencySG.choosing_to)
        await message.answer("Выберите целевую валюту:", reply_markup=currencies_list_kb("to"))
    else:
        await state.update_data(to_cur=code)
        await finish_conversion(message, state)


async def finish_conversion(event, state: FSMContext):
    data = await state.get_data()
    amount = data["amount"]
    from_cur = data["from_cur"]
    to_cur = data["to_cur"]

    result = await get_exchange_rate(from_cur, to_cur)
    if not result:
        text = "⚠️ Не удалось получить курс. Попробуйте позже."
        if isinstance(event, CallbackQuery):
            await event.message.edit_text(text, reply_markup=currency_kb())
        else:
            await event.answer(text)
        await state.clear()
        return

    rate, date_str = result
    total = round(amount * rate, 2)
    text = (
        f"💱 <b>Результат конвертации</b>\n\n"
        f"{amount} {from_cur} = <b>{total} {to_cur}</b>\n\n"
        f"Курс: 1 {from_cur} = {rate:.4f} {to_cur}\n"
        f"Дата: {date_str}"
    )
    if isinstance(event, CallbackQuery):
        await event.message.edit_text(text, reply_markup=currency_kb())
    else:
        await event.answer(text, reply_markup=currency_kb())
    await state.clear()


# ---------- Сохранение валюты ----------
@router.callback_query(F.data == "currency:save")
async def save_currency_start(call: CallbackQuery, state: FSMContext):
    await state.set_state(CurrencySG.choosing_default)
    await call.message.edit_text(
        "Выберите валюту по умолчанию:",
        reply_markup=currencies_list_kb("def"),
    )
    await call.answer()


@router.callback_query(F.data.startswith("def:"))
async def save_currency(call: CallbackQuery, state: FSMContext):
    val = call.data.split(":", 1)[1]
    if val == "manual":
        await call.message.edit_text("Введите код валюты вручную (например, BYN):")
        await state.update_data(manual_for="def")
        await state.set_state(CurrencySG.waiting_manual_code)
        await call.answer()
        return
    set_preferred_currency(call.from_user.id, val)
    await state.clear()
    await call.message.edit_text(
        f"✅ Валюта по умолчанию сохранена: <b>{val}</b>",
        reply_markup=currency_kb(),
    )
    await call.answer("Сохранено")