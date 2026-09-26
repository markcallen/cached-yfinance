# S3 cache backend

`S3Cache` stores the same Parquet market data and JSON metadata as `FileSystemCache`, but writes objects to AWS S3 or an S3-compatible service such as DigitalOcean Spaces.

## Install

```bash
pip install 'cached-yfinance[s3]'
```

## AWS S3

```python
from cached_yfinance import CachedYFClient, S3Cache

cache = S3Cache(
    bucket="market-data",
    prefix="yfinance",
    region_name="us-east-1",
)
client = CachedYFClient(cache)
```

Authentication uses boto3's normal credential chain, including environment variables, shared AWS configuration, and workload credentials.

## DigitalOcean Spaces

```python
from cached_yfinance import CachedYFClient, S3Cache

cache = S3Cache(
    bucket="market-data",
    prefix="yfinance",
    endpoint_url="https://tor1.digitaloceanspaces.com",
    region_name="tor1",
)
client = CachedYFClient(cache)
```

Set `AWS_ACCESS_KEY_ID` and `AWS_SECRET_ACCESS_KEY` to the DigitalOcean Spaces key and secret.

## Historical option chains

`CachedYFClient.get_option_chain()` automatically timestamps newly fetched chains. With `S3Cache`, a chain is written directly to object storage:

```text
yfinance/IWM/options/2026-09-18/historical/2026-08-27/
├── calls_143000.parquet
├── puts_143000.parquet
└── metadata_143000.json
```

Fetch a fresh snapshot for each expiration with:

```python
client.get_option_chain("IWM", "2026-09-18", use_cache=False)
```

The timestamped objects remain available for later analysis through `iter_cached_option_timestamps()` and `get_option_chain(..., timestamp=...)`.

## Automated one-minute price collection

`tools/ticker_collector.py` accepts the same S3 settings as the options
collector. This configuration writes daily one-minute IWM price objects below
`yfinance/IWM/1m/YYYY/MM/`:

```json
{
  "tickers": ["IWM"],
  "interval": "1m",
  "s3_bucket": "market-data",
  "s3_prefix": "yfinance",
  "s3_region": "us-east-1"
}
```

Run it with:

```bash
python tools/ticker_collector.py --config ticker_collector_config.json
```

For `1m` data, each execution requests `period="1d"` from Yahoo Finance and
replaces the current day's object. Schedule it during market hours to keep the
intraday session current; older daily objects remain unchanged.
