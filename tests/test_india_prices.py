"""
India price check (macbook_scraper/india_prices.py): every number it
publishes is compared against on the site ("save ₹X in Vietnam" / "cheaper
in India"), so each safeguard here maps to a real way it went wrong while
building it (2026-10-04/05).
"""
import json
import sys
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import patch

import pytest
import requests

sys.path.insert(0, str(Path(__file__).parent.parent / "macbook_scraper"))

import india_prices
from india_prices import (
    IndiaPriceUpdater, best_prices, parse_apple_india, parse_flipkart,
    parse_reliance, plausible,
)

FIXTURES = Path(__file__).parent / "fixtures" / "raw" / "india"


def fixture(name):
    return (FIXTURES / name).read_text(encoding="utf-8", errors="ignore")


def flipkart_card(title, *texts, href="/apple-iphone/p/itm123"):
    """A search-result card shaped like Flipkart's (title, specs, then the
    selling price first, MRP and exchange offers after)."""
    return f'<a href="{href}">{" ".join(texts[:1])} Add to Compare <div>{title}</div> 256 GB ROM {" ".join(texts[1:])}</a>'


# --- Apple India -----------------------------------------------------------

def test_apple_india_price_list():
    offers = parse_apple_india(fixture("apple_iphone_18_pro_products.json.txt"), "https://apple.example")
    assert offers[("iPhone 18 Pro", "256GB")]["price"] == 164900
    assert offers[("iPhone 18 Pro Max", "2TB")]["price"] == 329900
    offers = parse_apple_india(fixture("apple_iphone_17e_products.json.txt"), "https://apple.example")
    assert {k: v["price"] for k, v in offers.items()} == {
        ("iPhone 17e", "256GB"): 79900, ("iPhone 17e", "512GB"): 104900,
    }


def test_iphone_air_is_left_out():
    """Apple India's Air (₹1,49,900) is a newer model than the first-gen Air
    retailers sell (₹1,19,900); the name can't tell them apart."""
    html = '"price":{"fullPrice":149900.00},"category":"iphone","name":"iPhone Air 256GB Sky Blue"'
    assert parse_apple_india(html, "u") == {}


# --- Flipkart --------------------------------------------------------------

def test_flipkart_real_search_page():
    offers = parse_flipkart(fixture("flipkart_iphone_18_pro.html"))
    assert {(o["key"], o["price"]) for o in offers} == {
        (("iPhone 18 Pro", "256GB"), 164900), (("iPhone 18 Pro Max", "256GB"), 179900),
    }
    # Accessory cards on the same page (tempered glass, ₹230) are not phones.
    assert all(o["price"] > 100000 for o in offers)
    assert all(o["url"].startswith("https://www.flipkart.com/") and "/p/itm" in o["url"] for o in offers)


def test_flipkart_takes_selling_price_not_mrp_or_exchange_offer():
    html = flipkart_card("Apple iPhone 17 (Black, 256 GB)", "",
                         "₹84,999 ₹99,900 14% off Upto ₹72,050 Off on Exchange")
    [offer] = parse_flipkart(html)
    assert offer["price"] == 84999


def test_flipkart_skips_coming_soon_and_unavailable():
    """Real 2026-10-05: iPhone 17 256GB listed at ₹84,999 but "Coming Soon",
    i.e. not buyable — it must not become "cheaper in India"."""
    html = (flipkart_card("Apple iPhone 17 (Black, 256 GB)", "Coming Soon", "₹84,999 ₹99,900")
            + flipkart_card("Apple iPhone 17 (Sage, 256 GB)", "", "₹84,999 Currently unavailable"))
    assert parse_flipkart(html) == []


def test_flipkart_blocked_page_parses_to_nothing():
    """A CAPTCHA/home page must read as 'no products' (a failed fetch),
    never as real prices."""
    assert parse_flipkart(fixture("flipkart_blocked_captcha.html")) == []


# --- Reliance Digital ------------------------------------------------------

def test_reliance_real_search_page():
    offers = parse_reliance(fixture("reliance_iphone_18_pro.html"))
    prices = {o["key"]: o["price"] for o in offers}
    assert prices[("iPhone 18 Pro", "256GB")] == 164900
    assert prices[("iPhone 18 Pro Max", "512GB")] == 204900
    assert all(o["url"].startswith("https://www.reliancedigital.in/product/") for o in offers)


