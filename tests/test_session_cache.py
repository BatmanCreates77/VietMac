"""
Coverage for the free Cloudflare-cookie-reuse mechanism (Phase 5, Option A):
solve the challenge once with a real browser, cache the resulting cookies,
and let subsequent runs skip the browser entirely until the cache expires
or gets rejected by the live site.
"""
import sys
import time
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(REPO_ROOT / "macbook_scraper"))

from utils import session_cache


@pytest.fixture(autouse=True)
def isolated_cache_dir(tmp_path, monkeypatch):
    """Never touch the real macbook_scraper/.cache/sessions/ directory."""
    monkeypatch.setattr(session_cache, "CACHE_DIR", tmp_path / "sessions")


def selenium_cookies(expiry=None):
    cookie = {'name': 'cf_clearance', 'value': 'abc123', 'domain': '.fptshop.com.vn'}
    if expiry is not None:
        cookie['expiry'] = expiry
    return [cookie, {'name': 'other', 'value': 'xyz', 'domain': '.fptshop.com.vn'}]


def test_save_then_load_roundtrips():
    session_cache.save_session('fptshop', selenium_cookies(expiry=time.time() + 3600), 'UA/1.0')

    loaded = session_cache.load_session('fptshop')

    assert loaded is not None
    assert loaded['cookies'] == {'cf_clearance': 'abc123', 'other': 'xyz'}
    assert loaded['user_agent'] == 'UA/1.0'


def test_load_returns_none_when_no_cache_exists():
    assert session_cache.load_session('fptshop') is None


def test_expired_cookie_is_not_returned():
    session_cache.save_session('fptshop', selenium_cookies(expiry=time.time() - 10), 'UA/1.0')

    assert session_cache.load_session('fptshop') is None


def test_cookie_without_expiry_uses_default_ttl_fallback():
    session_cache.save_session('fptshop', selenium_cookies(expiry=None), 'UA/1.0')

    # Should still be valid immediately after saving (within the fallback TTL)
    assert session_cache.load_session('fptshop') is not None


def test_invalidate_removes_cache():
    session_cache.save_session('fptshop', selenium_cookies(expiry=time.time() + 3600), 'UA/1.0')
    assert session_cache.load_session('fptshop') is not None

    session_cache.invalidate_session('fptshop')

    assert session_cache.load_session('fptshop') is None


def test_invalidate_on_missing_cache_does_not_raise():
    session_cache.invalidate_session('never_saved_shop')  # must not raise


@pytest.mark.parametrize("status_code,html,expected", [
    (403, "anything", True),
    (200, "<html>Just a moment...</html>", True),
    (200, "<html>Checking your browser - Cloudflare</html>", True),
    (200, "<html><body>MacBook Pro listing page</body></html>", False),
    (200, "", False),
    (200, None, False),
])
def test_is_challenge_response(status_code, html, expected):
    assert session_cache.is_challenge_response(status_code, html) is expected


def test_shops_have_independent_caches():
    session_cache.save_session('fptshop', selenium_cookies(expiry=time.time() + 3600), 'UA-fpt')
    session_cache.save_session('topzone', selenium_cookies(expiry=time.time() + 3600), 'UA-tz')

    assert session_cache.load_session('fptshop')['user_agent'] == 'UA-fpt'
    assert session_cache.load_session('topzone')['user_agent'] == 'UA-tz'
