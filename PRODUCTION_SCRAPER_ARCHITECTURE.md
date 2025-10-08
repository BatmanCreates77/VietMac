# Production-Grade "Set It and Forget It" Scraper Architecture

## Goal
Build a fully automated, resilient scraper that runs daily and maintains 95%+ uptime without manual intervention.

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                   PRODUCTION SCRAPER SYSTEM                  │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────────┐      ┌──────────────┐      ┌───────────┐ │
│  │   Scheduler  │──────│   Scraper    │──────│  Database │ │
│  │   (Cron)     │      │   Manager    │      │ (MongoDB) │ │
│  └──────────────┘      └──────────────┘      └───────────┘ │
│                              │                               │
│                    ┌─────────┴─────────┐                    │
│                    │                   │                     │
│              ┌─────▼─────┐      ┌─────▼─────┐              │
│              │  Worker 1  │      │  Worker 2  │              │
│              │ CellphoneS │      │  ShopDunk  │              │
│              │  (Simple)  │      │(Playwright)│              │
│              └─────┬─────┘      └─────┬─────┘              │
│                    │                   │                     │
│              ┌─────▼─────┐      ┌─────▼─────┐              │
│              │  Worker 3  │      │  Worker 4  │              │
│              │  FPT Shop  │      │  TopZone   │              │
│              │(SeleniumUC)│      │(SeleniumUC)│              │
│              └─────┬─────┘      └─────┬─────┘              │
│                    │                   │                     │
│                    └───────┬───────────┘                     │
│                            │                                 │
│                     ┌──────▼──────┐                         │
│                     │   Monitor   │                         │
│                     │  & Alerts   │                         │
│                     └─────────────┘                         │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

---

## Component Design

### 1. Multi-Strategy Scraper Manager

Each shop gets the **best scraping strategy** based on its protection level:

| Shop | Strategy | Library | Reliability |
|------|----------|---------|-------------|
| **CellphoneS** | Simple HTTP | requests + BeautifulSoup | 99% |
| **ShopDunk** | Playwright | playwright-stealth | 85% |
| **FPT Shop** | SeleniumBase UC | undetected-chromedriver | 70% |
| **TopZone** | SeleniumBase UC + Proxy | UC + rotating proxies | 70% |

### 2. Retry & Fallback Logic

```
Attempt 1: Primary Strategy
  ↓ (if fails)
Attempt 2: Wait 5 min, retry with different User-Agent
  ↓ (if fails)
Attempt 3: Wait 15 min, retry with residential proxy
  ↓ (if fails)
Attempt 4: Wait 1 hour, retry with CAPTCHA solver
  ↓ (if all fail)
Alert admin + Use cached data from yesterday
```

### 3. Data Validation & Caching

- Validate scraped data (price ranges, model names)
- Compare with previous scrape (flag >20% price changes)
- Cache last 7 days of data
- If scrape fails, serve cached data (with timestamp)
- Never show empty data to users

### 4. Monitoring & Alerts

- Log every scrape attempt to MongoDB
- Track success rate per shop
- Alert if success rate drops below 80% for 3 consecutive days
- Daily email report with scraping stats
- Prometheus metrics + Grafana dashboard (optional)

---

## Implementation Plan

### Phase 1: Core Scraper Workers (Week 1)

#### Worker 1: CellphoneS (Simple)
```python
# cellphones_scraper.py
import requests
from bs4 import BeautifulSoup
import random
import time

class CellphonesScraper:
    def __init__(self):
        self.user_agents = [
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)...',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64)...',
            # 10+ user agents for rotation
        ]
    
    def scrape(self, retry=3):
        for attempt in range(retry):
            try:
                headers = {'User-Agent': random.choice(self.user_agents)}
                urls = [
                    'https://cellphones.com.vn/laptop/mac/macbook-pro.html',
                    'https://cellphones.com.vn/laptop/mac/macbook-air.html',
                ]
                
                all_products = []
                for url in urls:
                    response = requests.get(url, headers=headers, timeout=10)
                    soup = BeautifulSoup(response.content, 'html.parser')
                    products = self._parse_products(soup)
                    all_products.extend(products)
                    time.sleep(3)  # Polite delay
                
                return {'success': True, 'products': all_products, 'count': len(all_products)}
                
            except Exception as e:
                if attempt < retry - 1:
                    time.sleep(60 * (attempt + 1))  # Exponential backoff
                else:
                    return {'success': False, 'error': str(e)}
    
    def _parse_products(self, soup):
        # Extract product data
        products = []
        for item in soup.select('.product-info'):
            # Parse name, price, URL, etc.
            pass
        return products
```

