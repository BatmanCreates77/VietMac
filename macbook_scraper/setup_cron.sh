#!/bin/bash
# Setup automated price updates with cron

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
PYTHON_PATH=$(which python3)

echo "🔧 Setting up automated price updates..."
echo "Script directory: $SCRIPT_DIR"
echo "Python: $PYTHON_PATH"
echo ""

# Create log directory
LOG_DIR="$SCRIPT_DIR/logs"
mkdir -p "$LOG_DIR"
echo "✅ Created log directory: $LOG_DIR"

# Create wrapper script for cron
WRAPPER_SCRIPT="$SCRIPT_DIR/cron_update.sh"
cat > "$WRAPPER_SCRIPT" << 'EOF'
#!/bin/bash
# Wrapper script for cron job

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_DIR="$SCRIPT_DIR/logs"
PYTHON_PATH=PYTHON_PATH_PLACEHOLDER

# Create dated log file
LOG_FILE="$LOG_DIR/update_$(date +\%Y\%m\%d).log"

# Add timestamp to log
echo "====================================" >> "$LOG_FILE"
echo "Update started: $(date)" >> "$LOG_FILE"
echo "====================================" >> "$LOG_FILE"

# Run the update script
cd "$SCRIPT_DIR"
$PYTHON_PATH update_prices.py >> "$LOG_FILE" 2>&1
EXIT_CODE=$?

# Log completion
echo "Update finished: $(date)" >> "$LOG_FILE"
echo "Exit code: $EXIT_CODE" >> "$LOG_FILE"
echo "" >> "$LOG_FILE"

# Clean up old logs (keep last 30 days)
find "$LOG_DIR" -name "update_*.log" -type f -mtime +30 -delete

exit $EXIT_CODE
EOF

# Replace placeholder with actual Python path
sed -i.bak "s|PYTHON_PATH_PLACEHOLDER|$PYTHON_PATH|g" "$WRAPPER_SCRIPT"
rm -f "${WRAPPER_SCRIPT}.bak"

chmod +x "$WRAPPER_SCRIPT"
echo "✅ Created cron wrapper script: $WRAPPER_SCRIPT"

# Display cron job suggestions
echo ""
echo "📋 CRON JOB SETUP"
echo "=================================="
echo ""
echo "To schedule automatic price updates, add one of these to your crontab:"
echo ""
echo "1. Daily at 2 AM (recommended):"
echo "   0 2 * * * $WRAPPER_SCRIPT"
echo ""
echo "2. Every 6 hours:"
echo "   0 */6 * * * $WRAPPER_SCRIPT"
echo ""
echo "3. Every 12 hours (2 AM and 2 PM):"
echo "   0 2,14 * * * $WRAPPER_SCRIPT"
echo ""
echo "4. Twice daily (2 AM and 8 PM):"
echo "   0 2,20 * * * $WRAPPER_SCRIPT"
echo ""
echo "To add to crontab:"
echo "  1. Run: crontab -e"
echo "  2. Add one of the lines above"
echo "  3. Save and exit"
echo ""
echo "To view logs:"
echo "  tail -f $LOG_DIR/update_$(date +%Y%m%d).log"
echo ""

# Test the script
echo "🧪 Testing the update script..."
echo ""
read -p "Run a test update now? (y/n) " -n 1 -r
echo ""
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "Running test update..."
    "$WRAPPER_SCRIPT"
    echo ""
    echo "✅ Test complete! Check the log: $LOG_DIR/update_$(date +%Y%m%d).log"
fi

echo ""
echo "✅ Setup complete!"
echo ""
