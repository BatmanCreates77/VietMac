# 🤖 Automated Price Update System - Complete

## ✅ What Was Built

A complete automated system to keep MacBook prices updated from Vietnamese retailers.

---

## 📦 New Files Created

### Core Scripts
1. **`macbook_scraper/update_prices.py`** ⭐
   - Main automation script
   - Runs CellphoneS + ShopDunk scrapers
   - Saves to `output/latest_products.json`
   - Used by Next.js API

2. **`macbook_scraper/monitor_prices.py`**
   - Tracks price changes
   - Detects price drops/increases
   - Generates alerts

3. **`macbook_scraper/setup_cron.sh`**
   - One-click cron setup
   - Creates log directories
   - Generates wrapper script

4. **`macbook_scraper/cron_update.sh`** (auto-generated)
   - Wrapper for cron jobs
   - Handles logging
   - Cleans old logs

### Documentation
5. **`macbook_scraper/AUTOMATION_GUIDE.md`**
   - Complete setup guide
   - All scheduling options
   - Troubleshooting tips

6. **`macbook_scraper/UPDATED_SCRAPER_REPORT.md`**
   - Scraper update summary
   - Test results
   - Coverage analysis

7. **`PRICE_AUTOMATION_SUMMARY.md`** (this file)
   - Quick reference
   - What to do next

### Systemd (Linux)
8. **`macbook_scraper/systemd/` directory**
   - Service files
   - Timer configuration
   - Setup instructions

---

## 🚀 How to Use

### Quick Start (Run Once)

```bash
cd /Users/gaurav/Documents/VietMac/macbook_scraper
python3 update_prices.py
```

**Result:** `output/latest_products.json` updated with ~80 MacBooks

---

### Setup Automation (Daily Updates)

#### Option 1: Auto-Setup (Easiest)

```bash
cd /Users/gaurav/Documents/VietMac/macbook_scraper
./setup_cron.sh
```

Follow the prompts!

#### Option 2: Manual Cron

```bash
crontab -e
```

Add this line for daily 2 AM updates:
```
0 2 * * * /Users/gaurav/Documents/VietMac/macbook_scraper/cron_update.sh
```

#### Option 3: GitHub Actions (Cloud)

See `macbook_scraper/AUTOMATION_GUIDE.md` for GitHub Actions setup.

---

## 📊 What Gets Updated

### Data Flow

```
┌──────────────┐
│  Scrapers    │  CellphoneS (40) + ShopDunk (44) = 84 products
│  Run Daily   │  Takes ~2 minutes
└──────┬───────┘
       │
       ▼
┌──────────────────────────┐
│ latest_products.json     │  Saved automatically
│ {                        │
│   "timestamp": "...",    │
│   "products": [...],     │
│   "summary": {...}       │
│ }                        │
└──────┬───────────────────┘
       │
       ▼
┌──────────────┐
│  Next.js API │  Reads JSON file
│  Auto-reload │  No restart needed!
└──────┬───────┘
       │
       ▼
┌──────────────┐
│   Website    │  Shows updated prices
└──────────────┘
```

### File Locations

**Prices:** `macbook_scraper/output/latest_products.json`  
**Logs:** `macbook_scraper/logs/update_YYYYMMDD.log`  
**History:** `macbook_scraper/output/price_history.json`  
**Alerts:** `macbook_scraper/output/price_alerts.json`

---

## 🎯 Recommended Schedule

### For Development
```bash
# Run manually when needed
python3 update_prices.py
```

### For Production
```bash
# Daily at 2 AM (quietest time, fresh prices for morning)
0 2 * * * /path/to/cron_update.sh
```

**Why 2 AM?**
- Low server load
- Vietnamese business hours: 8 AM-8 PM
- Prices updated overnight
- Fresh data by morning

---

## 📈 Monitoring

### Check Last Update

```bash
# View timestamp
cat macbook_scraper/output/latest_products.json | grep timestamp

# Count products
cat macbook_scraper/output/latest_products.json | grep -o '"shop"' | wc -l
```

### View Logs

```bash
# Today's log
tail -f macbook_scraper/logs/update_$(date +%Y%m%d).log

# Last update summary
tail -30 macbook_scraper/logs/update_$(date +%Y%m%d).log
```

### Price Changes

