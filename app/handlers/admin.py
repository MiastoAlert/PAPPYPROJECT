from __future__ import annotations

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from app.config import load_config
from app.database.db import get_db
from app.database.queries import get_totals

router = Router()
_config = load_config()


@router.message(Command("admin_stats"))
async def cmd_admin_stats(message: Message) -> None:
    if message.chat.type != "private":
        return

    user = message.from_user
    if not user or user.id not in _config.admin_ids:
        await message.answer("Недостаточно прав.")
        return

    async with get_db() as db:
        totals = await get_totals(db)

    text = (
        "Статистика проекта\n\n"
        f"Пользователей: {totals['users']}\n"
        f"Рефералов: {totals['referrals']}\n"
        f"Обменов: {totals['exchanges']}\n"
        f"Суммарный баланс: {totals['total_balance']:.2f} Pappy"
    )
    await message.answer(text)
