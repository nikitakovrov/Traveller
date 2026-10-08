from aiogram import Router, F
from aiogram.types import CallbackQuery
from aiogram.fsm.context import FSMContext

from database import get_or_create_user, set_preferred_currency
from keyboards import settings_kb, currencies_list_kb, main_menu_kb
from .currency import CurrencySG

router = Router()


@router.callback_query(F.data == "menu:settings")
async def settings_menu(call: CallbackQuery):
    user = get_or_create_user(call.from_user.id)
    await call.message.edit_text(
        f"⚙️ <b>Настройки</b>\n\n"
        f"💱 Валюта по умолчанию: <b>{user.get('preferred_currency', 'BYN')}</b>",
        reply_markup=settings_kb(),
    )
    await call.answer()


@router.callback_query(F.data == "settings:currency")
async def settings_currency(call: CallbackQuery, state: FSMContext):
    await state.set_state(CurrencySG.choosing_default)
    await call.message.edit_text(
        "Выберите валюту по умолчанию:",
        reply_markup=currencies_list_kb("def"),
    )
    await call.answer()