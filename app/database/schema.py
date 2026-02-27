from __future__ import annotations

import aiosqlite


async def init_db(db: aiosqlite.Connection) -> None:
    await db.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY,
            username TEXT,
            balance REAL DEFAULT 0,
            invited_by INTEGER,
            total_referrals INTEGER DEFAULT 0,
            total_referral_messages INTEGER DEFAULT 0
        )
        """
    )
    await db.execute(
        """
        CREATE TABLE IF NOT EXISTS referrals (
            inviter_id INTEGER NOT NULL,
            invited_id INTEGER NOT NULL,
            created_at INTEGER NOT NULL,
            PRIMARY KEY (inviter_id, invited_id)
        )
        """
    )
    await db.execute(
        """
        CREATE TABLE IF NOT EXISTS messages (
            user_id INTEGER PRIMARY KEY,
            last_message_time INTEGER NOT NULL,
            counted_messages INTEGER DEFAULT 0
        )
        """
    )
    await db.execute(
        """
        CREATE TABLE IF NOT EXISTS exchanges (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            amount REAL NOT NULL,
            steam_link TEXT NOT NULL,
            timestamp INTEGER NOT NULL
        )
        """
    )
    await db.execute(
        """
        CREATE TABLE IF NOT EXISTS invite_links (
            user_id INTEGER PRIMARY KEY,
            invite_link TEXT NOT NULL UNIQUE,
            created_at INTEGER NOT NULL
        )
        """
    )

    await db.execute(
        "CREATE INDEX IF NOT EXISTS idx_users_balance ON users(balance DESC)"
    )
    await db.execute(
        "CREATE INDEX IF NOT EXISTS idx_users_referrals ON users(total_referrals DESC)"
    )
    await db.execute(
        "CREATE INDEX IF NOT EXISTS idx_referrals_inviter ON referrals(inviter_id)"
    )
    await db.execute(
        "CREATE INDEX IF NOT EXISTS idx_exchanges_user ON exchanges(user_id)"
    )
    await db.execute(
        "CREATE INDEX IF NOT EXISTS idx_invite_links_link ON invite_links(invite_link)"
    )
    await db.commit()
