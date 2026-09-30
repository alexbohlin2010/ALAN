"""Local server for the globe: threaded, with long-lived caching for tiles.

Tile URLs carry ?v=<TILE_V>, so they can be cached as immutable; bump TILE_V in index.html whenever
tiles_rgba is rebuilt. index.html and cities.json are always revalidated.

    python3 serve.py [port]
"""
import sys
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path


class Handler(SimpleHTTPRequestHandler):
    def end_headers(self):
        if self.path.startswith('/tiles_rgba/') or self.path.startswith('/empty.webp'):
            self.send_header('Cache-Control', 'public, max-age=31536000, immutable')
        else:
            self.send_header('Cache-Control', 'no-cache')
        super().end_headers()

    def log_message(self, *a):
        pass


if __name__ == '__main__':
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8766
    root = Path(__file__).resolve().parent
    ThreadingHTTPServer(('127.0.0.1', port), partial(Handler, directory=str(root))).serve_forever()
