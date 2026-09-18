import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        body = "DEPENDENCY_OK\n" if self.path == "/health" else "NOT_FOUND\n"
        status = 200 if self.path == "/health" else 404
        payload = body.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def log_message(self, fmt, *args):
        print(json.dumps({
            "event": "dependency_http_request",
            "scenario": "19",
            "client": self.client_address[0],
            "message": fmt % args,
        }), flush=True)


print(json.dumps({"event": "lab_dependency_started", "scenario": "19", "port": 8081}), flush=True)
ThreadingHTTPServer(("0.0.0.0", 8081), Handler).serve_forever()
