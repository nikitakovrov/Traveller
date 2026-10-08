from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder


# ================== ОБЫЧНЫЕ КЛАВИАТУРЫ ==================

def main_menu_kb(is_admin: bool = False) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="🌍 Страны", callback_data="menu:countries")
    kb.button(text="💱 Конвертер валют", callback_data="menu:currency")
    kb.button(text="📄 Мои документы", callback_data="menu:documents")
    kb.button(text="⭐ Избранное", callback_data="menu:favorites")
    kb.button(text="⚙️ Настройки", callback_data="menu:settings")
    kb.button(text="❓ Помощь", callback_data="menu:help")
    if is_admin:
        kb.button(text="🛠 Админ-панель", callback_data="admin:menu")
        kb.adjust(2, 2, 2, 1)
    else:
        kb.adjust(2, 2, 2)
    return kb.as_markup()


def regions_kb(regions: list[dict]) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    for r in regions:
        kb.button(text=r["name"], callback_data=f"region:{r['id']}")
    kb.button(text="🔍 Поиск страны", callback_data="search:start")
    kb.button(text="⬅️ Назад", callback_data="menu:main")
    kb.adjust(2, 2, 1, 1)
    return kb.as_markup()


def countries_kb(countries: list[dict], back_cb: str = "menu:countries") -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    for c in countries:
        kb.button(text=c["name"], callback_data=f"country:{c['id']}")
    kb.button(text="⬅️ Назад", callback_data=back_cb)
    kb.adjust(2)
    return kb.as_markup()


def country_card_kb(country_id: int, fav: bool) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="ℹ️ Общая информация", callback_data=f"cinfo:{country_id}")
    kb.button(text="🛂 Визовые требования", callback_data=f"cvisa:{country_id}")
    kb.button(text="💡 Советы", callback_data=f"cadvice:{country_id}")
    if fav:
        kb.button(text="💔 Убрать из избранного", callback_data=f"favdel:{country_id}")
    else:
        kb.button(text="⭐ В избранное", callback_data=f"favadd:{country_id}")
    kb.button(text="⬅️ Назад", callback_data="menu:countries")
    kb.adjust(2, 1, 1)
    return kb.as_markup()


def back_to_country_kb(country_id: int) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="⬅️ К стране", callback_data=f"country:{country_id}")
    kb.button(text="🏠 Главное меню", callback_data="menu:main")
    kb.adjust(2)
    return kb.as_markup()


def advice_categories_kb(country_id: int, categories: list[str]) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    for cat in categories:
        kb.button(text=cat, callback_data=f"advcat:{country_id}:{cat}")
    kb.button(text="⬅️ К стране", callback_data=f"country:{country_id}")
    kb.adjust(2)
    return kb.as_markup()


def currency_kb(back_cb: str = "menu:main") -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="💱 Конвертировать", callback_data="currency:convert")
    kb.button(text="⭐ Сохранить валюту", callback_data="currency:save")
    kb.button(text="⬅️ Назад", callback_data=back_cb)
    kb.adjust(1, 1, 1)
    return kb.as_markup()


def currencies_list_kb(prefix: str) -> InlineKeyboardMarkup:
    currencies = ["BYN", "USD", "EUR", "RUB", "PLN", "UAH", "KZT", "GBP", "CNY", "TRY"]
    kb = InlineKeyboardBuilder()
    for c in currencies:
        kb.button(text=c, callback_data=f"{prefix}:{c}")
    kb.button(text="✏️ Ввести вручную", callback_data=f"{prefix}:manual")
    kb.button(text="⬅️ Назад", callback_data="menu:currency")
    kb.adjust(3)
    return kb.as_markup()


def documents_menu_kb() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="➕ Добавить документ", callback_data="doc:add")
    kb.button(text="📋 Список документов", callback_data="doc:list")
    kb.button(text="⬅️ Назад", callback_data="menu:main")
    kb.adjust(1, 1, 1)
    return kb.as_markup()


