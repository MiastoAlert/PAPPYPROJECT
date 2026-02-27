from __future__ import annotations

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

router = Router()


@router.message(Command("myid"))
async def cmd_myid(message: Message) -> None:
    user = message.from_user
    if not user:
        return
    await message.answer(f"Ваш ID: {user.id}")


@router.message(Command("chatid"))
async def cmd_chatid(message: Message) -> None:
    chat = message.chat
    await message.answer(f"ID этого чата: {chat.id}")