def test_reliance_skips_out_of_stock_cards():
    html = ('<div class="product-card"><div class="product-card-details"><a href="/product/x">'
            '<div class="product-card-title">Apple iPhone 17 256 GB, Black</div>'
            '<div class="price">₹99,900.00</div></a></div><span>Out of Stock</span></div>')
    assert parse_reliance(html) == []


def test_utf8_is_forced_for_pages_without_a_charset():
    """Reliance sends no charset; requests then decodes as Latin-1 and "₹"
    becomes "â¹", so no price ever matched (2026-10-05)."""
    response = requests.Response()
    response.status_code = 200
    response._content = "₹1,64,900.00".encode("utf-8")
    response.headers["Content-Type"] = "text/html"
    updater = IndiaPriceUpdater("/tmp", delay_seconds=0)
    with patch.object(updater.session, "get", return_value=response):
        assert updater._get("https://example.com") == "₹1,64,900.00"


# --- Choosing the best price ----------------------------------------------

def test_implausible_prices_are_ignored():
    """An accessory titled like a phone (Reliance's "iPhone Air" at ₹11,900)
    or an exchange-offer amount must never become the best price."""
    assert not plausible({"price": 11900}, 164900)
    assert not plausible({"price": 72050}, 164900)
    assert not plausible({"price": 200000}, 164900)
    assert plausible({"price": 134900}, 164900)
    assert plausible({"price": 134900}, None)       # model Apple no longer sells
    assert not plausible({"price": 5900}, None)


def test_best_price_is_lowest_plausible_across_sources():
    key = ["iPhone 17e", "256GB"]
    apple = {("iPhone 17e", "256GB"): {"price": 79900}}
    result = best_prices({
        "Apple India": [{"key": key, "source": "Apple India", "price": 79900, "url": "a"}],
        "Reliance Digital": [{"key": key, "source": "Reliance Digital", "price": 64900, "url": "r"}],
        "Flipkart": [{"key": key, "source": "Flipkart", "price": 5900, "url": "f"}],  # a case
    }, apple)
    entry = result["iPhone 17e 256GB"]
    assert (entry["best_price"], entry["best_source"], entry["best_url"]) == (64900, "Reliance Digital", "r")
    assert [o["source"] for o in entry["offers"]] == ["Reliance Digital", "Apple India"]


# --- Failed sources --------------------------------------------------------

def _updater(tmp_path, apple=None, flipkart=None, reliance=None):
    updater = IndiaPriceUpdater(tmp_path, delay_seconds=0)
    updater.fetch_apple = lambda: apple if apple is not None else {
        ("iPhone 18 Pro", "256GB"): {"source": "Apple India", "price": 164900, "url": "a", "title": "t"}}
    updater.fetch_retailer = lambda source: (flipkart if source == "Flipkart" else reliance) or []
    return updater


def _seed(tmp_path, source, hours_ago, price):
    payload = {"sources": {source: {
        "checked_at": (datetime.now() - timedelta(hours=hours_ago)).isoformat(),
        "status": "fresh",
        "offers": [{"key": ["iPhone 18 Pro", "256GB"], "source": source, "price": price, "url": "old"}],
    }}}
    (tmp_path / "india_prices.json").write_text(json.dumps(payload))


def test_failed_source_keeps_recent_prices_marked_carried_forward(tmp_path):
    _seed(tmp_path, "Flipkart", hours_ago=48, price=159900)
    result = _updater(tmp_path).run()
    assert result["sources"]["Flipkart"]["status"] == "carried_forward"
    assert result["products"]["iPhone 18 Pro 256GB"]["best_price"] == 159900


def test_failed_source_drops_prices_older_than_one_missed_run(tmp_path):
    """A sale price from a source that keeps failing must not stay up for
    weeks after the sale ends."""
    _seed(tmp_path, "Flipkart", hours_ago=150, price=159900)
    result = _updater(tmp_path).run()
    assert "Flipkart" not in result["sources"]
    assert result["products"]["iPhone 18 Pro 256GB"]["best_price"] == 164900


def test_one_failed_search_does_not_lose_the_retailer(tmp_path):
    updater = IndiaPriceUpdater(tmp_path, delay_seconds=0)
    html = flipkart_card("Apple iPhone 18 Pro (Black, 256 GB)", "", "₹1,64,900")
    calls = iter([requests.ConnectionError("503")] + [html] * 20)

    def fake_get(url):
        value = next(calls)
        if isinstance(value, Exception):
            raise value
        return value

    with patch.object(updater, "_get", side_effect=fake_get):
        offers = updater.fetch_retailer("Flipkart")
    assert offers and offers[0]["price"] == 164900
