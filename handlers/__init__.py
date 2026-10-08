from aiogram import Router
from . import start, countries, currency, documents, favorites, settings, help, admin


def setup_routers() -> Router:
    root = Router()
    root.include_router(admin.router)
    root.include_router(start.router)
    root.include_router(countries.router)
    root.include_router(currency.router)
    root.include_router(documents.router)
    root.include_router(favorites.router)
    root.include_router(settings.router)
    root.include_router(help.router)
    return root