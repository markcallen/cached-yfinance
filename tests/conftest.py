"""Test configuration and fixtures."""

import tempfile
from pathlib import Path
from typing import Generator
import pytest
import pandas as pd
from datetime import date, datetime

from cached_yfinance.cache import FileSystemCache


@pytest.fixture
def temp_cache_dir() -> Generator[Path, None, None]:
    """Create a temporary directory for cache testing."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield Path(temp_dir)


@pytest.fixture
def cache(temp_cache_dir: Path) -> FileSystemCache:
    """Create a FileSystemCache instance with temporary directory."""
    return FileSystemCache(temp_cache_dir)


@pytest.fixture
def sample_dataframe() -> pd.DataFrame:
    """Create a sample DataFrame for testing."""
    dates = pd.date_range('2023-01-01', periods=5, freq='D')
    return pd.DataFrame({
        'Open': [100.0, 101.0, 102.0, 103.0, 104.0],
        'High': [105.0, 106.0, 107.0, 108.0, 109.0],
        'Low': [95.0, 96.0, 97.0, 98.0, 99.0],
        'Close': [102.0, 103.0, 104.0, 105.0, 106.0],
        'Volume': [1000000, 1100000, 1200000, 1300000, 1400000]
    }, index=dates)


@pytest.fixture
def sample_option_dataframe() -> pd.DataFrame:
    """Create a sample option DataFrame for testing."""
    return pd.DataFrame({
        'contractSymbol': ['AAPL230120C00150000', 'AAPL230120C00155000'],
        'strike': [150.0, 155.0],
        'lastPrice': [5.25, 2.10],
        'bid': [5.20, 2.05],
        'ask': [5.30, 2.15],
        'volume': [100, 50],
        'openInterest': [500, 250],
        'impliedVolatility': [0.25, 0.28]
    })


@pytest.fixture
def sample_underlying_data() -> dict:
    """Create sample underlying data for option chains."""
    return {
        'regularMarketPrice': 152.75,
        'regularMarketTime': 1674240000,
        'currency': 'USD',
        'exchangeName': 'NMS'
    }