def doc_types_kb() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="🛂 Загранпаспорт", callback_data="doctype:passport")
    kb.button(text="📃 Виза", callback_data="doctype:visa")
    kb.button(text="🏥 Мед. страховка", callback_data="doctype:insurance")
    kb.button(text="⬅️ Назад", callback_data="menu:documents")
    kb.adjust(1, 1, 1, 1)
    return kb.as_markup()


def doc_delete_kb(docs: list[dict]) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    for d in docs:
        kb.button(
            text=f"❌ {d['doc_type']} ({d['expire_date']})",
            callback_data=f"docdel:{d['id']}",
        )
    kb.button(text="⬅️ Назад", callback_data="menu:documents")
    kb.adjust(1)
    return kb.as_markup()


def favorites_kb(favs: list[dict]) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    for f in favs:
        c = f.get("countries") or {}
        if c.get("id"):
            kb.button(text=c["name"], callback_data=f"country:{c['id']}")
    kb.button(text="⬅️ Назад", callback_data="menu:main")
    kb.adjust(2)
    return kb.as_markup()


def settings_kb() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="💱 Валюта по умолчанию", callback_data="settings:currency")
    kb.button(text="⬅️ Назад", callback_data="menu:main")
    kb.adjust(1, 1)
    return kb.as_markup()


def help_kb() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="ℹ️ О боте", callback_data="help:about")
    kb.button(text="❓ FAQ", callback_data="help:faq")
    kb.button(text="📊 Источники данных", callback_data="help:sources")
    kb.button(text="⬅️ Назад", callback_data="menu:main")
    kb.adjust(1, 1, 1, 1)
    return kb.as_markup()


def cancel_kb(cancel_cb: str = "menu:main") -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="❌ Отмена", callback_data=cancel_cb)
    return kb.as_markup()


# ================== АДМИН-КЛАВИАТУРЫ ==================

def admin_menu_kb() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="🌍 Регионы", callback_data="admin:regions")
    kb.button(text="🏙 Страны", callback_data="admin:countries")
    kb.button(text="🛂 Визы", callback_data="admin:visa")
    kb.button(text="💡 Советы", callback_data="admin:advice")
    kb.button(text="⬅️ В меню", callback_data="menu:main")
    kb.adjust(2, 1, 1)
    return kb.as_markup()


def admin_regions_kb(regions: list[dict]) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="➕ Добавить регион", callback_data="admin:region:add")
    for r in regions:
        kb.button(text=f"❌ {r['name']}", callback_data=f"admin:region:del:{r['id']}")
    kb.button(text="⬅️ Назад", callback_data="admin:menu")
    kb.adjust(1)
    return kb.as_markup()


def admin_countries_kb() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="➕ Добавить страну", callback_data="admin:country:add")
    kb.button(text="📋 Список стран", callback_data="admin:country:list")
    kb.button(text="✏️ Редактировать страну", callback_data="admin:country:edit_list")
    kb.button(text="🗑 Удалить страну", callback_data="admin:country:del_list")
    kb.button(text="⬅️ Назад", callback_data="admin:menu")
    kb.adjust(1)
    return kb.as_markup()


def admin_regions_select_kb(regions: list[dict], prefix: str) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    for r in regions:
        kb.button(text=r["name"], callback_data=f"{prefix}:{r['id']}")
    kb.button(text="❌ Отмена", callback_data="admin:menu")
    kb.adjust(2)
    return kb.as_markup()


def admin_countries_select_kb(countries: list[dict], prefix: str, back_cb: str = "admin:menu") -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    for c in countries:
        kb.button(text=c["name"], callback_data=f"{prefix}:{c['id']}")
    kb.button(text="⬅️ Назад", callback_data=back_cb)
    kb.adjust(2)
    return kb.as_markup()


def admin_delete_countries_kb(countries: list[dict]) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    for c in countries:
        kb.button(text=f"🗑 {c['name']}", callback_data=f"admin:country:del_confirm:{c['id']}")
    kb.button(text="⬅️ Назад", callback_data="admin:countries")
    kb.adjust(1)
    return kb.as_markup()


