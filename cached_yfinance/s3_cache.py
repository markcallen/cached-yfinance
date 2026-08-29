from __future__ import annotations

import io
import json
from datetime import date, datetime
from typing import Any, Iterable, Optional

import pandas as pd

from .cache import CacheKey, FileSystemCache, OptionCacheKey, _sanitize_symbol


class S3Cache(FileSystemCache):
    """Persist cached yfinance data in S3-compatible object storage.

    Works with AWS S3 and compatible services such as DigitalOcean Spaces.
    The object layout mirrors :class:`FileSystemCache` so market history and
    timestamped option chains remain easy to inspect and query externally.
    """

    def __init__(
        self,
        bucket: str,
        prefix: str = "",
        *,
        endpoint_url: Optional[str] = None,
        region_name: Optional[str] = None,
        s3_client: Any = None,
    ) -> None:
        super().__init__()
        self.bucket = bucket
        self.prefix = prefix.strip("/")
        if s3_client is None:
            try:
                import boto3  # type: ignore[import-untyped]
            except ModuleNotFoundError as exc:  # pragma: no cover
                raise ModuleNotFoundError(
                    "S3Cache requires boto3. Install cached-yfinance[s3]."
                ) from exc
            s3_client = boto3.client(
                "s3", endpoint_url=endpoint_url, region_name=region_name
            )
        self.s3 = s3_client

    def _key(self, *parts: str) -> str:
        pieces = [self.prefix] if self.prefix else []
        pieces.extend(part.strip("/") for part in parts if part)
        return "/".join(pieces)

    def _base_key(self, symbol: str, interval: str, day: date) -> str:
        return self._key(
            _sanitize_symbol(symbol), interval, f"{day.year:04d}", f"{day.month:02d}"
        )

    def _data_key(self, symbol: str, interval: str, day: date) -> str:
        return (
            f"{self._base_key(symbol, interval, day)}/"
            f"{day:%Y-%m-%d}-{interval}.parquet"
        )

    def _meta_key(self, symbol: str, interval: str, day: date) -> str:
        return (
            f"{self._base_key(symbol, interval, day)}/"
            f"{day:%Y-%m-%d}-{interval}.json"
        )

    def _option_base_key(
        self, symbol: str, expiration_date: str, timestamp: Optional[str] = None
    ) -> str:
        sym = _sanitize_symbol(symbol)
        if timestamp:
            ts = pd.Timestamp(timestamp)
            return self._key(
                sym,
                "options",
                expiration_date,
                "historical",
                ts.strftime("%Y-%m-%d"),
            )
        return self._key(sym, "options", expiration_date)

    def _option_data_key(
        self,
        symbol: str,
        expiration_date: str,
        data_type: str,
        timestamp: Optional[str] = None,
    ) -> str:
        base = self._option_base_key(symbol, expiration_date, timestamp)
        if timestamp:
            ts = pd.Timestamp(timestamp)
            return f"{base}/{data_type}_{ts:%H%M%S}.parquet"
        return f"{base}/{data_type}.parquet"

    def _option_meta_key(
        self, symbol: str, expiration_date: str, timestamp: Optional[str] = None
    ) -> str:
        base = self._option_base_key(symbol, expiration_date, timestamp)
        if timestamp:
            ts = pd.Timestamp(timestamp)
            return f"{base}/metadata_{ts:%H%M%S}.json"
        return f"{base}/metadata.json"

    def _exists(self, key: str) -> bool:
        try:
            self.s3.head_object(Bucket=self.bucket, Key=key)
            return True
        except Exception as exc:
            response = getattr(exc, "response", {})
            status = response.get("ResponseMetadata", {}).get("HTTPStatusCode")
            code = response.get("Error", {}).get("Code")
            if code in {"404", "NoSuchKey", "NotFound"} or (
                status == 404 and code is None
            ):
                return False
            raise

    def _get_bytes(self, key: str) -> bytes:
        response = self.s3.get_object(Bucket=self.bucket, Key=key)
        return response["Body"].read()

    def _put_bytes(self, key: str, value: bytes, content_type: str) -> None:
        self.s3.put_object(
            Bucket=self.bucket,
            Key=key,
            Body=value,
            ContentType=content_type,
        )

    def _list_keys(self, prefix: str) -> Iterable[str]:
        continuation_token: Optional[str] = None
        while True:
            kwargs: dict[str, Any] = {"Bucket": self.bucket, "Prefix": prefix}
            if continuation_token:
                kwargs["ContinuationToken"] = continuation_token
            response = self.s3.list_objects_v2(**kwargs)
            for item in response.get("Contents", []):
                yield item["Key"]
            if not response.get("IsTruncated"):
                break
            continuation_token = response.get("NextContinuationToken")

    def has(self, key: CacheKey) -> bool:
        return self._exists(self._data_key(key.symbol, key.interval, key.day))

    def load(self, key: CacheKey) -> Optional[pd.DataFrame]:
        object_key = self._data_key(key.symbol, key.interval, key.day)
        if not self._exists(object_key):
            return None
        return pd.read_parquet(io.BytesIO(self._get_bytes(object_key)))

    def store(self, key: CacheKey, frame: pd.DataFrame) -> None:
        if frame.empty:
            return
        buffer = io.BytesIO()
        frame.to_parquet(buffer)
        self._put_bytes(
            self._data_key(key.symbol, key.interval, key.day),
            buffer.getvalue(),
            "application/vnd.apache.parquet",
        )
        meta = {
            "symbol": key.symbol,
            "interval": key.interval,
            "day": key.day.isoformat(),
            "rows": int(len(frame)),
            "columns": list(frame.columns),
        }
        self._put_bytes(
            self._meta_key(key.symbol, key.interval, key.day),
            json.dumps(meta, indent=2).encode("utf-8"),
            "application/json",
        )

    def has_option_chain(self, key: OptionCacheKey) -> bool:
        if key.data_type in ("calls", "puts"):
            return self._exists(
                self._option_data_key(
                    key.symbol, key.expiration_date, key.data_type, key.timestamp
                )
            )
        if key.data_type == "underlying":
            return self._exists(
                self._option_meta_key(key.symbol, key.expiration_date, key.timestamp)
            )
        return False

    def load_option_chain(
        self, key: OptionCacheKey
    ) -> Optional[pd.DataFrame | dict[str, Any]]:
        if key.data_type in ("calls", "puts"):
            object_key = self._option_data_key(
                key.symbol, key.expiration_date, key.data_type, key.timestamp
            )
            if not self._exists(object_key):
                return None
            return pd.read_parquet(io.BytesIO(self._get_bytes(object_key)))
        if key.data_type == "underlying":
            object_key = self._option_meta_key(
                key.symbol, key.expiration_date, key.timestamp
            )
            if not self._exists(object_key):
                return None
            data = json.loads(self._get_bytes(object_key).decode("utf-8"))
            return data.get("underlying")
        return None

    def store_option_chain(
        self,
        symbol: str,
        expiration_date: str,
        calls: pd.DataFrame,
        puts: pd.DataFrame,
        underlying: dict[str, Any],
        timestamp: Optional[str] = None,
    ) -> None:
        for data_type, frame in (("calls", calls), ("puts", puts)):
            if frame.empty:
                continue
            buffer = io.BytesIO()
            frame.to_parquet(buffer)
            self._put_bytes(
                self._option_data_key(symbol, expiration_date, data_type, timestamp),
                buffer.getvalue(),
                "application/vnd.apache.parquet",
            )

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
        self._put_bytes(
            self._option_meta_key(symbol, expiration_date, timestamp),
            json.dumps(meta, indent=2).encode("utf-8"),
            "application/json",
        )

    def iter_cached_days(self, symbol: str, interval: str) -> Iterable[date]:
        prefix = self._key(_sanitize_symbol(symbol), interval) + "/"
        seen: set[date] = set()
        for key in self._list_keys(prefix):
            if not key.endswith(f"-{interval}.parquet"):
                continue
            filename = key.rsplit("/", 1)[-1]
            try:
                cached_day = datetime.strptime(filename[:10], "%Y-%m-%d").date()
            except ValueError:
                continue
            if cached_day not in seen:
                seen.add(cached_day)
        return iter(sorted(seen))

    def iter_cached_option_expirations(self, symbol: str) -> Iterable[str]:
        prefix = self._key(_sanitize_symbol(symbol), "options") + "/"
        expirations: set[str] = set()
        for key in self._list_keys(prefix):
            remainder = key[len(prefix) :]
            expiration = remainder.split("/", 1)[0]
            try:
                datetime.strptime(expiration, "%Y-%m-%d")
            except ValueError:
                continue
            expirations.add(expiration)
        return iter(sorted(expirations))

    def iter_cached_option_timestamps(
        self, symbol: str, expiration_date: str
    ) -> Iterable[str]:
        prefix = (
            self._key(
                _sanitize_symbol(symbol), "options", expiration_date, "historical"
            )
            + "/"
        )
        timestamps: list[str] = []
        for key in self._list_keys(prefix):
            filename = key.rsplit("/", 1)[-1]
            if not filename.startswith("metadata_") or not filename.endswith(".json"):
                continue
            date_part = key.split("/")[-2]
            time_part = filename.removeprefix("metadata_").removesuffix(".json")
            try:
                ts = pd.Timestamp(
                    f"{date_part}T{time_part[:2]}:{time_part[2:4]}:{time_part[4:6]}"
                )
            except Exception:
                continue
            timestamps.append(ts.isoformat())
        return iter(sorted(timestamps))
