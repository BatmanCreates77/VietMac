"""
Verifies that a scraped product's URL really leads to that product on the
shop's site: the page loads, stays on the shop's domain, names the same
chip, and shows the price we scraped.
"""

import re
import threading
from html import unescape
import time
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup

SHOP_DOMAINS = {
    'cellphones': 'cellphones.com.vn',
    'shopdunk': 'shopdunk.com',
    'fptshop': 'fptshop.com.vn',
    'topzone': 'topzone.vn',
}

USER_AGENT = (
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 '
    '(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36'
)

CHIP_PATTERN = re.compile(r'(m[1-9])(pro|max)?')
SIZE_PATTERN = re.compile(r'(\d+)(gb|tb)')


def page_title(html):
    match = re.search(r'<title[^>]*>(.*?)</title>', html, re.S | re.I)
    return unescape(match.group(1)).strip() if match else ''


def is_real_page(html):
    """False for anti-bot interstitials: Cloudflare's "Just a moment..."
    (FPTShop) and the untitled obfuscated-JS challenge CellphoneS serves to
    non-browser clients."""
    title = page_title(html)
    return bool(title) and 'just a moment' not in title.lower()


class PageFetcher:
    """Plain HTTP first; falls back to one shared real browser (SeleniumBase
    pure CDP mode) for pages behind an anti-bot challenge. The browser is
    serialised behind a lock — it's a single tab."""

    BROWSER_READY_TIMEOUT_SECONDS = 25

    def __init__(self):
        self._browser = None
        self._lock = threading.Lock()

    def fetch(self, url):
        try:
            response = requests.get(url, headers={'User-Agent': USER_AGENT}, timeout=20)
            # Vietnamese shops serve UTF-8 but don't always declare it, and
            # requests then defaults to ISO-8859-1 (mojibake).
            html = response.content.decode('utf-8', 'replace')
            if response.status_code == 200 and is_real_page(html):
                return {'method': 'http', 'http_status': 200, 'final_url': response.url, 'html': html}
            if response.status_code == 404:
                return {'method': 'http', 'http_status': 404, 'final_url': response.url, 'html': html}
        except requests.RequestException:
            pass
        return self._fetch_with_browser(url)

    def _fetch_with_browser(self, url):
        from seleniumbase import sb_cdp

        with self._lock:
            try:
                if self._browser is None:
                    self._browser = sb_cdp.Chrome()
                self._browser.open(url)
                html = ''
                deadline = time.time() + self.BROWSER_READY_TIMEOUT_SECONDS
                while time.time() < deadline:
                    html = self._browser.get_page_source()
                    if is_real_page(html):
                        break
                    time.sleep(2)
                return {
                    'method': 'browser',
                    'http_status': 200 if is_real_page(html) else None,
                    'final_url': self._browser.get_current_url(),
                    'html': html,
                }
            except Exception as e:
                self.close()
                return {'method': 'browser', 'http_status': None, 'final_url': url,
                        'html': '', 'error': str(e)}

    def close(self):
        if self._browser is not None:
            try:
                self._browser.driver.stop()
            except Exception:
                pass
            self._browser = None


def _normalise(text):
    return re.sub(r'[^a-z0-9]', '', text.lower())


def _heading_text(html):
    soup = BeautifulSoup(html, 'html.parser')
    parts = [page_title(html)]
    if soup.h1:
        parts.append(soup.h1.get_text(' ', strip=True))
    og = soup.find('meta', attrs={'property': 'og:title'})
    if og and og.get('content'):
        parts.append(og['content'])
    return ' | '.join(p for p in parts if p)


def format_vnd(price):
    return f"{price:,}".replace(',', '.')


def evaluate(product, fetched):
    """Returns a verdict plus the evidence behind it, so the UI can show why.

    verdict:
      verified — page loads on the shop's domain, no conflicting chip, and
                 the scraped price appears on the page
      check    — page loads and nothing contradicts it, but the scraped
                 price wasn't found (price may have changed since the
                 scrape) or the title's sizes don't include ours
      wrong    — the page names a different chip than ours
      broken   — doesn't load, 404s, leaves the shop's domain, bounces to
                 the homepage, or stays stuck on an anti-bot challenge
    """
    url = product.get('url') or ''
    shop = product.get('shop')
    final_url = fetched.get('final_url') or url
    html = fetched.get('html') or ''
    result = {
        'method': fetched.get('method'),
        'http_status': fetched.get('http_status'),
        'final_url': final_url,
        'redirected': final_url.rstrip('/') != url.rstrip('/'),
        'page_heading': '',
        'price_on_page': None,
        'notes': [],
    }

    def done(verdict, note=None):
        if note:
            result['notes'].append(note)
        result['verdict'] = verdict
        return result

    if not url:
        return done('broken', 'product has no URL')
    if fetched.get('error'):
        return done('broken', f"could not load: {fetched['error']}")
    if fetched.get('http_status') == 404:
        return done('broken', 'page not found (404) — listing removed or URL wrong')
    if not is_real_page(html):
        return done('broken', 'stuck on an anti-bot challenge page')

    final = urlparse(final_url)
    if not final.netloc.endswith(SHOP_DOMAINS.get(shop, '\0')):
        return done('broken', f"left the shop's domain (landed on {final.netloc})")
    if final.path.strip('/') == '':
        return done('broken', 'redirected to the homepage — listing likely removed')

    heading = _heading_text(html)
    result['page_heading'] = heading
    norm_heading = _normalise(heading)

    specs = product.get('specs') or {}
    chip = (specs.get('chip') or '').lower()
    variant = (specs.get('chip_variant') or '').lower()
    page_chips = {c + v for c, v in CHIP_PATTERN.findall(norm_heading)}
    if chip and page_chips and (chip + variant) not in page_chips:
        return done('wrong', f"page title names chip {sorted(page_chips)}, we scraped {chip + variant}")

    our_sizes = set()
    if specs.get('ram_gb'):
        our_sizes.add(f"{specs['ram_gb']}gb")
    if specs.get('storage_display'):
        our_sizes.add(_normalise(specs['storage_display']))
    page_sizes = {n + u for n, u in SIZE_PATTERN.findall(norm_heading)}
    sizes_conflict = bool(our_sizes and page_sizes and not (our_sizes & page_sizes))
    if sizes_conflict:
        result['notes'].append(
            f"title sizes {sorted(page_sizes)} don't include ours {sorted(our_sizes)}"
        )

    price = product.get('price_vnd')
    if price:
        result['price_on_page'] = format_vnd(price) in html or str(price) in html
        if not result['price_on_page']:
            result['notes'].append(
                f"scraped price {format_vnd(price)}đ not found on the page — may have changed since the scrape"
            )

    if result['price_on_page'] and not sizes_conflict:
        return done('verified')
    return done('check')
