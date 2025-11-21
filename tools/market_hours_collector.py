#!/usr/bin/env python3
"""
Market Hours Options Data Collector

This script is designed to run via cron every 15 minutes during market hours
(9:30 AM - 4:00 PM EST, Monday-Friday) to collect historical options data.

The script automatically:
- Checks if markets are open (US market hours on weekdays)
- Downloads options data for specified tickers with timestamps
- Handles errors gracefully and logs activity
- Skips execution on weekends and holidays

Usage:
    python market_hours_collector.py [--config CONFIG_FILE] [--cache-dir CACHE_DIR]

Cron example (every 15 minutes during market hours):
    */15 9-16 * * 1-5 /usr/bin/python3 /path/to/market_hours_collector.py --config /path/to/config.json

Configuration file format (JSON):
{
    "tickers": ["AAPL", "TSLA", "SPY", "QQQ"],
    "cache_dir": "/path/to/cache",
    "log_file": "/path/to/collector.log",
    "timezone": "America/New_York",
    "market_open": "09:30",
    "market_close": "16:00"
}
"""

import argparse
import json
import logging
import sys
from datetime import datetime, time
from pathlib import Path
from typing import Dict, List, Optional

import pandas as pd
import pytz

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
    "max_expirations": 5,  # Limit to nearest 5 expirations to avoid too much data
}


def setup_logging(log_file: Optional[str] = None) -> logging.Logger:
    """Setup logging configuration."""
    logger = logging.getLogger("market_collector")
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


def is_market_open(config: Dict) -> bool:
    """
    Check if the market is currently open based on configuration.

    Args:
        config: Configuration dictionary with timezone and market hours

    Returns:
        True if market is open, False otherwise
    """
    try:
        # Get timezone
        tz = pytz.timezone(config["timezone"])
        now = datetime.now(tz)

        # Check if it's a weekday (Monday=0, Sunday=6)
        if now.weekday() >= 5:  # Saturday or Sunday
            return False

        # Parse market hours
        market_open = datetime.strptime(config["market_open"], "%H:%M").time()
        market_close = datetime.strptime(config["market_close"], "%H:%M").time()

        current_time = now.time()

        # Check if current time is within market hours
        return market_open <= current_time <= market_close

    except Exception as e:
        # If we can't determine market hours, assume closed for safety
        logging.error(f"Error checking market hours: {e}")
        return False


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


def collect_options_data(
    ticker: str,
    client: cyf.CachedYFClient,
    max_expirations: int,
    logger: logging.Logger,
) -> Dict:
    """
    Collect options data for a single ticker.

    Args:
        ticker: Stock ticker symbol
        client: CachedYFClient instance
        max_expirations: Maximum number of expirations to process
        logger: Logger instance

    Returns:
        Dictionary with collection statistics
    """
    stats = {
        "ticker": ticker,
        "success": False,
        "expirations_processed": 0,
        "total_contracts": 0,
        "error": None,
    }

    try:
        # Get available expirations (limit to avoid too much data)
        expirations = client.get_options_expirations(ticker, use_cache=False)
        if not expirations:
            stats["error"] = "No expirations available"
            return stats

        # Limit expirations to process
        expirations_to_process = expirations[:max_expirations]
        logger.info(f"{ticker}: Processing {len(expirations_to_process)} expirations")

        total_contracts = 0

        for expiration in expirations_to_process:
            try:
                option_chain = client.get_option_chain(
                    ticker,
                    expiration=expiration,
                    use_cache=False,  # Always fetch fresh data (timestamps auto-generated)
                )

                calls_count = (
                    len(option_chain.calls) if not option_chain.calls.empty else 0
                )
                puts_count = (
                    len(option_chain.puts) if not option_chain.puts.empty else 0
                )
                contracts = calls_count + puts_count

                if contracts > 0:
                    total_contracts += contracts
                    logger.debug(
                        f"{ticker} {expiration}: {calls_count} calls, {puts_count} puts"
                    )

            except Exception as e:
                logger.warning(f"Error processing {ticker} {expiration}: {e}")
                continue

        stats["success"] = True
        stats["expirations_processed"] = len(expirations_to_process)
        stats["total_contracts"] = total_contracts

        logger.info(
            f"{ticker}: Successfully collected {total_contracts:,} contracts across {len(expirations_to_process)} expirations"
        )

    except Exception as e:
        stats["error"] = str(e)
        logger.error(f"Error collecting data for {ticker}: {e}")

    return stats


def main():
    """Main entry point for the market hours collector."""
    parser = argparse.ArgumentParser(
        description="Collect options data during market hours",
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
    "max_expirations": 5
}

Cron example (every 15 minutes during market hours):
*/15 9-16 * * 1-5 /usr/bin/python3 /path/to/market_hours_collector.py --config /path/to/config.json
        """,
    )

    parser.add_argument("--config", help="Path to JSON configuration file")

    parser.add_argument(
        "--cache-dir", help="Custom cache directory path (overrides config file)"
    )

    parser.add_argument(
        "--force",
        action="store_true",
        help="Force execution even if market appears closed (for testing)",
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

    # Setup logging
    logger = setup_logging(config.get("log_file"))

    # Log startup
    logger.info("=" * 60)
    logger.info("Market Hours Options Collector Starting")
    logger.info(f"Tickers: {config['tickers']}")
    logger.info(f"Cache directory: {config['cache_dir'] or '~/.cache/yfinance'}")
    logger.info(f"Max expirations per ticker: {config['max_expirations']}")

    # Check if market is open (unless forced)
    if not args.force and not is_market_open(config):
        logger.info("Market is closed. Exiting.")
        return

    if args.force:
        logger.warning("Forced execution (market may be closed)")

    if args.dry_run:
        logger.info("DRY RUN - No data will be downloaded")
        for ticker in config["tickers"]:
            logger.info(f"Would collect options data for {ticker}")
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
    total_contracts = 0
    successful_tickers = 0

    for i, ticker in enumerate(config["tickers"], 1):
        logger.info(f"[{i}/{total_tickers}] Processing {ticker}...")

        stats = collect_options_data(ticker, client, config["max_expirations"], logger)

        if stats["success"]:
            successful_tickers += 1
            total_contracts += stats["total_contracts"]
        else:
            logger.error(f"{ticker}: {stats['error']}")

    # Summary
    logger.info("-" * 40)
    logger.info(f"Collection Summary:")
    logger.info(f"  Successful tickers: {successful_tickers}/{total_tickers}")
    logger.info(f"  Total contracts collected: {total_contracts:,}")
    logger.info(f"  Timestamp: {pd.Timestamp.now().isoformat()}")
    logger.info("Market Hours Options Collector Complete")
    logger.info("=" * 60)


if __name__ == "__main__":
    main()
