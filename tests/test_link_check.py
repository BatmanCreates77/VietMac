"""
The viewer's link check returned 89/89 "verified" on live data — these make
sure that's because the links are right, not because the check can't fail.
"""
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(REPO_ROOT / "macbook_scraper" / "viewer"))

from link_check import evaluate, is_real_page

URL = "https://shopdunk.com/macbook-air-m5-13-inch-16gb-512gb"


def product(**overrides):
    p = {
        'shop': 'shopdunk',
        'url': URL,
        'price_vnd': 34990000,
        'specs': {'chip': 'M5', 'chip_variant': None, 'ram_gb': 16, 'storage_display': '512GB'},
    }
    p.update(overrides)
    return p


def page(title, body=''):
    return f"<html><head><title>{title}</title></head><body><h1>{title}</h1>{body}</body></html>"


def fetched(html, final_url=URL, status=200):
    return {'method': 'http', 'http_status': status, 'final_url': final_url, 'html': html}


def test_matching_page_with_price_is_verified():
    html = page("MacBook Air M5 13 inch 16GB 512GB", "<p>34.990.000₫</p>")
    assert evaluate(product(), fetched(html))['verdict'] == 'verified'


def test_different_chip_is_wrong_product():
    html = page("MacBook Air M4 13 inch 16GB 512GB", "<p>34.990.000₫</p>")
    result = evaluate(product(), fetched(html))
    assert result['verdict'] == 'wrong'


def test_pro_variant_page_for_base_chip_product_is_wrong():
    html = page("MacBook Pro M5 Pro 14 inch 24GB 1TB", "<p>34.990.000₫</p>")
    assert evaluate(product(), fetched(html))['verdict'] == 'wrong'


def test_price_missing_from_page_needs_a_look():
    html = page("MacBook Air M5 13 inch 16GB 512GB", "<p>36.490.000₫</p>")
    result = evaluate(product(), fetched(html))
    assert result['verdict'] == 'check'
    assert result['price_on_page'] is False


def test_title_sizes_not_including_ours_needs_a_look():
    html = page("MacBook Air M5 13 inch 24GB 1TB", "<p>34.990.000₫</p>")
    assert evaluate(product(), fetched(html))['verdict'] == 'check'


def test_redirect_to_homepage_is_broken():
    html = page("ShopDunk - Apple Authorized Reseller")
    assert evaluate(product(), fetched(html, final_url="https://shopdunk.com/"))['verdict'] == 'broken'


def test_leaving_shop_domain_is_broken():
    html = page("Something else")
    assert evaluate(product(), fetched(html, final_url="https://example.com/x"))['verdict'] == 'broken'


def test_404_is_broken():
    assert evaluate(product(), fetched(page("Not found"), status=404))['verdict'] == 'broken'


def test_stuck_on_challenge_is_broken():
    challenge = "<html><head><title>Just a moment...</title></head></html>"
    assert evaluate(product(), fetched(challenge))['verdict'] == 'broken'


def test_untitled_js_challenge_is_not_a_real_page():
    # What CellphoneS serves to non-browsers: no <title>, obfuscated script.
    assert not is_real_page("<html><head><script>var _0x4cb6=...</script></head></html>")
