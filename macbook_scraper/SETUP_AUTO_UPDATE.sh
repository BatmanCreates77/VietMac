#!/bin/bash

# Setup Script for Automatic Price Updates
# This script helps you set up automatic MacBook price updates

set -e

echo "========================================="
echo "VietMac Auto-Update Setup"
echo "========================================="
echo ""

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PLIST_FILE="$SCRIPT_DIR/com.vietmac.price-update.plist"
LAUNCH_AGENTS_DIR="$HOME/Library/LaunchAgents"
INSTALLED_PLIST="$LAUNCH_AGENTS_DIR/com.vietmac.price-update.plist"

# Function to display menu
show_menu() {
    echo "Choose an option:"
    echo ""
    echo "1) Install automatic updates (runs every 6 hours)"
    echo "2) Uninstall automatic updates"
    echo "3) Check status"
    echo "4) Run manual update now"
    echo "5) View recent logs"
    echo "6) Exit"
    echo ""
    read -p "Enter choice [1-6]: " choice
}

# Install launchd job
install_auto_update() {
    echo ""
    echo "📦 Installing automatic price updates..."

    # Create LaunchAgents directory if it doesn't exist
    mkdir -p "$LAUNCH_AGENTS_DIR"

    # Copy plist file
    cp "$PLIST_FILE" "$INSTALLED_PLIST"

    # Load the job
    launchctl load "$INSTALLED_PLIST" 2>/dev/null || true

    echo "✅ Automatic updates installed!"
    echo ""
    echo "Prices will update automatically every 6 hours at:"
    echo "  - 00:00 (midnight)"
    echo "  - 06:00 (6 AM)"
    echo "  - 12:00 (noon)"
    echo "  - 18:00 (6 PM)"
    echo ""
    echo "Logs will be saved to: $SCRIPT_DIR/logs/"
}

# Uninstall launchd job
uninstall_auto_update() {
    echo ""
    echo "🗑️  Uninstalling automatic price updates..."

    if [ -f "$INSTALLED_PLIST" ]; then
        launchctl unload "$INSTALLED_PLIST" 2>/dev/null || true
        rm "$INSTALLED_PLIST"
        echo "✅ Automatic updates uninstalled!"
    else
        echo "ℹ️  Automatic updates are not currently installed."
    fi
}

# Check status
check_status() {
    echo ""
    echo "📊 Checking status..."
    echo ""

    if [ -f "$INSTALLED_PLIST" ]; then
        echo "✅ Automatic updates are INSTALLED"
        echo ""

        # Check if loaded
        if launchctl list | grep -q "com.vietmac.price-update"; then
            echo "✅ Job is LOADED and ACTIVE"
        else
            echo "⚠️  Job is installed but not loaded"
            echo "   Try: launchctl load $INSTALLED_PLIST"
        fi

        # Show last update time
        if [ -f "$SCRIPT_DIR/output/latest_products.json" ]; then
            LAST_UPDATE=$(stat -f "%Sm" -t "%Y-%m-%d %H:%M:%S" "$SCRIPT_DIR/output/latest_products.json")
            echo ""
            echo "📅 Last update: $LAST_UPDATE"
        fi
    else
        echo "❌ Automatic updates are NOT installed"
        echo "   Run option 1 to install"
    fi
    echo ""
}

# Run manual update
run_manual_update() {
    echo ""
    echo "🚀 Running manual price update..."
    echo ""
    "$SCRIPT_DIR/auto-update-prices.sh"
}

# View logs
view_logs() {
    echo ""
    echo "📜 Recent logs:"
    echo "========================================="

    LOG_DIR="$SCRIPT_DIR/logs"
    if [ -d "$LOG_DIR" ]; then
        LATEST_LOG=$(ls -t "$LOG_DIR"/auto-update-*.log 2>/dev/null | head -1)
        if [ -n "$LATEST_LOG" ]; then
            tail -50 "$LATEST_LOG"
        else
            echo "No logs found yet."
        fi
    else
        echo "No logs directory found."
    fi
    echo "========================================="
}

# Main loop
while true; do
    show_menu

    case $choice in
        1)
            install_auto_update
            ;;
        2)
            uninstall_auto_update
            ;;
        3)
            check_status
            ;;
        4)
            run_manual_update
            ;;
        5)
            view_logs
            ;;
        6)
            echo "Goodbye!"
            exit 0
            ;;
        *)
            echo "Invalid option. Please try again."
            ;;
    esac

    echo ""
    read -p "Press Enter to continue..."
    clear
done
