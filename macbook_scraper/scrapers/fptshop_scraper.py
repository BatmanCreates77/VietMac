#!/usr/bin/env python3
"""
FPT Shop Scraper - SeleniumBase UC (Undetected Chrome) mode
Bypasses Cloudflare WAF protection
"""

from seleniumbase import Driver
from bs4 import BeautifulSoup
import requests
import re
import time
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from scrapers.base_scraper import BaseScraper
from utils import session_cache

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class FPTShopScraper(BaseScraper):
    shop_name = 'fptshop'
    base_url = 'https://fptshop.com.vn'

    def _parse_model_name(self, name):
        """Parse and clean MacBook model name"""
        if not name:
            return None

        name = name.strip()
        name = re.sub(r'\s*\(.*?\)\s*$', '', name)

        return name

    def page_urls(self):
        return [
            "https://fptshop.com.vn/may-tinh-xach-tay/apple-macbook",
            "https://fptshop.com.vn/may-tinh-xach-tay/macbook-air?kich-thuoc-man-hinh=13-inch&sort=noi-bat",
            "https://fptshop.com.vn/may-tinh-xach-tay/macbook-air?kich-thuoc-man-hinh=15-inch&sort=noi-bat",
            "https://fptshop.com.vn/may-tinh-xach-tay/macbook-pro?kich-thuoc-man-hinh=14-inch&sort=noi-bat",
            "https://fptshop.com.vn/may-tinh-xach-tay/macbook-pro?kich-thuoc-man-hinh=16-inch&sort=noi-bat",
        ]

    def fetch_html(self, url, retry=3):
        """Try a cached, already-Cloudflare-cleared cookie jar first (free,
        no browser launch) before paying the cost of a full UC-mode solve.
        The cache is populated by _fetch_with_uc_mode() on a successful
        solve and reused by every call until it expires or gets rejected."""
        cached_html = self._fetch_with_cached_session(url)
        if cached_html is not None:
            return cached_html

        return self._fetch_with_uc_mode(url, retry=retry)

    def _fetch_with_cached_session(self, url):
        session = session_cache.load_session(self.shop_name)
        if not session:
            return None

        try:
            logger.info("  Trying cached Cloudflare-cleared session (no browser)...")
            response = requests.get(
                url,
                cookies=session['cookies'],
                headers={'User-Agent': session['user_agent']},
                timeout=15,
            )
        except Exception as e:
            logger.warning(f"  Cached-session request failed: {e}")
            return None

        if session_cache.is_challenge_response(response.status_code, response.text):
            logger.warning("  Cached session was rejected (expired/invalidated) — falling back to full solve")
            session_cache.invalidate_session(self.shop_name)
            return None

        logger.info("  Cached session accepted — skipped browser entirely")
        return response.text

    def _fetch_with_uc_mode(self, url, retry=3):
        """Full SeleniumBase UC mode solve. Expensive and the highest-risk
        step, so a successful solve's cookies get cached for reuse."""
        for attempt in range(retry):
            driver = None
            try:
                logger.info(f"Launching UC Chrome for: {url} (attempt {attempt + 1}/{retry})")

                driver = Driver(
                    uc=True,
                    headless=False,
                    chromium_arg="--disable-blink-features=AutomationControlled",
                )

                logger.info("  Navigating to page...")
                driver.get(url)

                logger.info("  Waiting for page to load (checking for Cloudflare)...")
                time.sleep(10)

                page_source = driver.page_source
                if '403' in page_source or 'Forbidden' in driver.title:
                    raise Exception('Got 403 Forbidden')

                if 'Cloudflare' in driver.title or 'Just a moment' in page_source:
                    logger.warning("  Cloudflare challenge detected, waiting longer...")
                    time.sleep(15)
                    page_source = driver.page_source

                logger.info("  Scrolling to load all products...")
                driver.execute_script('window.scrollTo(0, document.body.scrollHeight)')
                time.sleep(3)

                html = driver.page_source
                user_agent = driver.execute_script("return navigator.userAgent;")
                cookies = driver.get_cookies()
                driver.quit()

                if not session_cache.is_challenge_response(200, html):
                    session_cache.save_session(self.shop_name, cookies, user_agent)
                    logger.info("  Cached this session's cookies for reuse on future runs")

                return html

            except Exception as e:
                logger.error(f"Error with UC Chrome: {e}")
                if driver:
                    try:
                        driver.quit()
                    except:
                        pass

                if attempt < retry - 1:
                    wait_time = (attempt + 1) * 120  # 2 min, 4 min, 6 min
                    logger.info(f"Retrying in {wait_time}s...")
                    time.sleep(wait_time)

        return None

    def parse_products(self, html):
        """Parse products from HTML. Pure function, no network I/O."""
        soup = BeautifulSoup(html, 'html.parser')
        products = []

        selectors = [
            '.cdt-product',
            '.product-item',
            '[data-product]',
            '.product-card',
        ]

        product_items = []
        for selector in selectors:
            product_items = soup.select(selector)
            if product_items:
                logger.info(f"Found {len(product_items)} items with selector: {selector}")
                break

        if not product_items:
            logger.warning("No product items found with any selector")
            return []

        for item in product_items:
            try:
                name_elem = (item.select_one('h3') or
                            item.select_one('.product-name') or
                            item.select_one('[data-title]') or
                            item.find('a', {'title': True}))

                if not name_elem:
                    continue

                raw_name = name_elem.get('title') or name_elem.get_text(strip=True)

                if 'MacBook' not in raw_name:
                    continue

                model_name = self._parse_model_name(raw_name)

                price_elem = (item.select_one('.price') or
                             item.select_one('.product-price') or
                             item.select_one('[data-price]'))

                price_text = None
                if price_elem:
                    price_text = price_elem.get('data-price') or price_elem.get_text(strip=True)

                link_elem = item.select_one('a')
                url = link_elem.get('href') if link_elem else None
                if url and not url.startswith('http'):
                    url = self.base_url + url if url.startswith('/') else self.base_url + '/' + url

                product = self._build_product(
                    model_name=model_name,
                    raw_name=raw_name,
                    price_text=price_text,
                    url=url,
                    extra_specs_source=raw_name,
                )

                products.append(product)
                logger.info(f"  ✓ {model_name[:60]} - {price_text}")

            except Exception as e:
                logger.error(f"Error parsing product: {e}")
                continue

        return products

    def page_delay_seconds(self):
        return 10

    def failure_message(self):
        return 'Cloudflare block or timeout'


if __name__ == '__main__':
    scraper = FPTShopScraper()
    result = scraper.scrape()

    print(f"\n{'='*80}")
    print(f"RESULTS:")
    print(f"{'='*80}")
    print(f"Success: {result['success']}")
    print(f"Products found: {result['count']}")

    if result['products']:
        print(f"\nSample products:")
        for i, product in enumerate(result['products'][:10], 1):
            print(f"\n{i}. {product['model']}")
            print(f"   Price: {product['price_text']}")
            if product.get('url'):
                print(f"   URL: {product['url'][:80]}...")
