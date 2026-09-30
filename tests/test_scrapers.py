"""
Milestone 2 gate: parse_products() must be pure (no network I/O) and must
parse each frozen fixture to its manifest-recorded product count. Run:

    pytest tests/test_scrapers.py -v

A failure here means a scraper's parsing logic changed behavior — the
fixture HTML is frozen, so it is never the site's fault.
"""
import json
import socket
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

REPO_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(REPO_ROOT / "macbook_scraper"))

from scrapers.cellphones_scraper import CellphonesScraper
from scrapers.shopdunk_scraper import ShopDunkScraper
from scrapers.fptshop_scraper import FPTShopScraper
from scrapers.topzone_scraper import TopZoneScraper

SCRAPER_CLASSES = {
    'cellphones': CellphonesScraper,
    'shopdunk': ShopDunkScraper,
    'fptshop': FPTShopScraper,
    'topzone': TopZoneScraper,
}

MANIFEST = json.loads((Path(__file__).parent / "fixtures" / "manifest.json").read_text())


class NetworkAccessDuringParse(Exception):
    pass


def _block_network(monkeypatch):
    def guard(*args, **kwargs):
        raise NetworkAccessDuringParse(
            "parse_products() must be pure — no network access allowed"
        )
    monkeypatch.setattr(socket, "socket", guard)


@pytest.mark.parametrize(
    "fixture",
    MANIFEST["fixtures"],
    ids=[f"{f['shop']}:{Path(f['file']).name}" for f in MANIFEST["fixtures"]],
)
def test_parse_products_matches_manifest_count(fixture, monkeypatch):
    scraper_cls = SCRAPER_CLASSES[fixture["shop"]]
    scraper = scraper_cls()

    fixture_path = Path(__file__).parent / "fixtures" / fixture["file"]
    html = fixture_path.read_text(encoding="utf-8")

    _block_network(monkeypatch)
    products = scraper.parse_products(html)

    assert len(products) == fixture["expected_product_count"], (
        f"{fixture['shop']} parsed {len(products)} products from "
        f"{fixture['file']}, expected {fixture['expected_product_count']}"
    )


@pytest.mark.parametrize("shop, scraper_cls", SCRAPER_CLASSES.items())
def test_product_schema_shape(shop, scraper_cls):
    """Every product dict must carry the full formalized schema, regardless
    of shop — this is what route.js's loadScrapedData() relies on."""
    matching_fixtures = [f for f in MANIFEST["fixtures"] if f["shop"] == shop]
    assert matching_fixtures, f"no fixture registered for {shop}"

    scraper = scraper_cls()
    fixture_path = Path(__file__).parent / "fixtures" / matching_fixtures[0]["file"]
    html = fixture_path.read_text(encoding="utf-8")
    products = scraper.parse_products(html)
    assert products, f"fixture for {shop} produced zero products"

    required_keys = {
        'model', 'raw_name', 'price_vnd', 'price_text', 'url', 'image_url',
        'shop', 'specs', 'product_id', 'clean_name',
    }
    for product in products:
        missing = required_keys - product.keys()
        assert not missing, f"{shop} product missing keys: {missing}"
        assert product['shop'] == shop


def test_cellphones_playwright_fetch_preserves_encoding():
    """Regression test for a real bug caught live 2026-09-19: the old code
    did `return content.encode('utf-8')` on Playwright's page.content()
    (which is already a correctly-decoded str), forcing BeautifulSoup to
    guess the byte encoding when parsing — it guessed wrong for Vietnamese
    text, producing mojibake ("Chính hãng" -> "Ch√≠nh h√£ng") and, worse,
    silently dropping the price element on 4 of 17 products, which is
    exactly what the validation gate is supposed to catch (and did — the
    scraper itself should still get this right so the gate isn't the only
    line of defense). Asserts the fetch returns the str unchanged, with no
    encode/decode round-trip in between."""
    vietnamese_text = "MacBook Pro 14 M5 10CPU 10GPU 16GB 1TB | Chính hãng Apple Việt Nam"

    mock_page = MagicMock()
    mock_page.content.return_value = f"<html><body>{vietnamese_text}</body></html>"

    mock_context = MagicMock()
    mock_context.new_page.return_value = mock_page

    mock_browser = MagicMock()
    mock_browser.new_context.return_value = mock_context

    mock_playwright_instance = MagicMock()
    mock_playwright_instance.chromium.launch.return_value = mock_browser

    mock_sync_playwright_cm = MagicMock()
    mock_sync_playwright_cm.__enter__.return_value = mock_playwright_instance

    with patch("scrapers.cellphones_scraper.sync_playwright", return_value=mock_sync_playwright_cm):
        scraper = CellphonesScraper()
        html = scraper._fetch_with_playwright("https://example.com/fake", retry=1)

    assert isinstance(html, str), "fetch must return str, not re-encoded bytes"
    assert vietnamese_text in html, "Vietnamese text must survive unchanged, no mojibake"