#### Worker 2: ShopDunk (Playwright)
```python
# shopdunk_scraper.py
from playwright.sync_api import sync_playwright
from playwright_stealth import stealth_sync
import time

class ShopDunkScraper:
    def scrape(self, retry=3):
        for attempt in range(retry):
            try:
                with sync_playwright() as p:
                    browser = p.chromium.launch(headless=True)
                    context = browser.new_context(
                        user_agent='Mozilla/5.0...',
                        viewport={'width': 1920, 'height': 1080}
                    )
                    page = context.new_page()
                    stealth_sync(page)
                    
                    page.goto('https://shopdunk.com/macbook', 
                             wait_until='domcontentloaded', 
                             timeout=60000)
                    time.sleep(5)
                    
                    # Scroll to load all products
                    page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
                    time.sleep(3)
                    
                    content = page.content()
                    browser.close()
                    
                    products = self._parse_html(content)
                    return {'success': True, 'products': products}
                    
            except Exception as e:
                if attempt < retry - 1:
                    time.sleep(180 * (attempt + 1))
                else:
                    return {'success': False, 'error': str(e)}
    
    def _parse_html(self, html):
        # Parse with BeautifulSoup
        pass
```

#### Worker 3 & 4: FPT Shop + TopZone (SeleniumBase UC)
```python
# fptshop_scraper.py
from seleniumbase import Driver
import time
import random

class FPTShopScraper:
    def __init__(self):
        self.proxies = [
            # Optional: Add residential proxy list
            # 'http://user:pass@proxy1.com:8080',
        ]
    
    def scrape(self, retry=3, use_proxy=False):
        for attempt in range(retry):
            try:
                proxy = random.choice(self.proxies) if use_proxy and self.proxies else None
                
                driver = Driver(
                    uc=True,  # Undetected Chrome
                    headless=False,  # Headless has higher detection rate
                    # proxy=proxy,  # Uncomment if using proxies
                )
                
                driver.get('https://fptshop.com.vn/may-tinh-xach-tay/apple-macbook')
                
                # Wait for potential Cloudflare challenge
                time.sleep(10)
                
                # Check if we bypassed Cloudflare
                if '403' in driver.page_source or 'Cloudflare' in driver.title:
                    raise Exception('Cloudflare block detected')
                
                # Scroll to load products
                driver.execute_script('window.scrollTo(0, document.body.scrollHeight)')
                time.sleep(3)
                
                html = driver.page_source
                driver.quit()
                
                products = self._parse_html(html)
                return {'success': True, 'products': products}
                
            except Exception as e:
                if attempt < retry - 1:
                    # Try with proxy on second attempt
                    use_proxy = True
                    time.sleep(300 * (attempt + 1))  # 5 min, 10 min backoff
                else:
                    return {'success': False, 'error': str(e)}
```

### Phase 2: Scraper Manager & Orchestration

```python
# scraper_manager.py
import asyncio
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
import logging

from cellphones_scraper import CellphonesScraper
from shopdunk_scraper import ShopDunkScraper
from fptshop_scraper import FPTShopScraper
from topzone_scraper import TopZoneScraper
from database import MongoDB
from alerts import AlertManager

class ScraperManager:
    def __init__(self):
        self.scrapers = {
            'cellphones': CellphonesScraper(),
            'shopdunk': ShopDunkScraper(),
            'fptshop': FPTShopScraper(),
            'topzone': TopZoneScraper(),
        }
        self.db = MongoDB()
        self.alerts = AlertManager()
        self.logger = logging.getLogger(__name__)
    
    def run_all_scrapers(self):
        """Run all scrapers in parallel"""
        self.logger.info('Starting daily scrape run...')
        start_time = datetime.now()
        
        results = {}
        with ThreadPoolExecutor(max_workers=4) as executor:
            futures = {
                executor.submit(scraper.scrape): name 
                for name, scraper in self.scrapers.items()
            }
            
            for future in futures:
                shop_name = futures[future]
                try:
                    result = future.result(timeout=600)  # 10 min timeout per shop
                    results[shop_name] = result
                    
                    if result['success']:
                        self.logger.info(f"✅ {shop_name}: {result.get('count', 0)} products")
                        self._save_to_db(shop_name, result['products'])
                    else:
                        self.logger.error(f"❌ {shop_name}: {result['error']}")
                        self._handle_failure(shop_name, result['error'])
                        
                except Exception as e:
                    self.logger.error(f"❌ {shop_name} crashed: {str(e)}")
                    results[shop_name] = {'success': False, 'error': str(e)}
        
        # Generate report
        self._generate_report(results, start_time)
        
        # Check if we need to alert
        self._check_and_alert(results)
        
        return results
    
    def _save_to_db(self, shop_name, products):
        """Save scraped products to MongoDB"""
        self.db.save_products(shop_name, products, timestamp=datetime.now())
    
    def _handle_failure(self, shop_name, error):
        """Use cached data when scrape fails"""
        cached = self.db.get_cached_products(shop_name, max_age_days=7)
        if cached:
            self.logger.warning(f"Using cached data for {shop_name} (age: {cached['age']} days)")
        else:
            self.logger.critical(f"No cached data available for {shop_name}!")
            self.alerts.send_critical(f"{shop_name} scrape failed with no cache")
    
    def _generate_report(self, results, start_time):
        """Generate daily scraping report"""
        duration = (datetime.now() - start_time).total_seconds()
        success_count = sum(1 for r in results.values() if r['success'])
        total_products = sum(r.get('count', 0) for r in results.values() if r['success'])
        
        report = f"""
Daily Scrape Report - {datetime.now().strftime('%Y-%m-%d')}
{'='*60}
Duration: {duration:.1f}s
Success Rate: {success_count}/4 shops ({success_count/4*100:.0f}%)
Total Products: {total_products}

Results:
"""
        for shop, result in results.items():
            status = "✅" if result['success'] else "❌"
            count = result.get('count', 0) if result['success'] else 'N/A'
            report += f"  {status} {shop}: {count} products\n"
        
        self.logger.info(report)
        self.db.save_report(report)
        self.alerts.send_daily_report(report)
    
    def _check_and_alert(self, results):
        """Alert if success rate is concerning"""
        success_count = sum(1 for r in results.values() if r['success'])
        
        if success_count < 2:  # Less than 50% success
            self.alerts.send_critical(f"Only {success_count}/4 shops scraped successfully!")
        
        # Check historical success rate
        history = self.db.get_scrape_history(days=3)
        if all(h['success_rate'] < 0.8 for h in history):
            self.alerts.send_critical("Success rate below 80% for 3 consecutive days!")
```

