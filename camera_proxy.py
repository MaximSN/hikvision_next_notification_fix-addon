#!/usr/bin/env python3
import http.server
import http.client
import socketserver
import datetime
import sys
import os

# Чтение конфигурации из переменных окружения (Home Assistant передаёт параметры через env)
LISTEN_PORT = int(os.environ.get("LISTEN_PORT", 8234))
TARGET_HOST = os.environ.get("TARGET_HOST", "192.168.0.32")
TARGET_PORT = int(os.environ.get("TARGET_PORT", 80))
FORCED_HOST_HEADER = os.environ.get("HOST_HEADER_VALUE", "192.168.0.32")

def ts():
    """Возвращает текущую дату и время в формате 'YYYY-MM-DD HH:MM:SS'."""
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

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
        headers = {k: v for k, v in self.headers.items() if k.lower() != "host"}
        headers["Host"] = FORCED_HOST_HEADER

        conn = http.client.HTTPConnection(TARGET_HOST, TARGET_PORT, timeout=10)
        try:
            conn.request(method, self.path, body=body, headers=headers)
            response = conn.getresponse()
            response_body = response.read()
            self.send_response(response.status, response.reason)
            for key, value in response.getheaders():
                if key.lower() not in ("transfer-encoding", "connection", "content-length"):
                    self.send_header(key, value)
            self.send_header("Content-Length", str(len(response_body)))
            self.end_headers()
            self.wfile.write(response_body)
        except Exception as e:
            sys.stderr.write(f"[{ts()}] [ERROR] {e}\n")
            self.send_error(502, "Bad Gateway")
        finally:
            conn.close()

    def log_message(self, format, *args):
        sys.stderr.write(f"[{ts()}] [{self.address_string()}] {format % args}\n")

class ThreadingHTTPServer(socketserver.ThreadingMixIn, http.server.HTTPServer):
    daemon_threads = True

if __name__ == "__main__":
    server = ThreadingHTTPServer(("0.0.0.0", LISTEN_PORT), ProxyHandler)
    print(f"[{ts()}] Listening on 0.0.0.0:{LISTEN_PORT} -> {TARGET_HOST}:{TARGET_PORT} (Host: {FORCED_HOST_HEADER})", flush=True)
    server.serve_forever()