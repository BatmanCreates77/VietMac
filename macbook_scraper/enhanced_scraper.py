#!/usr/bin/env python3
"""
Enhanced scraper using Playwright for JavaScript-rendered content
and better anti-bot evasion.
"""

import json
import time
import re
from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup

class EnhancedMacBookScraper:
    def __init__(self):
        self.results = {
            'fptshop': [],
            'shopdunk': [],
            'topzone': [],
            'cellphones': [],
        }

    def clean_price(self, price_text):
        """Extract numeric price from text"""
        if not price_text:
            return None
        # Remove all non-numeric characters except digits
        cleaned = re.sub(r'[^\d]', '', price_text)
        return int(cleaned) if cleaned else None

    def scrape_fptshop(self, playwright):
        """Scrape FPT Shop using Playwright"""
        print("\n" + "="*80)
        print("SCRAPING FPT SHOP")
        print("="*80)

        try:
            browser = playwright.chromium.launch(headless=True)
            context = browser.new_context(
                user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
                viewport={'width': 1920, 'height': 1080}
            )
            page = context.new_page()

            url = "https://fptshop.com.vn/may-tinh-xach-tay/apple-macbook"
            print(f"📍 Navigating to: {url}")

            page.goto(url, wait_until='networkidle', timeout=30000)
            time.sleep(3)  # Wait for dynamic content

            # Try to scroll to load more products
            page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            time.sleep(2)

            content = page.content()
            soup = BeautifulSoup(content, 'html.parser')

            # Try multiple selectors
            product_selectors = [
                '.cdt-product',
                '.product-item',
                '[data-product]',
                '.product-card',
            ]

            products_found = []
            for selector in product_selectors:
                products = soup.select(selector)
                if products:
                    print(f"  ✅ Found {len(products)} products with selector: {selector}")

                    for product in products[:10]:  # Limit to first 10 for testing
                        data = {}

                        # Extract model name
                        name_elem = (product.find('h3') or
                                    product.find(class_='product-name') or
                                    product.find('a', {'title': True}))
                        if name_elem:
                            data['model'] = name_elem.get('title') or name_elem.get_text(strip=True)

                        # Extract price
                        price_elem = (product.find(class_='price') or
                                     product.find(class_='product-price') or
                                     product.find('span', string=re.compile(r'\d+[,.]?\d*')))
                        if price_elem:
                            price_text = price_elem.get_text(strip=True)
                            data['price_vnd'] = self.clean_price(price_text)
                            data['price_text'] = price_text

                        # Extract URL
                        link_elem = product.find('a', href=True)
                        if link_elem:
                            data['url'] = 'https://fptshop.com.vn' + link_elem['href'] if link_elem['href'].startswith('/') else link_elem['href']

                        if data.get('model'):
                            products_found.append(data)

                    break  # Stop after first successful selector

            self.results['fptshop'] = products_found
            print(f"  ✅ Extracted {len(products_found)} MacBook models")

            browser.close()

        except Exception as e:
            print(f"  ❌ Error: {str(e)}")
            self.results['fptshop'] = []

    def scrape_shopdunk(self, playwright):
        """Scrape ShopDunk using Playwright"""
        print("\n" + "="*80)
        print("SCRAPING SHOPDUNK")
        print("="*80)

        try:
            browser = playwright.chromium.launch(headless=True)
            context = browser.new_context(
                user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
                viewport={'width': 1920, 'height': 1080}
            )
            page = context.new_page()

            url = "https://shopdunk.com/macbook"
            print(f"📍 Navigating to: {url}")

            page.goto(url, wait_until='networkidle', timeout=30000)
            time.sleep(3)

            # Scroll to load more
            page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            time.sleep(2)

            content = page.content()
            soup = BeautifulSoup(content, 'html.parser')

            products = soup.select('.product-item')
            print(f"  ✅ Found {len(products)} products")

            products_found = []
            for product in products[:50]:  # Get more products
                data = {}

                # Extract model name
                name_elem = product.find('h3') or product.find(class_='product-name')
                if name_elem:
                    data['model'] = name_elem.get_text(strip=True)

                # Extract price - ShopDunk has special price structure
                price_elem = product.find(class_='special-price') or product.find(class_='price')
                if price_elem:
                    price_text = price_elem.get_text(strip=True)
                    data['price_vnd'] = self.clean_price(price_text)
                    data['price_text'] = price_text

                # Extract URL
                link_elem = product.find('a', href=True)
                if link_elem:
                    data['url'] = 'https://shopdunk.com' + link_elem['href'] if link_elem['href'].startswith('/') else link_elem['href']

                if data.get('model'):
                    products_found.append(data)

            self.results['shopdunk'] = products_found
            print(f"  ✅ Extracted {len(products_found)} MacBook models")

            browser.close()

        except Exception as e:
            print(f"  ❌ Error: {str(e)}")
            self.results['shopdunk'] = []

    def scrape_topzone(self, playwright):
        """Scrape TopZone using Playwright"""
        print("\n" + "="*80)
        print("SCRAPING TOPZONE")
        print("="*80)

        try:
            browser = playwright.chromium.launch(headless=True)
            context = browser.new_context(
                user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
                viewport={'width': 1920, 'height': 1080}
            )
            page = context.new_page()

            url = "https://www.topzone.vn/apple/macbook"
            print(f"📍 Navigating to: {url}")

            page.goto(url, wait_until='networkidle', timeout=30000)
            time.sleep(3)

            page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            time.sleep(2)

            content = page.content()
            soup = BeautifulSoup(content, 'html.parser')

            # Try multiple selectors
            product_selectors = ['.product-item', '.product-card', '.item', '.product']

            products_found = []
            for selector in product_selectors:
                products = soup.select(selector)
                if products:
                    print(f"  ✅ Found {len(products)} products with selector: {selector}")

                    for product in products[:50]:
                        data = {}

                        name_elem = product.find('h3') or product.find(class_='name')
                        if name_elem:
                            data['model'] = name_elem.get_text(strip=True)

                        price_elem = product.find(class_='price') or product.find(class_='product-price')
                        if price_elem:
                            price_text = price_elem.get_text(strip=True)
                            data['price_vnd'] = self.clean_price(price_text)
                            data['price_text'] = price_text

                        link_elem = product.find('a', href=True)
                        if link_elem:
                            data['url'] = 'https://www.topzone.vn' + link_elem['href'] if link_elem['href'].startswith('/') else link_elem['href']

                        if data.get('model'):
                            products_found.append(data)

                    break

            self.results['topzone'] = products_found
            print(f"  ✅ Extracted {len(products_found)} MacBook models")

            browser.close()

        except Exception as e:
            print(f"  ❌ Error: {str(e)}")
            self.results['topzone'] = []

    def scrape_cellphones(self, playwright):
        """Scrape CellphoneS using Playwright"""
        print("\n" + "="*80)
        print("SCRAPING CELLPHONES")
        print("="*80)

        try:
            browser = playwright.chromium.launch(headless=True)
            context = browser.new_context(
                user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
                viewport={'width': 1920, 'height': 1080}
            )
            page = context.new_page()

            # Test both MacBook Pro and Air pages
            urls = [
                "https://cellphones.com.vn/laptop/mac/macbook-pro.html",
                "https://cellphones.com.vn/laptop/mac/macbook-air.html",
            ]

            products_found = []

            for url in urls:
                print(f"📍 Navigating to: {url}")

                page.goto(url, wait_until='networkidle', timeout=30000)
                time.sleep(3)

                page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                time.sleep(2)

                content = page.content()
                soup = BeautifulSoup(content, 'html.parser')

                products = soup.select('.product-info')
                print(f"  ✅ Found {len(products)} products")

                for product in products:
                    data = {}

                    name_elem = product.find('h3') or product.find(class_='product__name')
                    if name_elem:
                        data['model'] = name_elem.get_text(strip=True)

                    price_elem = product.find(class_='product__price--show') or product.find(class_='price')
                    if price_elem:
                        price_text = price_elem.get_text(strip=True)
                        data['price_vnd'] = self.clean_price(price_text)
                        data['price_text'] = price_text

                    link_elem = product.find('a', href=True)
                    if link_elem:
                        data['url'] = link_elem['href']

                    if data.get('model') and 'MacBook' in data['model']:
                        products_found.append(data)

            self.results['cellphones'] = products_found
            print(f"  ✅ Extracted {len(products_found)} MacBook models total")

            browser.close()

        except Exception as e:
            print(f"  ❌ Error: {str(e)}")
            self.results['cellphones'] = []

    def save_results(self):
        """Save scraped results to JSON"""
        output_file = 'data/scraped_macbooks.json'
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, indent=2, ensure_ascii=False)
        print(f"\n✅ Results saved to {output_file}")

    def print_summary(self):
        """Print summary of scraped data"""
        print("\n" + "="*80)
        print("SCRAPING SUMMARY")
        print("="*80)

        total_models = 0
        for shop, products in self.results.items():
            count = len(products)
            total_models += count
            print(f"\n{shop.upper()}: {count} models")

            if products:
                # Show first 3 examples
                for i, product in enumerate(products[:3], 1):
                    print(f"  {i}. {product.get('model', 'Unknown')[:60]}")
                    if product.get('price_text'):
                        print(f"     Price: {product['price_text']}")

        print(f"\n📊 TOTAL: {total_models} MacBook models scraped across all shops")

    def run(self):
        """Run the scraper for all shops"""
        print("🚀 Starting enhanced MacBook scraper with Playwright...")
        print("This will scrape MacBook data from all 4 Vietnamese retailers.\n")

        with sync_playwright() as playwright:
            self.scrape_fptshop(playwright)
            time.sleep(3)  # Polite delay

            self.scrape_shopdunk(playwright)
            time.sleep(3)

            self.scrape_topzone(playwright)
            time.sleep(3)

            self.scrape_cellphones(playwright)

        self.print_summary()
        self.save_results()

        print("\n✅ Scraping complete!")

if __name__ == '__main__':
    scraper = EnhancedMacBookScraper()
    scraper.run()
