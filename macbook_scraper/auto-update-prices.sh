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
AUTOMATED_COMMIT_PREFIX="chore: automated price update"

# True when every local commit not on origin/main is one of this job's own
# price commits — i.e. a previous push failed and nothing else was done here.
only_automated_commits_unpushed() {
    local subjects
    subjects=$(git -C "$REPO_ROOT" log --format=%s origin/main..HEAD) || return 1
    [ -n "$subjects" ] || return 1
    ! printf '%s\n' "$subjects" | grep -qv "^$AUTOMATED_COMMIT_PREFIX"
}

# A push can report failure yet have landed (seen 2026-10-01 06:53: "cannot
# lock ref" after a slow push that GitHub had already applied), or fail
# because main moved (a PR merged mid-run). Check before declaring failure.
push_with_recovery() {
    git -C "$REPO_ROOT" push -q >> "$LOG_FILE" 2>&1 && return 0
    log "⚠️  push reported failure — checking GitHub..."
    git -C "$REPO_ROOT" fetch -q origin >> "$LOG_FILE" 2>&1 || return 1
    if git -C "$REPO_ROOT" merge-base --is-ancestor HEAD origin/main; then
        log "ℹ️  GitHub already has this commit — push did land"
        return 0
    fi
    log "main moved during the run — rebasing and retrying once..."
    if ! git -C "$REPO_ROOT" rebase -q origin/main >> "$LOG_FILE" 2>&1; then
        git -C "$REPO_ROOT" rebase --abort >> "$LOG_FILE" 2>&1
        return 1
    fi
    git -C "$REPO_ROOT" push -q >> "$LOG_FILE" 2>&1
}

log "Pulling latest main..."
if ! git -C "$REPO_ROOT" pull -q --ff-only >> "$LOG_FILE" 2>&1; then
    # An unpushed price commit from an earlier failed run would otherwise
    # block every future run here. Its data is about to be re-scraped
    # anyway, so it's safe to drop — but only if that's all it is.
    git -C "$REPO_ROOT" fetch -q origin >> "$LOG_FILE" 2>&1
    if only_automated_commits_unpushed && git -C "$REPO_ROOT" diff --quiet HEAD; then
        log "⚠️  Dropping unpushed automated price commit(s) and syncing to origin/main"
        git -C "$REPO_ROOT" reset -q --hard origin/main >> "$LOG_FILE" 2>&1
    else
        log "❌ git pull --ff-only failed — clone is diverged or dirty, not scraping"
        exit 1
    fi
fi

# Scrape every other day. launchd wakes this script twice a day (see the
# plist); it only scrapes once the last published data is MIN_AGE_HOURS
# old, so a missed or failed run is retried 12h later instead of 2 days
# later. Set VIETMAC_FORCE=1 to scrape now regardless.
MIN_AGE_HOURS=44
if [ "${VIETMAC_FORCE:-0}" != "1" ]; then
    AGE_HOURS=$($PYTHON_CMD -c '
import json, sys
from datetime import datetime
try:
    ts = json.load(open("output/latest_products.json"))["timestamp"]
    print(int((datetime.now() - datetime.fromisoformat(ts)).total_seconds() // 3600))
except Exception:
    print(-1)
')
    if [ "$AGE_HOURS" -ge 0 ] && [ "$AGE_HOURS" -lt "$MIN_AGE_HOURS" ]; then
        log "⏭️  Last scrape was ${AGE_HOURS}h ago (< ${MIN_AGE_HOURS}h) — skipping this run"
        exit 0
    fi
    if [ "$AGE_HOURS" -ge 0 ]; then
        log "Last scrape was ${AGE_HOURS}h ago — scraping"
    else
        log "No readable previous scrape — scraping"
    fi
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
    # india_prices.json (Indian prices for comparison) is published
    # alongside; `git status` rather than `git diff` so the file's first,
    # still-untracked version is picked up too.
    PRICE_FILES=()
    for f in macbook_scraper/output/latest_products.json macbook_scraper/output/india_prices.json; do
        [ -f "$REPO_ROOT/$f" ] && PRICE_FILES+=("$f")
    done
    if [ -z "$(git -C "$REPO_ROOT" status --porcelain -- "${PRICE_FILES[@]}")" ]; then
        log "ℹ️  No change to the price files — nothing to commit"
    else
        log "Committing updated prices..."
        if git -C "$REPO_ROOT" add -- "${PRICE_FILES[@]}" \
            && git -C "$REPO_ROOT" commit -q -m "$AUTOMATED_COMMIT_PREFIX $(date '+%Y-%m-%d %H:%M')" \
            && push_with_recovery; then
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
