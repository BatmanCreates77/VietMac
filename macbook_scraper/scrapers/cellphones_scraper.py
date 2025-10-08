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

                # Extract image
                img_elem = item.select_one('.product__image img')
                image_url = img_elem.get('src') if img_elem else None

                product = {
                    'model': model_name,
                    'raw_name': raw_name,
                    'price_vnd': price_vnd,
                    'price_text': price_text,
                    'url': url,
                    'image_url': image_url,
                    'shop': 'cellphones',
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

        # Pages to scrape
        pages = [
            {
                'name': 'MacBook Pro',
                'url': 'https://cellphones.com.vn/laptop/mac/macbook-pro.html'
            },
            {
                'name': 'MacBook Air',
                'url': 'https://cellphones.com.vn/laptop/mac/macbook-air.html'
            },
        ]

        for page_info in pages:
            logger.info(f"\nScraping {page_info['name']}...")
            html = self.scrape_page(page_info['url'])

            if html:
                products = self.parse_products(html)
                all_products.extend(products)
                logger.info(f"Found {len(products)} {page_info['name']} models")
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
