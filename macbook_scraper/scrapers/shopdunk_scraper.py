#!/usr/bin/env python3
"""
ShopDunk Scraper - Playwright-based scraper
Handles JavaScript-rendered content
"""

from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout
from bs4 import BeautifulSoup
import re
import time
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from scrapers.base_scraper import BaseScraper

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ShopDunkScraper(BaseScraper):
    shop_name = 'shopdunk'
    base_url = 'https://shopdunk.com'

    def _parse_model_name(self, name):
        """Parse and clean Mac model name"""
        if not name:
            return None

        name = name.strip()
        # Remove common suffixes
        # Remove notes like "(Đủ hộp, PK)", but keep a trailing config such
        # as "(10 core GPU| 16GB RAM| 512GB SSD)": it is the only thing that
        # tells apart e.g. 12 "MacBook Pro 14 inch M5 2025" listings.
        name = re.sub(r'\s*\([^()\d]*\)\s*$', '', name)
        name = re.sub(r'\s*-\s*Cũ.*', '', name)  # Remove "Cũ đẹp"
        name = re.sub(r'\s*Cũ.*', '', name)

        return name

    def page_urls(self):
        # /macbook-pro-m4 and /macbook-air-m4 were removed after the M5
        # launch (404 -> /page-not-found as of 2026-10-01).
        return [
            "https://shopdunk.com/mac",
            "https://shopdunk.com/macbook-pro-m5",
            "https://shopdunk.com/macbook-air",
            "https://shopdunk.com/macbook-pro-2",
            "https://shopdunk.com/mac-mini",
            "https://shopdunk.com/imac",
            "https://shopdunk.com/mac-studio",
        ]

    @staticmethod
    def _is_missing_page(response, final_url):
        return (response is not None and response.status == 404) or 'page-not-found' in final_url

    def fetch_html(self, url, retry=3):
        """Scrape using Playwright"""
        for attempt in range(retry):
            try:
                logger.info(f"Launching browser for: {url} (attempt {attempt + 1}/{retry})")

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
                    response = page.goto(url, wait_until='domcontentloaded', timeout=60000)

                    # A removed category page will never show products, so
                    # don't burn ~9 minutes of selector timeouts and retry
                    # backoff waiting for them.
                    if self._is_missing_page(response, page.url):
                        logger.warning(
                            f"  Listing page is gone (404, landed on {page.url}) — "
                            f"remove it from page_urls"
                        )
                        browser.close()
                        return None

                    logger.info("  Waiting for products to load...")
                    page.wait_for_selector('.product-item', timeout=30000)
                    time.sleep(2)

                    logger.info("  Scrolling to load all products...")
                    page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
                    time.sleep(3)

                    content = page.content()
                    browser.close()

                    return content

            except PlaywrightTimeout as e:
                logger.error(f"Timeout error: {e}")
                if attempt < retry - 1:
                    wait_time = (attempt + 1) * 60
                    logger.info(f"Retrying in {wait_time}s...")
                    time.sleep(wait_time)

            except Exception as e:
                logger.error(f"Error with Playwright: {e}")
                if attempt < retry - 1:
                    time.sleep(30)

        return None

    def parse_products(self, html):
        """Parse products from HTML. Pure function, no network I/O."""
        soup = BeautifulSoup(html, 'html.parser')
        products = []

        product_items = soup.select('.product-item')
        logger.info(f"Found {len(product_items)} product items")

        for item in product_items:
            try:
                name_elem = item.select_one('h3') or item.select_one('.product-name')
                if not name_elem:
                    continue

                raw_name = name_elem.get_text(strip=True)

                if not self._is_mac(raw_name):
                    continue

                model_name = self._parse_model_name(raw_name)

                price_elem = item.select_one('.actual-price')
                price_text = price_elem.get_text(strip=True) if price_elem else None

                link_elem = item.select_one('a')
                url = link_elem.get('href') if link_elem else None
                if url and not url.startswith('http'):
                    url = self.base_url + url if url.startswith('/') else self.base_url + '/' + url

                product_id = item.get('data-productid')

                img_elem = item.select_one('img')
                image_url = img_elem.get('src') or img_elem.get('data-src') if img_elem else None

                product = self._build_product(
                    model_name=model_name,
                    raw_name=raw_name,
                    price_text=price_text,
                    url=url,
                    image_url=image_url,
                    product_id=product_id,
                    extra_specs_source=raw_name,
                )

                products.append(product)
                logger.info(f"  ✓ {model_name[:60]} - {price_text}")

            except Exception as e:
                logger.error(f"Error parsing product: {e}")
                continue

        return products

    def page_delay_seconds(self):
        return 5

    def failure_message(self):
        return 'No products found'


if __name__ == '__main__':
    scraper = ShopDunkScraper()
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
            print(f"   URL: {product['url'][:80]}...")
