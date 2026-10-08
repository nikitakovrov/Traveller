from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.filters import Command

from keyboards import help_kb, main_menu_kb

router = Router()


@router.message(Command("help"))
async def cmd_help(message: Message):
    await message.answer(
        "❓ <b>Помощь</b>\n\nВыберите раздел:",
        reply_markup=help_kb(),
    )


@router.callback_query(F.data == "menu:help")
async def help_menu(call: CallbackQuery):
    await call.message.edit_text("❓ <b>Помощь</b>\n\nВыберите раздел:", reply_markup=help_kb())
    await call.answer()


@router.callback_query(F.data == "help:about")
async def help_about(call: CallbackQuery):
    text = (
        "ℹ️ <b>О боте</b>\n\n"
        "<b>Помощник путешественника</b> — Telegram-бот для комплексной "
        "информационной поддержки при подготовке к поездкам и во время путешествий.\n\n"
        "<b>Возможности:</b>\n"
        "🌍 Информация о странах\n"
        "🛂 Визовые требования\n"
        "💡 Советы путешественникам\n"
        "💱 Конвертер валют\n"
        "📄 Учёт документов и напоминания\n"
        "⭐ Избранные страны"
    )
    await call.message.edit_text(text, reply_markup=help_kb())
    await call.answer()


@router.callback_query(F.data == "help:faq")
async def help_faq(call: CallbackQuery):
    text = (
        "❓ <b>Частые вопросы</b>\n\n"
        "<b>Как найти страну?</b>\n"
        "Раздел «Страны» → выберите регион или нажмите «Поиск страны».\n\n"
        "<b>Как добавить документ?</b>\n"
        "«Мои документы» → «Добавить документ» → выберите тип и введите дату.\n\n"
        "<b>Когда придёт напоминание?</b>\n"
        "За 30 дней для паспорта и за 7 дней для визы/страховки "
        "(по умолчанию).\n\n"
        "<b>Как изменить валюту по умолчанию?</b>\n"
        "«Настройки» → «Валюта по умолчанию»."
    )
    await call.message.edit_text(text, reply_markup=help_kb())
    await call.answer()


@router.callback_query(F.data == "help:sources")
async def help_sources(call: CallbackQuery):
    text = (
        "📊 <b>Источники данных</b>\n\n"
        "• Курсы валют — внешний API (ExchangeRate-API)\n"
        "• Информация о странах — база данных бота (обновляется администратором)\n"
        "• Визовые требования — справочные данные, обновляются вручную\n\n"
        "⚠️ Информация о визовых требованиях носит <b>справочный характер</b> "
        "и не является официальным источником. Проверяйте актуальные данные "
        "на сайтах посольств и консульств."
    )
    await call.message.edit_text(text, reply_markup=help_kb())
    await call.answer()