#!/usr/bin/env python3
"""
Daily 1-Minute Ticker Data Collector

This script is designed to run daily (typically after market close) to collect
1-minute historical data for a set of tickers. The data is automatically cached
to disk for faster subsequent access.

The script automatically:
- Downloads 1-minute data for specified tickers
- Handles errors gracefully and logs activity
- Supports configurable date ranges (default: last 7 days for 1-minute data)
- Automatically adjusts to 29 days max for 1-minute data (Yahoo Finance limit is <30 days)

Usage:
    python ticker_collector.py [--config CONFIG_FILE] [--cache-dir CACHE_DIR]

Cron example (daily at 5:00 PM EST after market close):
    0 17 * * 1-5 /usr/bin/python3 /path/to/ticker_collector.py --config /path/to/config.json

Configuration file format (JSON):
{
    "tickers": ["AAPL", "TSLA", "SPY", "QQQ"],
    "cache_dir": "/path/to/cache",
    "log_file": "/path/to/collector.log",
    "timezone": "America/New_York",
    "market_open": "09:30",
    "market_close": "16:00",
    "days": 7
}
"""

import argparse
import json
import logging
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Optional

import pandas as pd


# Add the parent directory to the path so we can import cached_yfinance
sys.path.insert(0, str(Path(__file__).parent.parent))

import cached_yfinance as cyf
from cached_yfinance import FileSystemCache


# Default configuration
DEFAULT_CONFIG = {
    "tickers": ["SPY", "QQQ", "IWM"],
    "cache_dir": None,  # Uses default ~/.cache/yfinance
    "log_file": None,  # Uses stdout
    "timezone": "America/New_York",
    "market_open": "09:30",
    "market_close": "16:00",
    "days": 7,  # Number of days to download (Yahoo Finance limits 1m data to <30 days)
    "interval": "1m",  # Data interval (1m, 5m, 15m, 30m, 1h, 1d, etc.)
}


def setup_logging(log_file: Optional[str] = None) -> logging.Logger:
    """Setup logging configuration."""
    logger = logging.getLogger("ticker_collector")
    logger.setLevel(logging.INFO)

    # Remove existing handlers
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)

    # Create formatter
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    # Add handler
    if log_file:
        handler = logging.FileHandler(log_file)
    else:
        handler = logging.StreamHandler(sys.stdout)

    handler.setFormatter(formatter)
    logger.addHandler(handler)

    return logger


def load_config(config_file: Optional[str] = None) -> Dict:
    """
    Load configuration from file or use defaults.

    Args:
        config_file: Path to JSON configuration file

    Returns:
        Configuration dictionary
    """
    config = DEFAULT_CONFIG.copy()

    if config_file and Path(config_file).exists():
        try:
            with open(config_file, "r") as f:
                file_config = json.load(f)
                config.update(file_config)
        except Exception as e:
            logging.warning(f"Error loading config file {config_file}: {e}")
            logging.info("Using default configuration")

    return config


def collect_1m_data(
    ticker: str,
    client: cyf.CachedYFClient,
    days: int,
    interval: str,
    logger: logging.Logger,
) -> Dict:
    """
    Collect ticker data for a single ticker.

    Args:
        ticker: Stock ticker symbol
        client: CachedYFClient instance
        days: Number of days to download
        interval: Data interval (1m, 5m, 15m, 30m, 1h, 1d, etc.)
        logger: Logger instance

    Returns:
        Dictionary with collection statistics
    """
    stats = {
        "ticker": ticker,
        "success": False,
        "data_points": 0,
        "date_range": None,
        "error": None,
    }

    try:
        # Validate days for 1-minute data (Yahoo Finance limits to <30 days)
        # Yahoo Finance requires start date to be strictly less than 30 days ago
        adjusted_days = days
        if interval == "1m" and adjusted_days >= 30:
            logger.warning(
                f"{ticker}: Yahoo Finance limits 1-minute data to less than 30 days. "
                f"Adjusting from {adjusted_days} to 29 days."
            )
            adjusted_days = 29

        # Calculate date range
        end_date = datetime.now()
        start_date = end_date - timedelta(days=adjusted_days)

        logger.info(
            f"{ticker}: Downloading {interval} data from {start_date.strftime('%Y-%m-%d')} "
            f"to {end_date.strftime('%Y-%m-%d')}"
        )

        # Download the data
        data = client.download(
            ticker.upper(),
            start=start_date,
            end=end_date,
            interval=interval,
            progress=False,
        )

        if data.empty:
            stats["error"] = "No data returned"
            logger.warning(f"{ticker}: No data found")
            return stats

        stats["success"] = True
        stats["data_points"] = len(data)
        stats["date_range"] = (
            f"{data.index[0].strftime('%Y-%m-%d %H:%M')} to "
            f"{data.index[-1].strftime('%Y-%m-%d %H:%M')}"
        )

        logger.info(
            f"{ticker}: Successfully collected {stats['data_points']:,} data points "
            f"({stats['date_range']})"
        )

    except Exception as e:
        stats["error"] = str(e)
        logger.error(f"Error collecting {interval} data for {ticker}: {e}")

    return stats


