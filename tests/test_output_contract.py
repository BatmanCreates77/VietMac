"""
Milestone 3 gate: the validation gate in update_prices.py's save_results()
must block a bad write from ever reaching latest_products.json, and must
leave last-known-good data in place when it does. Run:

    pytest tests/test_output_contract.py -v

Every test uses an isolated tmp_path output_dir — never touches
macbook_scraper/output/ (production data).
"""
import json
import sys
from datetime import datetime, timedelta
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(REPO_ROOT / "macbook_scraper"))

from update_prices import (
    PriceUpdater, ValidationFailure, MIN_PRODUCTS_PER_SHOP, MAX_DROP_RATIO,
    STALE_THRESHOLD_HOURS,
)


def make_product(shop, model="MacBook Air M5", price_vnd=25000000, url="https://example.com/p1"):
    return {
        'model': model,
        'raw_name': model,
        'price_vnd': price_vnd,
        'price_text': f"{price_vnd:,} VND",
        'url': url,
        'image_url': None,
        'shop': shop,
        'specs': {},
        'product_id': '1',
        'clean_name': model,
    }


def seed_previous(output_dir, by_shop_counts, timestamp=None):
    """Write a pre-existing latest_products.json, simulating last-known-good.
    Defaults to "just now" so the relative-drop check actually runs in tests
    that exercise it — pass an explicit old `timestamp` to test staleness."""
    products = []
    summary_by_shop = {}
    for shop, count in by_shop_counts.items():
        for i in range(count):
            products.append(make_product(shop, url=f"https://example.com/{shop}/{i}"))
        summary_by_shop[shop] = {'count': count, 'success': True}

    payload = {
        'timestamp': timestamp or datetime.now().isoformat(),
        'products': products,
        'summary': {'total_products': len(products), 'by_shop': summary_by_shop, 'errors': []},
    }
    (output_dir / "latest_products.json").write_text(json.dumps(payload), encoding='utf-8')
    return payload


def make_updater_with_results(output_dir, by_shop_counts, price_vnd=25000000, missing_field=None):
    updater = PriceUpdater(output_dir=output_dir)
    products = []
    for shop, count in by_shop_counts.items():
        for i in range(count):
            p = make_product(shop, price_vnd=price_vnd, url=f"https://example.com/{shop}/new/{i}")
            if missing_field:
                p[missing_field] = None
            products.append(p)
        updater.results['summary']['by_shop'][shop] = {'count': count, 'success': True}
    updater.results['products'] = products
    return updater


def test_well_formed_run_writes_through(tmp_path):
    """No prior file, counts clear the absolute floor -> should pass and write."""
    floor = MIN_PRODUCTS_PER_SHOP['shopdunk']
    updater = make_updater_with_results(tmp_path, {'shopdunk': floor + 5})

    updater.save_results()  # must not raise

    latest = json.loads((tmp_path / "latest_products.json").read_text())
    assert latest['summary']['total_products'] == floor + 5
    assert not (tmp_path / "failed").exists() or not list((tmp_path / "failed").glob("*.json"))


def test_zero_products_rejected(tmp_path):
    """A shop reporting success=True with 0 products (the historical bug
    shape) must be rejected, not written."""
    updater = make_updater_with_results(tmp_path, {'shopdunk': 0})

    with pytest.raises(ValidationFailure):
        updater.save_results()

    assert not (tmp_path / "latest_products.json").exists()
    failed_files = list((tmp_path / "failed").glob("rejected_*.json"))
    assert len(failed_files) == 1
    failed_content = json.loads(failed_files[0].read_text())
    assert any('floor' in r for r in failed_content['validation_failures'])


def test_below_absolute_floor_rejected(tmp_path):
    """Below-floor but non-zero count (the 'partial failure' shape, e.g.
    4 products instead of ~40) must also be rejected."""
    floor = MIN_PRODUCTS_PER_SHOP['cellphones']
    updater = make_updater_with_results(tmp_path, {'cellphones': floor - 1})

    with pytest.raises(ValidationFailure):
        updater.save_results()

    assert not (tmp_path / "latest_products.json").exists()


