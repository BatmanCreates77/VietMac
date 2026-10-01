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

from scrapers.cellphones_scraper import CellphonesScraper, CellphonesIphoneScraper
from scrapers.shopdunk_scraper import ShopDunkScraper, ShopDunkIphoneScraper
from scrapers.fptshop_scraper import FPTShopScraper, FPTShopIphoneScraper
from scrapers.topzone_scraper import TopZoneScraper

SCRAPER_CLASSES = {
    'cellphones': CellphonesScraper,
    'shopdunk': ShopDunkScraper,
    'fptshop': FPTShopScraper,
    'topzone': TopZoneScraper,
    'cellphones-iphone': CellphonesIphoneScraper,
    'shopdunk-iphone': ShopDunkIphoneScraper,
    'fptshop-iphone': FPTShopIphoneScraper,
}


def scraper_key(fixture):
    """Which scraper parses a fixture: the shop's Mac scraper unless the
    manifest names another (its iPhone scraper)."""
    return fixture.get("scraper", fixture["shop"])

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
    ids=[f"{scraper_key(f)}:{Path(f['file']).name}" for f in MANIFEST["fixtures"]],
)
def test_parse_products_matches_manifest_count(fixture, monkeypatch):
    scraper_cls = SCRAPER_CLASSES[scraper_key(fixture)]
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
    matching_fixtures = [f for f in MANIFEST["fixtures"] if scraper_key(f) == shop]
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
        assert product['shop'] == scraper_cls.shop_name
        assert product['source'] == shop
        assert product['product_line'] == scraper_cls.product_line


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
    # No "show more" button to click, and every card already priced.
    mock_page.evaluate.side_effect = lambda js: 0 if js == CellphonesScraper.UNPRICED_CARDS_JS else False

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


class FakeCellphonesPage:
    """Listing with `hidden` products behind "show more" (20 per click) and
    prices that fill in over successive checks."""

    def __init__(self, shown, hidden, unpriced_checks):
        self.shown, self.hidden = shown, hidden
        self.unpriced_checks = list(unpriced_checks)
        self.clicks = 0

    def locator(self, selector):
        count = MagicMock()
        count.count.return_value = self.shown
        return count

    def evaluate(self, js):
        if js == CellphonesScraper.CLICK_SHOW_MORE_JS:
            if not self.hidden:
                return False
            batch = min(20, self.hidden)
            self.shown, self.hidden = self.shown + batch, self.hidden - batch
            self.clicks += 1
            return True
        if js == CellphonesScraper.UNPRICED_CARDS_JS:
            return self.unpriced_checks.pop(0) if len(self.unpriced_checks) > 1 else self.unpriced_checks[0]
        raise AssertionError(f"unexpected script: {js}")

    def wait_for_function(self, js, timeout):
        pass


def test_cellphones_expands_show_more_until_everything_is_listed():
    """laptop/mac.html showed 20 of 75 products until "Xem thêm" had been
    clicked 3 times (2026-10-01)."""
    page = FakeCellphonesPage(shown=20, hidden=55, unpriced_checks=[0])
    CellphonesScraper()._expand_listing(page)
    assert (page.shown, page.clicks) == (75, 3)


def test_cellphones_waits_for_prices_to_fill_in():
    page = FakeCellphonesPage(shown=20, hidden=0, unpriced_checks=[12, 3, 0])
    with patch("scrapers.cellphones_scraper.time.sleep") as sleep:
        CellphonesScraper()._wait_for_prices(page)
    assert sleep.call_count == 2
    assert page.unpriced_checks == [0]