```bash
# Run monitoring
python3 macbook_scraper/monitor_prices.py

# View alerts
cat macbook_scraper/output/price_alerts.json
```

---

## ✅ Success Indicators

**Scraper is working if:**
- ✅ `latest_products.json` exists
- ✅ Timestamp is recent (< 24 hours)
- ✅ Products count ≥ 80
- ✅ Both shops present (cellphones + shopdunk)

**API is working if:**
- ✅ `http://localhost:3000/api/macbook-prices` returns data
- ✅ Website shows prices
- ✅ Currency conversion works

**Automation is working if:**
- ✅ Cron job listed: `crontab -l`
- ✅ New log files appear daily
- ✅ JSON file updates daily

---

## 🔍 Troubleshooting

### Scraper Fails

```bash
# Check dependencies
pip install -r macbook_scraper/requirements.txt
playwright install chromium

# Test scrapers individually
python3 macbook_scraper/scrapers/cellphones_scraper.py
python3 macbook_scraper/scrapers/shopdunk_scraper.py
```

### Cron Not Running

```bash
# Check if cron is scheduled
crontab -l

# Check cron logs (macOS)
tail -f /var/log/system.log | grep cron

# Test manually
/Users/gaurav/Documents/VietMac/macbook_scraper/cron_update.sh
```

### API Not Showing New Prices

```bash
# Verify file exists and is recent
ls -lh macbook_scraper/output/latest_products.json

# Restart Next.js dev server
npm run dev

# Check API directly
curl http://localhost:3000/api/macbook-prices | jq '.timestamp'
```

---

## 📚 Documentation

| File | Description |
|------|-------------|
| `AUTOMATION_GUIDE.md` | Complete setup guide |
| `UPDATED_SCRAPER_REPORT.md` | Scraper test results |
| `PRICE_AUTOMATION_SUMMARY.md` | This file - quick reference |
| `systemd/README.md` | Linux systemd setup |

---

## 🎯 Next Steps

### Immediate
1. ✅ Test the update script
2. ✅ Verify `latest_products.json` is created
3. ✅ Check Next.js API returns data

### Setup Automation
4. Run `./setup_cron.sh` to schedule updates
5. Wait 24 hours and verify log file appears
6. Check prices auto-update on website

### Optional Enhancements
7. Setup price monitoring for alerts
8. Configure email notifications
9. Add GitHub Actions for cloud updates
10. Setup Vercel/Railway cron jobs

---

## 🏆 What You Get

**Automatic Updates:**
- ✅ 80+ MacBooks from 2 major retailers
- ✅ 60-70% Vietnam market coverage
- ✅ Daily price updates
- ✅ No manual work needed

**Price Tracking:**
- ✅ Historical price data
- ✅ Price drop detection
- ✅ New product alerts
- ✅ Change percentage tracking

**Reliability:**
- ✅ Automatic retries
- ✅ Error logging
- ✅ Graceful failures
- ✅ Backup old data

**Zero Maintenance:**
- ✅ Set it and forget it
- ✅ Auto log rotation
- ✅ No server restarts needed
- ✅ API auto-reloads data

---

## 💡 Pro Tips

1. **Schedule for 2 AM** - Lowest load, fresh prices by morning
2. **Check logs weekly** - Catch issues early
3. **Monitor price_alerts.json** - Find best deals
4. **Keep 30 days of logs** - Troubleshooting history
5. **Use GitHub Actions** - No server needed

---

## 📞 Quick Commands

```bash
# Run update now
cd /Users/gaurav/Documents/VietMac/macbook_scraper && python3 update_prices.py

# Setup automation
./setup_cron.sh

# Check cron
crontab -l

# View today's log
tail -f logs/update_$(date +%Y%m%d).log

# Monitor prices
python3 monitor_prices.py

# Test API
curl http://localhost:3000/api/macbook-prices | jq '.summary'
```

---

## 🎉 Summary

You now have a **fully automated price tracking system** that:
- Scrapes 2 Vietnamese retailers daily
- Updates 80+ MacBook prices automatically
- Tracks price changes and alerts
- Requires zero maintenance
- Works seamlessly with your Next.js API

**Just run `./setup_cron.sh` and you're done!** ✨

---

**Questions?** Check `AUTOMATION_GUIDE.md` for detailed instructions.
