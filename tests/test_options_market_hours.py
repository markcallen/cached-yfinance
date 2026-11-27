"""Exchange-calendar behavior for scheduled options snapshots."""

from datetime import datetime
from zoneinfo import ZoneInfo

from tools.options_collector import is_market_open, is_scheduled_close


CONFIG = {
    "timezone": "America/New_York",
    "market_open": "09:30",
    "market_close": "16:00",
}
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


def test_configured_collection_window_is_intersected_with_exchange_session() -> None:
    restricted = {**CONFIG, "market_open": "10:00", "market_close": "15:00"}
    assert not is_market_open(restricted, at("2026-11-30", 9, 45))
    assert is_market_open(restricted, at("2026-11-30", 10))
    assert not is_market_open(restricted, at("2026-11-30", 15))
    assert not is_market_open(restricted, at("2026-11-27", 14))


def test_session_lookup_uses_new_york_date_for_other_configured_timezone() -> None:
    tokyo = ZoneInfo("Asia/Tokyo")
    config = {
        "timezone": "Asia/Tokyo",
        "market_open": "00:00",
        "market_close": "23:59",
    }
    assert is_market_open(config, datetime(2026, 12, 1, 5, 0, tzinfo=tokyo))
    assert is_scheduled_close(config, datetime(2026, 12, 1, 6, 2, tzinfo=tokyo))
