from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()


def _parse_admin_ids(raw: str) -> set[int]:
    if not raw:
        return set()
    result: set[int] = set()
    for part in raw.split(","):
        part = part.strip()
        if not part:
            continue
        try:
            result.add(int(part))
        except ValueError:
            continue
    return result


@dataclass(frozen=True)
class Config:
    bot_token: str
    admin_ids: set[int]
    group_id: int | None
    webapp_url: str | None
    group_invite_url: str | None
    db_path: str


def load_config() -> Config:
    bot_token = os.getenv("BOT_TOKEN", "").strip()
    if not bot_token:
        raise RuntimeError("BOT_TOKEN не задан в переменных окружения.")

    admin_ids = _parse_admin_ids(os.getenv("ADMIN_IDS", ""))

    group_id_raw = os.getenv("GROUP_ID", "").strip()
    group_id = int(group_id_raw) if group_id_raw else None

    webapp_url = os.getenv("WEBAPP_URL", "").strip() or None
    group_invite_url = os.getenv("GROUP_INVITE_URL", "").strip() or None

    db_path = os.getenv("DB_PATH", "./pappy.sqlite3").strip()

    return Config(
        bot_token=bot_token,
        admin_ids=admin_ids,
        group_id=group_id,
        webapp_url=webapp_url,
        group_invite_url=group_invite_url,
        db_path=db_path,
    )
