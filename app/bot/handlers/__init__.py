from aiogram import Router

from app.bot.handlers.common import router as common_router
from app.bot.handlers.start import router as start_router


def setup_routers() -> Router:
    router = Router()
    router.include_router(start_router)
    router.include_router(common_router)
    return router