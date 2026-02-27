from __future__ import annotations

from aiogram import Bot, Router
from aiogram.filters import Command
from aiogram.types import Message

from app.config import load_config
from app.database.db import get_db
from app.database.queries import ensure_user, get_user
from app.services.levels import get_level

router = Router()
_config = load_config()


@router.message(Command("profile"))
async def cmd_profile(message: Message, bot: Bot) -> None:
    if message.chat.type != "private":
        return

    user = message.from_user
    if not user:
        return

    async with get_db() as db:
        await ensure_user(db, user.id, user.username)
        row = await get_user(db, user.id)

    if row is None:
        await message.answer("Не удалось загрузить профиль.")
        return

    total_referrals = int(row["total_referrals"])
    level = get_level(total_referrals)
    balance = float(row["balance"])
    total_messages = int(row["total_referral_messages"])

    bot_me = await bot.get_me()
    referral_link = f"https://t.me/{bot_me.username}?start={user.id}"

    text = (
        "Профиль\n\n"
        f"Баланс: {balance:.2f} Pappy\n"
        f"Приглашено: {total_referrals}\n"
        f"Уровень: {level['name']}\n"
        f"Сообщений рефералов: {total_messages}\n\n"
        f"Твоя ссылка: {referral_link}"
    )
    await message.answer(text)
