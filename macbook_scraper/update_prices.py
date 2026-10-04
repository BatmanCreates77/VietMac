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

from scrapers.cellphones_scraper import CellphonesScraper, CellphonesIphoneScraper
from scrapers.shopdunk_scraper import ShopDunkScraper, ShopDunkIphoneScraper

# Optional: Try to import FPT and TopZone (may fail due to blocks)
try:
    from scrapers.fptshop_scraper import FPTShopScraper, FPTShopIphoneScraper
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
# iPhone sources (2026-10-02 live run, about a third of each count):
#   cellphones-iphone=34, shopdunk-iphone=37, fptshop-iphone=12 models
# Keyed by source (see BaseScraper.source): each shop's Macs and iPhones
# are validated, published and carried forward independently.
MIN_PRODUCTS_PER_SHOP = {
    'cellphones': 8,
    'shopdunk': 10,
    'fptshop': 20,
    'topzone': 3,
    'cellphones-iphone': 10,
    'shopdunk-iphone': 10,
    'fptshop-iphone': 10,
}

# Reject a shop's new count if it dropped more than this fraction versus its
# own last-known-good count, even if it still clears the absolute floor above.
MAX_DROP_RATIO = 0.4

# The relative-drop check is skipped when the previous latest_products.json
# is older than this — comparing against data this old isn't "did something
# just break," it's "did the site's real listings change over months,"
# which the absolute floor is the right tool for, not a drop-ratio built
# for catching regressions between adjacent runs.
# Scrapes run every other day (auto-update-prices.sh), so the previous
# shop data is normally ~48h old and must still count as recent here.
STALE_THRESHOLD_HOURS = 72

REQUIRED_PRODUCT_FIELDS = ('model', 'price_vnd', 'shop')


def source_of(product):
    """Validation unit a product belongs to. Products written before iPhones
    were added have no 'source'; they are all Macs, keyed by shop."""
    return product.get('source') or product.get('shop')

