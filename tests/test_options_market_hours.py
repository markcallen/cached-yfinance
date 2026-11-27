"""Exchange-calendar behavior for scheduled options snapshots."""

from datetime import datetime
from zoneinfo import ZoneInfo

from tools.options_collector import is_market_open, is_scheduled_close


CONFIG = {"timezone": "America/New_York"}
EASTERN = ZoneInfo("America/New_York")


def at(day: str, hour: int, minute: int = 0) -> datetime:
    return datetime.fromisoformat(day).replace(hour=hour, minute=minute, tzinfo=EASTERN)


def test_early_close_uses_exchange_schedule() -> None:
    assert is_market_open(CONFIG, at("2026-11-27", 12, 45))
    assert not is_market_open(CONFIG, at("2026-11-27", 13))
    assert is_scheduled_close(CONFIG, at("2026-11-27", 13, 2))
    assert not is_scheduled_close(CONFIG, at("2026-11-27", 13, 15))
    assert not is_scheduled_close(CONFIG, at("2026-11-27", 16))


def test_regular_close_and_holiday() -> None:
    assert is_market_open(CONFIG, at("2026-11-30", 15, 45))
    assert is_scheduled_close(CONFIG, at("2026-11-30", 16, 2))
    assert not is_scheduled_close(CONFIG, at("2026-11-30", 13))
    assert not is_market_open(CONFIG, at("2026-12-25", 12))
    assert not is_scheduled_close(CONFIG, at("2026-12-25", 16))
