from __future__ import annotations

import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode

from app.config import load_config
from app.database.db import get_db
from app.database.schema import init_db
from app.handlers import setup_routers


async def _init_database() -> None:
    async with get_db() as db:
        await init_db(db)


async def main() -> None:
    logging.basicConfig(level=logging.INFO)
    config = load_config()

    await _init_database()

    bot = Bot(token=config.bot_token, parse_mode=ParseMode.HTML)
    await bot.get_me()
    await bot.delete_webhook(drop_pending_updates=True)

    dp = Dispatcher()
    for router in setup_routers():
        dp.include_router(router)

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
