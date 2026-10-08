from supabase import create_client, Client
from config import SUPABASE_URL, SUPABASE_KEY
from typing import Optional

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)


# ================== USERS ==================

def get_or_create_user(telegram_id: int, username: Optional[str] = None) -> dict:
    res = supabase.table("users").select("*").eq("telegram_id", telegram_id).execute()
    if res.data:
        return res.data[0]
    new_user = {
        "telegram_id": telegram_id,
        "username": username,
        "preferred_currency": "BYN",
    }
    created = supabase.table("users").insert(new_user).execute()
    return created.data[0]


def set_preferred_currency(telegram_id: int, currency: str) -> None:
    supabase.table("users").update({"preferred_currency": currency}).eq(
        "telegram_id", telegram_id
    ).execute()


# ================== REGIONS ==================

def get_regions() -> list[dict]:
    return supabase.table("regions").select("*").order("name").execute().data


def add_region(name: str) -> dict:
    res = supabase.table("regions").insert({"name": name}).execute()
    return res.data[0]


def delete_region(region_id: int) -> None:
    supabase.table("regions").delete().eq("id", region_id).execute()


# ================== COUNTRIES ==================

def get_countries_by_region(region_id: int) -> list[dict]:
    """Возвращает страны, привязанные к региону, через country_regions."""
    rows = (
        supabase.table("country_regions")
        .select("countries(id, name)")
        .eq("region_id", region_id)
        .execute()
        .data
    )
    result = []
    for r in rows:
        c = r.get("countries") or {}
        if c.get("id"):
            result.append({"id": c["id"], "name": c["name"]})
    return sorted(result, key=lambda x: x["name"])


def search_countries(query: str) -> list[dict]:
    return (
        supabase.table("countries")
        .select("id, name")
        .ilike("name", f"%{query}%")
        .order("name")
        .execute()
        .data
    )


def get_country_full(country_id: int) -> Optional[dict]:
    res = supabase.table("countries").select("*").eq("id", country_id).execute()
    return res.data[0] if res.data else None


def get_all_countries() -> list[dict]:
    return supabase.table("countries").select("id, name").order("name").execute().data


def add_country(data: dict) -> dict:
    """Создаёт страну и возвращает её запись.
    Регионы передаются отдельно через set_country_regions()."""
    res = supabase.table("countries").insert(data).execute()
    return res.data[0]


def delete_country(country_id: int) -> None:
    supabase.table("countries").delete().eq("id", country_id).execute()


def get_country(country_id: int) -> Optional[dict]:
    res = supabase.table("countries").select("*").eq("id", country_id).execute()
    return res.data[0] if res.data else None


def update_country_field(country_id: int, field: str, value) -> None:
    supabase.table("countries").update({field: value}).eq("id", country_id).execute()


# ---------- СВЯЗЬ СТРАНА ↔ РЕГИОНЫ ----------

def get_country_regions(country_id: int) -> list[dict]:
    """Возвращает список регионов, к которым привязана страна."""
    rows = (
        supabase.table("country_regions")
        .select("region_id, regions(id, name)")
        .eq("country_id", country_id)
        .execute()
        .data
    )
    result = []
    for r in rows:
        reg = r.get("regions") or {}
        if reg.get("id"):
            result.append({"id": reg["id"], "name": reg["name"]})
    return result


def set_country_regions(country_id: int, region_ids: list[int]) -> None:
    """Полностью переписывает связи страны с регионами."""
    supabase.table("country_regions").delete().eq("country_id", country_id).execute()
    if not region_ids:
        return
    payload = [{"country_id": country_id, "region_id": rid} for rid in region_ids]
    supabase.table("country_regions").insert(payload).execute()


def add_country_region(country_id: int, region_id: int) -> None:
    try:
        supabase.table("country_regions").insert(
            {"country_id": country_id, "region_id": region_id}
        ).execute()
    except Exception:
        # Скорее всего, уже существует — unique(country_id, region_id)
        pass


def remove_country_region(country_id: int, region_id: int) -> None:
    supabase.table("country_regions").delete().eq("country_id", country_id).eq(
        "region_id", region_id
    ).execute()


