#!/usr/bin/env python3
"""
CellphoneS Scraper - Playwright for every listing page.

Plain HTTP used to be used for most pages, but CellphoneS now serves an
obfuscated JS challenge (Server: Byte-nginx) to non-browser clients, and its
Air/Pro category pages only render products in a real browser anyway — over
HTTP they always parsed to 0 products (live check 2026-10-01: 20 and 18 via
Playwright).
"""

from bs4 import BeautifulSoup
import re
import time
import logging
import sys
from pathlib import Path
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout

sys.path.insert(0, str(Path(__file__).parent.parent))
from scrapers.base_scraper import BaseScraper

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class CellphonesScraper(BaseScraper):
    shop_name = 'cellphones'
    base_url = 'https://cellphones.com.vn'

    def _parse_model_name(self, name):
        """Parse Mac model name and extract specs"""
        if not name:
            return None

        name = name.strip()
        name = re.sub(r'\s*\|\s*Chính hãng.*', '', name)
        name = re.sub(r'\s*Chính hãng.*', '', name)

        return name

    def page_urls(self):
        return [
            'https://cellphones.com.vn/laptop/mac.html',
            'https://cellphones.com.vn/laptop/mac/macbook-pro/macbook-pro-2025.html',
            'https://cellphones.com.vn/laptop/mac/macbook-air.html',
            'https://cellphones.com.vn/laptop/mac/macbook-pro.html',
            'https://cellphones.com.vn/laptop/mac/mini.html',
            'https://cellphones.com.vn/laptop/mac/imac.html',
            'https://cellphones.com.vn/laptop/mac/mac-studio.html',
        ]

    # Listings show 20 cards, then an "Xem thêm N sản phẩm" ("show N more")
    # button: laptop/mac.html held 75 products behind 3 clicks (2026-10-01).
    # Clicked from JS because a newsletter overlay intercepts real clicks.
    MAX_SHOW_MORE_CLICKS = 10
    SHOW_MORE_ATTEMPTS = 3
    CLICK_SHOW_MORE_JS = """() => {
        const button = document.querySelector('a.button__show-more-product');
        if (!button || !/\\d/.test(button.textContent)) return false;
        button.click();
        return true;
    }"""
    # Every card has a price element, but it is sometimes still empty when
    # the cards appear: one 18:00 run saw 17/40 unpriced, a probe 12/12.
    UNPRICED_CARDS_JS = """() => [...document.querySelectorAll('.product-info')]
        .filter(card => !card.querySelector('.product__price--show')?.textContent.trim()).length"""
    PRICE_WAIT_SECONDS = 15

    def fetch_html(self, url, retry=3):
        return self._fetch_with_playwright(url, retry=retry)

    def _expand_listing(self, page):
        for _ in range(self.MAX_SHOW_MORE_CLICKS):
            before = page.locator('.product-info').count()
            if not self._click_show_more(page, before):
                return
            logger.info(f"  Expanded listing: {before} -> {page.locator('.product-info').count()} products")

    def _click_show_more(self, page, before):
        """True once a click has added products. A click that lands before
        the page's scripts are ready does nothing (seen 2026-10-02: the
        iPhone listing stayed at 20 of 38), so it is retried."""
        for attempt in range(self.SHOW_MORE_ATTEMPTS):
            if not page.evaluate(self.CLICK_SHOW_MORE_JS):
                return False
            try:
                page.wait_for_function(
                    f"() => document.querySelectorAll('.product-info').length > {before}",
                    timeout=5000,
                )
                return True
            except PlaywrightTimeout:
                continue
        logger.warning(f"  'Show more' clicked {self.SHOW_MORE_ATTEMPTS}x but no new products appeared")
        return False

    def _wait_for_prices(self, page):
        for _ in range(self.PRICE_WAIT_SECONDS):
            unpriced = page.evaluate(self.UNPRICED_CARDS_JS)
            if unpriced == 0:
                return
            time.sleep(1)
        logger.warning(f"  {unpriced} products still unpriced after {self.PRICE_WAIT_SECONDS}s")

    def _fetch_with_playwright(self, url, retry=3):
        for attempt in range(retry):
            try:
                logger.info(f"Fetching with Playwright: {url} (attempt {attempt + 1}/{retry})")
                with sync_playwright() as p:
                    browser = p.chromium.launch(
                        headless=True,
                        args=['--disable-blink-features=AutomationControlled']
                    )
                    context = browser.new_context(
                        user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                        viewport={'width': 1920, 'height': 1080},
                        locale='vi-VN',
                    )
                    page = context.new_page()

                    logger.info("  Navigating to page...")
                    page.goto(url, wait_until='domcontentloaded', timeout=60000)

                    logger.info("  Waiting for products to load...")
                    try:
                        page.wait_for_selector('.product-item, .product, .item-product', timeout=15000)
                    except:
                        logger.warning("  Product selector not found, continuing anyway...")

                    time.sleep(2)
                    self._expand_listing(page)

                    logger.info("  Scrolling to load all products...")
                    page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
                    time.sleep(2)
                    self._wait_for_prices(page)

                    content = page.content()
                    browser.close()

                    # page.content() is already a correctly-decoded str.
                    # Re-encoding to bytes here made BeautifulSoup guess the
                    # encoding when parsing (no charset sniffing needed for
                    # str input) — it guessed wrong for Vietnamese text,
                    # producing mojibake ("Chính hãng" -> "Ch√≠nh h√£ng") and,
                    # worse, silently swallowing the price element entirely
                    # on affected products (caught live by the validation
                    # gate: 2026-09-19, 4/17 cellphones products rejected
                    # for null price_vnd). Returning the str directly skips
                    # that guess altogether.
                    return content

            except PlaywrightTimeout as e:
                logger.error(f"Timeout error: {e}")
                if attempt < retry - 1:
                    wait_time = (attempt + 1) * 30
                    logger.info(f"Retrying in {wait_time}s...")
                    time.sleep(wait_time)
            except Exception as e:
                logger.error(f"Error with Playwright: {e}")
                if attempt < retry - 1:
                    time.sleep(20)

        return None

    def parse_products(self, html):
        """Parse products from HTML. Pure function, no network I/O."""
        soup = BeautifulSoup(html, 'html.parser')
        products = []

        product_items = soup.select('.product-info')
        logger.info(f"Found {len(product_items)} product items")

        for item in product_items:
            try:
                name_elem = item.select_one('.product__name h3')
                if not name_elem:
                    continue

                raw_name = name_elem.get_text(strip=True)

                if not self._is_wanted(raw_name):
                    continue

                model_name = self._parse_model_name(raw_name)

                price_elem = item.select_one('.product__price--show')
                price_text = price_elem.get_text(strip=True) if price_elem else None

                link_elem = item.select_one('a.product__link')
                url = link_elem.get('href') if link_elem else None
                if url and not url.startswith('http'):
                    url = self.base_url + url if url.startswith('/') else self.base_url + '/' + url

                img_elem = item.select_one('.product__image img')
                image_url = img_elem.get('src') if img_elem else None

                product = self._build_product(
                    model_name=model_name,
                    raw_name=raw_name,
                    price_text=price_text,
                    url=url,
                    image_url=image_url,
                    extra_specs_source=model_name,
                )

                products.append(product)
                logger.info(f"  ✓ {model_name[:60]} - {price_text}")

            except Exception as e:
                logger.error(f"Error parsing product: {e}")
                continue

        return products

    def page_delay_seconds(self):
        return 3

    def failure_message(self):
        return 'No products found'


