#!/usr/bin/env python3
"""
India price check: the best price an Indian buyer can get for each iPhone
model + storage, so the site can say "save ₹X in Vietnam" or "cheaper in
India" honestly.

Sources, all live listings (never articles):
  - Apple India (apple.com/in): the official price list embedded in each
    buy page. Also the reference price every retailer price is checked
    against.
  - Flipkart and Reliance Digital: search results pages (plain HTTP).

Safeguards, each from a real failure mode seen on 2026-10-04:
  - Only a card's selling price counts: Flipkart cards also show the
    struck-through MRP and "Upto ₹72,050 Off on Exchange"; the selling
    price is the first ₹ amount in the card.
  - Sold-out / unavailable cards are skipped (they keep showing a price).
  - Accessories, AppleCare bundles, refurbished units are skipped, and a
    retailer price must sit within a sane band of Apple's price for the
    same model, which catches anything that slips past the name filter
    (Reliance returned an "iPhone Air" accessory at ₹11,900).
  - iPhone Air and Duo are left out: Apple India's current Air (₹1,49,900)
    is a newer model than the first-generation Air retailers still sell
    (₹1,19,900), and the name alone can't tell them apart.
  - A source that fails keeps its previous prices for one missed run at
    most, then they are dropped — sale prices must not linger after a sale.
"""

import json
import logging
import re
import time
from datetime import datetime
from pathlib import Path

import requests
from bs4 import BeautifulSoup

from utils.spec_parser import SpecParser

logger = logging.getLogger(__name__)

USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/130.0 Safari/537.36"
)

APPLE_INDIA_PAGES = [
    "https://www.apple.com/in/shop/buy-iphone/iphone-18-pro",
    "https://www.apple.com/in/shop/buy-iphone/iphone-17",
    "https://www.apple.com/in/shop/buy-iphone/iphone-17e",
    "https://www.apple.com/in/shop/buy-iphone/iphone-16",
]
SEARCH_QUERIES = [
    "iphone 18 pro max", "iphone 18 pro", "iphone 17 pro max", "iphone 17 pro",
    "iphone 17", "iphone 17e", "iphone 16 plus", "iphone 16", "iphone 16e",
]
RETAILER_SEARCH = {
    "Flipkart": "https://www.flipkart.com/search?q={q}",
    "Reliance Digital": "https://www.reliancedigital.in/products?q={q}",
}

EXCLUDED_MODELS = {"iPhone Air", "iPhone Duo"}
NOT_A_PHONE = re.compile(
    r"case|cover|glass|guard|protector|charger|cable|adapter|skin|back panel|"
    r"applecare|protect\+|refurb|renewed|unboxed|pre-?owned|used",
    re.IGNORECASE,
)
UNAVAILABLE = re.compile(
    r"sold out|out of stock|currently unavailable|coming soon|notify me",
    re.IGNORECASE,
)
PRICE = re.compile(r"₹\s?([\d,]{4,})(?:\.\d+)?")

# A retailer price outside this band of Apple India's price for the same
# model is not the phone at its selling price (an exchange offer, an
# accessory, a bundle). For models Apple no longer sells, only the floor.
MIN_SHARE_OF_APPLE_PRICE = 0.5
MAX_SHARE_OF_APPLE_PRICE = 1.05
FLOOR_WITHOUT_APPLE_PRICE = 30000

# Scrapes run every other day; a failed source keeps its last prices for
# one missed run (2 x 48h, plus slack), never longer.
MAX_SOURCE_AGE_HOURS = 100


def _price(text):
    m = PRICE.search(text or "")
    return int(m.group(1).replace(",", "")) if m else None


def _key(title, parser):
    specs = parser.parse_iphone(title)
    model, storage = specs.get("model_type"), specs.get("storage_display")
    if not storage or model in (None, "iPhone") or model in EXCLUDED_MODELS:
        return None
    return model, storage