# ---------- ВИЗЫ ----------

def get_visa_info(country_id: int) -> Optional[dict]:
    res = supabase.table("visa_requirements").select("*").eq("country_id", country_id).execute()
    return res.data[0] if res.data else None


def upsert_visa_info(country_id: int, data: dict) -> None:
    existing = get_visa_info(country_id)
    payload = {"country_id": country_id, **data}
    if existing:
        supabase.table("visa_requirements").update(payload).eq("id", existing["id"]).execute()
    else:
        supabase.table("visa_requirements").insert(payload).execute()


def delete_visa_info(visa_id: int) -> None:
    supabase.table("visa_requirements").delete().eq("id", visa_id).execute()


def get_all_visa_with_countries() -> list[dict]:
    rows = (
        supabase.table("visa_requirements")
        .select("id, country_id, countries(name)")
        .execute()
        .data
    )
    result = []
    for r in rows:
        c = r.get("countries") or {}
        result.append({"id": r["id"], "country_id": r["country_id"], "country_name": c.get("name", "—")})
    return result


# ================== ADVICE ==================

def get_country_advice(country_id: int) -> list[dict]:
    return (
        supabase.table("advice")
        .select("*")
        .eq("country_id", country_id)
        .execute()
        .data
    )


def get_all_advice() -> list[dict]:
    return (
        supabase.table("advice")
        .select("id, category, text, country_id, countries(name)")
        .order("id")
        .execute()
        .data
    )


def add_advice(country_id: int, category: str, text: str) -> dict:
    res = supabase.table("advice").insert({
        "country_id": country_id,
        "category": category,
        "text": text,
    }).execute()
    return res.data[0]


def delete_advice(advice_id: int) -> None:
    supabase.table("advice").delete().eq("id", advice_id).execute()


# ================== FAVORITES ==================

def add_favorite(telegram_id: int, country_id: int) -> None:
    supabase.table("favorites").insert(
        {"telegram_id": telegram_id, "country_id": country_id}
    ).execute()


def remove_favorite(telegram_id: int, country_id: int) -> None:
    supabase.table("favorites").delete().eq("telegram_id", telegram_id).eq(
        "country_id", country_id
    ).execute()


def get_favorites(telegram_id: int) -> list[dict]:
    return (
        supabase.table("favorites")
        .select("country_id, countries(id, name)")
        .eq("telegram_id", telegram_id)
        .execute()
        .data
    )


def is_favorite(telegram_id: int, country_id: int) -> bool:
    res = (
        supabase.table("favorites")
        .select("id")
        .eq("telegram_id", telegram_id)
        .eq("country_id", country_id)
        .execute()
    )
    return bool(res.data)


# ================== DOCUMENTS ==================

def add_document(telegram_id: int, doc_type: str, expire_date: str, number: Optional[str], reminder_days: int) -> dict:
    res = supabase.table("documents").insert({
        "telegram_id": telegram_id,
        "doc_type": doc_type,
        "expire_date": expire_date,
        "number": number,
        "reminder_days": reminder_days,
    }).execute()
    return res.data[0]


def get_documents(telegram_id: int) -> list[dict]:
    return (
        supabase.table("documents")
        .select("*")
        .eq("telegram_id", telegram_id)
        .order("expire_date")
        .execute()
        .data
    )


def delete_document(doc_id: int, telegram_id: int) -> None:
    supabase.table("documents").delete().eq("id", doc_id).eq(
        "telegram_id", telegram_id
    ).execute()


def get_document(doc_id: int) -> Optional[dict]:
    res = supabase.table("documents").select("*").eq("id", doc_id).execute()
    return res.data[0] if res.data else None


# ================== NOTIFICATIONS ==================

def notification_already_sent(doc_id: int) -> bool:
    res = supabase.table("notifications_log").select("id").eq("document_id", doc_id).execute()
    return bool(res.data)


def log_notification(doc_id: int, telegram_id: int, message: str) -> None:
    supabase.table("notifications_log").insert({
        "document_id": doc_id,
        "telegram_id": telegram_id,
        "message": message,
    }).execute()