### Phase 3: Database Layer

```python
# database.py
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime, timedelta
import os

class MongoDB:
    def __init__(self):
        self.client = AsyncIOMotorClient(os.getenv('MONGODB_URI'))
        self.db = self.client['vietmac']
        self.products = self.db['products']
        self.scrape_logs = self.db['scrape_logs']
    
    def save_products(self, shop_name, products, timestamp):
        """Save products with timestamp"""
        doc = {
            'shop': shop_name,
            'products': products,
            'timestamp': timestamp,
            'count': len(products),
        }
        self.products.insert_one(doc)
    
    def get_cached_products(self, shop_name, max_age_days=7):
        """Get most recent cached products"""
        cutoff = datetime.now() - timedelta(days=max_age_days)
        result = self.products.find_one(
            {'shop': shop_name, 'timestamp': {'$gte': cutoff}},
            sort=[('timestamp', -1)]
        )
        if result:
            result['age'] = (datetime.now() - result['timestamp']).days
        return result
    
    def get_scrape_history(self, days=7):
        """Get scraping history for monitoring"""
        cutoff = datetime.now() - timedelta(days=days)
        logs = self.scrape_logs.find(
            {'timestamp': {'$gte': cutoff}}
        ).sort('timestamp', -1)
        return list(logs)
```

### Phase 4: Monitoring & Alerts

```python
# alerts.py
import smtplib
from email.message import EmailMessage
import os

class AlertManager:
    def __init__(self):
        self.email_from = os.getenv('ALERT_EMAIL_FROM')
        self.email_to = os.getenv('ALERT_EMAIL_TO')
        self.smtp_server = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
        self.smtp_port = int(os.getenv('SMTP_PORT', 587))
        self.smtp_password = os.getenv('SMTP_PASSWORD')
    
    def send_critical(self, message):
        """Send critical alert email"""
        subject = f"🚨 CRITICAL: VietMac Scraper Alert"
        self._send_email(subject, message)
    
    def send_daily_report(self, report):
        """Send daily scraping report"""
        subject = f"📊 VietMac Daily Scrape Report - {datetime.now().strftime('%Y-%m-%d')}"
        self._send_email(subject, report)
    
    def _send_email(self, subject, body):
        if not all([self.email_from, self.email_to, self.smtp_password]):
            print(f"Email not configured. Alert: {subject}")
            return
        
        msg = EmailMessage()
        msg['Subject'] = subject
        msg['From'] = self.email_from
        msg['To'] = self.email_to
        msg.set_content(body)
        
        try:
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as smtp:
                smtp.starttls()
                smtp.login(self.email_from, self.smtp_password)
                smtp.send_message(msg)
        except Exception as e:
            print(f"Failed to send email: {e}")
```

### Phase 5: Scheduler & Deployment

```python
# scheduler.py
import schedule
import time
from scraper_manager import ScraperManager

def daily_scrape_job():
    manager = ScraperManager()
    manager.run_all_scrapers()

# Run every day at 2 AM Vietnam time
schedule.every().day.at("02:00").do(daily_scrape_job)

# Optional: Run every 6 hours
# schedule.every(6).hours.do(daily_scrape_job)

if __name__ == '__main__':
    print("🚀 VietMac Scraper Scheduler started")
    print("Next run:", schedule.next_run())
    
    while True:
        schedule.run_pending()
        time.sleep(60)  # Check every minute
```

