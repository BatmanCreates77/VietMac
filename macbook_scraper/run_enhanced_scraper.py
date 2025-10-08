#!/usr/bin/env python3
"""
Enhanced Scraper - Runs scrapers and adds parsed specs
"""

import json
import logging
from datetime import datetime
from scrapers.cellphones_scraper import CellphonesScraper
from scrapers.shopdunk_scraper import ShopDunkScraper
from utils.spec_parser import SpecParser

logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class EnhancedScraperManager:
    def __init__(self):
        self.scrapers = {
            'cellphones': CellphonesScraper(),
            'shopdunk': ShopDunkScraper(),
        }
        self.parser = SpecParser()
        self.results = {}

    def run_all(self):
        """Run all scrapers and enhance with parsed specs"""
        print("\n" + "="*80)
        print("Enhanced MacBook Scraper - With Spec Parsing")
        print("="*80 + "\n")

        all_products = []

        # Run scrapers
        for shop_name, scraper in self.scrapers.items():
            logger.info(f"Scraping {shop_name.upper()}...")
            result = scraper.scrape()
            self.results[shop_name] = result

            if result['success']:
                # Parse specs for each product
                for product in result['products']:
                    specs = self.parser.parse(product['model'])
                    product['specs'] = specs
                    all_products.append(product)

                logger.info(f"✅ {shop_name}: {result['count']} products")
            else:
                logger.error(f"❌ {shop_name}: Failed")

            print()

        # Summary
        print("="*80)
        print("SUMMARY")
        print("="*80)
        total = len(all_products)
        print(f"Total Products: {total}")
        print(f"Shops: {len([r for r in self.results.values() if r['success']])}/2")
        print("="*80)

        # Group by chip
        self._print_chip_summary(all_products)

        # Save enhanced data
        self._save_enhanced_data(all_products)

        return all_products

    def _print_chip_summary(self, products):
        """Print summary grouped by chip"""
        chip_groups = {}

        for p in products:
            chip = p['specs'].get('chip')
            variant = p['specs'].get('chip_variant')
            chip_key = f"{chip} {variant}" if variant else chip

            if chip_key not in chip_groups:
                chip_groups[chip_key] = []
            chip_groups[chip_key].append(p)

        print("\nProducts by Chip:")
        print("-"*80)
        # Sort with None values last
        sorted_chips = sorted(chip_groups.items(), key=lambda x: (x[0] is None, x[0] or ''))
        for chip, products_list in sorted_chips:
            if chip:
                print(f"{chip}: {len(products_list)} products")
            else:
                print(f"Unknown Chip: {len(products_list)} products")

    def _save_enhanced_data(self, products):
        """Save enhanced data with specs"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

        # Save full enhanced data
        output_file = f'output/enhanced_products_{timestamp}.json'
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump({
                'timestamp': datetime.now().isoformat(),
                'total_count': len(products),
                'products': products,
            }, f, indent=2, ensure_ascii=False)

        logger.info(f"\n✅ Enhanced data saved to: {output_file}")

        # Also save to latest
        latest_file = 'output/latest_products.json'
        with open(latest_file, 'w', encoding='utf-8') as f:
            json.dump({
                'timestamp': datetime.now().isoformat(),
                'total_count': len(products),
                'products': products,
            }, f, indent=2, ensure_ascii=False)

        logger.info(f"✅ Latest data saved to: {latest_file}")

        # Print sample enhanced product
        print("\n" + "="*80)
        print("Sample Enhanced Product:")
        print("="*80)
        if products:
            sample = products[0]
            print(json.dumps({
                'model': sample['model'],
                'shop': sample['shop'],
                'price_vnd': sample['price_vnd'],
                'specs': sample['specs'],
                'url': sample['url'][:70] + '...'
            }, indent=2, ensure_ascii=False))

        print("\n" + "="*80)
        print("✅ Scraping complete!")
        print("="*80 + "\n")


def main():
    manager = EnhancedScraperManager()
    manager.run_all()


if __name__ == '__main__':
    main()
