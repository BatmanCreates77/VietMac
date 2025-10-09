# 🔄 Automatic Price Updates - Quick Start

Your MacBook price scraper can now update automatically! No manual scraping needed during sales.

## 🚀 Quickest Setup (Choose One)

### For Production (Vercel) - Recommended ✨
1. Deploy to Vercel: `vercel` or connect GitHub repo
2. Done! Prices update every 6 hours automatically
3. (Optional) Add `CRON_SECRET` env var for security

### For Local Development (macOS)
```bash
cd macbook_scraper
./SETUP_AUTO_UPDATE.sh
# Choose option 1 - Install
```

Prices will update every 6 hours at: 00:00, 06:00, 12:00, 18:00

---

## 📅 Update Schedule

**Default**: Every 6 hours (4 times per day)

**During sales** (recommended):
- Change to every 2-4 hours to catch flash deals
- Edit `vercel.json` or launchd config

---

## 🎯 Three Ways to Update Prices

### 1. Automatic (Vercel Cron)
✅ Already configured in `vercel.json`
- Runs every 6 hours when deployed
- No maintenance needed

### 2. Automatic (macOS)
```bash
./macbook_scraper/SETUP_AUTO_UPDATE.sh
```
- Option 1: Install auto-updates
- Option 3: Check status
- Option 4: Run manual update

### 3. Manual API Call
```bash
# Local
curl http://localhost:3001/api/scrape

# Production  
curl https://your-site.vercel.app/api/scrape
```

---

## 📊 Check Status

**See last update time:**
```bash
stat macbook_scraper/output/latest_products.json
```

**View logs:**
```bash
tail -f macbook_scraper/logs/auto-update-$(date +%Y%m%d).log
```

**Check if running:**
```bash
launchctl list | grep vietmac
```

---

## 🛠️ Common Tasks

### Run Update Now (Manual)
```bash
cd macbook_scraper
./auto-update-prices.sh
```

### Stop Auto Updates
```bash
./SETUP_AUTO_UPDATE.sh
# Choose option 2 - Uninstall
```

### Change Update Frequency
Edit `vercel.json`:
```json
{
  "crons": [{
    "path": "/api/scrape",
    "schedule": "0 */2 * * *"  ← Change this (every 2 hours)
  }]
}
```

---

## 📚 Full Documentation

See `macbook_scraper/AUTO_UPDATE_GUIDE.md` for:
- Detailed setup instructions
- Troubleshooting guide
- Advanced configuration
- Monitoring tips

---

## ✅ Quick Test

Test that everything works:
```bash
cd macbook_scraper
./auto-update-prices.sh
```

You should see:
- ✅ Scraper starts
- ✅ Products scraped from shops
- ✅ "Update completed successfully"
- ✅ `output/latest_products.json` updated

---

## 🔔 Tips

- **Monitor logs** during first few runs
- **Increase frequency** before major sales
- **Set CRON_SECRET** in production for security
- **Check every few days** to ensure it's working

Need help? Check `macbook_scraper/AUTO_UPDATE_GUIDE.md` 📖
