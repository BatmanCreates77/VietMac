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

# Sync with origin before scraping. This job runs in a dedicated clone, so
# without this it would scrape with stale code and push on top of a stale
# base (rejected as non-fast-forward). --ff-only refuses to run on a
# diverged or dirty clone rather than guessing how to reconcile it.
REPO_ROOT="$( cd "$SCRIPT_DIR/.." && pwd )"
log "Pulling latest main..."
if ! git -C "$REPO_ROOT" pull --ff-only >> "$LOG_FILE" 2>&1; then
    log "❌ git pull --ff-only failed — clone is diverged or dirty, not scraping"
    exit 1
fi

# Run the scraper
log "Running price scraper..."
$PYTHON_CMD update_prices.py >> "$LOG_FILE" 2>&1
EXIT_CODE=$?

if [ $EXIT_CODE -eq 0 ]; then
    log "✅ Price update completed successfully"

    # Check if latest_products.json was updated
    if [ -f "output/latest_products.json" ]; then
        PRODUCT_COUNT=$(grep -o '"total_products":[[:space:]]*[0-9]*' output/latest_products.json | grep -o '[0-9]*')
        log "📊 Total products scraped: $PRODUCT_COUNT"
    fi

    # Commit and push the new data so the live site picks it up on the
    # next Vercel deploy. update_prices.py's validation gate already
    # rejected this run (non-zero exit, caught above) if the data looked
    # bad, so a successful exit here means latest_products.json genuinely
    # changed to something validated — safe to publish.
    if git -C "$REPO_ROOT" diff --quiet -- macbook_scraper/output/latest_products.json; then
        log "ℹ️  No change to latest_products.json — nothing to commit"
    else
        log "Committing updated prices..."
        if git -C "$REPO_ROOT" add macbook_scraper/output/latest_products.json \
            && git -C "$REPO_ROOT" commit -m "chore: automated price update $(date '+%Y-%m-%d %H:%M')" \
            && git -C "$REPO_ROOT" push; then
            log "✅ Committed and pushed updated prices"
        else
            log "❌ git commit/push failed — new prices are on disk but NOT live"
            EXIT_CODE=1
        fi
    fi
else
    log "❌ Price update failed with exit code: $EXIT_CODE"
fi

log "========================================="
log "Update completed"
log "========================================="
echo ""

exit $EXIT_CODE