def test_relative_drop_rejected_even_above_floor(tmp_path):
    """A count that clears the absolute floor but dropped more than
    MAX_DROP_RATIO vs last-known-good must still be rejected."""
    seed_previous(tmp_path, {'shopdunk': 30})
    floor = MIN_PRODUCTS_PER_SHOP['shopdunk']
    new_count = floor + 2  # clears the floor
    assert (1 - new_count / 30) > MAX_DROP_RATIO, "test setup must exceed the drop threshold"

    updater = make_updater_with_results(tmp_path, {'shopdunk': new_count})

    with pytest.raises(ValidationFailure):
        updater.save_results()

    # last-known-good must be untouched
    latest = json.loads((tmp_path / "latest_products.json").read_text())
    assert latest['summary']['by_shop']['shopdunk']['count'] == 30


def test_missing_required_field_rejected(tmp_path):
    """A product missing model/price_vnd/shop must fail validation even if
    the count looks fine."""
    floor = MIN_PRODUCTS_PER_SHOP['shopdunk']
    updater = make_updater_with_results(tmp_path, {'shopdunk': floor + 5}, missing_field='price_vnd')

    with pytest.raises(ValidationFailure):
        updater.save_results()

    assert not (tmp_path / "latest_products.json").exists()


def test_normal_drop_within_threshold_passes(tmp_path):
    """A small, normal fluctuation (e.g. one delisted product) must NOT be
    treated as a failure — the gate should not be overly strict."""
    seed_previous(tmp_path, {'shopdunk': 20})
    new_count = 18  # 10% drop, well under MAX_DROP_RATIO

    updater = make_updater_with_results(tmp_path, {'shopdunk': new_count})
    updater.save_results()  # must not raise

    latest = json.loads((tmp_path / "latest_products.json").read_text())
    assert latest['summary']['by_shop']['shopdunk']['count'] == new_count


def test_stale_previous_data_skips_drop_check(tmp_path):
    """Real scenario hit during Phase 5: production had been stale for
    months, so the committed latest_products.json's counts (e.g. shopdunk
    47 from a redesign-era listing) don't reflect current reality (23,
    reproduced across multiple fresh live runs) — comparing against them
    would reject every legitimate run indefinitely. Old last-known-good
    data must not trigger the relative-drop check; the absolute floor
    still applies."""
    old_timestamp = (datetime.now() - timedelta(hours=STALE_THRESHOLD_HOURS + 1)).isoformat()
    seed_previous(tmp_path, {'shopdunk': 47}, timestamp=old_timestamp)

    floor = MIN_PRODUCTS_PER_SHOP['shopdunk']
    new_count = floor + 3  # clears the floor but would be a huge "drop" from 47
    assert (1 - new_count / 47) > MAX_DROP_RATIO, "test setup must exceed the drop threshold"

    updater = make_updater_with_results(tmp_path, {'shopdunk': new_count})
    updater.save_results()  # must NOT raise — previous data is stale

    latest = json.loads((tmp_path / "latest_products.json").read_text())
    assert latest['summary']['by_shop']['shopdunk']['count'] == new_count


def test_fresh_previous_data_still_enforces_drop_check(tmp_path):
    """Sanity check that staleness-skipping doesn't quietly disable the
    drop check for the normal case — only genuinely old data skips it."""
    seed_previous(tmp_path, {'shopdunk': 30})  # defaults to "just now"
    floor = MIN_PRODUCTS_PER_SHOP['shopdunk']
    new_count = floor + 2
    assert (1 - new_count / 30) > MAX_DROP_RATIO, "test setup must exceed the drop threshold"

    updater = make_updater_with_results(tmp_path, {'shopdunk': new_count})

    with pytest.raises(ValidationFailure):
        updater.save_results()


def mark_failed(updater, shop, error="Cloudflare block or timeout"):
    updater.results['summary']['by_shop'][shop] = {'count': 0, 'success': False, 'error': error}


def load_latest(tmp_path):
    return json.loads((tmp_path / "latest_products.json").read_text())


