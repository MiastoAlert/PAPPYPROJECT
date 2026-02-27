from __future__ import annotations

from contextlib import asynccontextmanager

import aiosqlite

from app.config import load_config

_config = load_config()


@asynccontextmanager
async def get_db() -> aiosqlite.Connection:
    db = await aiosqlite.connect(_config.db_path)
    db.row_factory = aiosqlite.Row
    await db.execute("PRAGMA journal_mode=WAL")
    await db.execute("PRAGMA synchronous=NORMAL")
    try:
        yield db
    finally:
        await db.close()
