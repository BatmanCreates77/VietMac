#!/usr/bin/env python3
"""
FPT Shop Scraper - SeleniumBase UC (Undetected Chrome) mode
Bypasses Cloudflare WAF protection
"""

from seleniumbase import Driver
from bs4 import BeautifulSoup
import re
import time
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class FPTShopScraper:
    def __init__(self):
        self.base_url = "https://fptshop.com.vn"

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
        # Clean up common patterns
        name = re.sub(r'\s*\(.*?\)\s*$', '', name)

        return name

    def scrape_with_uc(self, url, retry=3):
        """Scrape using SeleniumBase UC mode"""
        for attempt in range(retry):
            driver = None
            try:
                logger.info(f"Launching UC Chrome for: {url} (attempt {attempt + 1}/{retry})")

                # Launch undetected Chrome
                driver = Driver(
                    uc=True,  # Undetected Chrome mode
                    headless=False,  # Headless has higher detection rate
                    # Add these for better stealth
                    chromium_arg="--disable-blink-features=AutomationControlled",
                )

                logger.info("  Navigating to page...")
                driver.get(url)

                # Wait for potential Cloudflare challenge
                logger.info("  Waiting for page to load (checking for Cloudflare)...")
                time.sleep(10)

                # Check if we got blocked
                page_source = driver.page_source
                if '403' in page_source or 'Forbidden' in driver.title:
                    raise Exception('Got 403 Forbidden')

                if 'Cloudflare' in driver.title or 'Just a moment' in page_source:
                    logger.warning("  Cloudflare challenge detected, waiting longer...")
                    time.sleep(15)
                    page_source = driver.page_source

                # Scroll to load products
                logger.info("  Scrolling to load all products...")
                driver.execute_script('window.scrollTo(0, document.body.scrollHeight)')
                time.sleep(3)

                # Get final HTML
                html = driver.page_source

                # Close driver
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
                    wait_time = (attempt + 1) * 120  # 2 min, 4 min, 6 min
                    logger.info(f"Retrying in {wait_time}s...")
                    time.sleep(wait_time)

        return None

    def parse_products(self, html):
        """Parse products from HTML"""
        soup = BeautifulSoup(html, 'html.parser')
        products = []

        # Try multiple selectors for FPT Shop
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
                # Extract product name
                name_elem = (item.select_one('h3') or
                            item.select_one('.product-name') or
                            item.select_one('[data-title]') or
                            item.find('a', {'title': True}))

                if not name_elem:
                    continue

                raw_name = name_elem.get('title') or name_elem.get_text(strip=True)

                # Filter only MacBooks
                if 'MacBook' not in raw_name:
                    continue

                model_name = self._parse_model_name(raw_name)

                # Extract price
                price_elem = (item.select_one('.price') or
                             item.select_one('.product-price') or
                             item.select_one('[data-price]'))

                price_text = None
                if price_elem:
                    price_text = price_elem.get('data-price') or price_elem.get_text(strip=True)

                price_vnd = self._clean_price(price_text)

                # Extract URL
                link_elem = item.select_one('a')
                url = link_elem.get('href') if link_elem else None
                if url and not url.startswith('http'):
                    url = self.base_url + url if url.startswith('/') else self.base_url + '/' + url

                product = {
                    'model': model_name,
                    'raw_name': raw_name,
                    'price_vnd': price_vnd,
                    'price_text': price_text,
                    'url': url,
                    'shop': 'fptshop',
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
        logger.info("Starting FPT Shop scraper with UC Chrome...")
        logger.info("="*80)

        url = "https://fptshop.com.vn/may-tinh-xach-tay/apple-macbook"

        logger.info(f"\nScraping: {url}")
        html = self.scrape_with_uc(url)

        if html:
            products = self.parse_products(html)
            logger.info(f"Found {len(products)} MacBook models")

            logger.info("="*80)
            logger.info(f"FPT Shop scraping complete: {len(products)} total products")
            logger.info("="*80)

            return {
                'success': True,
                'shop': 'fptshop',
                'products': products,
                'count': len(products),
            }
        else:
            logger.error("Failed to scrape FPT Shop - Cloudflare block")
            return {
                'success': False,
                'shop': 'fptshop',
                'error': 'Cloudflare block or timeout',
                'products': [],
                'count': 0,
            }


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
