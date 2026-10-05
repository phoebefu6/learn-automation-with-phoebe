"""The bench's mock endpoints as a real local HTTP server, for running the same workflows on n8n.

    python3 materials/mock_server.py              # listens on http://127.0.0.1:8787
    python3 materials/mock_server.py --no-store   # the break button: ignore Idempotency-Key

Endpoints (identical decisions to assets/wf-bench.js, imported from flow_reference.py):
    GET  /crm/customers/<id>?event_id=evt_0042    may time out (sleeps past the client timeout) or 500
    POST /sms/send                                may 500, may SEND then drop the reply, 503 in the outage
    POST /queue/dead-letter                       always 200
    GET  /log                                     the delivery log and dead-letter list, as JSON
    POST /reset                                   forget attempts, keys, deliveries
The outage applies to events whose ts falls 13:00-13:30, whatever the wall clock says.
tools: python3 standard library only.
"""
import json
import sys
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse, parse_qs

from flow_reference import DAY, World

EVENTS = {e["event_id"]: e for e in DAY["events"]}
FAILS = {"timeouts": True, "errors5xx": True, "ackLost": True, "outage": True}
STORE = "--no-store" not in sys.argv
SLEEP_FOR_TIMEOUT = float(next((a.split("=")[1] for a in sys.argv if a.startswith("--timeout-sleep=")), "12"))
world = World(FAILS, STORE)


class Handler(BaseHTTPRequestHandler):
    def _send(self, code, obj):
        data = json.dumps(obj).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def _route(self, method):
        global world
        u = urlparse(self.path)
        body = None
        if method == "POST":
            n = int(self.headers.get("Content-Length") or 0)
            body = json.loads(self.rfile.read(n) or b"{}")
        if u.path == "/log":
            return self._send(200, {"deliveries": world.deliveries, "deadLetter": [d["event_id"] for d in world.dead_letter]})
        if u.path == "/reset":
            world = World(FAILS, STORE)
            return self._send(200, {"reset": True})
        if u.path.startswith("/crm/"):
            ev = EVENTS[parse_qs(u.query)["event_id"][0]]
        else:
            ev = EVENTS[body["event_id"]]
        headers = {"Idempotency-Key": self.headers.get("Idempotency-Key")} if self.headers.get("Idempotency-Key") else {}
        ok, r = world.call(method, "http://localhost" + self.path, headers, body, ev)
        if ok:
            return self._send(200, r)
        if r.startswith("timeout"):
            time.sleep(SLEEP_FOR_TIMEOUT)  # past the client's timeout: it gives up, the work (if any) is already done
            return self._send(504, {"error": r})
        return self._send(int(r[:3]), {"error": r})

    def do_GET(self):
        self._route("GET")

    def do_POST(self):
        self._route("POST")

    def log_message(self, fmt, *args):
        sys.stderr.write("%s %s\n" % (self.command, self.path))


if __name__ == "__main__":
    print("mock endpoints on http://127.0.0.1:8787  (idempotency store %s)" % ("ON" if STORE else "OFF"), flush=True)
    ThreadingHTTPServer(("127.0.0.1", 8787), Handler).serve_forever()
