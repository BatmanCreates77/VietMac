# Automatic Price Updates Guide

This guide explains how to set up automatic price updates so your MacBook prices are always fresh, especially during sales and promotions.

## 🎯 Overview

You have **three options** for automatic updates:

1. **Vercel Cron** (Recommended for production) - Automatic when deployed
2. **Local macOS Automation** - For development/testing on your Mac
3. **API Endpoint** - Manual trigger or custom scheduling

---

## Option 1: Vercel Cron (Production - Recommended)

### What is it?
When you deploy to Vercel, prices automatically update every 6 hours without you doing anything!

### Setup (Already Done! ✅)
The `vercel.json` file is already configured to run price updates automatically:
- **Schedule**: Every 6 hours (00:00, 06:00, 12:00, 18:00 UTC)
- **No setup needed** - Just deploy to Vercel

### How to Deploy:
```bash
# Install Vercel CLI (one time)
npm i -g vercel

# Deploy
vercel

# Or connect your GitHub repo to Vercel dashboard
# Visit: https://vercel.com/new
```

### Security (Important!)
Add this environment variable in Vercel dashboard:
```
CRON_SECRET=your-random-secret-key-here
```
Generate a random key: `openssl rand -base64 32`

---

## Option 2: Local macOS Automation (Development)

### Quick Start
Run the setup wizard:
```bash
cd macbook_scraper
./SETUP_AUTO_UPDATE.sh
```

Choose option 1 to install automatic updates.

### What it does:
- ✅ Updates prices every 6 hours automatically
- ✅ Runs at: 00:00, 06:00, 12:00, 18:00 (local time)
- ✅ Logs all updates to `macbook_scraper/logs/`
- ✅ Runs in background (even if you close terminal)

### Manual Commands:

**Install auto-updates:**
```bash
cp macbook_scraper/com.vietmac.price-update.plist ~/Library/LaunchAgents/
launchctl load ~/Library/LaunchAgents/com.vietmac.price-update.plist
```

**Check status:**
```bash
launchctl list | grep vietmac
```

**Uninstall:**
```bash
launchctl unload ~/Library/LaunchAgents/com.vietmac.price-update.plist
rm ~/Library/LaunchAgents/com.vietmac.price-update.plist
```

**View logs:**
```bash
tail -f macbook_scraper/logs/auto-update-$(date +%Y%m%d).log
```

---

## Option 3: API Endpoint (Manual/Custom)

### Trigger Price Update Manually
You can trigger a price update anytime by calling:

```bash
# Local development
curl http://localhost:3001/api/scrape

# Production (with auth)
curl -H "Authorization: Bearer YOUR_CRON_SECRET" \
     https://your-domain.vercel.app/api/scrape
```

### Response:
```json
{
  "success": true,
  "message": "Price scraper completed successfully",
  "timestamp": "2025-01-10T12:00:00.000Z",
  "duration": "45.2s",
  "summary": {
    "total_products": 60,
    "by_shop": {
      "shopdunk": { "count": 44, "success": true },
      "cellphones": { "count": 16, "success": true }
    }
  }
}
```

### Use Cases:
- Manual price updates before sales
- Custom scheduling (hourly, daily, etc.)
- Triggered by other services (Zapier, IFTTT, etc.)

---

## 🔔 Update Schedule Recommendations

### During Normal Times:
- **Every 6 hours** (default) - Good balance

### During Sales Events:
- **Every 2-4 hours** - Catch flash sales

To change frequency:

**Vercel** - Edit `vercel.json`:
```json
{
  "crons": [{
    "path": "/api/scrape",
    "schedule": "0 */2 * * *"  // Every 2 hours
  }]
}
```

**macOS launchd** - Edit `com.vietmac.price-update.plist` and add more time intervals

---

## 📊 Monitoring

### Check Last Update:
```bash
cd macbook_scraper
stat output/latest_products.json
```

### View Update History:
```bash
ls -lh output/products_*.json
```

### Recent Logs:
```bash
tail -50 logs/auto-update-$(date +%Y%m%d).log
```

### Product Count:
```bash
grep -o '"total_products":[0-9]*' output/latest_products.json
```

---

## 🐛 Troubleshooting

### Updates not running?

**Check if installed:**
```bash
launchctl list | grep vietmac
```

**Check logs:**
```bash
cat macbook_scraper/logs/launchd-stderr.log
```

**Manually test scraper:**
```bash
cd macbook_scraper
./auto-update-prices.sh
```

### Python errors?
Make sure dependencies are installed:
```bash
cd macbook_scraper
pip3 install -r requirements.txt
```

### Playwright/Browser issues?
Install Playwright browsers:
```bash
python3 -m playwright install chromium
```

---

## 📝 Files Overview

| File | Purpose |
|------|---------|
| `vercel.json` | Vercel Cron configuration |
| `auto-update-prices.sh` | Main update script |
| `com.vietmac.price-update.plist` | macOS scheduler config |
| `SETUP_AUTO_UPDATE.sh` | Interactive setup wizard |
| `app/api/scrape/route.js` | API endpoint for updates |
| `update_prices.py` | Python scraper script |
| `output/latest_products.json` | Latest scraped prices |
| `logs/` | Update logs directory |

---

## 🚀 Quick Test

Run a manual update to verify everything works:

```bash
cd macbook_scraper
./auto-update-prices.sh
```

You should see:
- ✅ Scraper running
- ✅ Products being scraped
- ✅ Success message
- ✅ Updated `output/latest_products.json`

---

## 💡 Tips

1. **Check logs regularly** to ensure updates are working
2. **Increase frequency during sales** (Black Friday, Tết, etc.)
3. **Monitor for errors** - Some shops may block scrapers occasionally
4. **Keep Python dependencies updated**: `pip3 install -U -r requirements.txt`
5. **Set up CRON_SECRET** for production security

---

## Need Help?

- Check logs first: `macbook_scraper/logs/`
- Test manually: `./auto-update-prices.sh`
- Check status: `./SETUP_AUTO_UPDATE.sh` (option 3)
- Review API: `http://localhost:3001/api/scrape`

Happy price tracking! 🎉