def parse_apple_india(html, page_url, parser=None):
    """Pure: Apple's buy page embeds every SKU as
    {"price":{"fullPrice":164900.00},"category":"iphone","name":"iPhone 18 Pro 256GB Silver"}.
    Colours share a price; returns {(model, storage): offer}."""
    parser = parser or SpecParser()
    offers = {}
    pattern = r'"price":\{"fullPrice":([\d.]+)\},"category":"iphone","name":"([^"]+)"'
    for price, name in re.findall(pattern, html):
        key = _key(name, parser)
        if key and key not in offers:
            offers[key] = {"source": "Apple India", "price": int(float(price)),
                           "url": page_url, "title": name}
    return offers


def parse_flipkart(html, parser=None):
    """Pure: each product is an <a href=".../p/itm..."> card holding the
    title, specs, then the selling price as its first ₹ amount (followed by
    the struck-through MRP and exchange-offer amounts)."""
    parser = parser or SpecParser()
    offers = []
    for card in BeautifulSoup(html, "html.parser").select('a[href*="/p/itm"]'):
        text = card.get_text(" ", strip=True)
        title = re.search(r"Apple iPhone [^₹]*?\(\s*[^)]*?\d+\s?(?:GB|TB)\s*\)", text)
        if not title or NOT_A_PHONE.search(title.group(0)) or UNAVAILABLE.search(text):
            continue
        key = _key(title.group(0), parser)
        price = _price(text[title.end():])
        if key and price:
            href = card.get("href", "").split("?")[0]
            offers.append({"key": key, "source": "Flipkart", "price": price,
                           "url": "https://www.flipkart.com" + href, "title": title.group(0)})
    return offers


def parse_reliance(html, parser=None):
    """Pure: .product-card-details holds a .product-card-title and a .price
    (the selling price; bank-offer "best price" sits outside it)."""
    parser = parser or SpecParser()
    offers = []
    for card in BeautifulSoup(html, "html.parser").select(".product-card-details"):
        title_el, price_el = card.select_one(".product-card-title"), card.select_one(".price")
        if not title_el or not price_el:
            continue
        title = title_el.get_text(" ", strip=True)
        container = card.find_parent(class_="product-card") or card.parent or card
        if (not title.startswith("Apple iPhone") or NOT_A_PHONE.search(title)
                or UNAVAILABLE.search(container.get_text(" ", strip=True))):
            continue
        key = _key(title, parser)
        price = _price(price_el.get_text())
        link = card.select_one("a[href]")
        if key and price:
            href = link.get("href", "").split("?")[0] if link else ""
            offers.append({"key": key, "source": "Reliance Digital", "price": price,
                           "url": "https://www.reliancedigital.in" + href, "title": title})
    return offers


def plausible(offer, apple_price):
    if apple_price:
        return (MIN_SHARE_OF_APPLE_PRICE * apple_price <= offer["price"]
                <= MAX_SHARE_OF_APPLE_PRICE * apple_price)
    return offer["price"] >= FLOOR_WITHOUT_APPLE_PRICE


def best_prices(source_offers, apple):
    """{source: [offer]} -> {"model storage": entry}: the lowest plausible
    price per model + storage across sources, with every source's price."""
    by_key = {}
    for source, offers in source_offers.items():
        for offer in offers:
            key = tuple(offer["key"])
            apple_offer = apple.get(key)
            if not plausible(offer, apple_offer["price"] if apple_offer else None):
                logger.warning(f"  Ignoring implausible {source} price {offer['price']} for {key}")
                continue
            current = by_key.setdefault(key, {}).get(source)
            if current is None or offer["price"] < current["price"]:
                by_key[key][source] = offer
    result = {}
    for (model, storage), per_source in by_key.items():
        best = min(per_source.values(), key=lambda o: o["price"])
        result[f"{model} {storage}"] = {
            "model_type": model, "storage": storage,
            "best_price": best["price"], "best_source": best["source"], "best_url": best["url"],
            "offers": sorted(({k: o[k] for k in ("source", "price", "url")} for o in per_source.values()),
                             key=lambda o: o["price"]),
        }
    return result


