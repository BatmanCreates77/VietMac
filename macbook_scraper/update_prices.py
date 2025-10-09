#!/usr/bin/env python3
"""
Automated Price Update Script
Runs scrapers and updates the latest_products.json file for the Next.js API
"""
import json
import sys
import os
from datetime import datetime
from pathlib import Path

# Add scrapers directory to path
sys.path.insert(0, str(Path(__file__).parent))

from scrapers.cellphones_scraper import CellphonesScraper
from scrapers.shopdunk_scraper import ShopDunkScraper

# Optional: Try to import FPT and TopZone (may fail due to blocks)
try:
    from scrapers.fptshop_scraper import FPTShopScraper
    FPTSHOP_AVAILABLE = True
except:
    FPTSHOP_AVAILABLE = False

try:
    from scrapers.topzone_scraper import TopZoneScraper
    TOPZONE_AVAILABLE = False  # Disable by default due to timeouts
except:
    TOPZONE_AVAILABLE = False


class PriceUpdater:
    def __init__(self):
        self.output_dir = Path(__file__).parent / "output"
        self.output_dir.mkdir(exist_ok=True)

        self.results = {
            'timestamp': datetime.now().isoformat(),
            'products': [],
            'summary': {
                'total_products': 0,
                'by_shop': {},
                'errors': []
            }
        }

    def run_scraper(self, scraper_class, shop_name):
        """Run a scraper and collect results"""
        print(f"\n{'='*80}")
        print(f"Running {shop_name} scraper...")
        print(f"{'='*80}")

        try:
            scraper = scraper_class()
            result = scraper.scrape()

            if result.get('success') and result.get('products'):
                products = result['products']
                self.results['products'].extend(products)
                self.results['summary']['by_shop'][shop_name] = {
                    'count': len(products),
                    'success': True
                }
                print(f"✅ {shop_name}: Successfully scraped {len(products)} products")
                return True
            else:
                error_msg = result.get('error', 'Unknown error')
                self.results['summary']['errors'].append({
                    'shop': shop_name,
                    'error': error_msg
                })
                self.results['summary']['by_shop'][shop_name] = {
                    'count': 0,
                    'success': False,
                    'error': error_msg
                }
                print(f"❌ {shop_name}: Failed - {error_msg}")
                return False

        except Exception as e:
            error_msg = str(e)
            self.results['summary']['errors'].append({
                'shop': shop_name,
                'error': error_msg
            })
            self.results['summary']['by_shop'][shop_name] = {
                'count': 0,
                'success': False,
                'error': error_msg
            }
            print(f"❌ {shop_name}: Exception - {error_msg}")
            return False

    def save_results(self):
        """Save results to JSON files"""
        # Update total count
        self.results['summary']['total_products'] = len(self.results['products'])

        # Save to latest_products.json (used by Next.js API)
        latest_file = self.output_dir / "latest_products.json"
        with open(latest_file, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, indent=2, ensure_ascii=False)
        print(f"\n✅ Saved latest prices to: {latest_file}")

        # Also save timestamped backup
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_file = self.output_dir / f"products_{timestamp}.json"
        with open(backup_file, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, indent=2, ensure_ascii=False)
        print(f"✅ Saved backup to: {backup_file}")

    def print_summary(self):
        """Print execution summary"""
        print(f"\n{'='*80}")
        print("PRICE UPDATE SUMMARY")
        print(f"{'='*80}")
        print(f"Timestamp: {self.results['timestamp']}")
        print(f"Total Products: {self.results['summary']['total_products']}")
        print(f"\nBy Shop:")

        for shop, info in self.results['summary']['by_shop'].items():
            status = "✅" if info['success'] else "❌"
            print(f"  {status} {shop}: {info['count']} products")
            if not info['success']:
                print(f"     Error: {info.get('error', 'Unknown')}")

        if self.results['summary']['errors']:
            print(f"\n⚠️  Errors encountered: {len(self.results['summary']['errors'])}")

        print(f"{'='*80}\n")

    def run(self, include_all=False):
        """Run all scrapers and update prices"""
        print("\n🚀 Starting automated price update...")
        print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        # Always run the reliable scrapers
        self.run_scraper(CellphonesScraper, 'cellphones')
        self.run_scraper(ShopDunkScraper, 'shopdunk')

        # Optionally run FPT and TopZone (usually blocked)
        if include_all:
            if FPTSHOP_AVAILABLE:
                print("\n⚠️  Warning: FPTShop usually gets blocked by Cloudflare")
                self.run_scraper(FPTShopScraper, 'fptshop')

            if TOPZONE_AVAILABLE:
                print("\n⚠️  Warning: TopZone usually times out")
                self.run_scraper(TopZoneScraper, 'topzone')

        # Save results
        self.save_results()

        # Print summary
        self.print_summary()

        # Return success if we got at least some products
        success = self.results['summary']['total_products'] > 0
        print(f"{'✅ Update completed successfully!' if success else '❌ Update failed - no products scraped'}\n")

        return 0 if success else 1


def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(description='Update MacBook prices from Vietnamese retailers')
    parser.add_argument('--all', action='store_true',
                       help='Include FPTShop and TopZone (usually blocked/timeout)')
    parser.add_argument('--quiet', action='store_true',
                       help='Minimal output')

    args = parser.parse_args()

    # Redirect output if quiet mode
    if args.quiet:
        sys.stdout = open(os.devnull, 'w')

    updater = PriceUpdater()
    exit_code = updater.run(include_all=args.all)

    sys.exit(exit_code)


if __name__ == '__main__':
    main()
