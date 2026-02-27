from __future__ import annotations

import hashlib
import hmac
import json
import os
from typing import Any
from urllib.parse import parse_qsl

from aiogram import Bot
from aiogram.enums import ParseMode
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from app.config import load_config
from app.database.db import get_db
from app.database.queries import (
    ensure_user,
    get_invite_link_for_user,
    get_top_users,
    get_user,
    save_invite_link,
    try_exchange,
)
from app.services.levels import get_level

config = load_config()
bot = Bot(token=config.bot_token, parse_mode=ParseMode.HTML)
bot_username: str | None = None

STATIC_DIR = os.path.join(os.path.dirname(__file__), "webapp")


class ExchangeRequest(BaseModel):
    amount: float
    steam_link: str


def _validate_init_data(init_data: str) -> dict[str, Any]:
    if not init_data:
        raise HTTPException(status_code=401, detail="Нет данных авторизации.")

    data = dict(parse_qsl(init_data, keep_blank_values=True))
    received_hash = data.pop("hash", "")
    if not received_hash:
        raise HTTPException(status_code=401, detail="Нет подписи авторизации.")

    data_check_string = "\n".join(f"{k}={v}" for k, v in sorted(data.items()))
    secret_key = hmac.new(b"WebAppData", config.bot_token.encode(), hashlib.sha256).digest()
    calculated_hash = hmac.new(
        secret_key, data_check_string.encode(), hashlib.sha256
    ).hexdigest()

    if not hmac.compare_digest(calculated_hash, received_hash):
        raise HTTPException(status_code=401, detail="Некорректная подпись.")

    return data


def _extract_user(data: dict[str, Any]) -> dict[str, Any]:
    raw_user = data.get("user")
    if not raw_user:
        raise HTTPException(status_code=401, detail="Нет данных пользователя.")
    try:
        user = json.loads(raw_user)
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=401, detail="Невозможно разобрать пользователя.") from exc
    if "id" not in user:
        raise HTTPException(status_code=401, detail="Не найден идентификатор пользователя.")
    return user


async def _get_user_from_request(request: Request) -> dict[str, Any]:
    init_data = request.headers.get("X-Tg-Init-Data", "")
    data = _validate_init_data(init_data)
    return _extract_user(data)


app = FastAPI(title="Pappy мини-приложение")


@app.get("/")
async def root() -> RedirectResponse:
    return RedirectResponse(url="/app")


@app.get("/api/me")
async def api_me(request: Request) -> dict[str, Any]:
    tg_user = await _get_user_from_request(request)
    user_id = int(tg_user["id"])
    username = tg_user.get("username")

    async with get_db() as db:
        await ensure_user(db, user_id, username)
        row = await get_user(db, user_id)

        referral_link = None
        if config.group_id is not None:
            referral_link = await get_invite_link_for_user(db, user_id)
            if referral_link is None:
                try:
                    invite = await bot.create_chat_invite_link(
                        chat_id=config.group_id,
                        name=f"ref-{user_id}",
                    )
                    referral_link = invite.invite_link
                    await save_invite_link(db, user_id, referral_link)
                except Exception:
                    referral_link = None

    if not row:
        raise HTTPException(status_code=404, detail="Пользователь не найден.")

    total_referrals = int(row["total_referrals"])
    level = get_level(total_referrals)

    return {
        "id": user_id,
        "username": username,
        "balance": float(row["balance"]),
        "total_referrals": total_referrals,
        "total_referral_messages": int(row["total_referral_messages"]),
        "level": level,
        "referral_link": referral_link,
    }


@app.get("/api/leaderboard")
async def api_leaderboard(request: Request) -> dict[str, Any]:
    await _get_user_from_request(request)
    async with get_db() as db:
        rows = await get_top_users(db, limit=20)

    items = []
    for row in rows:
        username = row["username"]
        display = f"@{username}" if username else f"Пользователь {row['id']}"
        level = get_level(int(row["total_referrals"]))
        items.append(
            {
                "id": int(row["id"]),
                "name": display,
                "balance": float(row["balance"]),
                "level": level["name"],
            }
        )

    return {"items": items}


@app.post("/api/exchange")
async def api_exchange(request: Request, payload: ExchangeRequest) -> dict[str, Any]:
    tg_user = await _get_user_from_request(request)
    user_id = int(tg_user["id"])
    username = tg_user.get("username")

    amount = float(payload.amount)
    steam_link = payload.steam_link.strip()
    if amount not in (10, 20, 50, 100):
        raise HTTPException(status_code=400, detail="Некорректная сумма обмена.")
    if not steam_link:
        raise HTTPException(status_code=400, detail="Введите SteamLink.")

    async with get_db() as db:
        await ensure_user(db, user_id, username)
        success = await try_exchange(db, user_id, amount, steam_link)

    if not success:
        raise HTTPException(status_code=400, detail="Недостаточно Pappy для обмена.")

    if config.admin_ids:
        display = f"@{username}" if username else "без ника"
        text = (
            f"Пользователь {display} (айди: {user_id}) обменял {amount:.2f} Pappy.\n"
            f"SteamLink: {steam_link}"
        )
        for admin_id in config.admin_ids:
            await bot.send_message(admin_id, text)

    return {"ok": True}


@app.on_event("shutdown")
async def shutdown_event() -> None:
    await bot.session.close()


@app.on_event("startup")
async def startup_event() -> None:
    global bot_username
    try:
        me = await bot.get_me()
        bot_username = me.username
    except Exception:
        bot_username = None


app.mount("/app", StaticFiles(directory=STATIC_DIR, html=True), name="webapp")
