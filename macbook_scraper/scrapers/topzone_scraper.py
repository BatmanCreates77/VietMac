#!/usr/bin/env python3
"""
TopZone Scraper - SeleniumBase UC mode
Handles connection timeouts and rate limiting
"""

from seleniumbase import Driver
from bs4 import BeautifulSoup
import re
import time
import logging
import sys
from pathlib import Path

# Add utils directory to path for spec parser
sys.path.insert(0, str(Path(__file__).parent.parent))
from utils.spec_parser import SpecParser

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TopZoneScraper:
    def __init__(self):
        self.base_url = "https://www.topzone.vn"
        self.spec_parser = SpecParser()

    def _clean_price(self, price_text):
        """Extract numeric price from text"""
        if not price_text:
            return None
        cleaned = re.sub(r'[^\d]', '', price_text)
        return int(cleaned) if cleaned else None

    def _parse_model_name(self, name):
        """Parse and clean MacBook model name"""
        if not name:
            return None
        return name.strip()

    def scrape_with_uc(self, url, retry=3):
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

                # Scroll to load products
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
        """Parse products from HTML"""
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

                if 'MacBook' not in raw_name:
                    continue

                model_name = self._parse_model_name(raw_name)

                price_elem = item.select_one('.price') or item.select_one('.product-price')
                price_text = price_elem.get_text(strip=True) if price_elem else None
                price_vnd = self._clean_price(price_text)

                link_elem = item.select_one('a')
                url = link_elem.get('href') if link_elem else None
                if url and not url.startswith('http'):
                    url = self.base_url + url if url.startswith('/') else self.base_url + '/' + url

                # Parse specs using spec parser
                parsed_specs = self.spec_parser.parse(raw_name)

                product = {
                    'model': model_name,
                    'raw_name': raw_name,
                    'price_vnd': price_vnd,
                    'price_text': price_text,
                    'url': url,
                    'shop': 'topzone',
                    # Add parsed specs
                    'specs': {
                        'model_type': parsed_specs.get('model_type'),
                        'chip': parsed_specs.get('chip'),
                        'chip_variant': parsed_specs.get('chip_variant'),
                        'screen_size': parsed_specs.get('screen_size'),
                        'cpu_cores': parsed_specs.get('cpu_cores'),
                        'gpu_cores': parsed_specs.get('gpu_cores'),
                        'ram_gb': parsed_specs.get('ram_gb'),
                        'storage_gb': parsed_specs.get('storage_gb'),
                        'storage_display': parsed_specs.get('storage_display'),
                        'year': parsed_specs.get('year'),
                    },
                    'product_id': parsed_specs.get('id'),
                    'clean_name': parsed_specs.get('clean_name'),
                }

                products.append(product)
                logger.info(f"  ✓ {model_name[:60]} - {price_text}")

            except Exception as e:
                logger.error(f"Error parsing product: {e}")
                continue

        return products

    def scrape(self):
        """Main scraping method"""
        logger.info("="*80)
        logger.info("Starting TopZone scraper...")
        logger.info("="*80)

        # All TopZone MacBook URLs
        urls = [
            "https://www.topzone.vn/mac",
            "https://www.topzone.vn/mac-macbook-air-m4-series",
            "https://www.topzone.vn/mac-macbook-pro-m4",
            "https://www.topzone.vn/mac-macbook-pro",
            "https://www.topzone.vn/mac-macbook-air",
        ]

        all_products = []
        seen_urls = set()  # Avoid duplicates

        for url in urls:
            logger.info(f"\nScraping: {url}")
            html = self.scrape_with_uc(url)

            if html:
                products = self.parse_products(html)
                # Filter out duplicates based on product URL
                for product in products:
                    product_url = product.get('url')
                    if product_url and product_url not in seen_urls:
                        seen_urls.add(product_url)
                        all_products.append(product)
                logger.info(f"Found {len(products)} MacBook models from this page ({len(all_products)} unique total)")
            else:
                logger.warning(f"Failed to scrape {url}")

            # Polite delay between pages
            time.sleep(10)

        logger.info("="*80)
        logger.info(f"TopZone scraping complete: {len(all_products)} total unique products")
        logger.info("="*80)

        if all_products:
            return {
                'success': True,
                'shop': 'topzone',
                'products': all_products,
                'count': len(all_products),
            }
        else:
            logger.error("Failed to scrape TopZone - no products found")
            return {
                'success': False,
                'shop': 'topzone',
                'error': 'Connection timeout or block',
                'products': [],
                'count': 0,
            }


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
