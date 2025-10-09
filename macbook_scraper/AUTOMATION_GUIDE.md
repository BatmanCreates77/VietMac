# Automated Price Updates - Complete Guide

This guide explains how to automatically update MacBook prices from Vietnamese retailers.

---

## 🎯 Quick Start

### 1. Test the Update Script

```bash
cd /Users/gaurav/Documents/VietMac/macbook_scraper
python3 update_prices.py
```

This will:
- ✅ Scrape CellphoneS (~40 products)
- ✅ Scrape ShopDunk (~44 products)
- 💾 Save to `output/latest_products.json`
- 🔄 Next.js API automatically reads this file

### 2. Setup Automated Updates (macOS/Linux)

```bash
chmod +x setup_cron.sh
./setup_cron.sh
```

Follow the prompts to schedule automatic updates.

---

## 📋 How It Works

### Data Flow

```
┌─────────────────────┐
│  Scrapers Run       │  CellphoneS + ShopDunk
│  (Python)           │  ~2 minutes total
└──────┬──────────────┘
       │
       ▼
┌─────────────────────┐
│ update_prices.py    │  Orchestrates scraping
└──────┬──────────────┘
       │
       ▼
┌─────────────────────┐
│ latest_products.json│  Saved to output/
│                     │  {timestamp, products[]}
└──────┬──────────────┘
       │
       ▼
┌─────────────────────┐
│ Next.js API         │  Reads JSON file
│ /api/macbook-prices │  Serves to frontend
└──────┬──────────────┘
       │
       ▼
┌─────────────────────┐
│ User's Browser      │  Live prices displayed
└─────────────────────┘
```

### File Structure

```
macbook_scraper/
├── update_prices.py           # Main automation script
├── monitor_prices.py          # Price change monitoring
├── setup_cron.sh              # Auto-setup scheduling
├── cron_update.sh             # Generated cron wrapper
├── scrapers/
│   ├── cellphones_scraper.py  # Working ✅
│   ├── shopdunk_scraper.py    # Working ✅
│   ├── fptshop_scraper.py     # Blocked ⚠️
│   └── topzone_scraper.py     # Timeout ⚠️
├── output/
│   ├── latest_products.json   # Used by Next.js API
│   ├── products_*.json        # Timestamped backups
│   ├── price_history.json     # Price tracking
│   └── price_alerts.json      # Change alerts
└── logs/
    └── update_YYYYMMDD.log    # Daily logs
```

---

## ⚙️ Scheduling Options

### Option 1: Cron (macOS/Linux) - Recommended

**Setup:**
```bash
./setup_cron.sh
```

**Manual Setup:**
```bash
crontab -e
```

Add one of these lines:

```bash
# Daily at 2 AM (recommended)
0 2 * * * /path/to/macbook_scraper/cron_update.sh

# Every 6 hours
0 */6 * * * /path/to/macbook_scraper/cron_update.sh

# Twice daily (2 AM and 8 PM)
0 2,20 * * * /path/to/macbook_scraper/cron_update.sh
```

**View scheduled jobs:**
```bash
crontab -l
```

**View logs:**
```bash
tail -f macbook_scraper/logs/update_$(date +%Y%m%d).log
```

---

### Option 2: Systemd (Linux Only)

For Linux servers with systemd:

```bash
cd macbook_scraper/systemd

# Edit service files with correct paths
nano macbook-price-update.service

# Install
sudo cp *.service *.timer /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable macbook-price-update.timer
sudo systemctl start macbook-price-update.timer

# Check status
sudo systemctl status macbook-price-update.timer
```

See `systemd/README.md` for details.

---

### Option 3: GitHub Actions (Cloud)

Create `.github/workflows/update-prices.yml`:

```yaml
name: Update MacBook Prices

on:
  schedule:
    - cron: '0 2 * * *'  # Daily at 2 AM UTC
  workflow_dispatch:  # Manual trigger

jobs:
  update:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: |
          cd macbook_scraper
          pip install -r requirements.txt
          playwright install chromium
      
      - name: Update prices
        run: |
          cd macbook_scraper
          python3 update_prices.py
      
      - name: Commit and push
        run: |
          git config --global user.name 'Price Bot'
          git config --global user.email 'bot@example.com'
          git add macbook_scraper/output/latest_products.json
          git commit -m "🤖 Update prices $(date)" || exit 0
          git push
```

**Pros:**
- ✅ No server needed
- ✅ Free (GitHub Actions)
- ✅ Reliable

**Cons:**
- ⚠️ Slower (cold start)
- ⚠️ 2000 minutes/month limit

---

## 📊 Monitoring & Alerts

### Track Price Changes

```bash
python3 monitor_prices.py
```

This will:
- Compare current prices with history
- Detect price drops and increases
- Save alerts to `output/price_alerts.json`
- Print summary to console

### Add to Cron

```bash
# Update prices then check for changes
0 2 * * * /path/to/macbook_scraper/cron_update.sh && /usr/bin/python3 /path/to/macbook_scraper/monitor_prices.py
```

### Email Alerts (Optional)

Configure SMTP settings and use:

```bash
python3 monitor_prices.py --email your@email.com
```

---

## 🔧 Advanced Configuration

### Include All Shops (Even Blocked Ones)

