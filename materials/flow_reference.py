"""Independent Python reference for the workflow bench (assets/wf-bench.js).

Reads materials/wf-day.json (written by build-flow-day.py from the same seed as assets/wf-day.js),
executes each n8n-format workflow over the seeded day against the same mock endpoints, and prints
every count the bench shows. tools: python3 only.

    python3 materials/flow_reference.py            # the ladder, store on and off, all failures on
    python3 materials/flow_reference.py --json     # every combination, as JSON (for the parity check)
"""
import itertools
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DAY = json.loads((ROOT / "wf-day.json").read_text())
M32 = 0xFFFFFFFF


def imul(a, b):
    return (a * b) & M32


def fmix(x):
    x ^= x >> 16
    x = imul(x, 0x85EBCA6B)
    x ^= x >> 13
    x = imul(x, 0xC2B2AE35)
    x ^= x >> 16
    return x & M32


def draw(seed, ev_num, step, attempt):
    h = (imul(ev_num, 0x9E3779B1) ^ imul(step + 1, 0x85EBCA77) ^ imul(attempt + 1, 0xC2B2AE3D) ^ seed) & M32
    return fmix(h) / 4294967296


def get_path(obj, path):
    for part in path.split("."):
        if obj is None:
            return None
        obj = obj.get(part) if isinstance(obj, dict) else None
    return obj


def eval_expr(expr, js, outputs):
    expr = expr.strip()
    m = re.match(r"^\$json\.(.+)$", expr)
    if m:
        return get_path(js, m.group(1))
    m = re.match(r"^\$\('([^']+)'\)\.item\.json\.(.+)$", expr)
    if m:
        return get_path(outputs[m.group(1)], m.group(2))
    raise ValueError("unsupported expression " + expr)


def resolve(value, js, outputs):
    if not isinstance(value, str) or not value.startswith("="):
        return value
    body = value[1:]
    whole = re.match(r"^\{\{([^}]*)\}\}$", body.strip())
    if whole:
        return eval_expr(whole.group(1), js, outputs)

    def sub(m):
        v = eval_expr(m.group(1), js, outputs)
        if v is None:
            return ""
        if isinstance(v, bool):
            return "true" if v else "false"
        if isinstance(v, float) and v.is_integer():
            return str(int(v))
        return str(v)
    return re.sub(r"\{\{([^}]*)\}\}", sub, body)


class World:
    def __init__(self, failures, idem_store):
        self.on = failures
        self.idem_store = idem_store
        self.phase = "main"
        self.attempts = {}
        self.store = {}
        self.deliveries = []
        self.dead_letter = []

    def call(self, method, url, headers, body, ev):
        F = DAY["failures"]
        ev_num = int(ev["event_id"][4:])
        path = re.sub(r"^https?://[^/]+", "", url).split("?")[0]
        if method == "GET" and path.startswith("/crm/customers/"):
            n = self.attempts.get((ev["event_id"], "lookup"), 0)
            self.attempts[(ev["event_id"], "lookup")] = n + 1
            u = draw(DAY["seed"], ev_num, 1, n)
            if self.on["timeouts"] and u < F["lookupTimeout"]:
                return False, "timeout"
            if self.on["errors5xx"] and F["lookupTimeout"] <= u < F["lookupTimeout"] + F["lookup5xx"]:
                return False, "500"
            cid = path.split("/")[-1]
            return True, {"customer_id": cid, "phone": "+1555010" + cid[2:], "name": "Customer " + cid[2:]}
        if method == "POST" and path == "/sms/send":
            k = self.attempts.get((ev["event_id"], "send"), 0)
            self.attempts[(ev["event_id"], "send")] = k + 1
            if self.on["outage"] and self.phase == "main" and F["outageStart"] <= ev["ts"] < F["outageEnd"]:
                return False, "503"
            v = draw(DAY["seed"], ev_num, 2, k)
            if self.on["errors5xx"] and v < F["send5xx"]:
                return False, "500"
            key = headers.get("Idempotency-Key")
            if key and self.idem_store and key in self.store:
                resp = {"status": "duplicate-suppressed", "message_id": self.store[key]}
            else:
                mid = "msg_%d" % (len(self.deliveries) + 1)
                self.deliveries.append({"event_id": body["event_id"], "message_id": mid, "phase": self.phase})
                if key and self.idem_store:
                    self.store[key] = mid
                resp = {"status": "sent", "message_id": mid}
            if self.on["ackLost"] and F["send5xx"] <= v < F["send5xx"] + F["ackLost"]:
                return False, "timeout (sent, response lost)"
            return True, resp
        if method == "POST" and path == "/queue/dead-letter":
            self.dead_letter.append({"event_id": body["event_id"], "ev": ev})
            return True, {"queued": True}
        return False, "404"


def tries_for(node):
    if not node.get("retryOnFail"):
        return 1
    return min(5, max(2, node.get("maxTries") or 3))


