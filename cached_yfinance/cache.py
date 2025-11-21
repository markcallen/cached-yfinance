from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Iterable, Optional

import pandas as pd


def _sanitize_symbol(symbol: str) -> str:
    return symbol.replace("/", "_").replace(" ", "_").upper()


def _ensure_datetime(value: datetime | pd.Timestamp) -> pd.Timestamp:
    if isinstance(value, pd.Timestamp):
        return value
    return pd.Timestamp(value)


@dataclass(frozen=True)
class CacheKey:
    symbol: str
    interval: str
    day: date

    @classmethod
    def from_timestamp(cls, symbol: str, interval: str, ts: datetime | pd.Timestamp) -> "CacheKey":
        ts = _ensure_datetime(ts)
        day = ts.tz_convert("UTC").date() if ts.tzinfo else ts.date()
        return cls(symbol=symbol, interval=interval, day=day)


@dataclass(frozen=True)
class OptionCacheKey:
    symbol: str
    expiration_date: str
    data_type: str  # 'calls', 'puts', or 'underlying'
    timestamp: Optional[str] = None  # ISO format timestamp for historical data

    @classmethod
    def for_calls(cls, symbol: str, expiration_date: str, timestamp: Optional[str] = None) -> "OptionCacheKey":
        return cls(symbol=symbol, expiration_date=expiration_date, data_type="calls", timestamp=timestamp)
    
    @classmethod
    def for_puts(cls, symbol: str, expiration_date: str, timestamp: Optional[str] = None) -> "OptionCacheKey":
        return cls(symbol=symbol, expiration_date=expiration_date, data_type="puts", timestamp=timestamp)
    
    @classmethod
    def for_underlying(cls, symbol: str, expiration_date: str, timestamp: Optional[str] = None) -> "OptionCacheKey":
        return cls(symbol=symbol, expiration_date=expiration_date, data_type="underlying", timestamp=timestamp)


