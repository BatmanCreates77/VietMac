#!/bin/bash

# Auto-update MacBook Prices Script
# This script runs the price scraper and logs the results
# Can be called manually or scheduled via cron/launchd

# Set up paths
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
LOG_DIR="$SCRIPT_DIR/logs"
LOG_FILE="$LOG_DIR/auto-update-$(date +%Y%m%d).log"

# Create logs directory if it doesn't exist
mkdir -p "$LOG_DIR"

# Function to log with timestamp
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

log "========================================="
log "Starting automatic price update"
log "========================================="

# Change to scraper directory
cd "$SCRIPT_DIR" || exit 1

# Check if Python is available
if command -v python3 &> /dev/null; then
    PYTHON_CMD="python3"
elif command -v python &> /dev/null; then
    PYTHON_CMD="python"
else
    log "ERROR: Python not found!"
    exit 1
fi

log "Using Python: $PYTHON_CMD"

# Run the scraper
log "Running price scraper..."
$PYTHON_CMD update_prices.py >> "$LOG_FILE" 2>&1
EXIT_CODE=$?

if [ $EXIT_CODE -eq 0 ]; then
    log "✅ Price update completed successfully"

    # Check if latest_products.json was updated
    if [ -f "output/latest_products.json" ]; then
        PRODUCT_COUNT=$(grep -o '"total_products":[0-9]*' output/latest_products.json | grep -o '[0-9]*')
        log "📊 Total products scraped: $PRODUCT_COUNT"
    fi
else
    log "❌ Price update failed with exit code: $EXIT_CODE"
fi

log "========================================="
log "Update completed"
log "========================================="
echo ""

exit $EXIT_CODE
