from __future__ import annotations

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from app.database.db import get_db
from app.database.queries import get_top_users
from app.services.levels import get_level

router = Router()


@router.message(Command("top"))
async def cmd_top(message: Message) -> None:
    if message.chat.type != "private":
        return

    async with get_db() as db:
        rows = await get_top_users(db, limit=10)

    if not rows:
        await message.answer("Пока нет участников в таблице лидеров.")
        return

    lines = ["Топ по Pappy:\n"]
    for idx, row in enumerate(rows, start=1):
        username = row["username"]
        display = f"@{username}" if username else f"Пользователь {row['id']}"
        level = get_level(int(row["total_referrals"]))
        balance = float(row["balance"])
        lines.append(f"{idx}. {display} — {balance:.2f} Pappy — {level['name']}")

    await message.answer("\n".join(lines))
