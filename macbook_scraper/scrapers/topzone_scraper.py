#!/usr/bin/env python3
"""
TopZone Scraper - SeleniumBase UC mode
Handles connection timeouts and rate limiting
"""

from seleniumbase import Driver
from bs4 import BeautifulSoup
import time
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from scrapers.base_scraper import BaseScraper

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TopZoneScraper(BaseScraper):
    shop_name = 'topzone'
    base_url = 'https://www.topzone.vn'

    def page_urls(self):
        return [
            "https://www.topzone.vn/mac",
            "https://www.topzone.vn/mac-macbook-air-m4-series",
            "https://www.topzone.vn/mac-macbook-pro-m4",
            "https://www.topzone.vn/mac-macbook-pro",
            "https://www.topzone.vn/mac-macbook-air",
        ]

    def fetch_html(self, url, retry=3):
        """Scrape using SeleniumBase UC mode"""
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
                driver.set_page_load_timeout(60)
                driver.get(url)

                logger.info("  Waiting for page to load...")
                time.sleep(10)

                logger.info("  Scrolling to load all products...")
                driver.execute_script('window.scrollTo(0, document.body.scrollHeight)')
                time.sleep(3)

                html = driver.page_source
                driver.quit()

                return html

            except Exception as e:
                logger.error(f"Error with UC Chrome: {e}")
                if driver:
                    try:
                        driver.quit()
                    except:
                        pass

                if attempt < retry - 1:
                    wait_time = (attempt + 1) * 120
                    logger.info(f"Retrying in {wait_time}s...")
                    time.sleep(wait_time)

        return None

    def parse_products(self, html):
        """Parse products from HTML. Pure function, no network I/O."""
        soup = BeautifulSoup(html, 'html.parser')
        products = []

        selectors = [
            '.product-item',
            '.product-card',
            '.item',
            '.product',
        ]

        product_items = []
        for selector in selectors:
            product_items = soup.select(selector)
            if product_items:
                logger.info(f"Found {len(product_items)} items with selector: {selector}")
                break

        if not product_items:
            logger.warning("No product items found")
            return []

        for item in product_items:
            try:
                name_elem = item.select_one('h3') or item.select_one('.name') or item.select_one('.product-name')
                if not name_elem:
                    continue

                raw_name = name_elem.get_text(strip=True)

                if not self._is_mac(raw_name):
                    continue

                model_name = self._parse_model_name(raw_name)

                price_elem = item.select_one('.price') or item.select_one('.product-price')
                price_text = price_elem.get_text(strip=True) if price_elem else None

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
        return 'Connection timeout or block'


if __name__ == '__main__':
    scraper = TopZoneScraper()
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