class CellphonesIphoneScraper(CellphonesScraper):
    product_line = 'iphone'

    def page_urls(self):
        # apple.html lists every iPhone behind "show more"; the series pages
        # are a backstop for listings it misses (duplicates are dropped).
        return [
            'https://cellphones.com.vn/mobile/apple.html',
            'https://cellphones.com.vn/mobile/apple/iphone-18.html',
            'https://cellphones.com.vn/mobile/apple/iphone-duo.html',
            'https://cellphones.com.vn/mobile/apple/iphone-air.html',
            'https://cellphones.com.vn/mobile/apple/iphone-17.html',
            'https://cellphones.com.vn/mobile/apple/iphone-16.html',
        ]

    def _parse_model_name(self, name):
        name = super()._parse_model_name(name)
        return re.sub(r'^(?:Điện thoại|Apple)\s+', '', name) if name else name


if __name__ == '__main__':
    scraper = CellphonesScraper()
    result = scraper.scrape()

    print(f"\n{'='*80}")
    print(f"RESULTS:")
    print(f"{'='*80}")
    print(f"Success: {result['success']}")
    print(f"Products found: {result['count']}")
    print(f"\nSample products:")
    for i, product in enumerate(result['products'][:5], 1):
        print(f"\n{i}. {product['model']}")
        print(f"   Price: {product['price_text']}")
        print(f"   URL: {product['url'][:80]}...")