def admin_visa_kb() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="➕ Добавить/Обновить визу", callback_data="admin:visa:add")
    kb.button(text="🗑 Удалить визу", callback_data="admin:visa:del_list")
    kb.button(text="⬅️ Назад", callback_data="admin:menu")
    kb.adjust(1)
    return kb.as_markup()


def admin_advice_kb() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="➕ Добавить совет", callback_data="admin:advice:add")
    kb.button(text="📋 Список советов", callback_data="admin:advice:list")
    kb.button(text="🗑 Удалить совет", callback_data="admin:advice:del_list")
    kb.button(text="⬅️ Назад", callback_data="admin:menu")
    kb.adjust(1)
    return kb.as_markup()


def admin_advice_delete_kb(items: list[dict]) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    for a in items:
        short = (a["text"][:25] + "…") if len(a["text"]) > 25 else a["text"]
        kb.button(text=f"🗑 [{a['category']}] {short}", callback_data=f"admin:advice:del_confirm:{a['id']}")
    kb.button(text="⬅️ Назад", callback_data="admin:advice")
    kb.adjust(1)
    return kb.as_markup()


def admin_visa_delete_kb(items: list[dict]) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    for v in items:
        kb.button(text=f"🗑 {v['country_name']}", callback_data=f"admin:visa:del_confirm:{v['id']}")
    kb.button(text="⬅️ Назад", callback_data="admin:visa")
    kb.adjust(1)
    return kb.as_markup()


def admin_countries_edit_kb(countries: list[dict]) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    for c in countries:
        kb.button(text=f"✏️ {c['name']}", callback_data=f"admin:country:edit:{c['id']}")
    kb.button(text="⬅️ Назад", callback_data="admin:countries")
    kb.adjust(1)
    return kb.as_markup()


def admin_country_fields_kb(country_id: int) -> InlineKeyboardMarkup:
    fields = [
        ("name", "Название"),
        ("capital", "Столица"),
        ("currency", "Валюта"),
        ("language", "Язык"),
        ("timezone", "Часовой пояс"),
        ("phone_code", "Телефонный код"),
        ("domain", "Домен"),
        ("population", "Население"),
    ]
    kb = InlineKeyboardBuilder()
    for field, label in fields:
        kb.button(text=label, callback_data=f"admin:country:setfield:{country_id}:{field}")
    kb.button(text="🌍 Регионы", callback_data=f"admin:country:regions:{country_id}")
    kb.button(text="⬅️ Назад", callback_data="admin:country:edit_list")
    kb.adjust(2, 1, 1)
    return kb.as_markup()


def admin_regions_select_for_country_kb(regions: list[dict], country_id: int) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    for r in regions:
        kb.button(text=r["name"], callback_data=f"admin:country:setreg:{country_id}:{r['id']}")
    kb.button(text="⬅️ Отмена", callback_data=f"admin:country:edit:{country_id}")
    kb.adjust(2)
    return kb.as_markup()


def admin_country_regions_select_kb(
    regions: list[dict],
    selected_ids: list[int],
    country_id: int,
) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    for r in regions:
        mark = "✅" if r["id"] in selected_ids else "⬜"
        kb.button(
            text=f"{mark} {r['name']}",
            callback_data=f"admin:cregion:toggle:{country_id}:{r['id']}",
        )
    kb.button(text="💾 Готово", callback_data=f"admin:cregion:done:{country_id}")
    kb.button(text="⬅️ Отмена", callback_data=f"admin:country:edit:{country_id}")
    kb.adjust(2, 1, 1)
    return kb.as_markup()


def admin_country_regions_add_kb(
    regions: list[dict],
    country_id: int,
) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    for r in regions:
        kb.button(
            text=f"➕ {r['name']}",
            callback_data=f"admin:cregion:add:{country_id}:{r['id']}",
        )
    kb.button(text="⬅️ Отмена", callback_data=f"admin:cregion:manage:{country_id}")
    kb.adjust(2)
    return kb.as_markup()