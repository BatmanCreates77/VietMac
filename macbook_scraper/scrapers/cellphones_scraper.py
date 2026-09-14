#!/usr/bin/env python3
"""
CellphoneS Scraper - Hybrid HTTP + Playwright scraper
Uses simple HTTP for most pages, Playwright for JavaScript-heavy pages (M5)
"""

import requests
from bs4 import BeautifulSoup
import re
import time
import random
import logging
import sys
from pathlib import Path
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout

sys.path.insert(0, str(Path(__file__).parent.parent))
from scrapers.base_scraper import BaseScraper

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class CellphonesScraper(BaseScraper):
    shop_name = 'cellphones'
    base_url = 'https://cellphones.com.vn'

    def __init__(self):
        super().__init__()
        self.user_agents = [
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        ]
        self.session = requests.Session()

    def _get_headers(self):
        """Generate random headers to avoid detection"""
        return {
            'User-Agent': random.choice(self.user_agents),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }

    def _parse_model_name(self, name):
        """Parse MacBook model name and extract specs"""
        if not name:
            return None

        name = name.strip()
        name = re.sub(r'\s*\|\s*Chính hãng.*', '', name)
        name = re.sub(r'\s*Chính hãng.*', '', name)

        return name

    def page_urls(self):
        # Plain URL list — the base scrape() orchestrator iterates these
        # directly. The original per-page "name" was only used for log
        # lines and for picking the Playwright path; the latter now
        # checks the URL itself (_uses_playwright), so name isn't needed.
        return [
            'https://cellphones.com.vn/laptop/mac.html',
            'https://cellphones.com.vn/laptop/mac/macbook-pro/macbook-pro-2025.html',
            'https://cellphones.com.vn/laptop/mac/macbook-air.html',
            'https://cellphones.com.vn/laptop/mac/macbook-pro.html',
        ]

    def _uses_playwright(self, url):
        return 'macbook-pro-2025' in url

    def fetch_html(self, url, retry=3):
        """Requests for most pages, Playwright for the JS-heavy M5 page."""
        if self._uses_playwright(url):
            return self._fetch_with_playwright(url, retry=retry)
        return self._fetch_with_requests(url, retry=retry)

    def _fetch_with_requests(self, url, retry=3):
        for attempt in range(retry):
            try:
                logger.info(f"Fetching: {url} (attempt {attempt + 1}/{retry})")
                response = self.session.get(url, headers=self._get_headers(), timeout=15)

                if response.status_code == 200:
                    return response.content
                else:
                    logger.warning(f"HTTP {response.status_code} for {url}")

            except Exception as e:
                logger.error(f"Error fetching {url}: {e}")
                if attempt < retry - 1:
                    sleep_time = (attempt + 1) * 5
                    logger.info(f"Retrying in {sleep_time}s...")
                    time.sleep(sleep_time)

        return None

    def _fetch_with_playwright(self, url, retry=3):
        for attempt in range(retry):
            try:
                logger.info(f"Fetching with Playwright: {url} (attempt {attempt + 1}/{retry})")
                with sync_playwright() as p:
                    browser = p.chromium.launch(
                        headless=True,
                        args=['--disable-blink-features=AutomationControlled']
                    )
                    context = browser.new_context(
                        user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                        viewport={'width': 1920, 'height': 1080},
                        locale='vi-VN',
                    )
                    page = context.new_page()

                    logger.info("  Navigating to page...")
                    page.goto(url, wait_until='domcontentloaded', timeout=60000)

                    logger.info("  Waiting for products to load...")
                    try:
                        page.wait_for_selector('.product-item, .product, .item-product', timeout=15000)
                    except:
                        logger.warning("  Product selector not found, continuing anyway...")

                    time.sleep(2)

                    logger.info("  Scrolling to load all products...")
                    page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
                    time.sleep(2)

                    content = page.content()
                    browser.close()

                    return content.encode('utf-8')

            except PlaywrightTimeout as e:
                logger.error(f"Timeout error: {e}")
                if attempt < retry - 1:
                    wait_time = (attempt + 1) * 30
                    logger.info(f"Retrying in {wait_time}s...")
                    time.sleep(wait_time)
            except Exception as e:
                logger.error(f"Error with Playwright: {e}")
                if attempt < retry - 1:
                    time.sleep(20)

        return None

    def parse_products(self, html):
        """Parse products from HTML. Pure function, no network I/O —
        screen-size enrichment (which needs a live fetch) happens in
        enrich_product(), not here."""
        soup = BeautifulSoup(html, 'html.parser')
        products = []

        product_items = soup.select('.product-info')
        logger.info(f"Found {len(product_items)} product items")

        for item in product_items:
            try:
                name_elem = item.select_one('.product__name h3')
                if not name_elem:
                    continue

                raw_name = name_elem.get_text(strip=True)

                if 'MacBook' not in raw_name:
                    continue

                model_name = self._parse_model_name(raw_name)

                price_elem = item.select_one('.product__price--show')
                price_text = price_elem.get_text(strip=True) if price_elem else None

                link_elem = item.select_one('a.product__link')
                url = link_elem.get('href') if link_elem else None
                if url and not url.startswith('http'):
                    url = self.base_url + url if url.startswith('/') else self.base_url + '/' + url

                img_elem = item.select_one('.product__image img')
                image_url = img_elem.get('src') if img_elem else None

                product = self._build_product(
                    model_name=model_name,
                    raw_name=raw_name,
                    price_text=price_text,
                    url=url,
                    image_url=image_url,
                    extra_specs_source=model_name,
                )
                # Stash for enrich_product — matches original behavior of
                # appending screen size onto model_name before spec parsing.
                product['_pending_screen_enrich'] = True

                products.append(product)
                logger.info(f"  ✓ {model_name[:60]} - {price_text}")

            except Exception as e:
                logger.error(f"Error parsing product: {e}")
                continue

        return products

    def _get_product_details(self, product_url):
        """Fetch product detail page to get more specs."""
        html = self._fetch_with_requests(product_url, retry=3)
        if not html:
            return {}

        soup = BeautifulSoup(html, 'html.parser')
        details = {}

        spec_table = soup.select_one('.technical-content')
        if spec_table:
            for row in spec_table.select('tr'):
                cells = row.select('td')
                if len(cells) == 2:
                    spec_name = cells[0].get_text(strip=True).lower()
                    spec_value = cells[1].get_text(strip=True)
                    if 'kích thước màn hình' in spec_name:
                        details['screen_size'] = spec_value
                        break
        return details

    def enrich_product(self, product):
        """Fetch the product detail page for screen size, append it to
        the model name if not already present, and re-derive specs from
        the enriched name — this is the one live network call per
        product that must not run inside parse_products()."""
        if not product.pop('_pending_screen_enrich', False):
            return product

        url = product.get('url')
        details = {}
        if url:
            details = self._get_product_details(url)
            time.sleep(1)  # Polite delay

        model_name = product['model']
        screen_size = details.get('screen_size')
        if screen_size and screen_size.replace(' inch', '') not in model_name:
            model_name = f"{model_name} {screen_size.replace(' inch', '')}"
            product['model'] = model_name
            self._apply_specs(product, model_name)

        return product

    def page_delay_seconds(self):
        return 3

    def failure_message(self):
        return 'No products found'


if __name__ == '__main__':
    scraper = CellphonesScraper()
    result = scraper.scrape()

    print(f"\n{'='*80}")
    print(f"RESULTS:")
    print(f"{'='*80}")
    print(f"Success: {result['success']}")
    print(f"Products found: {result['count']}")
    print(f"\nSample products:")
    for i, product in enumerate(result['products'][:5], 1):
        print(f"\n{i}. {product['model']}")
        print(f"   Price: {product['price_text']}")
        print(f"   URL: {product['url'][:80]}...")
