import asyncio
import logging

from aiogram import Bot, Dispatcher

from app.bot.handlers import setup_routers
from app.core.config import settings


async def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )

    bot = Bot(token=settings.bot_token)
    dp = Dispatcher()

    dp.include_router(setup_routers())

    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Bot stopped")