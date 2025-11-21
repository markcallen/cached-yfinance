#!/bin/bash
#
# Setup script for market hours options data collection via cron
#
# This script helps set up automated options data collection every 15 minutes
# during market hours (9:30 AM - 4:00 PM EST, Monday-Friday).
#

set -e

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

# Default paths
PYTHON_PATH="${PYTHON_PATH:-$(which python3)}"
COLLECTOR_SCRIPT="$SCRIPT_DIR/market_hours_collector.py"
CONFIG_FILE="$SCRIPT_DIR/market_collector_config.json"
LOG_FILE="${LOG_FILE:-/tmp/market_collector.log}"

echo "🚀 Market Hours Options Collector - Cron Setup"
echo "=============================================="
echo
echo "Project directory: $PROJECT_DIR"
echo "Python path: $PYTHON_PATH"
echo "Collector script: $COLLECTOR_SCRIPT"
echo "Config file: $CONFIG_FILE"
echo "Log file: $LOG_FILE"
echo

# Check if Python exists
if ! command -v "$PYTHON_PATH" &> /dev/null; then
    echo "❌ Error: Python not found at $PYTHON_PATH"
    echo "   Please set PYTHON_PATH environment variable or install Python 3"
    exit 1
fi

# Check if collector script exists
if [[ ! -f "$COLLECTOR_SCRIPT" ]]; then
    echo "❌ Error: Collector script not found at $COLLECTOR_SCRIPT"
    exit 1
fi

# Check if config file exists
if [[ ! -f "$CONFIG_FILE" ]]; then
    echo "❌ Error: Config file not found at $CONFIG_FILE"
    echo "   Please create the configuration file first"
    exit 1
fi

# Test the collector script
echo "🧪 Testing collector script..."
if ! "$PYTHON_PATH" "$COLLECTOR_SCRIPT" --config "$CONFIG_FILE" --dry-run; then
    echo "❌ Error: Collector script test failed"
    echo "   Please check your Python environment and dependencies"
    exit 1
fi
echo "✅ Collector script test passed"
echo

# Generate cron entry
CRON_ENTRY="# Market Hours Options Data Collection (every 15 minutes, 9:30 AM - 4:00 PM EST, weekdays)
*/15 9-16 * * 1-5 $PYTHON_PATH $COLLECTOR_SCRIPT --config $CONFIG_FILE"

echo "📋 Suggested cron entry:"
echo "========================"
echo "$CRON_ENTRY"
echo

# Ask user if they want to install the cron job
read -p "❓ Would you like to install this cron job? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    # Backup existing crontab
    echo "💾 Backing up existing crontab..."
    crontab -l > "/tmp/crontab_backup_$(date +%Y%m%d_%H%M%S)" 2>/dev/null || true
    
    # Add the new cron job
    echo "📝 Installing cron job..."
    (crontab -l 2>/dev/null || true; echo; echo "$CRON_ENTRY") | crontab -
    
    echo "✅ Cron job installed successfully!"
    echo
    echo "📊 You can monitor the collection with:"
    echo "   tail -f $LOG_FILE"
    echo
    echo "🗑️  To remove the cron job later:"
    echo "   crontab -e"
    echo "   (then delete the lines containing 'market_hours_collector.py')"
else
    echo "⏭️  Cron job not installed. You can add it manually with:"
    echo "   crontab -e"
    echo "   Then add the lines shown above."
fi

echo
echo "🎯 Next steps:"
echo "1. Customize tickers in: $CONFIG_FILE"
echo "2. Monitor logs at: $LOG_FILE"
echo "3. Check collected data in your cache directory"
echo
echo "📚 For more information, see the tools README.md"
echo "🏁 Setup complete!"
