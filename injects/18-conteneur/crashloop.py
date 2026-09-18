import json
import os
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer


ACTIVE_FILE = os.environ.get("ACTIVE_FILE", "/state/active")
START_TIME = time.time()
INJECT_ACTIVE = os.path.exists(ACTIVE_FILE)


def log(event, **fields):
    print(json.dumps({"event": event, "scenario": "18", **fields}), flush=True)


def scheduled_crash():
    log("restart_simulation_armed", delay_seconds=20)
    time.sleep(20)
    log("simulated_application_crash", exit_code=1)
    os._exit(1)


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
            self.reply(200, "CRASHLOOP_APP_OK\n")
            return
        if self.path == "/metrics":
            metrics = (
                "# HELP lab_container_start_time_seconds Start time of the test process.\n"
                "# TYPE lab_container_start_time_seconds gauge\n"
                f'lab_container_start_time_seconds{{scenario="18",service="lab-crashloop"}} {START_TIME:.3f}\n'
                "# HELP lab_container_restart_simulation_active Whether restart simulation was active at startup.\n"
                "# TYPE lab_container_restart_simulation_active gauge\n"
                f'lab_container_restart_simulation_active{{scenario="18",service="lab-crashloop"}} {int(INJECT_ACTIVE)}\n'
            )
            self.reply(200, metrics, "text/plain; version=0.0.4; charset=utf-8")
            return
        self.reply(404, "NOT_FOUND\n")

    def log_message(self, fmt, *args):
        log("http_request", client=self.client_address[0], message=fmt % args)


log("lab_crashloop_started", inject_active=INJECT_ACTIVE, port=8082)
if INJECT_ACTIVE:
    threading.Thread(target=scheduled_crash, daemon=True).start()
ThreadingHTTPServer(("0.0.0.0", 8082), Handler).serve_forever()