class FileSystemCache:
    """
    Persist yfinance data on disk, bucketed by symbol/interval/YYYY/MM/day files.
    Each cache entry stores a single day's worth of data in parquet format alongside
    a lightweight metadata json file.
    """

    def __init__(self, root: str | Path | None = None) -> None:
        if root is None:
            root = Path.home() / ".cache" / "yfinance"
        self.root = Path(root).expanduser()

    def _base_dir(self, symbol: str, interval: str, day: date) -> Path:
        sym = _sanitize_symbol(symbol)
        return self.root / sym / interval / f"{day.year:04d}" / f"{day.month:02d}"

    def _data_path(self, symbol: str, interval: str, day: date) -> Path:
        return self._base_dir(symbol, interval, day) / f"{day:%Y-%m-%d}-{interval}.parquet"

    def _meta_path(self, symbol: str, interval: str, day: date) -> Path:
        return self._base_dir(symbol, interval, day) / f"{day:%Y-%m-%d}-{interval}.json"
    
    def _option_base_dir(self, symbol: str, expiration_date: str, timestamp: Optional[str] = None) -> Path:
        sym = _sanitize_symbol(symbol)
        if timestamp:
            # For timestamped data, organize by date then time
            ts = pd.Timestamp(timestamp)
            date_str = ts.strftime('%Y-%m-%d')
            return self.root / sym / "options" / expiration_date / "historical" / date_str
        else:
            # For current data (backward compatibility)
            return self.root / sym / "options" / expiration_date
    
    def _option_data_path(self, symbol: str, expiration_date: str, data_type: str, timestamp: Optional[str] = None) -> Path:
        base_dir = self._option_base_dir(symbol, expiration_date, timestamp)
        if timestamp:
            ts = pd.Timestamp(timestamp)
            time_str = ts.strftime('%H%M%S')
            return base_dir / f"{data_type}_{time_str}.parquet"
        else:
            return base_dir / f"{data_type}.parquet"
    
    def _option_meta_path(self, symbol: str, expiration_date: str, timestamp: Optional[str] = None) -> Path:
        base_dir = self._option_base_dir(symbol, expiration_date, timestamp)
        if timestamp:
            ts = pd.Timestamp(timestamp)
            time_str = ts.strftime('%H%M%S')
            return base_dir / f"metadata_{time_str}.json"
        else:
            return base_dir / "metadata.json"

    def has(self, key: CacheKey) -> bool:
        return self._data_path(key.symbol, key.interval, key.day).exists()

    def load(self, key: CacheKey) -> Optional[pd.DataFrame]:
        path = self._data_path(key.symbol, key.interval, key.day)
        if not path.exists():
            return None
        return pd.read_parquet(path)

    def store(self, key: CacheKey, frame: pd.DataFrame) -> None:
        if frame.empty:
            return
        base_dir = self._base_dir(key.symbol, key.interval, key.day)
        base_dir.mkdir(parents=True, exist_ok=True)
        path = self._data_path(key.symbol, key.interval, key.day)
        frame.to_parquet(path)
        meta = {
            "symbol": key.symbol,
            "interval": key.interval,
            "day": key.day.isoformat(),
            "rows": int(len(frame)),
            "columns": list(frame.columns),
        }
        with open(self._meta_path(key.symbol, key.interval, key.day), "w", encoding="utf-8") as f:
            json.dump(meta, f, indent=2)
    
    def has_option_chain(self, key: OptionCacheKey) -> bool:
        """Check if option chain data exists in cache."""
        if key.data_type in ("calls", "puts"):
            return self._option_data_path(key.symbol, key.expiration_date, key.data_type, key.timestamp).exists()
        elif key.data_type == "underlying":
            return self._option_meta_path(key.symbol, key.expiration_date, key.timestamp).exists()
        return False
    
    def load_option_chain(self, key: OptionCacheKey) -> Optional[pd.DataFrame | dict]:
        """Load option chain data from cache."""
        if key.data_type in ("calls", "puts"):
            path = self._option_data_path(key.symbol, key.expiration_date, key.data_type, key.timestamp)
            if not path.exists():
                return None
            return pd.read_parquet(path)
        elif key.data_type == "underlying":
            path = self._option_meta_path(key.symbol, key.expiration_date, key.timestamp)
            if not path.exists():
                return None
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return data.get("underlying")
        return None
    
    def store_option_chain(self, symbol: str, expiration_date: str, calls: pd.DataFrame, puts: pd.DataFrame, underlying: dict, timestamp: Optional[str] = None) -> None:
        """Store complete option chain data in cache."""
        base_dir = self._option_base_dir(symbol, expiration_date, timestamp)
        base_dir.mkdir(parents=True, exist_ok=True)
        
        # Store calls and puts DataFrames
        if not calls.empty:
            calls_path = self._option_data_path(symbol, expiration_date, "calls", timestamp)
            calls.to_parquet(calls_path)
        
        if not puts.empty:
            puts_path = self._option_data_path(symbol, expiration_date, "puts", timestamp)
            puts.to_parquet(puts_path)
        
        # Store metadata including underlying data
        cache_timestamp = timestamp if timestamp else pd.Timestamp.utcnow().isoformat()
        meta = {
            "symbol": symbol,
            "expiration_date": expiration_date,
            "cached_at": cache_timestamp,
            "calls_rows": int(len(calls)) if not calls.empty else 0,
            "puts_rows": int(len(puts)) if not puts.empty else 0,
            "calls_columns": list(calls.columns) if not calls.empty else [],
            "puts_columns": list(puts.columns) if not puts.empty else [],
            "underlying": underlying,
        }
        
        meta_path = self._option_meta_path(symbol, expiration_date, timestamp)
        with open(meta_path, "w", encoding="utf-8") as f:
            json.dump(meta, f, indent=2)

    def iter_cached_days(self, symbol: str, interval: str) -> Iterable[date]:
        sym_dir = self.root / _sanitize_symbol(symbol) / interval
        if not sym_dir.exists():
            return []
        for year_dir in sorted(sym_dir.glob("*")):
            if not year_dir.is_dir():
                continue
            for month_dir in sorted(year_dir.glob("*")):
                if not month_dir.is_dir():
                    continue
                for file in sorted(month_dir.glob("*-*.parquet")):
                    try:
                        day_part = file.stem.split("-")[0:3]
                        day = datetime.strptime("-".join(day_part), "%Y-%m-%d").date()
                        yield day
                    except Exception:
                        continue
    
    def iter_cached_option_expirations(self, symbol: str) -> Iterable[str]:
        """Iterate over cached option expiration dates for a symbol."""
        options_dir = self.root / _sanitize_symbol(symbol) / "options"
        if not options_dir.exists():
            return []
        for exp_dir in sorted(options_dir.glob("*")):
            if exp_dir.is_dir():
                yield exp_dir.name
    
    def iter_cached_option_timestamps(self, symbol: str, expiration_date: str) -> Iterable[str]:
        """Iterate over cached timestamps for a specific symbol and expiration."""
        historical_dir = self.root / _sanitize_symbol(symbol) / "options" / expiration_date / "historical"
        if not historical_dir.exists():
            return []
        
        timestamps = []
        for date_dir in sorted(historical_dir.glob("*")):
            if not date_dir.is_dir():
                continue
            for meta_file in sorted(date_dir.glob("metadata_*.json")):
                try:
                    # Extract timestamp from filename (metadata_HHMMSS.json)
                    time_part = meta_file.stem.split("_")[1]
                    date_part = date_dir.name
                    # Reconstruct full timestamp
                    timestamp_str = f"{date_part}T{time_part[:2]}:{time_part[2:4]}:{time_part[4:6]}"
                    timestamps.append(pd.Timestamp(timestamp_str).isoformat())
                except Exception:
                    continue
        
        return sorted(timestamps)