def test_shopdunk_removed_listing_page_fails_fast():
    """Real case 2026-10-01: /macbook-pro-m4 and /macbook-air-m4 began 404ing
    after the M5 launch, and each cost ~9 minutes per run in selector
    timeouts + retry backoff. A missing page must fail on the first attempt
    without waiting for products that will never appear."""
    mock_response = MagicMock(status=404)
    mock_page = MagicMock(url="https://shopdunk.com/page-not-found")
    mock_page.goto.return_value = mock_response
    mock_context = MagicMock()
    mock_context.new_page.return_value = mock_page
    mock_browser = MagicMock()
    mock_browser.new_context.return_value = mock_context
    mock_pw = MagicMock()
    mock_pw.chromium.launch.return_value = mock_browser
    mock_cm = MagicMock()
    mock_cm.__enter__.return_value = mock_pw

    with patch("scrapers.shopdunk_scraper.sync_playwright", return_value=mock_cm) as sync_pw, \
         patch("scrapers.shopdunk_scraper.time.sleep") as sleep:
        html = ShopDunkScraper().fetch_html("https://shopdunk.com/macbook-pro-m4")

    assert html is None
    assert sync_pw.call_count == 1, "no retries for a page that's gone"
    mock_page.wait_for_selector.assert_not_called()
    sleep.assert_not_called()


FPT_READY_HTML =(Path(__file__).parent / "fixtures" / "raw" / "fptshop" / "live_macbook_listing.html").read_text(encoding="utf-8")
FPT_CHALLENGE_HTML = "<html><head><title>Just a moment...</title></head><body></body></html>"


def make_fake_cdp_browser(pages):
    """A stand-in for sb_cdp.Chrome whose get_page_source() walks through
    `pages` (repeating the last one)."""
    browser = MagicMock()
    sequence = list(pages)
    browser.get_page_source.side_effect = lambda: sequence.pop(0) if len(sequence) > 1 else sequence[0]
    return browser


@pytest.fixture
def no_sleep():
    with patch("scrapers.fptshop_scraper.time.sleep"), patch("scrapers.base_scraper.time.sleep"):
        yield


def test_fptshop_waits_through_cloudflare_challenge(no_sleep):
    browser = make_fake_cdp_browser([FPT_CHALLENGE_HTML, FPT_CHALLENGE_HTML, FPT_READY_HTML])
    with patch("scrapers.fptshop_scraper.sb_cdp.Chrome", return_value=browser):
        html = FPTShopScraper().fetch_html("https://fptshop.com.vn/x")

    assert html is not None and "cardInfo" in html


def test_fptshop_reuses_one_browser_and_always_closes_it(no_sleep):
    """Solve Cloudflare once per run, then reuse the session; and never leave
    a stray Chrome behind after a scheduled run."""
    browser = make_fake_cdp_browser([FPT_READY_HTML])
    with patch("scrapers.fptshop_scraper.sb_cdp.Chrome", return_value=browser) as chrome:
        result = FPTShopScraper().scrape()

    assert result['success'] and result['count'] > 0
    assert chrome.call_count == 1, "one browser for all listing pages"
    assert browser.open.call_count == len(FPTShopScraper().page_urls())
    browser.driver.stop.assert_called_once()


def test_fptshop_gives_up_with_fresh_browser_per_attempt(no_sleep):
    """A page stuck on the challenge must time out (not hang a scheduled run),
    and each retry must start a new browser rather than reuse a stuck one."""
    with patch("scrapers.fptshop_scraper.sb_cdp.Chrome",
               side_effect=lambda: make_fake_cdp_browser([FPT_CHALLENGE_HTML])) as chrome:
        html = FPTShopScraper().fetch_html("https://fptshop.com.vn/x", retry=2)

    assert html is None
    assert chrome.call_count == 2


@pytest.mark.parametrize("raw_name, expected", [
    ("MacBook Air M5 13 inch 2026", True),
    ("Macbook Air M5 13-inch", True),  # ShopDunk's casing; was dropped
    ("Apple Mac mini M6 12CPU 12GPU 16GB 256GB 2026", True),
    ("iMac M4 2024 24 inch", True),
    ("Apple Mac Studio M5 Max 18CPU 32GPU 36GB 512GB 2026", True),
    ("Apple Studio Display XDR 27 5K Ngàm VESA 2026", False),
    ("Studio Display", False),
    ("", False),
    (None, False),
])
def test_is_mac(raw_name, expected):
    assert CellphonesScraper._is_mac(raw_name) is expected