**Docker Deployment:**
```dockerfile
# Dockerfile
FROM python:3.11-slim

# Install Chrome and ChromeDriver for SeleniumBase
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    chromium \
    chromium-driver

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install Playwright browsers
RUN playwright install chromium

COPY . .

CMD ["python", "scheduler.py"]
```

**requirements.txt:**
```
requests==2.31.0
beautifulsoup4==4.12.3
lxml==5.1.0
playwright==1.44.0
playwright-stealth==1.0.6
seleniumbase==4.26.0
schedule==1.2.0
motor==3.4.0
pymongo==4.6.3
python-dotenv==1.0.1
```

**docker-compose.yml:**
```yaml
version: '3.8'

services:
  scraper:
    build: .
    environment:
      - MONGODB_URI=mongodb://mongo:27017/vietmac
      - ALERT_EMAIL_FROM=${ALERT_EMAIL_FROM}
      - ALERT_EMAIL_TO=${ALERT_EMAIL_TO}
      - SMTP_PASSWORD=${SMTP_PASSWORD}
    depends_on:
      - mongo
    restart: unless-stopped
  
  mongo:
    image: mongo:7
    volumes:
      - mongo_data:/data/db
    restart: unless-stopped

volumes:
  mongo_data:
```

---

## Reliability Improvements

### 1. Residential Proxy Rotation (Optional)

**Services to consider:**
- **Bright Data:** $500/month, 99% success rate
- **Oxylabs:** $300/month, 95% success rate
- **Smartproxy:** $75/month, 85% success rate

**Integration:**
```python
# With rotating proxies
proxies = RotatingProxyPool([
    'http://user:pass@proxy1.com:8080',
    'http://user:pass@proxy2.com:8080',
    # 100+ proxies
])

driver = Driver(uc=True, proxy=proxies.get_random())
```

### 2. CAPTCHA Solver Integration (If Needed)

**Services:**
- **2Captcha:** $2 per 1000 solves
- **Anti-Captcha:** $1.50 per 1000 solves

**Integration:**
```python
from twocaptcha import TwoCaptcha

solver = TwoCaptcha(os.getenv('2CAPTCHA_API_KEY'))

# If CAPTCHA detected
if 'captcha' in driver.page_source.lower():
    captcha_solution = solver.turnstile(
        sitekey=extract_sitekey(driver.page_source),
        url=driver.current_url
    )
    # Inject solution
    driver.execute_script(f"document.querySelector('[name=cf-turnstile-response]').value='{captcha_solution}'")
```

### 3. User-Agent Rotation

```python
# user_agents.py
USER_AGENTS = [
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36...',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36...',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36...',
    # 50+ real user agents
]
```

---

## Cost Analysis

### Free / Open-Source Setup
- **Cost:** $0/month (just server)
- **Success Rate:** 70-85%
- **Server:** $10-20/month (DigitalOcean/AWS)

### With Residential Proxies
- **Cost:** $75-500/month
- **Success Rate:** 90-95%
- **Server:** $10-20/month

### With Proxies + CAPTCHA Solver
- **Cost:** $100-600/month
- **Success Rate:** 95-99%
- **Server:** $10-20/month

### Commercial Scraping API (Alternative)
- **Cost:** $200-500/month
- **Success Rate:** 99%
- **No server management needed**

---

## Recommendation: Start Simple, Scale Up

### Week 1: MVP (Free tier)
- Implement all 4 scrapers with retry logic
- No proxies, no CAPTCHA solver
- Deploy to DigitalOcean droplet ($10/month)
- Run daily at 2 AM
- **Expected Success Rate: 70-80%**

### Week 2-3: Monitor & Optimize
- Track success rate per shop
- If FPT/TopZone fail consistently:
  - Add residential proxies ($75/month)
  - **Expected Success Rate: 85-90%**

### Week 4: Production Ready
- If still issues with FPT/TopZone:
  - Add CAPTCHA solver ($50/month)
  - **Expected Success Rate: 95%+**

**Total Cost:** $10-135/month depending on needs

---

## Timeline

- **Day 1-2:** Build 4 scraper workers
- **Day 3:** Build scraper manager & database
- **Day 4:** Add monitoring & alerts
- **Day 5:** Deploy to server & test
- **Day 6-7:** Monitor and fix issues

**Total: 1 week to production**

---

## Next Steps

1. Install required packages
2. Implement CellphoneS scraper (easiest)
3. Test for 24 hours
4. Implement ShopDunk scraper
5. Test for 24 hours
6. Implement FPT + TopZone (hardest)
7. Full system integration
8. Deploy to production

Ready to start implementation?
