"""
Lightweight API proxy for Vercel.
Forwards /api/* requests to the Python backend (deployed on Render/Railway).
Set BACKEND_URL in Vercel environment variables.
"""
from http.server import BaseHTTPRequestHandler
import os
import urllib.request
import urllib.error

BACKEND_URL = os.environ.get("BACKEND_URL", "").rstrip("/")
SKIP_HEADERS = {"host", "connection", "transfer-encoding", "content-length"}


class handler(BaseHTTPRequestHandler):
    def _send_cors(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")

    def _proxy(self, method):
        if not BACKEND_URL:
            self.send_response(503)
            self.send_header("Content-Type", "application/json")
            self._send_cors()
            self.end_headers()
            self.wfile.write(
                b'{"error":"BACKEND_URL is not set. Deploy the backend on Render and add BACKEND_URL in Vercel settings."}'
            )
            return

        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length) if content_length else None

        url = f"{BACKEND_URL}{self.path}"
        headers = {}
        content_type = self.headers.get("Content-Type")
        if content_type:
            headers["Content-Type"] = content_type

        req = urllib.request.Request(url, data=body, headers=headers, method=method)

        try:
            with urllib.request.urlopen(req, timeout=55) as resp:
                self.send_response(resp.status)
                for key, value in resp.headers.items():
                    if key.lower() not in SKIP_HEADERS:
                        self.send_header(key, value)
                self._send_cors()
                self.end_headers()
                self.wfile.write(resp.read())
        except urllib.error.HTTPError as e:
            self.send_response(e.code)
            for key, value in e.headers.items():
                if key.lower() not in SKIP_HEADERS:
                    self.send_header(key, value)
            self._send_cors()
            self.end_headers()
            self.wfile.write(e.read())
        except Exception as e:
            self.send_response(502)
            self.send_header("Content-Type", "application/json")
            self._send_cors()
            self.end_headers()
            self.wfile.write(
                f'{{"error":"Backend unavailable. Check BACKEND_URL and ensure the backend is running. Details: {str(e)}"}}'.encode()
            )

    def do_GET(self):
        self._proxy("GET")

    def do_POST(self):
        self._proxy("POST")

    def do_PUT(self):
        self._proxy("PUT")

    def do_DELETE(self):
        self._proxy("DELETE")

    def do_OPTIONS(self):
        self.send_response(200)
        self._send_cors()
        self.end_headers()
