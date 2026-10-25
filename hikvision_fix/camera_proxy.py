#!/usr/bin/env python3
import http.server
import http.client
import socketserver
import sys
import os
import datetime

LISTEN_PORT = int(os.environ.get("LISTEN_PORT", 8234))
TARGET_HOST = os.environ.get("TARGET_HOST", "127.0.0.1")
TARGET_PORT = int(os.environ.get("TARGET_PORT", 8123))
FORCED_HOST_HEADER = os.environ.get("HOST_HEADER_VALUE", "localhost")
LOG_LEVEL = os.environ.get("LOG_LEVEL", "info").lower()

LEVELS = {"debug": 10, "info": 20, "warning": 30, "error": 40}
CURRENT_LEVEL = LEVELS.get(LOG_LEVEL, 20)


def ts():
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def log(level, msg):
    if LEVELS.get(level, 20) >= CURRENT_LEVEL:
        sys.stderr.write(f"[{ts()}] [{level.upper()}] {msg}\n")
        sys.stderr.flush()


class ProxyHandler(http.server.BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def do_POST(self):
        self._handle_request("POST")
    def do_GET(self):
        self._handle_request("GET")
    def do_PUT(self):
        self._handle_request("PUT")
    def do_DELETE(self):
        self._handle_request("DELETE")

    def _handle_request(self, method):
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length) if content_length else b""

        log("info", f'[{self.address_string()}] {method} {self.path} ({len(body)} bytes)')

        if CURRENT_LEVEL <= LEVELS["debug"] and body:
            try:
                body_text = body.decode("utf-8", errors="replace")
            except Exception:
                body_text = repr(body)
            log("debug", f"Request body:\n{body_text}")

        headers = {k: v for k, v in self.headers.items() if k.lower() != "host"}
        headers["Host"] = FORCED_HOST_HEADER

        conn = http.client.HTTPConnection(TARGET_HOST, TARGET_PORT, timeout=10)
        try:
            conn.request(method, self.path, body=body, headers=headers)
            response = conn.getresponse()
            response_body = response.read()
            log("debug", f"Upstream response: {response.status} {response.reason}, {len(response_body)} bytes")

            self.send_response(response.status, response.reason)
            for key, value in response.getheaders():
                if key.lower() not in ("transfer-encoding", "connection", "content-length"):
                    self.send_header(key, value)
            self.send_header("Content-Length", str(len(response_body)))
            self.end_headers()
            self.wfile.write(response_body)
        except Exception as e:
            log("error", f"Proxy error: {e}")
            self.send_error(502, "Bad Gateway")
        finally:
            conn.close()

    def log_message(self, format, *args):
        pass  # отключаем стандартный лог, используем свой


class ThreadingHTTPServer(socketserver.ThreadingMixIn, http.server.HTTPServer):
    daemon_threads = True


if __name__ == "__main__":
    server = ThreadingHTTPServer(("0.0.0.0", LISTEN_PORT), ProxyHandler)
    log("info", f"Listening on 0.0.0.0:{LISTEN_PORT} -> {TARGET_HOST}:{TARGET_PORT} (Host: {FORCED_HOST_HEADER}, level: {LOG_LEVEL})")
    server.serve_forever()