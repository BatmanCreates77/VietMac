#!/usr/bin/env python3
"""
FPT Shop Scraper - SeleniumBase pure CDP mode
Gets past FPTShop's Cloudflare managed challenge by driving a real Chrome
directly over the DevTools protocol.

Pure CDP mode rather than UC mode: on Apple Silicon, SeleniumBase's UC mode
always uses the Intel chromedriver build (`intel_for_uc = True` in its
sb_install.py), so it silently depends on Rosetta 2 — the 2026-10-01 06:00
scheduled run failed outright when Rosetta was unavailable after a macOS
upgrade. CDP mode uses no chromedriver at all, so it runs natively.
"""

from seleniumbase import sb_cdp
from bs4 import BeautifulSoup
import json
import re
import time
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from scrapers.base_scraper import BaseScraper

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

CHALLENGE_MARKER = 'Just a moment'
# The product card class parse_products() selects on. Waiting for it — not
# just for the challenge to clear — matters: the page can be past the
# challenge with the product grid not yet rendered, which parses as 0.
PRODUCT_READY_MARKER = 'cardInfo'
# A product page is ready once its variant list (every storage/colour SKU
# with price and stock) has been streamed in.
VARIANTS_READY_MARKER = 'variantResult'
# Next.js streams page data as self.__next_f.push([1, "<JSON string>"])
# chunks; joined, they hold the product's variantResult object.
NEXT_FLIGHT_CHUNK = re.compile(r'self\.__next_f\.push\(\[1,\s*("(?:[^"\\]|\\.)*")\]\)')


