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


# Absolute per-shop floors, set from fresh live scrape runs on 2026-09-12,
# with headroom for normal listing fluctuation. Derived from those fresh
# runs, NOT from the previously-committed latest_products.json — that file
# had already shipped a silent partial failure (cellphones=3), so it can't
# be trusted as a floor source.
#   cellphones=17, shopdunk=23 — Phase 0 baseline run
#   fptshop=51 across all 5 pages — Phase 5 run, after fixing the
#     challenge-wait logic and stale selectors (see fptshop_scraper.py)
# topzone has no confirmed-good live run yet (still timeout-blocked);
# its floor is a conservative placeholder pending its own fix.
MIN_PRODUCTS_PER_SHOP = {
    'cellphones': 8,
    'shopdunk': 10,
    'fptshop': 20,
    'topzone': 3,
}

# Reject a shop's new count if it dropped more than this fraction versus its
# own last-known-good count, even if it still clears the absolute floor above.
MAX_DROP_RATIO = 0.4

# The relative-drop check is skipped when the previous latest_products.json
# is older than this — comparing against data this old isn't "did something
# just break," it's "did the site's real listings change over months,"
# which the absolute floor is the right tool for, not a drop-ratio built
# for catching regressions between adjacent runs.
STALE_THRESHOLD_HOURS = 24

REQUIRED_PRODUCT_FIELDS = ('model', 'price_vnd', 'shop')

BACKUP_RETENTION_COUNT = 10


class ValidationFailure(Exception):
    def __init__(self, reasons):
        self.reasons = reasons
        super().__init__('; '.join(reasons))


