#!/usr/bin/env python3
"""Simple SPA server: serves files normally, falls back to index.html for unknown paths."""
import http.server, os, sys

PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 8000

class SPAHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        # Strip query string to find the file
        path = self.path.split('?')[0].lstrip('/')

        # If it's a real file/directory, serve it normally
        if os.path.exists(path) and (os.path.isfile(path) or os.path.isdir(path)):
            super().do_GET()
            return

        # Otherwise, fall back to index.html (let the SPA handle routing)
        self.path = '/index.html'
        super().do_GET()

if __name__ == '__main__':
    http.server.test(HandlerClass=SPAHandler, port=PORT)