class FPTShopScraper(BaseScraper):
    shop_name = 'fptshop'
    base_url = 'https://fptshop.com.vn'

    POLL_INTERVAL_SECONDS = 3
    PAGE_READY_TIMEOUT_SECONDS = 30
    RETRY_BACKOFF_SECONDS = 30

    def __init__(self):
        super().__init__()
        self._browser = None

    def _parse_model_name(self, name):
        """Parse and clean Mac model name"""
        if not name:
            return None

        name = name.strip()
        name = re.sub(r'\s*\(.*?\)\s*$', '', name)

        return name

    def page_urls(self):
        return [
            "https://fptshop.com.vn/may-tinh-xach-tay/apple-macbook",
            "https://fptshop.com.vn/may-tinh-xach-tay/macbook-air?kich-thuoc-man-hinh=13-inch&sort=noi-bat",
            "https://fptshop.com.vn/may-tinh-xach-tay/macbook-air?kich-thuoc-man-hinh=15-inch&sort=noi-bat",
            "https://fptshop.com.vn/may-tinh-xach-tay/macbook-pro?kich-thuoc-man-hinh=14-inch&sort=noi-bat",
            "https://fptshop.com.vn/may-tinh-xach-tay/macbook-pro?kich-thuoc-man-hinh=16-inch&sort=noi-bat",
            # Mac mini, iMac and Mac Studio share one listing.
            "https://fptshop.com.vn/may-tinh-de-ban/apple-imac",
        ]

    def scrape(self):
        """One browser for the whole run: Cloudflare is solved on the first
        page and the session's clearance carries over to the rest (verified
        live 2026-10-01: 3 pages in 12s total). Always closed afterwards so
        a scheduled run can never leave a stray Chrome behind."""
        try:
            return super().scrape()
        finally:
            self._close_browser()

    def _close_browser(self):
        if self._browser is not None:
            try:
                self._browser.driver.stop()
            except Exception as e:
                logger.warning(f"  Error closing browser: {e}")
            self._browser = None

    def fetch_html(self, url, retry=3, ready_marker=PRODUCT_READY_MARKER):
        for attempt in range(retry):
            try:
                if self._browser is None:
                    logger.info("Launching Chrome (CDP mode)...")
                    self._browser = sb_cdp.Chrome()
                logger.info(f"  Opening: {url} (attempt {attempt + 1}/{retry})")
                self._browser.open(url)

                html = self._wait_for_products(self._browser, ready_marker)
                if html is not None:
                    return html
                raise Exception(
                    f"page not ready ({ready_marker!r} missing) within {self.PAGE_READY_TIMEOUT_SECONDS}s"
                )
            except Exception as e:
                logger.error(f"  Error fetching {url}: {e}")
                # A broken session (stuck challenge, crashed tab) won't heal
                # by itself — start the next attempt with a fresh browser.
                self._close_browser()
                if attempt < retry - 1:
                    logger.info(f"  Retrying in {self.RETRY_BACKOFF_SECONDS}s...")
                    time.sleep(self.RETRY_BACKOFF_SECONDS)
        return None

    def _wait_for_products(self, browser, ready_marker=PRODUCT_READY_MARKER):
        """Poll until Cloudflare's challenge has cleared AND the product grid
        has rendered. Cloudflare's managed challenge takes a variable time
        per visit (a single fixed wait was the cause of the original false
        "403 Forbidden" failures). Returns the page HTML, or None on timeout."""
        elapsed = 0
        while elapsed <= self.PAGE_READY_TIMEOUT_SECONDS:
            html = browser.get_page_source()
            if CHALLENGE_MARKER not in html and ready_marker in html:
                logger.info(f"  Products ready after ~{elapsed}s")
                browser.scroll_to_bottom()
                time.sleep(2)
                return browser.get_page_source()
            time.sleep(self.POLL_INTERVAL_SECONDS)
            elapsed += self.POLL_INTERVAL_SECONDS
        return None

    def _extract_price_text(self, item):
        """
        The card shows two prices when discounted: the original price in a
        <span class="line-through"> and the actual selling price as its
        parent <p>'s next-sibling <p> — e.g.
            <p><span class="line-through">21.990.000đ</span></p>
            <p class="...b1-semibold">21.290.000đ</p>   <- this one
            <p>Giảm 700.000đ</p>
        Structural (tag position), not exact Tailwind class names, since
        those are auto-generated utility classes prone to churn. Falls
        back to the first non-strikethrough, non-discount-label price text
        when there's no discount at all (untested live — no product on the
        page during verification lacked a discount — but kept as the
        honest fallback for when that happens).
        """
        strikethrough = item.select_one('span.line-through')
        if strikethrough:
            old_price_p = strikethrough.find_parent('p')
            current_price_p = old_price_p.find_next_sibling('p') if old_price_p else None
            if current_price_p:
                return current_price_p.get_text(strip=True)

        for el in item.select('p, span'):
            text = el.get_text(strip=True)
            css_classes = el.get('class') or []
            if (('đ' in text or '₫' in text)
                    and not text.startswith('Giảm')
                    and 'line-through' not in css_classes):
                return text

        return None

    def parse_products(self, html):
        """Parse products from HTML. Pure function, no network I/O."""
        soup = BeautifulSoup(html, 'html.parser')
        products = []

        selectors = [
            '.cardInfo',       # current live selector — verified 2026-09-12 against
                               # the real Next.js-rendered card (Tailwind utility
                               # classes, no semantic product-* class exists anymore)
            '.cdt-product',    # legacy selectors — none matched during the same
            '.product-item',   # verification, kept as harmless fallback in case
            '[data-product]',  # of A/B testing or a partial rollback
            '.product-card',
        ]

        product_items = []
        for selector in selectors:
            product_items = soup.select(selector)
            if product_items:
                logger.info(f"Found {len(product_items)} items with selector: {selector}")
                break

        if not product_items:
            logger.warning("No product items found with any selector")
            return []

        for item in product_items:
            try:
                name_elem = (item.select_one('h3') or
                            item.select_one('.product-name') or
                            item.select_one('[data-title]') or
                            item.find('a', {'title': True}))

                if not name_elem:
                    continue

                raw_name = name_elem.get('title') or name_elem.get_text(strip=True)

                if not self._is_wanted(raw_name):
                    continue

                model_name = self._parse_model_name(raw_name)

                price_text = self._extract_price_text(item)

                link_elem = item.select_one('a')
                url = link_elem.get('href') if link_elem else None
                if url and not url.startswith('http'):
                    url = self.base_url + url if url.startswith('/') else self.base_url + '/' + url

                product = self._build_product(
                    model_name=model_name,
                    raw_name=raw_name,
                    price_text=price_text,
                    url=url,
                    extra_specs_source=raw_name,
                )

                products.append(product)
                logger.info(f"  ✓ {model_name[:60]} - {price_text}")

            except Exception as e:
                logger.error(f"Error parsing product: {e}")
                continue

        return products

    def page_delay_seconds(self):
        return 10

    def failure_message(self):
        return 'Cloudflare block or timeout'


