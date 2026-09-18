import json
import os
import time
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer


DEPENDENCY_URL = os.environ.get("DEPENDENCY_URL", "http://lab-dependency:8081/health")
last_success = 1
last_duration = 0.0


def log(event, **fields):
    print(json.dumps({"event": event, "scenario": "19", **fields}), flush=True)


def call_dependency():
    global last_success, last_duration
    start = time.monotonic()
    try:
        with urllib.request.urlopen(DEPENDENCY_URL, timeout=2) as response:
            body = response.read().decode("utf-8", errors="replace")
            last_success = int(response.status == 200 and "DEPENDENCY_OK" in body)
    except (urllib.error.URLError, TimeoutError, OSError) as error:
        last_success = 0
        log("dependency_call_failed", dependency=DEPENDENCY_URL, error=str(error))
    last_duration = time.monotonic() - start
    return last_success


class Handler(BaseHTTPRequestHandler):
    def reply(self, status, body, content_type="text/plain; charset=utf-8"):
        payload = body.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def do_GET(self):
        if self.path == "/health":
            self.reply(200, "LAB_APP_OK\n")
            return

        if self.path == "/feature":
            if call_dependency():
                self.reply(200, "FEATURE_OK\n")
            else:
                self.reply(503, "FEATURE_DEPENDENCY_UNAVAILABLE\n")
            return

        if self.path == "/metrics":
            metrics = (
                "# HELP lab_dependency_request_success Last dependency request result.\n"
                "# TYPE lab_dependency_request_success gauge\n"
                f'lab_dependency_request_success{{scenario="19",service="lab-dependency"}} {last_success}\n'
                "# HELP lab_dependency_request_duration_seconds Last dependency request duration.\n"
                "# TYPE lab_dependency_request_duration_seconds gauge\n"
                f'lab_dependency_request_duration_seconds{{scenario="19",service="lab-dependency"}} {last_duration:.6f}\n'
            )
            self.reply(200, metrics, "text/plain; version=0.0.4; charset=utf-8")
            return

        self.reply(404, "NOT_FOUND\n")

    def log_message(self, fmt, *args):
        log("http_request", client=self.client_address[0], message=fmt % args)


log("lab_app_started", dependency=DEPENDENCY_URL, port=8080)
ThreadingHTTPServer(("0.0.0.0", 8080), Handler).serve_forever()
