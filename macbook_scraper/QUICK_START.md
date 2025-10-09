# 🚀 Quick Start - Automated Price Updates

## ⚡ 30-Second Setup

### Step 1: Test It Works
```bash
cd /Users/gaurav/Documents/VietMac/macbook_scraper
python3 update_prices.py
```

**Expected:** See "✅ Update completed successfully!" after ~2 minutes

### Step 2: Automate It
```bash
./setup_cron.sh
```

**Done!** Prices update daily at 2 AM automatically.

---

## 📋 What Just Happened?

1. **Scrapers ran:**
   - CellphoneS: ~40 MacBooks
   - ShopDunk: ~44 MacBooks
   - Total: ~80+ products

2. **File created:**
   - `output/latest_products.json`
   - Your Next.js API reads this automatically

3. **No code changes needed:**
   - API already configured
   - Website will show updated prices

---

## ✅ Verify It's Working

```bash
# Check file exists and is recent
ls -lh output/latest_products.json

# View product count
cat output/latest_products.json | grep -o '"shop"' | wc -l

# Check timestamp
cat output/latest_products.json | grep timestamp
```

**Should see:**
- File size: ~80-100 KB
- Product count: 80+
- Timestamp: Recent (today)

---

## 🔄 Daily Updates (Cron)

After running `./setup_cron.sh`, prices update automatically:

**When:** Daily at 2 AM  
**What:** Scrapes CellphoneS + ShopDunk  
**Where:** Updates `output/latest_products.json`  
**Logs:** Saved to `logs/update_YYYYMMDD.log`

---

## 📊 Check Status

```bash
# View cron schedule
crontab -l

# Check today's log
tail -f logs/update_$(date +%Y%m%d).log

# Monitor price changes
python3 monitor_prices.py
```

---

## 🎯 Common Tasks

### Run Update Manually
```bash
python3 update_prices.py
```

### View Latest Prices
```bash
cat output/latest_products.json | jq '.summary'
```

### Check Logs
```bash
tail -30 logs/update_$(date +%Y%m%d).log
```

### Test API
```bash
curl http://localhost:3000/api/macbook-prices | jq '.marketplaces.cellphones[0]'
```

---

## 🆘 Troubleshooting

### Script Fails
```bash
# Install dependencies
pip install -r requirements.txt
playwright install chromium

# Test scrapers individually
python3 scrapers/cellphones_scraper.py
```

### Cron Not Running
```bash
# Check cron is scheduled
crontab -l

# Run wrapper manually
./cron_update.sh
```

### Need Help?
Read: `AUTOMATION_GUIDE.md` for detailed instructions

---

## 🎉 You're Done!

✅ Prices update automatically  
✅ No maintenance needed  
✅ Website shows live prices  
✅ 80+ MacBooks tracked  

**Just check the logs weekly to make sure it's running smoothly.**

---

## 📚 More Info

- **Full Guide:** `AUTOMATION_GUIDE.md`
- **Technical Details:** `UPDATED_SCRAPER_REPORT.md`
- **Summary:** `PRICE_AUTOMATION_SUMMARY.md`