def main():
    """Main entry point for the daily 1-minute collector."""
    parser = argparse.ArgumentParser(
        description="Collect 1-minute ticker data daily",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Configuration file format (JSON):
{
    "tickers": ["AAPL", "TSLA", "SPY", "QQQ"],
    "cache_dir": "/path/to/cache",
    "log_file": "/path/to/collector.log",
    "timezone": "America/New_York",
    "market_open": "09:30",
    "market_close": "16:00",
    "days": 7
}

Cron example (daily at 5:00 PM EST after market close):
0 17 * * 1-5 /usr/bin/python3 /path/to/ticker_collector.py --config /path/to/config.json
        """,
    )

    parser.add_argument("--config", help="Path to JSON configuration file")

    parser.add_argument(
        "--cache-dir", help="Custom cache directory path (overrides config file)"
    )

    parser.add_argument(
        "--days",
        type=int,
        help="Number of days to download (overrides config file, default: 7)",
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be collected without actually downloading",
    )

    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s 1.0.0 (cached-yfinance {cyf.__version__})",
    )

    args = parser.parse_args()

    # Load configuration
    config = load_config(args.config)

    # Override cache directory if specified
    if args.cache_dir:
        config["cache_dir"] = args.cache_dir

    # Override days if specified
    if args.days:
        config["days"] = args.days

    # Setup logging
    logger = setup_logging(config.get("log_file"))

    # Log startup
    logger.info("=" * 60)
    logger.info("Daily 1-Minute Ticker Data Collector Starting")
    logger.info(f"Tickers: {config['tickers']}")
    logger.info(f"Cache directory: {config['cache_dir'] or '~/.cache/yfinance'}")
    logger.info(f"Days to download: {config['days']}")

    if args.dry_run:
        logger.info("DRY RUN - No data will be downloaded")
        for ticker in config["tickers"]:
            interval = config.get("interval", "1m")
            logger.info(
                f"Would collect {interval} data for {ticker} (last {config['days']} days)"
            )
        return

    # Initialize client
    try:
        if config["cache_dir"]:
            cache = FileSystemCache(config["cache_dir"])
            client = cyf.CachedYFClient(cache)
        else:
            client = cyf.CachedYFClient()
    except Exception as e:
        logger.error(f"Failed to initialize client: {e}")
        sys.exit(1)

    # Collect data for each ticker
    total_tickers = len(config["tickers"])
    total_data_points = 0
    successful_tickers = 0

    for i, ticker in enumerate(config["tickers"], 1):
        logger.info(f"[{i}/{total_tickers}] Processing {ticker}...")

        stats = collect_1m_data(
            ticker, client, config["days"], config.get("interval", "1m"), logger
        )

        if stats["success"]:
            successful_tickers += 1
            total_data_points += stats["data_points"]
        else:
            logger.error(f"{ticker}: {stats['error']}")

    # Summary
    logger.info("-" * 40)
    logger.info("Collection Summary:")
    logger.info(f"  Successful tickers: {successful_tickers}/{total_tickers}")
    logger.info(f"  Total data points collected: {total_data_points:,}")
    logger.info(f"  Timestamp: {pd.Timestamp.now().isoformat()}")
    logger.info("Daily 1-Minute Ticker Data Collector Complete")
    logger.info("=" * 60)


if __name__ == "__main__":
    main()
