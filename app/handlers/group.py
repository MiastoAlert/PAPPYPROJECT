from __future__ import annotations

import time

from aiogram import F, Router
from aiogram.types import Message

from app.config import load_config
from app.database.db import get_db
from app.database.queries import (
    add_referral,
    can_count_message,
    ensure_user,
    get_user,
    increment_inviter_for_message,
)

router = Router()
_config = load_config()
_MESSAGE_REWARD = 0.02


def _is_target_group(message: Message) -> bool:
    if message.chat.type not in ("group", "supergroup"):
        return False
    if _config.group_id is None:
        return False
    return message.chat.id == _config.group_id


@router.message(F.new_chat_members)
async def handle_new_members(message: Message) -> None:
    if not _is_target_group(message):
        return

    async with get_db() as db:
        for member in message.new_chat_members:
            await ensure_user(db, member.id, member.username)
            row = await get_user(db, member.id)
            if not row:
                continue
            inviter_id = row["invited_by"]
            if inviter_id is None or inviter_id == member.id:
                continue
            await add_referral(db, int(inviter_id), member.id)


@router.message(F.text)
async def handle_group_text(message: Message) -> None:
    if not _is_target_group(message):
        return

    user = message.from_user
    if not user or not message.text:
        return

    text = message.text.strip()
    if len(text) <= 5:
        return

    async with get_db() as db:
        await ensure_user(db, user.id, user.username)
        row = await get_user(db, user.id)
        if not row:
            return
        inviter_id = row["invited_by"]
        if inviter_id is None or inviter_id == user.id:
            return

        now_ts = int(time.time())
        if not await can_count_message(db, user.id, now_ts):
            return

        await increment_inviter_for_message(db, int(inviter_id), _MESSAGE_REWARD)
