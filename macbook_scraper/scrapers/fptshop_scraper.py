#!/usr/bin/env python3
"""
FPT Shop Scraper - SeleniumBase UC (Undetected Chrome) mode
Bypasses Cloudflare WAF protection
"""

from seleniumbase import Driver
from bs4 import BeautifulSoup
import requests
import re
import time
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from scrapers.base_scraper import BaseScraper
from utils import session_cache

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class FPTShopScraper(BaseScraper):
    shop_name = 'fptshop'
    base_url = 'https://fptshop.com.vn'

    CHALLENGE_POLL_INTERVAL_SECONDS = 5
    CHALLENGE_MAX_WAIT_SECONDS = 30

    def _parse_model_name(self, name):
        """Parse and clean MacBook model name"""
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
        ]

    def fetch_html(self, url, retry=3):
        """Try a cached, already-Cloudflare-cleared cookie jar first (free,
        no browser launch) before paying the cost of a full UC-mode solve.
        The cache is populated by _fetch_with_uc_mode() on a successful
        solve and reused by every call until it expires or gets rejected."""
        cached_html = self._fetch_with_cached_session(url)
        if cached_html is not None:
            return cached_html

        return self._fetch_with_uc_mode(url, retry=retry)

    def _fetch_with_cached_session(self, url):
        session = session_cache.load_session(self.shop_name)
        if not session:
            return None

        try:
            logger.info("  Trying cached Cloudflare-cleared session (no browser)...")
            response = requests.get(
                url,
                cookies=session['cookies'],
                headers={'User-Agent': session['user_agent']},
                timeout=15,
            )
        except Exception as e:
            logger.warning(f"  Cached-session request failed: {e}")
            return None

        if session_cache.is_challenge_response(response.status_code, response.text):
            logger.warning("  Cached session was rejected (expired/invalidated) — falling back to full solve")
            session_cache.invalidate_session(self.shop_name)
            return None

        logger.info("  Cached session accepted — skipped browser entirely")
        return response.text

    def _wait_for_challenge_to_clear(self, driver):
        """Poll for Cloudflare's managed challenge to resolve instead of a
        single fixed-wait check. Verified live 2026-09-12: the challenge
        cleared in ~5s on one run but the previous fixed 10s-wait-then-
        check design had already logged two straight 'Got 403 Forbidden'
        failures — a single early check was catching the page mid-
        challenge and declaring it a hard failure, when waiting longer
        would have let it clear on its own (Cloudflare's managed
        challenge appears to vary in how long it takes per visit).
        Returns the cleared page_source, or None if it never clears
        within CHALLENGE_MAX_WAIT_SECONDS."""
        elapsed = 0
        while elapsed <= self.CHALLENGE_MAX_WAIT_SECONDS:
            time.sleep(self.CHALLENGE_POLL_INTERVAL_SECONDS)
            elapsed += self.CHALLENGE_POLL_INTERVAL_SECONDS
            page_source = driver.page_source
            if not session_cache.is_challenge_response(200, page_source):
                logger.info(f"  Challenge cleared after ~{elapsed}s")
                return page_source
            logger.info(f"  Still on challenge page at {elapsed}s, continuing to wait...")
        return None

    def _fetch_with_uc_mode(self, url, retry=3):
        """Full SeleniumBase UC mode solve. Expensive and the highest-risk
        step, so a successful solve's cookies get cached for reuse."""
        for attempt in range(retry):
            driver = None
            try:
                logger.info(f"Launching UC Chrome for: {url} (attempt {attempt + 1}/{retry})")

                driver = Driver(
                    uc=True,
                    headless=False,
                    chromium_arg="--disable-blink-features=AutomationControlled",
                )

                logger.info("  Navigating to page...")
                driver.get(url)

                logger.info("  Waiting for Cloudflare challenge to clear...")
                page_source = self._wait_for_challenge_to_clear(driver)
                if page_source is None:
                    raise Exception(
                        f"Cloudflare challenge did not clear within "
                        f"{self.CHALLENGE_MAX_WAIT_SECONDS}s"
                    )

                logger.info("  Scrolling to load all products...")
                driver.execute_script('window.scrollTo(0, document.body.scrollHeight)')
                time.sleep(3)

                html = driver.page_source
                user_agent = driver.execute_script("return navigator.userAgent;")
                cookies = driver.get_cookies()
                driver.quit()

                if not session_cache.is_challenge_response(200, html):
                    session_cache.save_session(self.shop_name, cookies, user_agent)
                    logger.info("  Cached this session's cookies for reuse on future runs")

                return html

            except Exception as e:
                logger.error(f"Error with UC Chrome: {e}")
                if driver:
                    try:
                        driver.quit()
                    except:
                        pass

                if attempt < retry - 1:
                    wait_time = (attempt + 1) * 120  # 2 min, 4 min, 6 min
                    logger.info(f"Retrying in {wait_time}s...")
                    time.sleep(wait_time)

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

                if 'MacBook' not in raw_name:
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
