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

# Add utils directory to path for spec parser
sys.path.insert(0, str(Path(__file__).parent.parent))
from utils.spec_parser import SpecParser

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ShopDunkScraper:
    def __init__(self):
        self.base_url = "https://shopdunk.com"
        self.spec_parser = SpecParser()

    def _clean_price(self, price_text):
        """Extract numeric price from text"""
        if not price_text:
            return None
        # Remove all non-numeric characters
        cleaned = re.sub(r'[^\d]', '', price_text)
        return int(cleaned) if cleaned else None

    def _parse_model_name(self, name):
        """Parse and clean MacBook model name"""
        if not name:
            return None

        name = name.strip()
        # Remove common suffixes
        name = re.sub(r'\s*\(.*?\)\s*$', '', name)  # Remove (Đủ hộp, PK) etc
        name = re.sub(r'\s*-\s*Cũ.*', '', name)  # Remove "Cũ đẹp"
        name = re.sub(r'\s*Cũ.*', '', name)

        return name

    def scrape_with_playwright(self, url, retry=3):
        """Scrape using Playwright"""
        for attempt in range(retry):
            try:
                logger.info(f"Launching browser for: {url} (attempt {attempt + 1}/{retry})")

                with sync_playwright() as p:
                    # Launch browser
                    browser = p.chromium.launch(
                        headless=True,
                        args=['--disable-blink-features=AutomationControlled']
                    )

                    # Create context with realistic settings
                    context = browser.new_context(
                        user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                        viewport={'width': 1920, 'height': 1080},
                        locale='vi-VN',
                    )

                    page = context.new_page()

                    # Navigate to page
                    logger.info("  Navigating to page...")
                    page.goto(url, wait_until='domcontentloaded', timeout=60000)

                    # Wait for products to load
                    logger.info("  Waiting for products to load...")
                    page.wait_for_selector('.product-item', timeout=30000) # Wait for the product grid
                    time.sleep(2) # Extra wait for any lazy-loaded images or prices

                    # Scroll to load lazy-loaded content
                    logger.info("  Scrolling to load all products...")
                    page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
                    time.sleep(3)

                    # Get HTML content
                    content = page.content()

                    # Close browser
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
        """Parse products from HTML"""
        soup = BeautifulSoup(html, 'html.parser')
        products = []

        # Find all product items
        product_items = soup.select('.product-item')
        logger.info(f"Found {len(product_items)} product items")

        for item in product_items:
            try:
                # Extract product name
                name_elem = item.select_one('h3') or item.select_one('.product-name')
                if not name_elem:
                    continue

                raw_name = name_elem.get_text(strip=True)

                # Filter only MacBooks
                if 'MacBook' not in raw_name:
                    continue

                model_name = self._parse_model_name(raw_name)

                # Extract price - ShopDunk uses .actual-price for the final price
                price_elem = item.select_one('.actual-price')
                price_text = price_elem.get_text(strip=True) if price_elem else None
                price_vnd = self._clean_price(price_text)

                # Extract URL
                link_elem = item.select_one('a')
                url = link_elem.get('href') if link_elem else None
                if url and not url.startswith('http'):
                    url = self.base_url + url if url.startswith('/') else self.base_url + '/' + url

                # Extract product ID
                product_id = item.get('data-productid')

                # Extract image
                img_elem = item.select_one('img')
                image_url = img_elem.get('src') or img_elem.get('data-src') if img_elem else None

                # Parse specs using spec parser
                parsed_specs = self.spec_parser.parse(raw_name)

                product = {
                    'model': model_name,
                    'raw_name': raw_name,
                    'price_vnd': price_vnd,
                    'price_text': price_text,
                    'url': url,
                    'product_id': product_id,
                    'image_url': image_url,
                    'shop': 'shopdunk',
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
        logger.info("Starting ShopDunk scraper...")
        logger.info("="*80)

        # All ShopDunk MacBook URLs
        urls = [
            "https://shopdunk.com/mac",
            "https://shopdunk.com/macbook-pro-m4",
            "https://shopdunk.com/macbook-air-m4",
            "https://shopdunk.com/macbook-air",
            "https://shopdunk.com/macbook-pro-2",
        ]

        all_products = []
        seen_urls = set()  # Avoid duplicates

        for url in urls:
            logger.info(f"\nScraping: {url}")
            html = self.scrape_with_playwright(url)

            if html:
                products = self.parse_products(html)
                # Filter out duplicates based on product URL
                for product in products:
                    if product['url'] and product['url'] not in seen_urls:
                        seen_urls.add(product['url'])
                        all_products.append(product)
                logger.info(f"Found {len(products)} MacBook models from this page ({len(all_products)} unique total)")
            else:
                logger.warning(f"Failed to scrape {url}")

            # Polite delay between pages
            time.sleep(5)

        logger.info("="*80)
        logger.info(f"ShopDunk scraping complete: {len(all_products)} total unique products")
        logger.info("="*80)

        if all_products:
            return {
                'success': True,
                'shop': 'shopdunk',
                'products': all_products,
                'count': len(all_products),
            }
        else:
            logger.error("Failed to scrape ShopDunk - no products found")
            return {
                'success': False,
                'shop': 'shopdunk',
                'error': 'No products found',
                'products': [],
                'count': 0,
            }


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
