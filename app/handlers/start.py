from __future__ import annotations

from aiogram import Bot, Router
from aiogram.filters import CommandStart
from aiogram.filters.command import CommandObject
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message, WebAppInfo

from app.config import load_config
from app.database.db import get_db
from app.database.queries import ensure_user, get_user, set_invited_by

router = Router()
_config = load_config()


def _webapp_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Открыть Pappy",
                    web_app=WebAppInfo(url=_config.webapp_url),
                )
            ]
        ]
    )


@router.message(CommandStart())
async def cmd_start(message: Message, command: CommandObject, bot: Bot) -> None:
    if message.chat.type != "private":
        return

    user = message.from_user
    if not user:
        return

    async with get_db() as db:
        await ensure_user(db, user.id, user.username)

        inviter_id = None
        if command.args:
            try:
                inviter_id = int(command.args)
            except ValueError:
                inviter_id = None

        assigned = False
        if inviter_id and inviter_id != user.id:
            inviter = await get_user(db, inviter_id)
            if inviter:
                assigned = await set_invited_by(db, user.id, inviter_id)

    text = (
        "Добро пожаловать в Pappy.\n\n"
        "Здесь ты получаешь Pappy за активность своих рефералов в группе.\n"
        "Открой мини-приложение для баланса, обмена и таблицы лидеров."
    )
    if assigned:
        text += "\n\nРеферальная привязка подтверждена."

    await message.answer(text, reply_markup=_webapp_keyboard())
