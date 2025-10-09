#!/usr/bin/env python3
"""
CellphoneS Scraper - Simple HTTP-based scraper
No anti-bot protection, works with requests + BeautifulSoup
"""

import requests
from bs4 import BeautifulSoup
import re
import time
import random
import logging
import sys
from pathlib import Path

# Add utils directory to path for spec parser
sys.path.insert(0, str(Path(__file__).parent.parent))
from utils.spec_parser import SpecParser

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class CellphonesScraper:
    def __init__(self):
        self.base_url = "https://cellphones.com.vn"
        self.user_agents = [
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        ]
        self.session = requests.Session()
        self.spec_parser = SpecParser()

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

    def _clean_price(self, price_text):
        """Extract numeric price from text"""
        if not price_text:
            return None
        # Remove all non-numeric characters
        cleaned = re.sub(r'[^\d]', '', price_text)
        return int(cleaned) if cleaned else None

    def _parse_model_name(self, name):
        """Parse MacBook model name and extract specs"""
        if not name:
            return None

        # Clean up the name
        name = name.strip()
        # Remove "Chính hãng Apple Việt Nam" and similar
        name = re.sub(r'\s*\|\s*Chính hãng.*', '', name)
        name = re.sub(r'\s*Chính hãng.*', '', name)

        return name

    def scrape_page(self, url, retry=3):
        """Scrape a single page"""
        for attempt in range(retry):
            try:
                logger.info(f"Fetching: {url} (attempt {attempt + 1}/{retry})")
                response = self.session.get(
                    url,
                    headers=self._get_headers(),
                    timeout=15
                )

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

    def _get_product_details(self, product_url):
        """Fetch product detail page to get more specs."""
        html = self.scrape_page(product_url)
        if not html:
            return {}

        soup = BeautifulSoup(html, 'html.parser')
        details = {}

        # Find screen size from spec table
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

    def parse_products(self, html):
        """Parse products from HTML"""
        soup = BeautifulSoup(html, 'html.parser')
        products = []

        # Find all product items
        product_items = soup.select('.product-info')
        logger.info(f"Found {len(product_items)} product items")

        for item in product_items:
            try:
                # Extract product name
                name_elem = item.select_one('.product__name h3')
                if not name_elem:
                    continue

                raw_name = name_elem.get_text(strip=True)

                # Filter only MacBooks
                if 'MacBook' not in raw_name:
                    continue

                model_name = self._parse_model_name(raw_name)

                # Extract price
                price_elem = item.select_one('.product__price--show')
                price_text = price_elem.get_text(strip=True) if price_elem else None
                price_vnd = self._clean_price(price_text)

                # Extract URL
                link_elem = item.select_one('a.product__link')
                url = link_elem.get('href') if link_elem else None
                if url and not url.startswith('http'):
                    url = self.base_url + url if url.startswith('/') else self.base_url + '/' + url

                # Get additional details from product page
                details = {}
                if url:
                    details = self._get_product_details(url)
                    time.sleep(1) # Polite delay

                # Add screen size to model name if not present
                if details.get('screen_size') and details['screen_size'].replace(' inch','') not in model_name:
                    model_name = f"{model_name} {details['screen_size'].replace(' inch','')}"

                # Extract image
                img_elem = item.select_one('.product__image img')
                image_url = img_elem.get('src') if img_elem else None

                # Parse specs using spec parser
                parsed_specs = self.spec_parser.parse(model_name)

                product = {
                    'model': model_name,
                    'raw_name': raw_name,
                    'price_vnd': price_vnd,
                    'price_text': price_text,
                    'url': url,
                    'image_url': image_url,
                    'shop': 'cellphones',
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
        logger.info("Starting CellphoneS scraper...")
        logger.info("="*80)

        all_products = []

        # All CellphoneS MacBook URLs
        pages = [
            {
                'name': 'All Mac',
                'url': 'https://cellphones.com.vn/laptop/mac.html'
            },
            {
                'name': 'MacBook Air',
                'url': 'https://cellphones.com.vn/laptop/mac/macbook-air.html'
            },
            {
                'name': 'MacBook Pro',
                'url': 'https://cellphones.com.vn/laptop/mac/macbook-pro.html'
            },
        ]

        seen_urls = set()  # Avoid duplicates

        for page_info in pages:
            logger.info(f"\nScraping {page_info['name']}...")
            html = self.scrape_page(page_info['url'])

            if html:
                products = self.parse_products(html)
                # Filter out duplicates based on product URL
                for product in products:
                    product_url = product.get('url')
                    if product_url and product_url not in seen_urls:
                        seen_urls.add(product_url)
                        all_products.append(product)
                logger.info(f"Found {len(products)} {page_info['name']} models ({len(all_products)} unique total)")
            else:
                logger.error(f"Failed to scrape {page_info['name']}")

            # Polite delay between pages
            time.sleep(3)

        logger.info("="*80)
        logger.info(f"CellphoneS scraping complete: {len(all_products)} total products")
        logger.info("="*80)

        return {
            'success': True,
            'shop': 'cellphones',
            'products': all_products,
            'count': len(all_products),
        }


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