# A few listings with no price (out of stock, "contact for price") are normal
# and get dropped individually. Above this fraction it's a broken selector,
# not a few odd listings, and the shop's whole run is rejected. Calibrated
# against two real cases: 1/16 unpriced (2026-10-01, a genuinely unpriced
# listing) must pass; 4/17 (2026-09-19, an encoding bug) must not.
MAX_INCOMPLETE_RATIO = 0.2

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

    def _load_previous(self):
        """The currently-live latest_products.json, or None if absent or
        unreadable. This is both the last-known-good baseline for the drop
        check and the source of carried-forward data for failed shops."""
        latest_file = self.output_dir / "latest_products.json"
        if not latest_file.exists():
            return None
        try:
            with open(latest_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            return None

    @staticmethod
    def _is_stale(timestamp_str):
        """The relative-drop check exists to catch a sudden regression
        between nearby runs (a broken selector), not to compare against
        data from long ago — real listings shift that much on their own.
        Checked per shop, since a carried-forward shop can be much older
        than the file it sits in."""
        if not timestamp_str:
            return True
        try:
            previous_time = datetime.fromisoformat(timestamp_str)
        except ValueError:
            return True
        age_hours = (datetime.now() - previous_time).total_seconds() / 3600
        return age_hours > STALE_THRESHOLD_HOURS

    def _validate_shop(self, shop, fresh_products, previous_count, previous_scraped_at):
        """Returns (accepted_products, rejection_reason, skipped_urls).
        rejection_reason is None when the shop's fresh data is accepted."""
        incomplete_ids = {
            id(p) for p in fresh_products
            if any(not p.get(f) for f in REQUIRED_PRODUCT_FIELDS)
        }
        if fresh_products and len(incomplete_ids) / len(fresh_products) > MAX_INCOMPLETE_RATIO:
            return [], (
                f"{len(incomplete_ids)}/{len(fresh_products)} products missing required "
                f"fields {list(REQUIRED_PRODUCT_FIELDS)} — exceeds "
                f"{MAX_INCOMPLETE_RATIO:.0%}, looks like broken parsing"
            ), []

        accepted = [p for p in fresh_products if id(p) not in incomplete_ids]
        skipped = [p.get('url') for p in fresh_products if id(p) in incomplete_ids]

        floor = MIN_PRODUCTS_PER_SHOP.get(shop, 1)
        if len(accepted) < floor:
            return [], f"count {len(accepted)} is below the absolute floor of {floor}", []

        if previous_count > 0 and not self._is_stale(previous_scraped_at):
            drop_ratio = 1 - (len(accepted) / previous_count)
            if drop_ratio > MAX_DROP_RATIO:
                return [], (
                    f"count dropped {drop_ratio:.0%} vs last-known-good "
                    f"({previous_count} -> {len(accepted)}), exceeds {MAX_DROP_RATIO:.0%} threshold"
                ), []

        return accepted, None, skipped

    def _write_failed_attempt(self, reasons):
        self.failed_dir.mkdir(exist_ok=True)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        failed_file = self.failed_dir / f"rejected_{timestamp}.json"
        with open(failed_file, 'w', encoding='utf-8') as f:
            json.dump({**self.results, 'validation_failures': reasons},
                      f, indent=2, ensure_ascii=False)
        return failed_file

    def save_results(self):
        """Validate each shop independently, then write latest_products.json.

        A shop whose fresh data is accepted replaces its previous data. A
        shop that failed to scrape, or whose data fails validation, keeps
        its last-known-good products, marked stale — one flaky shop must
        never wipe its listings off the site (this happened 2026-10-01
        06:00: FPTShop failed and the old all-shops-or-nothing gate
        published a file with zero FPTShop products). The write is only
        refused outright (ValidationFailure, file untouched) when no shop
        produced acceptable fresh data at all."""
        previous = self._load_previous() or {}
        previous_timestamp = previous.get('timestamp')
        previous_summary = previous.get('summary', {}).get('by_shop', {})
        previous_by_shop = {}
        for product in previous.get('products', []):
            previous_by_shop.setdefault(source_of(product), []).append(product)

        fresh_by_shop = {}
        for product in self.results['products']:
            fresh_by_shop.setdefault(source_of(product), []).append(product)

        attempted = self.results['summary']['by_shop']
        run_timestamp = self.results['timestamp']
        shops = list(attempted) + [s for s in previous_summary if s not in attempted]

        final_products, final_summary, rejections = [], {}, []
        for shop in shops:
            info = attempted.get(shop)
            previous_info = previous_summary.get(shop, {})
            previous_scraped_at = previous_info.get('scraped_at') or previous_timestamp

            if info is None:
                reason = 'not run this time'
            elif not info.get('success'):
                reason = info.get('error', 'scrape failed')
            else:
                accepted, reason, skipped = self._validate_shop(
                    shop, fresh_by_shop.get(shop, []),
                    previous_info.get('count', 0), previous_scraped_at,
                )

            if reason is None:
                for p in accepted:
                    p['scraped_at'] = run_timestamp
                    p['stale'] = False
                final_products += accepted
                final_summary[shop] = {
                    'count': len(accepted), 'success': True,
                    'status': 'fresh', 'scraped_at': run_timestamp,
                }
                if skipped:
                    final_summary[shop]['skipped_incomplete'] = skipped
                    print(f"   ⚠️  {shop}: dropped {len(skipped)} listing(s) with missing fields: {skipped}")
                continue

            carried = previous_by_shop.get(shop, [])
            if info is None and not carried:
                continue
            if info is not None:
                rejections.append(f"{shop}: {reason}")
            for p in carried:
                p.setdefault('scraped_at', previous_scraped_at)
                p['stale'] = True
            final_products += carried
            final_summary[shop] = {
                'count': len(carried), 'success': False,
                'status': 'carried_forward' if carried else 'missing',
                'scraped_at': previous_scraped_at if carried else None,
                'error': reason,
            }

        if not any(s['status'] == 'fresh' for s in final_summary.values()):
            reasons = rejections or ['no shop produced fresh data']
            failed_file = self._write_failed_attempt(reasons)
            print(f"\n❌ Validation gate REJECTED this run — no shop produced acceptable fresh data")
            for r in reasons:
                print(f"   - {r}")
            print(f"   latest_products.json left unchanged. Attempt saved to: {failed_file}")
            raise ValidationFailure(reasons)

        if rejections:
            failed_file = self._write_failed_attempt(rejections)
            print(f"\n⚠️  Partial update — these shops keep their last-known-good data:")
            for r in rejections:
                print(f"   - {r}")
            print(f"   Rejected attempt saved to: {failed_file}")

        self.results['products'] = final_products
        self.results['summary']['by_shop'] = final_summary
        self.results['summary']['total_products'] = len(final_products)

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

    def update_india_prices(self):
        try:
            from india_prices import IndiaPriceUpdater
            result = IndiaPriceUpdater(self.output_dir).run()
            statuses = ", ".join(f"{name}: {source['status']}" for name, source in result["sources"].items())
            print(f"🇮🇳 India prices: {len(result['products'])} model/storage prices ({statuses})")
        except Exception as e:
            print(f"⚠️  India prices not updated: {e}")

    def print_summary(self):
        """Print execution summary"""
        print(f"\n{'='*80}")
        print("PRICE UPDATE SUMMARY")
        print(f"{'='*80}")
        print(f"Timestamp: {self.results['timestamp']}")
        print(f"Total Products: {self.results['summary']['total_products']}")
        print(f"\nBy Shop:")

        icons = {'fresh': '✅', 'carried_forward': '⚠️ ', 'missing': '❌'}
        for shop, info in self.results['summary']['by_shop'].items():
            status = info.get('status', 'fresh' if info['success'] else 'missing')
            print(f"  {icons.get(status, '❌')} {shop}: {info['count']} products ({status})")
            if not info['success']:
                print(f"     Error: {info.get('error', 'Unknown')}")

        if self.results['summary']['errors']:
            print(f"\n⚠️  Errors encountered: {len(self.results['summary']['errors'])}")

        print(f"{'='*80}\n")

    def run(self, include_all=False):
        """Run all scrapers and update prices"""
        print("\n🚀 Starting automated price update...")
        print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        # Always run the reliable scrapers. Names are validation sources
        # (BaseScraper.source): a shop's Macs and iPhones are separate units.
        self.run_scraper(CellphonesScraper, 'cellphones')
        self.run_scraper(ShopDunkScraper, 'shopdunk')
        self.run_scraper(CellphonesIphoneScraper, 'cellphones-iphone')
        self.run_scraper(ShopDunkIphoneScraper, 'shopdunk-iphone')

        # FPTShop: fixed 2026-09-12 (see fptshop_scraper.py) — the challenge-
        # wait logic was declaring a still-resolving Cloudflare challenge a
        # hard failure, and the selectors were stale after a site redesign.
        # Verified live: 51/51 products across all 5 pages, first page did
        # one browser solve (~5s), the other 4 reused the cached session.
        # No longer gated behind --all.
        if FPTSHOP_AVAILABLE:
            self.run_scraper(FPTShopScraper, 'fptshop')
            self.run_scraper(FPTShopIphoneScraper, 'fptshop-iphone')

        # TopZone: still gated behind --all, not yet fixed (Phase 5 continues).
        if include_all:
            if TOPZONE_AVAILABLE:
                print("\n⚠️  Warning: TopZone usually times out")
                self.run_scraper(TopZoneScraper, 'topzone')

        # Indian prices for the "cheaper than India" comparison. Separate
        # file, own safeguards, and it can never fail the Vietnam update.
        self.update_india_prices()

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

    parser = argparse.ArgumentParser(description='Update Mac and iPhone prices from Vietnamese retailers')
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