def execute(wf, ev, world, bill):
    by_name = {n["name"]: n for n in wf["nodes"]}
    trigger = next(n for n in wf["nodes"] if n["type"] == "n8n-nodes-base.webhook")
    outputs = {trigger["name"]: {"headers": {}, "params": {}, "query": {}, "body": dict(ev)}}
    bill["make"] += 1
    queue = []

    def fan_out(name, outs):
        conns = wf["connections"].get(name, {}).get("main", [])
        for idx, items in enumerate(outs):
            if idx < len(conns):
                for c in conns[idx]:
                    for it in items:
                        queue.append((by_name[c["node"]], it))

    fan_out(trigger["name"], [[outputs[trigger["name"]]]])
    while queue:
        node, js = queue.pop(0)
        p = node["parameters"]
        t = node["type"]
        if t == "n8n-nodes-base.if":
            c = p["conditions"]["conditions"][0]
            left = resolve(c["leftValue"], js, outputs)
            ok = c["operator"]["type"] == "string" and c["operator"]["operation"] == "equals" and str(left) == str(c["rightValue"])
            outs = [[js], []] if ok else [[], [js]]
        elif t == "n8n-nodes-base.set":
            o = {}
            for a in p["assignments"]["assignments"]:
                v = resolve(a["value"], js, outputs)
                o[a["name"]] = float(v) if a["type"] == "number" else v
            bill["make"] += 1
            outs = [[o]]
        elif t == "n8n-nodes-base.httpRequest":
            url = resolve(p["url"], js, outputs)
            headers = {h["name"]: resolve(h["value"], js, outputs) for h in p["headerParameters"]["parameters"]} if p.get("sendHeaders") else {}
            body = {b["name"]: resolve(b["value"], js, outputs) for b in p["bodyParameters"]["parameters"]} if p.get("sendBody") else None
            result = None
            last = None
            for _ in range(tries_for(node)):
                ok, r = world.call(p.get("method", "GET"), url, headers, body, ev)
                bill["make"] += 1
                bill["attempts"] += 1
                if ok:
                    bill["zapier"] += 1
                    result = r
                    break
                last = r
            if result is not None:
                outs = [[result]]
            elif node.get("onError") == "continueErrorOutput":
                outs = [[], [{"error": {"message": last, "node": node["name"]}}]]
            else:
                return "error"
        else:
            raise ValueError("node type not implemented: " + t)
        if outs[0]:
            outputs[node["name"]] = outs[0][0]
        fan_out(node["name"], outs)
    return "success"


def run_day(rung, failures=None, idem_store=True):
    failures = failures or {"timeouts": True, "errors5xx": True, "ackLost": True, "outage": True}
    wf = DAY["workflows"][rung]
    world = World(failures, idem_store)
    bill = {"zapier": 0, "make": 0, "n8n": 0, "attempts": 0}
    runs = failed = redrive = 0
    for ev in DAY["events"]:
        runs += 1
        bill["n8n"] += 1
        if execute(wf, ev, world, bill) == "error":
            failed += 1
    parked_day = len(world.dead_letter)
    if parked_day:
        parked = list(world.dead_letter)
        world.dead_letter = []
        world.phase = "redrive"
        for item in parked:
            runs += 1
            redrive += 1
            bill["n8n"] += 1
            if execute(wf, item["ev"], world, bill) == "error":
                failed += 1
    eligible = sum(1 for e in DAY["events"] if e["type"] == "order")
    per = {}
    for d in world.deliveries:
        per[d["event_id"]] = per.get(d["event_id"], 0) + 1
    delivered = len(per)
    still = sum(1 for d in world.dead_letter if d["event_id"] not in per)
    out = {
        "eligible": eligible, "delivered": delivered, "deliveries": len(world.deliveries),
        "duplicates": len(world.deliveries) - delivered, "lost": eligible - delivered - still,
        "parkedDuringDay": parked_day, "parkedAfterRedrive": still, "runs": runs, "failedRuns": failed,
        "redriveRuns": redrive, "httpAttempts": bill["attempts"],
        "units": {"zapier": bill["zapier"], "make": bill["make"], "n8n": bill["n8n"]},
    }
    for plat, pr in DAY["pricing"].items():
        unit = pr["price"] / pr["units"]
        out["perRun_" + plat] = round(out["units"][plat] * unit / runs, 6)
        out["perDay_" + plat] = round(out["units"][plat] * unit, 4)
    return out


def all_combinations():
    keys = ["timeouts", "errors5xx", "ackLost", "outage"]
    res = {}
    for bits in itertools.product([True, False], repeat=4):
        f = dict(zip(keys, bits))
        for store in (True, False):
            for rung in range(4):
                tag = "r%d-store%d-%s" % (rung, int(store), "".join(str(int(b)) for b in bits))
                res[tag] = run_day(rung, f, store)
    return res


if __name__ == "__main__":
    if "--json" in sys.argv:
        print(json.dumps(all_combinations(), sort_keys=True))
    else:
        for store in (True, False):
            for rung in range(4):
                r = run_day(rung, idem_store=store)
                print("store=%s rung=%d delivered=%d/%d dup=%d lost=%d parked=%d->%d runs=%d red=%d redrive=%d attempts=%d units z%d m%d n%d" % (
                    store, rung, r["delivered"], r["eligible"], r["duplicates"], r["lost"], r["parkedDuringDay"],
                    r["parkedAfterRedrive"], r["runs"], r["failedRuns"], r["redriveRuns"], r["httpAttempts"],
                    r["units"]["zapier"], r["units"]["make"], r["units"]["n8n"]))
