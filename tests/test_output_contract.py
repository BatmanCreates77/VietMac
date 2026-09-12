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


def test_rejected_run_preserves_last_known_good_exactly(tmp_path):
    """The core guarantee: after a rejected run, latest_products.json is
    byte-identical to what it was before — not partially overwritten."""
    seeded = seed_previous(tmp_path, {'shopdunk': 30, 'cellphones': 20})
    before = (tmp_path / "latest_products.json").read_text()

    updater = make_updater_with_results(tmp_path, {'shopdunk': 0, 'cellphones': 20})
    with pytest.raises(ValidationFailure):
        updater.save_results()

    after = (tmp_path / "latest_products.json").read_text()
    assert before == after
