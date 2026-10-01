#!/usr/bin/env python3
"""
CellphoneS Scraper - Playwright for every listing page.

Plain HTTP used to be used for most pages, but CellphoneS now serves an
obfuscated JS challenge (Server: Byte-nginx) to non-browser clients, and its
Air/Pro category pages only render products in a real browser anyway — over
HTTP they always parsed to 0 products (live check 2026-10-01: 20 and 18 via
Playwright).
"""

from bs4 import BeautifulSoup
import re
import time
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

    def _parse_model_name(self, name):
        """Parse MacBook model name and extract specs"""
        if not name:
            return None

        name = name.strip()
        name = re.sub(r'\s*\|\s*Chính hãng.*', '', name)
        name = re.sub(r'\s*Chính hãng.*', '', name)

        return name

    def page_urls(self):
        return [
            'https://cellphones.com.vn/laptop/mac.html',
            'https://cellphones.com.vn/laptop/mac/macbook-pro/macbook-pro-2025.html',
            'https://cellphones.com.vn/laptop/mac/macbook-air.html',
            'https://cellphones.com.vn/laptop/mac/macbook-pro.html',
        ]

    def fetch_html(self, url, retry=3):
        return self._fetch_with_playwright(url, retry=retry)

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

                    # page.content() is already a correctly-decoded str.
                    # Re-encoding to bytes here made BeautifulSoup guess the
                    # encoding when parsing (no charset sniffing needed for
                    # str input) — it guessed wrong for Vietnamese text,
                    # producing mojibake ("Chính hãng" -> "Ch√≠nh h√£ng") and,
                    # worse, silently swallowing the price element entirely
                    # on affected products (caught live by the validation
                    # gate: 2026-09-19, 4/17 cellphones products rejected
                    # for null price_vnd). Returning the str directly skips
                    # that guess altogether.
                    return content

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
        """Parse products from HTML. Pure function, no network I/O."""
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

                products.append(product)
                logger.info(f"  ✓ {model_name[:60]} - {price_text}")

            except Exception as e:
                logger.error(f"Error parsing product: {e}")
                continue

        return products

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