class FPTShopIphoneScraper(FPTShopScraper):
    """The iPhone listing has one card per model at its base storage; every
    storage size is on the model's own page. So: listing -> one product page
    per model -> one product per storage size."""
    product_line = 'iphone'
    VARIANT_PAGE_DELAY_SECONDS = 3

    def page_urls(self):
        return ["https://fptshop.com.vn/dien-thoai/apple-iphone"]

    def _parse_model_name(self, name):
        name = super()._parse_model_name(name)
        return re.sub(r'^(?:Điện thoại|Apple)\s+', '', name) if name else name

    def scrape(self):
        # BaseScraper.scrape, not FPTShopScraper.scrape: that one closes the
        # browser after the listing, and the product pages reuse it.
        try:
            listing = BaseScraper.scrape(self)
            if not listing['success']:
                return listing
            products, seen_urls = [], set()
            for model in listing['products']:
                for product in self._storage_variants(model):
                    if product['url'] not in seen_urls:
                        seen_urls.add(product['url'])
                        products.append(product)
            listing.update(products=products, count=len(products))
            return listing
        finally:
            self._close_browser()

    def _storage_variants(self, model):
        """All storage sizes for one listing card. If the product page fails,
        the card's own base-storage product is kept rather than losing the
        model."""
        html = self.fetch_html(model['url'], retry=2, ready_marker=VARIANTS_READY_MARKER)
        variants = self.parse_variants(html) if html else []
        if not variants:
            logger.warning(f"  No storage variants for {model['model']}; keeping the listing price")
            return [model]
        time.sleep(self.VARIANT_PAGE_DELAY_SECONDS)
        return variants

    def parse_variants(self, html):
        """Pure: a product page's SKUs -> one product per storage size, priced
        at its cheapest in-stock colour. A size with no colour in stock is
        left out: the site lists every row as available."""
        skus = self._variant_skus(html)
        cheapest = {}
        for sku in skus:
            size, price = sku.get('displayName'), sku.get('price')
            if not size or not price or not sku.get('inventory') or not sku.get('slug'):
                continue
            if not self._is_wanted(size):
                continue
            if size not in cheapest or price < cheapest[size]['price']:
                cheapest[size] = sku
        products = []
        for size, sku in cheapest.items():
            products.append(self._build_product(
                model_name=self._parse_model_name(size),
                raw_name=sku.get('name') or size,
                price_text=str(sku['price']),
                url=f"{self.base_url}/{sku['slug'].lstrip('/')}",
                extra_specs_source=size,
            ))
        return products

    @staticmethod
    def _variant_skus(html):
        chunks = []
        for match in NEXT_FLIGHT_CHUNK.finditer(html):
            try:
                chunks.append(json.loads(match.group(1)))
            except json.JSONDecodeError:
                continue
        flight = ''.join(chunks)
        key = '"variantResult":'
        start = flight.find(key)
        if start < 0:
            return []
        try:
            variant_result, _ = json.JSONDecoder().raw_decode(flight, start + len(key))
        except json.JSONDecodeError:
            return []
        skus = variant_result.get('skus') if isinstance(variant_result, dict) else None
        return skus if isinstance(skus, list) else []


if __name__ == '__main__':
    scraper = FPTShopScraper()
    result = scraper.scrape()

    print(f"\n{'='*80}")
    print(f"RESULTS:")
    print(f"{'='*80}")
    print(f"Success: {result['success']}")
    print(f"Products found: {result['count']}")

    if result['products']:
        print(f"\nSample products:")
        for i, product in enumerate(result['products'][:10], 1):
            print(f"\n{i}. {product['model']}")
            print(f"   Price: {product['price_text']}")
            if product.get('url'):
                print(f"   URL: {product['url'][:80]}...")
