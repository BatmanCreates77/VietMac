#!/usr/bin/env python3
"""
SessionCache - reuse a Cloudflare-cleared cookie jar across scraper runs.

Solving a Cloudflare JS challenge (what FPTShopScraper's UC-mode browser
does) is expensive and the highest-risk-of-failure step. The resulting
cf_clearance cookie is valid for a real window of time, not one request —
so the free win here isn't a better solver, it's solving less often:
cache the cookies + User-Agent from a successful browser solve, and let
plain `requests` calls reuse them until they expire or get rejected.
"""

import json
import time
from pathlib import Path

CACHE_DIR = Path(__file__).parent.parent / ".cache" / "sessions"

# Fallback TTL used only when a cookie has no explicit `expiry` (a pure
# session cookie). Conservative on purpose — cf_clearance is normally a
# persistent cookie with a real expiry we read directly; this is a
# placeholder for the rare case it isn't, not a measured value.
DEFAULT_TTL_SECONDS = 60 * 60  # 1 hour

# Substrings that indicate a response is a Cloudflare challenge/block page
# rather than real content. Shared here so both the lightweight
# requests-based check and the full browser-based check use one definition.
CHALLENGE_MARKERS = ('Just a moment', 'Cloudflare', 'Forbidden', 'Attention Required')


def is_challenge_response(status_code, html):
    if status_code == 403:
        return True
    if not html:
        return False
    return any(marker in html for marker in CHALLENGE_MARKERS)


def save_session(shop_name, selenium_cookies, user_agent):
    """selenium_cookies: the list of dicts from driver.get_cookies()."""
    CACHE_DIR.mkdir(parents=True, exist_ok=True)

    cookie_dict = {c['name']: c['value'] for c in selenium_cookies}
    expiries = [c['expiry'] for c in selenium_cookies if c.get('expiry')]
    expires_at = min(expiries) if expiries else time.time() + DEFAULT_TTL_SECONDS

    payload = {
        'cookies': cookie_dict,
        'user_agent': user_agent,
        'saved_at': time.time(),
        'expires_at': expires_at,
    }
    cache_file = CACHE_DIR / f"{shop_name}.json"
    cache_file.write_text(json.dumps(payload), encoding='utf-8')


def load_session(shop_name):
    """Returns {'cookies': {...}, 'user_agent': str} or None if there's no
    cached session or it's expired."""
    cache_file = CACHE_DIR / f"{shop_name}.json"
    if not cache_file.exists():
        return None

    try:
        payload = json.loads(cache_file.read_text(encoding='utf-8'))
    except (json.JSONDecodeError, OSError):
        return None

    if time.time() >= payload.get('expires_at', 0):
        return None

    return {'cookies': payload['cookies'], 'user_agent': payload['user_agent']}


def invalidate_session(shop_name):
    """Called when a cached session gets rejected by the live site (cookie
    revoked server-side before its recorded expiry)."""
    cache_file = CACHE_DIR / f"{shop_name}.json"
    if cache_file.exists():
        cache_file.unlink()
