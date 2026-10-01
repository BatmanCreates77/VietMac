#!/usr/bin/env python3
"""
Local viewer for scraped price data, with product-link verification.

    python3 macbook_scraper/viewer/server.py
    python3 macbook_scraper/viewer/server.py --data ~/vietmac-automation/macbook_scraper/output/latest_products.json

Then open http://localhost:8765. Link checks run server-side — a browser
page can't fetch other sites itself (CORS) — and fall back to a real Chrome
for pages behind an anti-bot challenge.
"""

import argparse
import json
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

sys.path.insert(0, str(Path(__file__).parent))
from link_check import PageFetcher, evaluate

VIEWER_DIR = Path(__file__).parent
DEFAULT_DATA = VIEWER_DIR.parent / 'output' / 'latest_products.json'


def make_handler(data_path, fetcher):
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, fmt, *args):
            pass

        def _send(self, status, body, content_type):
            payload = body.encode('utf-8') if isinstance(body, str) else body
            self.send_response(status)
            self.send_header('Content-Type', content_type)
            self.send_header('Content-Length', str(len(payload)))
            self.send_header('Cache-Control', 'no-store')
            self.end_headers()
            self.wfile.write(payload)

        def _json(self, status, obj):
            self._send(status, json.dumps(obj, ensure_ascii=False), 'application/json; charset=utf-8')

        def _load_data(self):
            with open(data_path, encoding='utf-8') as f:
                return json.load(f)

        def do_GET(self):
            parsed = urlparse(self.path)
            if parsed.path in ('/', '/index.html'):
                return self._send(200, (VIEWER_DIR / 'index.html').read_bytes(), 'text/html; charset=utf-8')

            if parsed.path == '/api/data':
                try:
                    data = self._load_data()
                except (OSError, json.JSONDecodeError) as e:
                    return self._json(500, {'error': f'could not read {data_path}: {e}'})
                return self._json(200, {'source': str(data_path), 'data': data})

            if parsed.path == '/api/check':
                # Look the product up server-side by index rather than taking a
                # URL from the query string, so this endpoint can only ever
                # fetch URLs that are actually in the scraped data.
                try:
                    index = int(parse_qs(parsed.query)['i'][0])
                    product = self._load_data()['products'][index]
                except (KeyError, ValueError, IndexError, OSError, json.JSONDecodeError):
                    return self._json(400, {'error': 'unknown product index'})
                fetched = fetcher.fetch(product['url']) if product.get('url') else {}
                return self._json(200, evaluate(product, fetched))

            self._send(404, 'not found', 'text/plain')

    return Handler


def main():
    parser = argparse.ArgumentParser(description='Local viewer for scraped MacBook prices')
    parser.add_argument('--data', type=Path, default=DEFAULT_DATA,
                        help=f'latest_products.json to view (default: {DEFAULT_DATA})')
    parser.add_argument('--port', type=int, default=8765)
    args = parser.parse_args()

    data_path = args.data.expanduser().resolve()
    if not data_path.exists():
        sys.exit(f'Data file not found: {data_path}')

    fetcher = PageFetcher()
    # Bound to localhost only: /api/check makes outbound requests and drives
    # a browser, which shouldn't be reachable from the network.
    server = ThreadingHTTPServer(('127.0.0.1', args.port), make_handler(data_path, fetcher))
    print(f'Viewing {data_path}')
    print(f'Open http://localhost:{args.port}  (Ctrl+C to stop)')
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        fetcher.close()
        server.server_close()


if __name__ == '__main__':
    main()
