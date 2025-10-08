#!/usr/bin/env python3
"""
Scraper Manager - Runs all 4 scrapers and generates final output
"""

import json
import logging
from datetime import datetime
from scrapers.cellphones_scraper import CellphonesScraper
from scrapers.shopdunk_scraper import ShopDunkScraper
from scrapers.fptshop_scraper import FPTShopScraper
from scrapers.topzone_scraper import TopZoneScraper

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ScraperManager:
    def __init__(self):
        self.scrapers = {
            'cellphones': CellphonesScraper(),
            'shopdunk': ShopDunkScraper(),
            'fptshop': FPTShopScraper(),
            'topzone': TopZoneScraper(),
        }
        self.results = {}

    def run_all(self):
        """Run all scrapers sequentially"""
        logger.info("="*80)
        logger.info("STARTING ALL SCRAPERS")
        logger.info("="*80)
        start_time = datetime.now()

        # Run each scraper
        for shop_name, scraper in self.scrapers.items():
            try:
                logger.info(f"\n{'='*80}")
                logger.info(f"Running {shop_name.upper()} scraper...")
                logger.info(f"{'='*80}")

                result = scraper.scrape()
                self.results[shop_name] = result

                if result['success']:
                    logger.info(f"✅ {shop_name}: {result['count']} products scraped")
                else:
                    logger.error(f"❌ {shop_name}: Failed - {result.get('error', 'Unknown error')}")

            except Exception as e:
                logger.error(f"❌ {shop_name} crashed: {str(e)}")
                self.results[shop_name] = {
                    'success': False,
                    'shop': shop_name,
                    'error': str(e),
                    'products': [],
                    'count': 0,
                }

        duration = (datetime.now() - start_time).total_seconds()

        # Generate summary
        self._print_summary(duration)

        # Save results
        self._save_results()

    def _print_summary(self, duration):
        """Print final summary"""
        logger.info("\n" + "="*80)
        logger.info("SCRAPING SUMMARY")
        logger.info("="*80)

        total_products = 0
        successful_shops = 0

        for shop, result in self.results.items():
            status = "✅" if result['success'] else "❌"
            count = result['count']
            total_products += count
            if result['success']:
                successful_shops += 1

            logger.info(f"{status} {shop.upper()}: {count} products")

        logger.info("="*80)
        logger.info(f"Total Duration: {duration:.1f}s")
        logger.info(f"Success Rate: {successful_shops}/4 shops ({successful_shops/4*100:.0f}%)")
        logger.info(f"Total Products: {total_products}")
        logger.info("="*80)

    def _save_results(self):
        """Save all scraped data to JSON files"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

        # Save detailed results (with all data)
        detailed_file = f'output/scraped_data_{timestamp}.json'
        with open(detailed_file, 'w', encoding='utf-8') as f:
            output = {
                'timestamp': datetime.now().isoformat(),
                'summary': {
                    'total_products': sum(r['count'] for r in self.results.values()),
                    'successful_shops': sum(1 for r in self.results.values() if r['success']),
                    'failed_shops': sum(1 for r in self.results.values() if not r['success']),
                },
                'results': self.results,
            }
            json.dump(output, f, indent=2, ensure_ascii=False)

        logger.info(f"\n✅ Detailed results saved to: {detailed_file}")

        # Save consolidated products (easier to use)
        products_file = 'output/all_products.json'
        all_products = []

        for shop_name, result in self.results.items():
            if result['success']:
                all_products.extend(result['products'])

        with open(products_file, 'w', encoding='utf-8') as f:
            json.dump({
                'timestamp': datetime.now().isoformat(),
                'total_count': len(all_products),
                'products': all_products,
            }, f, indent=2, ensure_ascii=False)

        logger.info(f"✅ Consolidated products saved to: {products_file}")

        # Save summary report
        report_file = f'output/scraping_report_{timestamp}.txt'
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(f"Scraping Report - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("="*80 + "\n\n")

            for shop, result in self.results.items():
                f.write(f"{shop.upper()}:\n")
                f.write(f"  Status: {'SUCCESS' if result['success'] else 'FAILED'}\n")
                f.write(f"  Products: {result['count']}\n")
                if not result['success']:
                    f.write(f"  Error: {result.get('error', 'Unknown')}\n")
                f.write("\n")

                if result['products']:
                    f.write("  Sample products:\n")
                    for i, product in enumerate(result['products'][:5], 1):
                        f.write(f"    {i}. {product['model']}\n")
                        f.write(f"       Price: {product['price_text']}\n")
                    f.write("\n")

            f.write("="*80 + "\n")
            f.write(f"Total Products: {sum(r['count'] for r in self.results.values())}\n")
            f.write(f"Successful Shops: {sum(1 for r in self.results.values() if r['success'])}/4\n")

        logger.info(f"✅ Report saved to: {report_file}")


def main():
    print("\n" + "="*80)
    print("MacBook Price Scraper - All Shops")
    print("="*80 + "\n")

    manager = ScraperManager()
    manager.run_all()

    print("\n✅ All scrapers complete! Check the output/ directory for results.\n")


if __name__ == '__main__':
    main()
