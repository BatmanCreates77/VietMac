#!/usr/bin/env python3
"""
BaseScraper - shared contract for all shop scrapers.

fetch_html() and parse_products() are split deliberately: parse_products()
must be a pure function (HTML in, product list out, no network I/O) so it
can be tested against frozen HTML fixtures without hitting the live site.
Adding a 5th shop means subclassing this and implementing the three
abstract methods; the retry loop, price cleaning, and specs-dict shape
are shared.
"""

from abc import ABC, abstractmethod
import re
import time
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from utils.spec_parser import SpecParser

logger = logging.getLogger(__name__)

# Product lines the site tracks. Shops' Mac pages also list Studio Display
# and accessories; those don't match and are skipped.
MAC_NAME_PATTERN = re.compile(r'\b(?:MacBook|Mac\s*mini|iMac|Mac\s*Studio)\b', re.IGNORECASE)
IPHONE_NAME_PATTERN = re.compile(r'\biPhone\b', re.IGNORECASE)
# On the shops' iPhone pages, but not a new phone at a comparable price:
# accessories, used stock, and carrier bundles ("iPhone 16e 128GB SIM
# Viettel" at FPTShop, sold cheaper with a contract).
IPHONE_EXCLUDE_PATTERN = re.compile(
    r'\b(?:ốp|cường lực|dán|cáp|sạc|tai nghe|case|cũ|like new|trôi bảo hành|SIM\s+\w+)\b',
    re.IGNORECASE,
)


class BaseScraper(ABC):
    shop_name: str
    base_url: str
    # 'mac' or 'iphone'. Each shop's product lines are scraped, validated
    # and published separately (see `source`), so a broken iPhone page
    # never holds back that shop's Mac prices, or the other way round.
    product_line = 'mac'

    @property
    def source(self):
        """Validation-gate key for this scraper's products. Macs keep the
        bare shop name: every latest_products.json written before iPhones
        were added uses it, and it must still match as last-known-good."""
        if self.product_line == 'mac':
            return self.shop_name
        return f"{self.shop_name}-{self.product_line}"

    def __init__(self):
        self.spec_parser = SpecParser()

    def _clean_price(self, price_text):
        """Extract numeric price from text. Identical across all shops."""
        if not price_text:
            return None
        cleaned = re.sub(r'[^\d]', '', price_text)
        return int(cleaned) if cleaned else None

    @staticmethod
    def _is_mac(raw_name):
        """True for a MacBook, Mac mini, iMac or Mac Studio listing."""
        return bool(raw_name and MAC_NAME_PATTERN.search(raw_name))

    @staticmethod
    def _is_iphone(raw_name):
        """True for a new iPhone sold on its own."""
        return bool(
            raw_name
            and IPHONE_NAME_PATTERN.search(raw_name)
            and not IPHONE_EXCLUDE_PATTERN.search(raw_name)
        )

    def _is_wanted(self, raw_name):
        """Whether a listing belongs to this scraper's product line."""
        if self.product_line == 'iphone':
            return self._is_iphone(raw_name)
        return self._is_mac(raw_name)

    def _parse_model_name(self, name):
        """
        Clean a raw product name into a model name.
        Default is a plain strip (matches TopZone's current behavior).
        Override per-shop when the site's name field needs stripping
        of suffixes/prefixes — do NOT assume shops agree on this.
        """
        if not name:
            return None
        return name.strip()

    def _build_product(self, *, model_name, raw_name, price_text, url,
                        image_url=None, product_id=None, extra_specs_source=None):
        """
        Assemble the product dict in the shared shape. `extra_specs_source`
        is the string handed to SpecParser (defaults to raw_name).
        """
        specs_source = extra_specs_source if extra_specs_source is not None else raw_name
        if self.product_line == 'iphone':
            parsed_specs = self.spec_parser.parse_iphone(specs_source)
        else:
            parsed_specs = self.spec_parser.parse(specs_source)
        price_vnd = self._clean_price(price_text)

        return {
            'model': model_name,
            'raw_name': raw_name,
            'price_vnd': price_vnd,
            'price_text': price_text,
            'url': url,
            'image_url': image_url,
            'shop': self.shop_name,
            'product_line': self.product_line,
            'source': self.source,
            'specs': {
                'model_type': parsed_specs.get('model_type'),
                'chip': parsed_specs.get('chip'),
                'chip_variant': parsed_specs.get('chip_variant'),
                'screen_size': parsed_specs.get('screen_size'),
                'cpu_cores': parsed_specs.get('cpu_cores'),
                'gpu_cores': parsed_specs.get('gpu_cores'),
                'ram_gb': parsed_specs.get('ram_gb'),
                'storage_gb': parsed_specs.get('storage_gb'),
                'storage_display': parsed_specs.get('storage_display'),
                'year': parsed_specs.get('year'),
            },
            'product_id': product_id if product_id is not None else parsed_specs.get('id'),
            'clean_name': parsed_specs.get('clean_name'),
        }

    @abstractmethod
    def page_urls(self):
        """Return the list of listing-page URLs to scrape for this shop."""
        raise NotImplementedError

    @abstractmethod
    def fetch_html(self, url, retry=3):
        """Fetch raw HTML for one listing page. May use requests, Playwright,
        or SeleniumBase UC depending on the shop. Returns None on failure
        after retries."""
        raise NotImplementedError

    @abstractmethod
    def parse_products(self, html):
        """Pure function: parse products out of already-fetched HTML.
        MUST NOT perform network I/O — this is what fixture tests call
        directly."""
        raise NotImplementedError

    def scrape(self):
        """Orchestrate fetch -> parse -> assemble result, shared by every
        shop."""
        logger.info("=" * 80)
        logger.info(f"Starting {self.shop_name} scraper...")
        logger.info("=" * 80)

        all_products = []
        seen_urls = set()

        for url in self.page_urls():
            logger.info(f"\nScraping: {url}")
            html = self.fetch_html(url)

            if html:
                products = self.parse_products(html)
                for product in products:
                    product_url = product.get('url')
                    if product_url and product_url not in seen_urls:
                        seen_urls.add(product_url)
                        all_products.append(product)
                logger.info(f"Found {len(products)} models from this page ({len(all_products)} unique total)")
            else:
                logger.warning(f"Failed to scrape {url}")

            time.sleep(self.page_delay_seconds())

        logger.info("=" * 80)
        logger.info(f"{self.shop_name} scraping complete: {len(all_products)} total unique products")
        logger.info("=" * 80)

        if all_products:
            return {
                'success': True,
                'shop': self.source,
                'products': all_products,
                'count': len(all_products),
            }
        return {
            'success': False,
            'shop': self.source,
            'error': self.failure_message(),
            'products': [],
            'count': 0,
        }

    def page_delay_seconds(self):
        """Polite delay between listing pages. Override per-shop."""
        return 5

    def failure_message(self):
        """Error string used when a shop returns zero products across all pages."""
        return 'No products found'
