# import_countries.py
import asyncio
import aiohttp
import os

from dotenv import load_dotenv
from database import supabase, get_regions, add_country

# Импортируем словарь переводов (создай файл ru_translations.py)
try:
    from ru_translations import translate_country
except ImportError:
    # Если файла нет — просто возвращаем как есть
    def translate_country(name: str) -> str:
        return name

load_dotenv()

API_KEY = os.getenv("RESTCOUNTRIES_KEY")
BASE_URL = "https://api.restcountries.com/countries/v5"

# Маппинг региона API → название региона в твоей БД.
# ВАЖНО: API возвращает "Americas" (не "America") и "Oceania" (не "Australia")
REGION_MAP = {
    "Europe":    "Европа",
    "Asia":      "Азия",
    "Americas":  "Америка",           # ← ключ именно "Americas"
    "Africa":    "Африка",
    "Oceania":   "Австралия и Океания",  # ← ключ именно "Oceania"
}


async def fetch_all_countries() -> list[dict]:
    """Забирает ВСЕ страны через v5 с учётом пагинации."""
    headers = {"Authorization": f"Bearer {API_KEY}"}
    all_countries = []
    limit = 100
    offset = 0

    async with aiohttp.ClientSession() as session:
        while True:
            url = (
                f"{BASE_URL}"
                f"?response_fields=names,capitals,population,currencies,languages,"
                f"timezones,calling_codes,tlds,region"
                f"&limit={limit}&offset={offset}"
            )
            async with session.get(url, headers=headers, timeout=60) as resp:
                if resp.status != 200:
                    text = await resp.text()
                    print(f"⚠️ API вернул {resp.status}: {text[:200]}")
                    break
                data = await resp.json()

            payload = data.get("data", {})
            objects = payload.get("objects", [])
            meta = payload.get("meta", {})

            if not objects:
                break

            all_countries.extend(objects)
            print(f"   → получено {len(objects)} (всего {len(all_countries)})")

            total = meta.get("total")
            if total is not None and len(all_countries) >= total:
                break

            if len(objects) < limit:
                break

            offset += limit
            await asyncio.sleep(0.2)

    return all_countries


def normalize_country(raw: dict) -> dict:
    """Преобразует ответ v5 в строку для таблицы countries (с переводом)."""
    names = raw.get("names") or {}
    common_name = names.get("common") or names.get("official")

    # ПЕРЕВОД НАЗВАНИЯ НА РУССКИЙ
    if common_name:
        common_name = translate_country(common_name)

    capitals = raw.get("capitals") or []
    capital = capitals[0]["name"] if capitals and capitals[0].get("name") else None

    currencies = raw.get("currencies") or []
    currency_code = currencies[0]["code"] if currencies else None

    languages = raw.get("languages") or []
    language = ", ".join(l["name"] for l in languages if l.get("name")) if languages else None

    timezones = raw.get("timezones") or []
    if len(timezones) == 1:
        timezone = timezones[0]
    elif timezones:
        timezone = f"от {min(timezones)} до {max(timezones)}"
    else:
        timezone = None

    calling_codes = raw.get("calling_codes") or []
    phone_code = calling_codes[0] if calling_codes else None

    tlds = raw.get("tlds") or []
    domain = tlds[0] if tlds else None

    population = raw.get("population")
    population_str = f"{population:,}".replace(",", " ") if population else None

    return {
        "name": common_name,
        "capital": capital,      # столицу тоже можно перевести, но это сложнее
        "currency": currency_code,
        "language": language,
        "timezone": timezone,
        "phone_code": phone_code,
        "domain": domain,
        "population": population_str,
    }


async def main():
    if not API_KEY:
        print("❌ Добавь RESTCOUNTRIES_KEY=rc_live_... в .env")
        return

    regions = get_regions()
    region_by_name = {r["name"]: r["id"] for r in regions}
    if not region_by_name:
        print("❌ В таблице regions пусто. Создай регионы в админке.")
        return

    print("🌐 Загружаю страны из REST Countries v5...")
    raw_countries = await fetch_all_countries()
    print(f"✅ Получено {len(raw_countries)} стран.\n")

    # Проверяем, какие регионы есть в API, но нет в БД
    api_regions = {r.get("region") for r in raw_countries if r.get("region")}
    for ar in api_regions:
        if ar and ar not in REGION_MAP:
            print(f"⚠️ Неизвестный регион в API: {ar}")

    existing = supabase.table("countries").select("name").execute().data
    existing_names = {row["name"] for row in existing}

    inserted = skipped = failed = 0

    for raw in raw_countries:
        region_en = raw.get("region")
        region_ru = REGION_MAP.get(region_en)
        if not region_ru:
            print(f"⏭ Пропущен (регион '{region_en}' не смапплен): {raw.get('names', {}).get('common')}")
            continue

        try:
            payload = normalize_country(raw)
        except Exception as e:
            print(f"⚠️ Не удалось разобрать: {e}")
            failed += 1
            continue

        if not payload["name"] or payload["name"] in existing_names:
            skipped += 1
            continue

        try:
            created = add_country(payload)
            country_id = created["id"]
            region_id = region_by_name.get(region_ru)
            if region_id:
                supabase.table("country_regions").insert({
                    "country_id": country_id,
                    "region_id": region_id,
                }).execute()
            print(f"➕ {payload['name']} ({region_ru})")
            inserted += 1
            await asyncio.sleep(0.05)
        except Exception as e:
            print(f"❌ Ошибка при вставке {payload['name']}: {e}")
            failed += 1

    print(f"\n📊 Итог:")
    print(f"   ✅ Добавлено: {inserted}")
    print(f"   ⏭ Пропущено:  {skipped}")
    print(f"   ❌ Ошибок:     {failed}")


if __name__ == "__main__":
    asyncio.run(main())