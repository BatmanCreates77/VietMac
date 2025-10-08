#!/usr/bin/env python3
"""
Test scraper to verify what data we can extract from all 4 shops
for the missing MacBook models.
"""

import requests
from bs4 import BeautifulSoup
import json
import time
from urllib.parse import urljoin

class ShopTester:
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
        }
        self.results = {
            'fptshop': {'status': 'pending', 'models_found': 0, 'data_available': []},
            'shopdunk': {'status': 'pending', 'models_found': 0, 'data_available': []},
            'topzone': {'status': 'pending', 'models_found': 0, 'data_available': []},
            'cellphones': {'status': 'pending', 'models_found': 0, 'data_available': []},
        }

    def test_fptshop(self):
        """Test FPT Shop scraping capabilities"""
        print("\n" + "="*80)
        print("TESTING FPT SHOP")
        print("="*80)

        test_urls = [
            "https://fptshop.com.vn/may-tinh-xach-tay/apple-macbook",
            "https://fptshop.com.vn/may-tinh-xach-tay/macbook-air-m2-2022-13-inch",
            "https://fptshop.com.vn/may-tinh-xach-tay/macbook-air-m3-13-2024-8cpu-8gpu-8gb-256gb",
        ]

        for url in test_urls[:1]:  # Test first URL only for now
            try:
                print(f"\n📍 Testing: {url}")
                response = requests.get(url, headers=self.headers, timeout=10)

                if response.status_code == 200:
                    soup = BeautifulSoup(response.content, 'html.parser')

                    # Try different selectors
                    selectors_to_try = [
                        {'name': 'Product cards', 'selector': '.product-item', 'type': 'class'},
                        {'name': 'Product list', 'selector': '.product-list-item', 'type': 'class'},
                        {'name': 'MacBook items', 'selector': '[data-product]', 'type': 'attribute'},
                        {'name': 'Product container', 'selector': '.cdt-product', 'type': 'class'},
                        {'name': 'Product box', 'selector': '.product-box', 'type': 'class'},
                    ]

                    found_data = []
                    for selector_info in selectors_to_try:
                        if selector_info['type'] == 'class':
                            elements = soup.select(selector_info['selector'])
                        else:
                            elements = soup.find_all(attrs={'data-product': True})

                        if elements:
                            print(f"  ✅ Found {len(elements)} elements with '{selector_info['name']}'")

                            # Try to extract data from first element
                            if len(elements) > 0:
                                elem = elements[0]
                                sample_data = {
                                    'selector': selector_info['selector'],
                                    'html_sample': str(elem)[:500] + '...' if len(str(elem)) > 500 else str(elem),
                                }

                                # Try to find product name
                                name = (elem.find('h3') or elem.find('h4') or
                                       elem.find(class_='product-name') or
                                       elem.find(class_='title'))
                                if name:
                                    sample_data['name'] = name.get_text(strip=True)

                                # Try to find price
                                price = (elem.find(class_='price') or
                                        elem.find(class_='product-price') or
                                        elem.find('span', string=lambda t: t and '₫' in str(t)))
                                if price:
                                    sample_data['price'] = price.get_text(strip=True)

                                found_data.append(sample_data)
                        else:
                            print(f"  ❌ No elements found with '{selector_info['name']}'")

                    self.results['fptshop']['status'] = 'success' if found_data else 'no_data'
                    self.results['fptshop']['models_found'] = len(found_data)
                    self.results['fptshop']['data_available'] = found_data

                else:
                    print(f"  ❌ HTTP {response.status_code}")
                    self.results['fptshop']['status'] = f'http_error_{response.status_code}'

            except Exception as e:
                print(f"  ❌ Error: {str(e)}")
                self.results['fptshop']['status'] = f'error: {str(e)}'

    def test_shopdunk(self):
        """Test ShopDunk scraping capabilities"""
        print("\n" + "="*80)
        print("TESTING SHOPDUNK")
        print("="*80)

        test_urls = [
            "https://shopdunk.com/macbook",
            "https://shopdunk.com/macbook-air-m4-13-inch-10-core-gpu-16gb-ram-256gb-ssd",
        ]

        for url in test_urls[:1]:
            try:
                print(f"\n📍 Testing: {url}")
                response = requests.get(url, headers=self.headers, timeout=10)

                if response.status_code == 200:
                    soup = BeautifulSoup(response.content, 'html.parser')

                    selectors_to_try = [
                        {'name': 'Product item', 'selector': '.product-item', 'type': 'class'},
                        {'name': 'Product card', 'selector': '.product-card', 'type': 'class'},
                        {'name': 'Item product', 'selector': '.item-product', 'type': 'class'},
                        {'name': 'Product grid item', 'selector': '.product-grid-item', 'type': 'class'},
                        {'name': 'Card product', 'selector': '.card-product', 'type': 'class'},
                    ]

                    found_data = []
                    for selector_info in selectors_to_try:
                        elements = soup.select(selector_info['selector'])

                        if elements:
                            print(f"  ✅ Found {len(elements)} elements with '{selector_info['name']}'")

                            if len(elements) > 0:
                                elem = elements[0]
                                sample_data = {
                                    'selector': selector_info['selector'],
                                    'html_sample': str(elem)[:500] + '...' if len(str(elem)) > 500 else str(elem),
                                }

                                name = (elem.find('h3') or elem.find('h4') or
                                       elem.find(class_='product-name') or
                                       elem.find(class_='name'))
                                if name:
                                    sample_data['name'] = name.get_text(strip=True)

                                price = (elem.find(class_='price') or
                                        elem.find(class_='product-price') or
                                        elem.find('span', string=lambda t: t and '₫' in str(t)))
                                if price:
                                    sample_data['price'] = price.get_text(strip=True)

                                found_data.append(sample_data)
                        else:
                            print(f"  ❌ No elements found with '{selector_info['name']}'")

                    self.results['shopdunk']['status'] = 'success' if found_data else 'no_data'
                    self.results['shopdunk']['models_found'] = len(found_data)
                    self.results['shopdunk']['data_available'] = found_data

                else:
                    print(f"  ❌ HTTP {response.status_code}")
                    self.results['shopdunk']['status'] = f'http_error_{response.status_code}'

            except Exception as e:
                print(f"  ❌ Error: {str(e)}")
                self.results['shopdunk']['status'] = f'error: {str(e)}'

    def test_topzone(self):
        """Test TopZone scraping capabilities"""
        print("\n" + "="*80)
        print("TESTING TOPZONE")
        print("="*80)

        test_urls = [
            "https://www.topzone.vn/apple/macbook",
            "https://www.topzone.vn/macbook-air",
        ]

        for url in test_urls[:1]:
            try:
                print(f"\n📍 Testing: {url}")
                response = requests.get(url, headers=self.headers, timeout=10)

                if response.status_code == 200:
                    soup = BeautifulSoup(response.content, 'html.parser')

                    selectors_to_try = [
                        {'name': 'Product item', 'selector': '.product-item', 'type': 'class'},
                        {'name': 'Product card', 'selector': '.product-card', 'type': 'class'},
                        {'name': 'Product', 'selector': '.product', 'type': 'class'},
                        {'name': 'Item', 'selector': '.item', 'type': 'class'},
                    ]

                    found_data = []
                    for selector_info in selectors_to_try:
                        elements = soup.select(selector_info['selector'])

                        if elements:
                            print(f"  ✅ Found {len(elements)} elements with '{selector_info['name']}'")

                            if len(elements) > 0:
                                elem = elements[0]
                                sample_data = {
                                    'selector': selector_info['selector'],
                                    'html_sample': str(elem)[:500] + '...' if len(str(elem)) > 500 else str(elem),
                                }

                                name = (elem.find('h3') or elem.find('h4') or
                                       elem.find(class_='name'))
                                if name:
                                    sample_data['name'] = name.get_text(strip=True)

                                price = (elem.find(class_='price') or
                                        elem.find('span', string=lambda t: t and '₫' in str(t)))
                                if price:
                                    sample_data['price'] = price.get_text(strip=True)

                                found_data.append(sample_data)
                        else:
                            print(f"  ❌ No elements found with '{selector_info['name']}'")

                    self.results['topzone']['status'] = 'success' if found_data else 'no_data'
                    self.results['topzone']['models_found'] = len(found_data)
                    self.results['topzone']['data_available'] = found_data

                else:
                    print(f"  ❌ HTTP {response.status_code}")
                    self.results['topzone']['status'] = f'http_error_{response.status_code}'

            except Exception as e:
                print(f"  ❌ Error: {str(e)}")
                self.results['topzone']['status'] = f'error: {str(e)}'

    def test_cellphones(self):
        """Test CellphoneS scraping capabilities"""
        print("\n" + "="*80)
        print("TESTING CELLPHONES")
        print("="*80)

        test_urls = [
            "https://cellphones.com.vn/laptop/mac/macbook-pro.html",
            "https://cellphones.com.vn/laptop/mac/macbook-air.html",
        ]

        for url in test_urls[:1]:
            try:
                print(f"\n📍 Testing: {url}")
                response = requests.get(url, headers=self.headers, timeout=10)

                if response.status_code == 200:
                    soup = BeautifulSoup(response.content, 'html.parser')

                    selectors_to_try = [
                        {'name': 'Product item', 'selector': '.product-item', 'type': 'class'},
                        {'name': 'Product info', 'selector': '.product-info', 'type': 'class'},
                        {'name': 'Block product', 'selector': '.block-product', 'type': 'class'},
                        {'name': 'Item', 'selector': '.item', 'type': 'class'},
                    ]

                    found_data = []
                    for selector_info in selectors_to_try:
                        elements = soup.select(selector_info['selector'])

                        if elements:
                            print(f"  ✅ Found {len(elements)} elements with '{selector_info['name']}'")

                            if len(elements) > 0:
                                elem = elements[0]
                                sample_data = {
                                    'selector': selector_info['selector'],
                                    'html_sample': str(elem)[:500] + '...' if len(str(elem)) > 500 else str(elem),
                                }

                                name = (elem.find('h3') or elem.find('h4') or
                                       elem.find(class_='product-name'))
                                if name:
                                    sample_data['name'] = name.get_text(strip=True)

                                price = (elem.find(class_='price') or
                                        elem.find(class_='product-price') or
                                        elem.find('span', string=lambda t: t and '₫' in str(t)))
                                if price:
                                    sample_data['price'] = price.get_text(strip=True)

                                found_data.append(sample_data)
                        else:
                            print(f"  ❌ No elements found with '{selector_info['name']}'")

                    self.results['cellphones']['status'] = 'success' if found_data else 'no_data'
                    self.results['cellphones']['models_found'] = len(found_data)
                    self.results['cellphones']['data_available'] = found_data

                else:
                    print(f"  ❌ HTTP {response.status_code}")
                    self.results['cellphones']['status'] = f'http_error_{response.status_code}'

            except Exception as e:
                print(f"  ❌ Error: {str(e)}")
                self.results['cellphones']['status'] = f'error: {str(e)}'

    def save_results(self):
        """Save test results to JSON"""
        output_file = 'data/scraper_test_results.json'
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, indent=2, ensure_ascii=False)
        print(f"\n✅ Results saved to {output_file}")

    def print_summary(self):
        """Print summary of test results"""
        print("\n" + "="*80)
        print("SCRAPING TEST SUMMARY")
        print("="*80)

        for shop, data in self.results.items():
            print(f"\n{shop.upper()}:")
            print(f"  Status: {data['status']}")
            print(f"  Models Found: {data['models_found']}")
            print(f"  Extractable Data: {'YES' if data['data_available'] else 'NO'}")

            if data['data_available']:
                print(f"  Available Fields:")
                sample = data['data_available'][0]
                for key in sample.keys():
                    if key != 'html_sample':
                        print(f"    - {key}")

def main():
    print("🚀 Starting scraper capability test for all 4 shops...")
    print("This will test if we can extract MacBook data from each website.\n")

    tester = ShopTester()

    # Test each shop
    tester.test_fptshop()
    time.sleep(2)  # Polite delay

    tester.test_shopdunk()
    time.sleep(2)

    tester.test_topzone()
    time.sleep(2)

    tester.test_cellphones()

    # Print summary
    tester.print_summary()

    # Save results
    tester.save_results()

    print("\n✅ Test complete!")

if __name__ == '__main__':
    main()