def test_all_shops_rejected_preserves_last_known_good_exactly(tmp_path):
    """When no shop produces acceptable fresh data, latest_products.json is
    byte-identical to before — not partially overwritten."""
    seed_previous(tmp_path, {'shopdunk': 30, 'cellphones': 20})
    before = (tmp_path / "latest_products.json").read_text()

    updater = make_updater_with_results(tmp_path, {'shopdunk': 0, 'cellphones': 0})
    with pytest.raises(ValidationFailure):
        updater.save_results()

    assert (tmp_path / "latest_products.json").read_text() == before


def test_rejected_shop_keeps_last_known_good_while_others_update(tmp_path):
    seed_previous(tmp_path, {'shopdunk': 30, 'cellphones': 20})

    updater = make_updater_with_results(tmp_path, {'shopdunk': 0, 'cellphones': 20})
    updater.save_results()  # partial update, must not raise

    latest = load_latest(tmp_path)
    shopdunk = latest['summary']['by_shop']['shopdunk']
    assert shopdunk['status'] == 'carried_forward'
    assert shopdunk['count'] == 30
    assert latest['summary']['by_shop']['cellphones']['status'] == 'fresh'
    by_shop = {}
    for p in latest['products']:
        by_shop.setdefault(p['shop'], []).append(p)
    assert len(by_shop['shopdunk']) == 30 and all(p['stale'] for p in by_shop['shopdunk'])
    assert len(by_shop['cellphones']) == 20 and not any(p['stale'] for p in by_shop['cellphones'])


def test_failed_shop_is_carried_forward_not_dropped(tmp_path):
    """Real incident 2026-10-01 06:00: FPTShop failed outright (missing
    Rosetta), and the old gate — which only checked shops that succeeded —
    published a file with zero FPTShop products."""
    seed_previous(tmp_path, {'cellphones': 16, 'shopdunk': 23, 'fptshop': 50})

    updater = make_updater_with_results(tmp_path, {'cellphones': 16, 'shopdunk': 23})
    mark_failed(updater, 'fptshop')
    updater.save_results()

    latest = load_latest(tmp_path)
    fpt = latest['summary']['by_shop']['fptshop']
    assert fpt['status'] == 'carried_forward'
    assert fpt['count'] == 50
    assert latest['summary']['total_products'] == 89


def test_single_unpriced_listing_is_dropped_not_fatal(tmp_path):
    """Real incident 2026-10-01 12:00: one CellphoneS listing with no price
    rejected the entire run, blocking all three shops' updates."""
    updater = make_updater_with_results(tmp_path, {'cellphones': 16})
    unpriced = updater.results['products'][0]
    unpriced['price_vnd'] = None
    updater.save_results()

    latest = load_latest(tmp_path)
    cellphones = latest['summary']['by_shop']['cellphones']
    assert cellphones['status'] == 'fresh'
    assert cellphones['count'] == 15
    assert cellphones['skipped_incomplete'] == [unpriced['url']]


def test_systematic_missing_prices_rejects_shop(tmp_path):
    """Real incident 2026-09-19: an encoding bug blanked 4/17 CellphoneS
    prices. That's broken parsing, not a few odd listings — the shop must
    fall back to last-known-good rather than publish a gutted list."""
    seed_previous(tmp_path, {'cellphones': 17, 'shopdunk': 23})
    updater = make_updater_with_results(tmp_path, {'cellphones': 17, 'shopdunk': 23})
    for p in [p for p in updater.results['products'] if p['shop'] == 'cellphones'][:4]:
        p['price_vnd'] = None
    updater.save_results()

    cellphones = load_latest(tmp_path)['summary']['by_shop']['cellphones']
    assert cellphones['status'] == 'carried_forward'
    assert cellphones['count'] == 17
    assert '4/17' in cellphones['error']


def test_failed_shop_with_no_history_is_reported_missing(tmp_path):
    updater = make_updater_with_results(tmp_path, {'shopdunk': 23})
    mark_failed(updater, 'fptshop')
    updater.save_results()

    fpt = load_latest(tmp_path)['summary']['by_shop']['fptshop']
    assert fpt['status'] == 'missing'
    assert fpt['count'] == 0
