#!/usr/bin/env python3
"""Verify that your proxy is actually injecting the required identifier header.

A local loopback listener is started, one request is sent through the proxy to
it, and the headers the proxy delivered are echoed back. Zero traffic goes to
the target -- this only proves the proxy rule is live before you rely on it.

Usage:
    bin/header-check.py                       # proxy 127.0.0.1:8080
    bin/header-check.py 8080
    bin/header-check.py 8080 X-Bug-Bounty-MyHandle
"""
import subprocess
import sys
import threading
import time
from http.server import BaseHTTPRequestHandler, HTTPServer

PORT = 9999
received: list[str] = []


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        received.append("\n".join(f"{k}: {v}" for k, v in self.headers.items()))
        body = received[-1].encode()
        self.send_response(200)
        self.send_header("Content-Type", "text/plain")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *args):
        pass


def main() -> int:
    proxy_port = sys.argv[1] if len(sys.argv) > 1 else "8080"
    needle = (sys.argv[2] if len(sys.argv) > 2 else "").lower()

    server = HTTPServer(("127.0.0.1", PORT), Handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    time.sleep(0.5)

    try:
        subprocess.run(
            ["curl", "-s", "-x", f"http://127.0.0.1:{proxy_port}",
             "--max-time", "10", f"http://127.0.0.1:{PORT}/"],
            capture_output=True, timeout=15,
        )
    except subprocess.TimeoutExpired:
        print("curl timed out -- is the proxy listening on that port?")
        server.shutdown()
        return 1

    server.shutdown()

    if not received:
        print("No request reached the listener. The proxy may be bypassing localhost.")
        return 1

    print("=== headers the proxy forwarded ===")
    print(received[-1])

    if needle:
        print("\n=== verdict ===")
        print(f"{needle}: {'PRESENT' if needle in received[-1].lower() else 'MISSING'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