class PriceUpdater:
    def __init__(self, output_dir=None):
        # output_dir is injectable so tests can point it at a tmp directory
        # instead of macbook_scraper/output/ — the validation-gate tests
        # need to write/read latest_products.json without touching
        # production data.
        self.output_dir = Path(output_dir) if output_dir else Path(__file__).parent / "output"
        self.output_dir.mkdir(exist_ok=True)
        self.failed_dir = self.output_dir / "failed"

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

    def _load_previous_summary(self):
        """Read the currently-live latest_products.json's per-shop counts
        and timestamp. Returns ({}, None) if the file doesn't exist or is
        unreadable."""
        latest_file = self.output_dir / "latest_products.json"
        if not latest_file.exists():
            return {}, None
        try:
            with open(latest_file, 'r', encoding='utf-8') as f:
                previous = json.load(f)
            by_shop = previous.get('summary', {}).get('by_shop', {})
            timestamp_str = previous.get('timestamp')
            return by_shop, timestamp_str
        except (json.JSONDecodeError, OSError):
            return {}, None

    def _is_previous_data_stale(self, timestamp_str):
        """The relative-drop check only makes sense when 'last-known-good'
        is actually recent — it exists to catch a sudden regression
        between nearby runs (e.g. a broken selector), not to compare
        against data from long before this scraper was even running
        reliably. If the previous run is older than STALE_THRESHOLD_HOURS,
        its counts are not a trustworthy drop-comparison baseline (the
        site's real listings can easily have shifted that much on their
        own), so the drop check is skipped for this run — the absolute
        floor and required-field checks still apply regardless."""
        if not timestamp_str:
            return True
        try:
            previous_time = datetime.fromisoformat(timestamp_str)
        except ValueError:
            return True
        age_hours = (datetime.now() - previous_time).total_seconds() / 3600
        return age_hours > STALE_THRESHOLD_HOURS

    def validate_results(self):
        """Gate checked before every write to latest_products.json. Returns
        a list of failure reasons (empty list = passed). Runs per shop that
        reported success this run:
          1. required fields non-null on every product
          2. count clears the absolute floor (MIN_PRODUCTS_PER_SHOP)
          3. count hasn't dropped more than MAX_DROP_RATIO vs last-known-good
             — skipped entirely if that last-known-good is stale (see
             _is_previous_data_stale): comparing against months-old data
             produces false rejections, not real regression detection.
        A shop that failed to scrape (success=False) is not re-penalized
        here — run_scraper() already recorded that as an error; this gate
        only exists to catch a *silent* partial failure that still reported
        success=True.
        """
        reasons = []
        previous_summary, previous_timestamp = self._load_previous_summary()
        skip_drop_check = self._is_previous_data_stale(previous_timestamp)
        if skip_drop_check and previous_timestamp:
            print(f"   (skipping relative-drop check — last-known-good is from "
                  f"{previous_timestamp}, older than {STALE_THRESHOLD_HOURS}h)")

        products_by_shop = {}
        for product in self.results['products']:
            products_by_shop.setdefault(product.get('shop'), []).append(product)

        for shop, info in self.results['summary']['by_shop'].items():
            if not info.get('success'):
                continue

            count = info.get('count', 0)

            for product in products_by_shop.get(shop, []):
                missing = [f for f in REQUIRED_PRODUCT_FIELDS if not product.get(f)]
                if missing:
                    reasons.append(
                        f"{shop}: product missing required field(s) {missing} "
                        f"(url={product.get('url')})"
                    )
                    break  # one bad product is enough to flag this shop

            floor = MIN_PRODUCTS_PER_SHOP.get(shop, 1)
            if count < floor:
                reasons.append(
                    f"{shop}: count {count} is below the absolute floor of {floor}"
                )

            if not skip_drop_check:
                previous_count = previous_summary.get(shop, {}).get('count', 0)
                if previous_count > 0:
                    drop_ratio = 1 - (count / previous_count)
                    if drop_ratio > MAX_DROP_RATIO:
                        reasons.append(
                            f"{shop}: count dropped {drop_ratio:.0%} vs last-known-good "
                            f"({previous_count} -> {count}), exceeds {MAX_DROP_RATIO:.0%} threshold"
                        )

        return reasons

    def save_results(self):
        """Validate, then save results to JSON files. Refuses to overwrite
        latest_products.json if validation fails — the site keeps serving
        the last-known-good data instead of a silently gutted or malformed
        one, and the rejected attempt is written to output/failed/ for
        debugging."""
        self.results['summary']['total_products'] = len(self.results['products'])

        failure_reasons = self.validate_results()
        if failure_reasons:
            self.failed_dir.mkdir(exist_ok=True)
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            failed_file = self.failed_dir / f"rejected_{timestamp}.json"
            with open(failed_file, 'w', encoding='utf-8') as f:
                json.dump({**self.results, 'validation_failures': failure_reasons},
                          f, indent=2, ensure_ascii=False)

            print(f"\n❌ Validation gate REJECTED this run — latest_products.json left unchanged")
            for reason in failure_reasons:
                print(f"   - {reason}")
            print(f"   Rejected attempt saved to: {failed_file}")
            raise ValidationFailure(failure_reasons)

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

        self._apply_backup_retention()

    def _apply_backup_retention(self):
        """Keep only the most recent BACKUP_RETENTION_COUNT timestamped
        backups; delete older ones so output/ doesn't grow unbounded."""
        backups = sorted(self.output_dir.glob("products_*.json"))
        stale = backups[:-BACKUP_RETENTION_COUNT] if len(backups) > BACKUP_RETENTION_COUNT else []
        for old_backup in stale:
            old_backup.unlink()
        if stale:
            print(f"   Pruned {len(stale)} old backup(s), kept most recent {BACKUP_RETENTION_COUNT}")

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

        # FPTShop: fixed 2026-09-12 (see fptshop_scraper.py) — the challenge-
        # wait logic was declaring a still-resolving Cloudflare challenge a
        # hard failure, and the selectors were stale after a site redesign.
        # Verified live: 51/51 products across all 5 pages, first page did
        # one browser solve (~5s), the other 4 reused the cached session.
        # No longer gated behind --all.
        if FPTSHOP_AVAILABLE:
            self.run_scraper(FPTShopScraper, 'fptshop')

        # TopZone: still gated behind --all, not yet fixed (Phase 5 continues).
        if include_all:
            if TOPZONE_AVAILABLE:
                print("\n⚠️  Warning: TopZone usually times out")
                self.run_scraper(TopZoneScraper, 'topzone')

        # Validate + save results. A ValidationFailure means the gate
        # rejected the write on purpose (see save_results/validate_results)
        # — latest_products.json was left untouched on last-known-good.
        try:
            self.save_results()
        except ValidationFailure:
            self.print_summary()
            print("❌ Update rejected by validation gate — see reasons above.\n")
            return 1

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
