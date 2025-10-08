#!/usr/bin/env python3
"""
Quick Test - Run only the working scrapers (CellphoneS + ShopDunk)
"""

import json
import logging
from datetime import datetime
from scrapers.cellphones_scraper import CellphonesScraper
from scrapers.shopdunk_scraper import ShopDunkScraper

logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    print("\n" + "="*80)
    print("Running Working Scrapers: CellphoneS + ShopDunk")
    print("="*80 + "\n")

    results = {}

    # 1. CellphoneS (Simple HTTP - always works)
    logger.info("Starting CellphoneS scraper...")
    cellphones = CellphonesScraper()
    results['cellphones'] = cellphones.scrape()

    print("\n" + "="*80 + "\n")

    # 2. ShopDunk (Playwright - works well)
    logger.info("Starting ShopDunk scraper...")
    shopdunk = ShopDunkScraper()
    results['shopdunk'] = shopdunk.scrape()

    # Summary
    print("\n" + "="*80)
    print("SUMMARY")
    print("="*80)

    total = 0
    for shop, result in results.items():
        count = result['count']
        total += count
        print(f"✅ {shop.upper()}: {count} products")

    print(f"\n📊 TOTAL: {total} products from 2 shops")
    print("="*80)

    # Save consolidated output
    all_products = []
    for result in results.values():
        if result['success']:
            all_products.extend(result['products'])

    output_file = 'output/scraped_products.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump({
            'timestamp': datetime.now().isoformat(),
            'total_count': len(all_products),
            'shops': ['cellphones', 'shopdunk'],
            'products': all_products,
        }, f, indent=2, ensure_ascii=False)

    print(f"\n✅ Results saved to: {output_file}")

    # Print sample products
    print(f"\n📦 Sample products (first 10):")
    print("="*80)
    for i, p in enumerate(all_products[:10], 1):
        print(f"\n{i}. {p['model']}")
        print(f"   Shop: {p['shop'].upper()}")
        print(f"   Price: {p['price_text']}")
        print(f"   URL: {p['url'][:70]}...")

    print("\n" + "="*80)
    print("✅ Scraping complete!")
    print("="*80 + "\n")


if __name__ == '__main__':
    main()