```bash
python3 update_prices.py --all
```

⚠️ Warning: FPTShop and TopZone usually fail due to blocking/timeouts.

### Quiet Mode (For Cron)

```bash
python3 update_prices.py --quiet
```

Only errors will be printed.

### Custom Schedule

Edit `cron_update.sh` or your cron entry.

---

## 🎯 Integration with Next.js

The Next.js API automatically reads the latest prices:

**File:** `app/api/[[...path]]/route.js`

```javascript
function loadScrapedData() {
  const filePath = join(
    process.cwd(),
    "macbook_scraper",
    "output",
    "latest_products.json"
  );
  const data = JSON.parse(readFileSync(filePath, "utf-8"));
  return data.products || [];
}
```

**No code changes needed!** Just run the scraper and the API picks it up.

---

## 📈 Production Deployment

### Vercel Deployment

1. **Add build command:**

```json
// package.json
{
  "scripts": {
    "build": "python3 macbook_scraper/update_prices.py && next build"
  }
}
```

2. **Add dependencies:**

```json
// package.json
{
  "dependencies": {
    "playwright": "^1.49.1"
  }
}
```

3. **Vercel Cron:**

Create `vercel.json`:

```json
{
  "crons": [{
    "path": "/api/update-prices",
    "schedule": "0 2 * * *"
  }]
}
```

Create API endpoint `app/api/update-prices/route.js`:

```javascript
import { exec } from 'child_process';
import { promisify } from 'util';

const execAsync = promisify(exec);

export async function GET(request) {
  try {
    const { stdout, stderr } = await execAsync(
      'cd macbook_scraper && python3 update_prices.py'
    );
    return NextResponse.json({ success: true, output: stdout });
  } catch (error) {
    return NextResponse.json({ success: false, error: error.message }, { status: 500 });
  }
}
```

---

### Railway/Render Deployment

Similar to Vercel, but use their native cron:

**Railway:**
```yaml
# railway.toml
[build]
builder = "nixpacks"

[deploy]
startCommand = "npm start"

[[crons]]
schedule = "0 2 * * *"
command = "cd macbook_scraper && python3 update_prices.py"
```

**Render:**
Add cron job in dashboard → New Cron Job

---

## 🐛 Troubleshooting

### Scrapers Fail

**Check logs:**
```bash
tail -f logs/update_$(date +%Y%m%d).log
```

**Common issues:**

1. **Playwright not installed:**
```bash
playwright install chromium
```

2. **Dependencies missing:**
```bash
pip install -r requirements.txt
```

3. **Permission denied:**
```bash
chmod +x update_prices.py
chmod +x cron_update.sh
```

### Cron Job Not Running

**Check if cron is running:**
```bash
ps aux | grep cron
```

**Check cron logs:**
```bash
# macOS
tail -f /var/log/system.log | grep cron

# Linux
tail -f /var/log/syslog | grep CRON
```

**Test cron script manually:**
```bash
./cron_update.sh
```

### Data Not Updating

**Verify file exists:**
```bash
ls -lh output/latest_products.json
```

**Check file contents:**
```bash
head output/latest_products.json
```

**Verify timestamp:**
```bash
jq '.timestamp' output/latest_products.json
```

---

## 📊 Monitoring Dashboard

### Check Update Status

```bash
# View last update time
jq '.timestamp' output/latest_products.json

# Count products
jq '.products | length' output/latest_products.json

# View summary
jq '.summary' output/latest_products.json
```

### Price History

```bash
# View price changes
cat output/price_alerts.json | jq '.price_drops'

# Count drops in last run
cat output/price_alerts.json | jq '.price_drops | length'
```

---

## 🚀 Recommended Setup

**For Development:**
```bash
# Manual updates when needed
python3 update_prices.py
```

**For Production:**
```bash
# Setup cron for daily updates
./setup_cron.sh

# Add price monitoring
crontab -e
# Add: 0 2 * * * /path/to/cron_update.sh && python3 /path/to/monitor_prices.py
```

**For Cloud Hosting:**
- Use GitHub Actions or Vercel Cron
- No server maintenance needed
- Free tier sufficient

---

## 📞 Support

**View logs:**
```bash
tail -f logs/update_$(date +%Y%m%d).log
```

**Test scrapers individually:**
```bash
python3 scrapers/cellphones_scraper.py
python3 scrapers/shopdunk_scraper.py
```

**Check dependencies:**
```bash
pip list | grep -E "playwright|beautifulsoup|requests"
```

---

## ✅ Success Checklist

- [ ] `update_prices.py` runs successfully
- [ ] `output/latest_products.json` is created
- [ ] Products count > 0 (should be ~80+)
- [ ] Timestamp is recent
- [ ] Next.js API returns prices
- [ ] Cron job is scheduled (if using)
- [ ] Logs are being created
- [ ] Price monitoring works (optional)

---

## 🎯 Quick Reference

```bash
# Run update
python3 update_prices.py

# Setup automation
./setup_cron.sh

# Check prices
python3 monitor_prices.py

# View logs
tail -f logs/update_$(date +%Y%m%d).log

# Check cron
crontab -l

# Test Next.js integration
curl http://localhost:3000/api/macbook-prices
```

---

**Questions?** Check the logs first, then review this guide.
