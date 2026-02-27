from __future__ import annotations

import time
from typing import Any

import aiosqlite


async def ensure_user(db: aiosqlite.Connection, user_id: int, username: str | None) -> None:
    row = await db.execute_fetchone("SELECT id, username FROM users WHERE id = ?", (user_id,))
    if row is None:
        await db.execute(
            "INSERT INTO users (id, username, balance, invited_by, total_referrals, total_referral_messages) "
            "VALUES (?, ?, 0, NULL, 0, 0)",
            (user_id, username),
        )
        await db.commit()
        return

    if username and row["username"] != username:
        await db.execute("UPDATE users SET username = ? WHERE id = ?", (username, user_id))
        await db.commit()


async def get_user(db: aiosqlite.Connection, user_id: int) -> aiosqlite.Row | None:
    return await db.execute_fetchone("SELECT * FROM users WHERE id = ?", (user_id,))


async def set_invited_by(
    db: aiosqlite.Connection, user_id: int, inviter_id: int
) -> bool:
    row = await db.execute_fetchone(
        "SELECT invited_by FROM users WHERE id = ?", (user_id,)
    )
    if row is None:
        return False
    if row["invited_by"] is not None:
        return False

    await db.execute(
        "UPDATE users SET invited_by = ? WHERE id = ?", (inviter_id, user_id)
    )
    await db.commit()
    return True


async def referral_exists(
    db: aiosqlite.Connection, inviter_id: int, invited_id: int
) -> bool:
    row = await db.execute_fetchone(
        "SELECT 1 FROM referrals WHERE inviter_id = ? AND invited_id = ?",
        (inviter_id, invited_id),
    )
    return row is not None


async def add_referral(
    db: aiosqlite.Connection, inviter_id: int, invited_id: int
) -> bool:
    if await referral_exists(db, inviter_id, invited_id):
        return False
    await db.execute(
        "INSERT INTO referrals (inviter_id, invited_id, created_at) VALUES (?, ?, ?)",
        (inviter_id, invited_id, int(time.time())),
    )
    await db.execute(
        "UPDATE users SET total_referrals = total_referrals + 1 WHERE id = ?",
        (inviter_id,),
    )
    await db.commit()
    return True


async def can_count_message(
    db: aiosqlite.Connection, user_id: int, now_ts: int
) -> bool:
    row = await db.execute_fetchone(
        "SELECT last_message_time, counted_messages FROM messages WHERE user_id = ?",
        (user_id,),
    )
    if row is None:
        await db.execute(
            "INSERT INTO messages (user_id, last_message_time, counted_messages) "
            "VALUES (?, ?, 1)",
            (user_id, now_ts),
        )
        await db.commit()
        return True

    if now_ts - int(row["last_message_time"]) < 10:
        return False

    await db.execute(
        "UPDATE messages SET last_message_time = ?, counted_messages = counted_messages + 1 "
        "WHERE user_id = ?",
        (now_ts, user_id),
    )
    await db.commit()
    return True


async def increment_inviter_for_message(
    db: aiosqlite.Connection, inviter_id: int, reward: float
) -> None:
    await db.execute(
        "UPDATE users SET balance = balance + ?, total_referral_messages = total_referral_messages + 1 "
        "WHERE id = ?",
        (reward, inviter_id),
    )
    await db.commit()


async def get_top_users(
    db: aiosqlite.Connection, limit: int = 10
) -> list[aiosqlite.Row]:
    rows = await db.execute_fetchall(
        "SELECT * FROM users ORDER BY balance DESC, total_referrals DESC LIMIT ?",
        (limit,),
    )
    return list(rows)


async def get_totals(db: aiosqlite.Connection) -> dict[str, Any]:
    users_row = await db.execute_fetchone("SELECT COUNT(*) AS cnt FROM users")
    referrals_row = await db.execute_fetchone("SELECT COUNT(*) AS cnt FROM referrals")
    exchanges_row = await db.execute_fetchone("SELECT COUNT(*) AS cnt FROM exchanges")
    balance_row = await db.execute_fetchone("SELECT COALESCE(SUM(balance), 0) AS total FROM users")
    return {
        "users": int(users_row["cnt"]) if users_row else 0,
        "referrals": int(referrals_row["cnt"]) if referrals_row else 0,
        "exchanges": int(exchanges_row["cnt"]) if exchanges_row else 0,
        "total_balance": float(balance_row["total"]) if balance_row else 0.0,
    }


async def try_exchange(
    db: aiosqlite.Connection, user_id: int, amount: float, steam_link: str
) -> bool:
    await db.execute("BEGIN IMMEDIATE")
    row = await db.execute_fetchone("SELECT balance FROM users WHERE id = ?", (user_id,))
    if row is None:
        await db.execute("ROLLBACK")
        return False
    if float(row["balance"]) < amount:
        await db.execute("ROLLBACK")
        return False

    await db.execute(
        "UPDATE users SET balance = balance - ? WHERE id = ?", (amount, user_id)
    )
    await db.execute(
        "INSERT INTO exchanges (user_id, amount, steam_link, timestamp) VALUES (?, ?, ?, ?)",
        (user_id, amount, steam_link, int(time.time())),
    )
    await db.commit()
    return True
