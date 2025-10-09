# Systemd Service Setup (Linux Only)

For Linux servers, you can use systemd for more robust scheduling than cron.

## Installation

1. **Update the service file paths:**
   ```bash
   # Edit macbook-price-update.service
   # Replace:
   # - YOUR_USERNAME with your actual username
   # - /path/to/VietMac with actual path
   ```

2. **Copy service files:**
   ```bash
   sudo cp macbook-price-update.service /etc/systemd/system/
   sudo cp macbook-price-update.timer /etc/systemd/system/
   ```

3. **Reload systemd:**
   ```bash
   sudo systemctl daemon-reload
   ```

4. **Enable and start the timer:**
   ```bash
   sudo systemctl enable macbook-price-update.timer
   sudo systemctl start macbook-price-update.timer
   ```

## Management Commands

```bash
# Check timer status
sudo systemctl status macbook-price-update.timer

# Check last run
sudo systemctl status macbook-price-update.service

# View logs
sudo journalctl -u macbook-price-update.service -n 50

# Run manually
sudo systemctl start macbook-price-update.service

# Disable
sudo systemctl stop macbook-price-update.timer
sudo systemctl disable macbook-price-update.timer
```

## Schedule Options

Edit the `.timer` file to change schedule:

```ini
# Every 6 hours
OnCalendar=*-*-* 00/6:00:00

# Twice daily (2 AM and 8 PM)
OnCalendar=*-*-* 02:00:00
OnCalendar=*-*-* 20:00:00

# Every day at 2 AM (default)
OnCalendar=daily
OnCalendar=*-*-* 02:00:00
```

After changes, run:
```bash
sudo systemctl daemon-reload
sudo systemctl restart macbook-price-update.timer
```