IPHONE_FIXTURES = Path(__file__).parent / "fixtures" / "raw"


@pytest.mark.parametrize("scraper_cls, fixture", [
    (CellphonesIphoneScraper, "cellphones/iphone_listing.html"),
    (ShopDunkIphoneScraper, "shopdunk/iphone_listing.html"),
    (FPTShopIphoneScraper, "fptshop/iphone_listing.html"),
])
def test_iphone_listings_parse_model_and_storage(scraper_cls, fixture):
    products = scraper_cls().parse_products((IPHONE_FIXTURES / fixture).read_text(encoding="utf-8"))
    for p in products:
        assert p['specs']['model_type'].startswith('iPhone ') and p['specs']['storage_display'], p['model']
        assert not p['model'].startswith(('Điện thoại', 'Apple')), p['model']
    unique = {p['url']: p for p in products}.values()
    pairs = [(p['specs']['model_type'], p['specs']['storage_display']) for p in unique]
    assert len(pairs) == len(set(pairs)), "same model + storage listed twice"


def test_fptshop_iphone_carrier_bundle_is_excluded():
    html = (IPHONE_FIXTURES / "fptshop/iphone_listing.html").read_text(encoding="utf-8")
    names = [p['model'] for p in FPTShopIphoneScraper().parse_products(html)]
    assert "iPhone 16e 128GB" in names
    assert not any("SIM" in n for n in names)


def test_fptshop_variants_one_product_per_storage_at_cheapest_in_stock_colour():
    """Real iPhone 18 Pro page data (2026-10-02): 4 sizes x 4 colours. The
    1TB tier has a colour with inventory 0, which must not set the price."""
    html = (IPHONE_FIXTURES / "fptshop/iphone_product_page.html").read_text(encoding="utf-8")
    products = FPTShopIphoneScraper().parse_variants(html)
    by_size = {p['specs']['storage_display']: p for p in products}
    assert sorted(by_size) == ['1TB', '256GB', '2TB', '512GB']
    assert {s: p['price_vnd'] for s, p in by_size.items()} == {
        '256GB': 38990000, '512GB': 45490000, '1TB': 58490000, '2TB': 77990000,
    }
    assert len({p['url'] for p in products}) == 4, "each size needs its own ?sku= URL"
    assert all('?sku=' in p['url'] and p['specs']['model_type'] == 'iPhone 18 Pro' for p in products)


def test_fptshop_variants_skip_sizes_with_nothing_in_stock():
    html = (IPHONE_FIXTURES / "fptshop/iphone_product_page.html").read_text(encoding="utf-8")
    html = html.replace('\\"inventory\\":', '\\"inventory\\":0,\\"was\\":')
    assert FPTShopIphoneScraper().parse_variants(html) == []


def test_fptshop_variants_absent_returns_empty():
    assert FPTShopIphoneScraper().parse_variants("<html><body>nothing</body></html>") == []


@pytest.mark.parametrize("raw_name, expected", [
    ("iPhone 17 Pro Max 256GB | Chính hãng", True),
    ("Điện thoại iPhone 16 Pro Max 256GB", True),
    ("iPhone 16e 128GB SIM Viettel", False),
    ("Ốp lưng iPhone 17 Pro Max MagSafe", False),
    ("Cáp sạc USB-C cho iPhone", False),
    ("iPhone 15 Pro Max 256GB cũ đẹp", False),
    ("MacBook Air M5 13 inch", False),
])
def test_is_iphone(raw_name, expected):
    assert CellphonesScraper._is_iphone(raw_name) is expected
