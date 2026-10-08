from aiogram import Router, F
from aiogram.filters import CommandStart
from aiogram.types import Message, CallbackQuery

from config import ADMIN_IDS
from database import get_or_create_user
from keyboards import main_menu_kb

router = Router()


@router.message(CommandStart())
async def cmd_start(message: Message):
    get_or_create_user(message.from_user.id, message.from_user.username)
    is_admin = message.from_user.id in ADMIN_IDS
    await message.answer(
        f"👋 Добро пожаловать, {message.from_user.first_name}!\n\n"
        f"Я — <b>Помощник путешественника</b>. Помогу с информацией о странах, "
        f"визовыми требованиями, советами, фразами и конвертацией валют.\n\n"
        f"Выберите раздел в меню ниже 👇",
        reply_markup=main_menu_kb(is_admin=is_admin),
    )


@router.callback_query(F.data == "menu:main")
async def back_to_main(call: CallbackQuery):
    is_admin = call.from_user.id in ADMIN_IDS
    await call.message.edit_text(
        "🏠 <b>Главное меню</b>\n\nВыберите раздел:",
        reply_markup=main_menu_kb(is_admin=is_admin),
    )
    await call.answer()


@router.callback_query(F.data == "menu:countries")
async def menu_countries(call: CallbackQuery):
    from database import get_regions
    from keyboards import regions_kb
    regions = get_regions()
    if not regions:
        is_admin = call.from_user.id in ADMIN_IDS
        await call.message.edit_text(
            "⚠️ Регионы пока не загружены.",
            reply_markup=main_menu_kb(is_admin=is_admin),
        )
        return
    await call.message.edit_text(
        "🌍 <b>Выбор страны</b>\n\nВыберите регион или воспользуйтесь поиском:",
        reply_markup=regions_kb(regions),
    )
    await call.answer()