"""Récepteur pédagogique interne : notifications dans les logs Docker."""
import json
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer


class Handler(BaseHTTPRequestHandler):
    def do_POST(self):
        if self.path != "/alerts":
            self.send_error(404)
            return
        try:
            size = int(self.headers.get("Content-Length", "0"))
            if not 0 < size <= 1048576:
                raise ValueError("Taille invalide")
            payload = json.loads(self.rfile.read(size))
            alerts = payload["alerts"]
            if not isinstance(alerts, list) or not all(isinstance(a, dict) for a in alerts):
                raise ValueError("Liste attendue")
        except (ValueError, KeyError, TypeError):
            self.send_error(400)
            return
        for alert in alerts:
            print(json.dumps({
                "received_at": datetime.now(timezone.utc).isoformat(),
                "status": alert.get("status"),
                "labels": alert.get("labels", {}),
                "annotations": alert.get("annotations", {}),
                "startsAt": alert.get("startsAt"),
                "endsAt": alert.get("endsAt"),
            }, ensure_ascii=False), flush=True)
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"OK\n")


if __name__ == "__main__":
    ThreadingHTTPServer(("0.0.0.0", 8080), Handler).serve_forever()