class IndiaPriceUpdater:
    # Flipkart answered 503 after ~10 quick searches (2026-10-05).
    RETRY_STATUSES = {429, 503}
    RETRY_WAIT_SECONDS = 20

    def __init__(self, output_dir, session=None, delay_seconds=4):
        self.output_file = Path(output_dir) / "india_prices.json"
        self.session = session or requests.Session()
        self.session.headers.update({"User-Agent": USER_AGENT, "Accept-Language": "en-IN,en;q=0.9"})
        self.delay_seconds = delay_seconds
        self.parser = SpecParser()

    def _get(self, url):
        response = self.session.get(url, timeout=30)
        if response.status_code in self.RETRY_STATUSES:
            time.sleep(self.RETRY_WAIT_SECONDS)
            response = self.session.get(url, timeout=30)
        response.raise_for_status()
        # Reliance sends no charset, so requests falls back to Latin-1 and
        # "₹" arrives mangled ("â¹"): no price would ever match.
        response.encoding = "utf-8"
        return response.text

    def fetch_apple(self):
        offers = {}
        for url in APPLE_INDIA_PAGES:
            offers.update(parse_apple_india(self._get(url), url, self.parser))
            time.sleep(self.delay_seconds)
        return offers

    def fetch_retailer(self, source):
        parse = parse_flipkart if source == "Flipkart" else parse_reliance
        offers, failures = [], []
        for query in SEARCH_QUERIES:
            # One failed search costs that search, not the whole retailer.
            try:
                html = self._get(RETAILER_SEARCH[source].format(q=requests.utils.quote(query)))
                offers += parse(html, self.parser)
            except requests.RequestException as e:
                failures.append(f"{query}: {e}")
            time.sleep(self.delay_seconds)
        if failures:
            logger.warning(f"India: {source} {len(failures)}/{len(SEARCH_QUERIES)} searches failed: {failures}")
        return offers

    def _previous(self):
        try:
            return json.loads(self.output_file.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return {}

    @staticmethod
    def _fresh_enough(checked_at, now):
        try:
            age = now - datetime.fromisoformat(checked_at)
        except (TypeError, ValueError):
            return False
        return age.total_seconds() / 3600 <= MAX_SOURCE_AGE_HOURS

    def run(self):
        """Fetch every source, keep a failed source's previous prices only
        while they are recent, then write india_prices.json. Never raises:
        the Vietnam update must not depend on this."""
        now = datetime.now()
        previous = self._previous().get("sources", {})
        sources = {}

        def record(name, fetch):
            try:
                offers = fetch()
                if not offers:
                    raise ValueError("no products parsed (blocked or page changed)")
                sources[name] = {"checked_at": now.isoformat(), "status": "fresh", "offers": offers}
                logger.info(f"India: {name} {len(offers)} offers")
            except Exception as e:
                old = previous.get(name)
                if old and self._fresh_enough(old.get("checked_at"), now):
                    sources[name] = {**old, "status": "carried_forward", "error": str(e)}
                    logger.warning(f"India: {name} failed ({e}); keeping prices from {old['checked_at']}")
                else:
                    logger.warning(f"India: {name} failed ({e}); no recent prices to keep")

        record("Apple India", lambda: [{"key": list(k), **v} for k, v in self.fetch_apple().items()])
        for retailer in RETAILER_SEARCH:
            record(retailer, lambda r=retailer: [{**o, "key": list(o["key"])} for o in self.fetch_retailer(r)])

        apple = {tuple(o["key"]): o for o in sources.get("Apple India", {}).get("offers", [])}
        products = best_prices({n: s["offers"] for n, s in sources.items()}, apple)
        payload = {
            "timestamp": now.isoformat(),
            "currency": "INR",
            "sources": sources,
            "products": products,
        }
        self.output_file.write_text(json.dumps(payload, indent=1, ensure_ascii=False), encoding="utf-8")
        logger.info(f"India: {len(products)} model/storage prices written to {self.output_file}")
        return payload
