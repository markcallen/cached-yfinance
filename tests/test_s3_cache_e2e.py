from __future__ import annotations

import socket
import subprocess
import time
import uuid
from collections.abc import Generator
from datetime import date
from os import environ
from typing import Any

import pandas as pd
import pytest

from cached_yfinance import CacheKey, OptionCacheKey, S3Cache


LOCALSTACK_IMAGE = environ.get("LOCALSTACK_IMAGE", "localstack/localstack:3.8")


def _free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def _docker_available() -> bool:
    try:
        result = subprocess.run(
            ["docker", "info"],
            check=False,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=10,
        )
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False
    return result.returncode == 0


@pytest.fixture(scope="session")
def localstack_s3_endpoint() -> Generator[str, None, None]:
    configured_endpoint = environ.get("LOCALSTACK_S3_ENDPOINT")
    if configured_endpoint:
        yield _wait_for_s3(configured_endpoint)
        return

    if not _docker_available():
        pytest.skip("Docker is required for LocalStack S3 e2e tests")

    port = _free_port()
    container_name = f"cached-yfinance-localstack-{uuid.uuid4().hex}"
    run_command = [
        "docker",
        "run",
        "--rm",
        "--detach",
        "--name",
        container_name,
        "--publish",
        f"127.0.0.1:{port}:4566",
        "--env",
        "SERVICES=s3",
        "--env",
        "AWS_ACCESS_KEY_ID=test",
        "--env",
        "AWS_SECRET_ACCESS_KEY=test",
        "--env",
        "AWS_DEFAULT_REGION=us-east-1",
        LOCALSTACK_IMAGE,
    ]
    result = subprocess.run(
        run_command,
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        timeout=60,
    )
    if result.returncode != 0:
        pytest.skip(f"Could not start LocalStack: {result.stderr.strip()}")

    endpoint_url = f"http://127.0.0.1:{port}"
    try:
        yield _wait_for_s3(endpoint_url)
    finally:
        subprocess.run(
            ["docker", "rm", "--force", container_name],
            check=False,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=20,
        )


def _s3_client(endpoint_url: str) -> Any:
    boto3 = pytest.importorskip("boto3")
    return boto3.client(
        "s3",
        endpoint_url=endpoint_url,
        region_name="us-east-1",
        aws_access_key_id="test",
        aws_secret_access_key="test",
    )


def _wait_for_s3(endpoint_url: str) -> str:
    client = _s3_client(endpoint_url)
    deadline = time.monotonic() + 60
    last_error: Exception | None = None
    while time.monotonic() < deadline:
        try:
            client.list_buckets()
            return endpoint_url
        except Exception as exc:  # pragma: no cover - diagnostic only
            last_error = exc
            time.sleep(1)
    pytest.fail(f"LocalStack S3 did not become ready: {last_error}")


def test_s3_e2e_localstack_market_data_and_options_round_trip(
    localstack_s3_endpoint: str,
) -> None:
    bucket = f"cached-yfinance-e2e-{uuid.uuid4().hex}"
    s3 = _s3_client(localstack_s3_endpoint)
    s3.create_bucket(Bucket=bucket)
    cache = S3Cache(bucket, prefix="yfinance", s3_client=s3)

    market_key = CacheKey(symbol="IWM", interval="1d", day=date(2026, 8, 27))
    market_frame = pd.DataFrame(
        {"Close": [223.5], "Volume": [123456]},
        index=pd.to_datetime(["2026-08-27"]),
    )
    cache.store(market_key, market_frame)

    assert cache.has(market_key)
    loaded_market_frame = cache.load(market_key)
    assert loaded_market_frame is not None
    pd.testing.assert_frame_equal(loaded_market_frame, market_frame)
    assert list(cache.iter_cached_days("IWM", "1d")) == [date(2026, 8, 27)]

    expiration = "2026-09-18"
    timestamp = "2026-08-27T14:30:00+00:00"
    calls = pd.DataFrame({"strike": [220.0, 225.0], "lastPrice": [6.1, 3.8]})
    puts = pd.DataFrame({"strike": [220.0, 225.0], "lastPrice": [2.4, 4.9]})
    underlying = {"regularMarketPrice": 223.5, "currency": "USD"}

    cache.store_option_chain(
        "IWM",
        expiration,
        calls,
        puts,
        underlying,
        timestamp=timestamp,
    )

    calls_key = OptionCacheKey.for_calls("IWM", expiration, timestamp)
    puts_key = OptionCacheKey.for_puts("IWM", expiration, timestamp)
    underlying_key = OptionCacheKey.for_underlying("IWM", expiration, timestamp)

    pd.testing.assert_frame_equal(cache.load_option_chain(calls_key), calls)
    pd.testing.assert_frame_equal(cache.load_option_chain(puts_key), puts)
    assert cache.load_option_chain(underlying_key) == underlying
    assert list(cache.iter_cached_option_expirations("IWM")) == [expiration]
    assert list(cache.iter_cached_option_timestamps("IWM", expiration)) == [
        "2026-08-27T14:30:00"
    ]

    objects = s3.list_objects_v2(Bucket=bucket, Prefix="yfinance/IWM/")
    object_keys = {item["Key"] for item in objects["Contents"]}
    assert "yfinance/IWM/1d/2026/08/2026-08-27-1d.parquet" in object_keys
    assert (
        "yfinance/IWM/options/2026-09-18/historical/2026-08-27/"
        "metadata_143000.json" in object_keys
    )
