from aiogram import Router, F
from aiogram.types import CallbackQuery

from database import get_favorites
from keyboards import favorites_kb, main_menu_kb

router = Router()


@router.callback_query(F.data == "menu:favorites")
async def show_favorites(call: CallbackQuery):
    favs = get_favorites(call.from_user.id)
    if not favs:
        await call.message.edit_text(
            "⭐ У вас пока нет избранных стран.\n\n"
            "Откройте любую страну и нажмите «⭐ В избранное».",
            reply_markup=main_menu_kb(),
        )
        await call.answer()
        return
    await call.message.edit_text(
        f"⭐ <b>Избранные страны ({len(favs)})</b>\n\nВыберите страну:",
        reply_markup=favorites_kb(favs),
    )
    await call.answer()