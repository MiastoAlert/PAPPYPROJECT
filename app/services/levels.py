from __future__ import annotations


def get_level(total_referrals: int) -> dict[str, object]:
    if total_referrals < 10:
        return _level(
            "🟢 Новичок",
            next_threshold=10,
            current=total_referrals,
        )
    if total_referrals < 20:
        return _level(
            "🔵 Активный",
            next_threshold=20,
            current=total_referrals,
            base=10,
        )
    if total_referrals < 40:
        return _level(
            "🟣 Лидер",
            next_threshold=40,
            current=total_referrals,
            base=20,
        )
    return {
        "name": "🔴 Легенда",
        "next_threshold": None,
        "progress_percent": 100,
    }


def _level(name: str, next_threshold: int, current: int, base: int = 0) -> dict[str, object]:
    span = max(next_threshold - base, 1)
    progress = int(((current - base) / span) * 100)
    progress = min(max(progress, 0), 100)
    return {
        "name": name,
        "next_threshold": next_threshold,
        "progress_percent": progress,
    }
