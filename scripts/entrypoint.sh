#!/bin/bash

if [ -z "$TICKER" ]; then
    echo "❌ Error: TICKER environment variable is required"
    exit 1
fi

echo "🐳 Starting download with:"
echo "   TICKER: $TICKER"
echo "   INTERVAL: $INTERVAL"
echo "   DAYS: $DAYS"
echo "   CACHE_DIR: $CACHE_DIR"
echo ""

python tools/download_data.py "$TICKER" --interval "$INTERVAL" --days "$DAYS" --cache-dir "$CACHE_DIR"
