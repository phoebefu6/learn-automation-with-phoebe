"""Build the seeded day of events and the four n8n-format workflows for the workflow bench.

Writes:
  assets/wf-day.js              window.WF_DAY = {events, workflows, failures, pricing}
  assets/workflows/rung-1..4.json  the same four workflows as plain n8n import files

Everything is generated with json.dumps, never string interpolation.
Run from the repo root:  python3 materials/build-flow-day.py
"""
import json
import random
from pathlib import Path

SEED = 1205  # after xkcd 1205, "Is It Worth the Time?"
N_EVENTS = 600
DAY_START = 7 * 3600   # 07:00
DAY_END = 22 * 3600    # 22:00

ROOT = Path(__file__).resolve().parent.parent
rng = random.Random(SEED)

# ---------- the day ----------
times = sorted(rng.randint(DAY_START, DAY_END - 1) for _ in range(N_EVENTS))
events = []
for i, ts in enumerate(times):
    r = rng.random()
    etype = "order" if r < 0.60 else ("signup" if r < 0.85 else "refund")
    events.append({
        "event_id": "evt_%04d" % (i + 1),
        "ts": ts,
        "type": etype,
        "customer_id": "c_%03d" % rng.randint(1, 240),
        "amount": rng.randint(8, 180) if etype != "signup" else 0,
    })

# ---------- the declared failure mix (per attempt, per step) ----------
FAILURES = {
    "lookupTimeout": 0.02,   # CRM lookup times out
    "lookup5xx": 0.03,       # CRM lookup returns 500
    "send5xx": 0.03,         # SMS provider rejects with 500 before sending anything
    "ackLost": 0.04,         # SMS provider SENDS the message, then the response is lost (client sees a timeout)
    "outageStart": 13 * 3600,          # SMS provider returns 503 for events arriving 13:00 ...
    "outageEnd": 13 * 3600 + 30 * 60,  # ... until 13:30
    "redriveAt": 23 * 3600 + 30 * 60,  # the dead-letter redrive runs once, at 23:30
}

# ---------- pricing, read at source 2026-10-05 (re-verify before delivery) ----------
PRICING = {
    "zapier": {"label": "Zapier task", "plan": "Professional, 750 tasks, billed monthly",
               "price": 29.99, "units": 750, "currency": "USD", "unit": "task",
               "source": "https://zapier.com/pricing"},
    "make": {"label": "Make credit (was: operation)", "plan": "Core, 10,000 credits, as displayed",
             "price": 9.00, "units": 10000, "currency": "USD", "unit": "credit",
             "source": "https://www.make.com/en/pricing"},
    "n8n": {"label": "n8n execution", "plan": "Cloud Starter, 2,500 executions, as displayed",
            "price": 20.00, "units": 2500, "currency": "EUR", "unit": "execution",
            "source": "https://n8n.io/pricing/"},
}

MOCK = "http://127.0.0.1:8787"


def node(nid, name, ntype, version, pos, params, **settings):
    n = {"id": nid, "name": name, "type": ntype, "typeVersion": version,
         "position": pos, "parameters": params}
    n.update(settings)
    return n


def workflow(rung):
    """index 0..3 = rungs 1..4: no retry, retry everything, + idempotency key, + dead-letter queue"""
    retry = rung >= 1
    keyed = rung >= 2
    dlq = rung >= 3
    retry_settings = {"retryOnFail": True, "maxTries": 3, "waitBetweenTries": 5000} if retry else {}
    err = {"onError": "continueErrorOutput"} if dlq else {}

    send_headers = [{"name": "Idempotency-Key", "value": "={{ $('Shape the message').item.json.event_id }}"}] if keyed else []
    send_params = {
        "method": "POST",
        "url": MOCK + "/sms/send",
        "sendHeaders": bool(send_headers),
        "headerParameters": {"parameters": send_headers},
        "sendBody": True,
        "contentType": "json",
        "specifyBody": "keypair",
        "bodyParameters": {"parameters": [
            {"name": "event_id", "value": "={{ $('Shape the message').item.json.event_id }}"},
            {"name": "to", "value": "={{ $json.phone }}"},
            {"name": "text", "value": "=Order {{ $('Shape the message').item.json.event_id }} confirmed, {{ $('Shape the message').item.json.amount }} paid. Thank you."},
        ]},
        "options": {"timeout": 10000},
    }
    nodes = [
        node("n1", "Order webhook", "n8n-nodes-base.webhook", 2, [0, 300],
             {"httpMethod": "POST", "path": "orders", "responseMode": "onReceived", "options": {}},
             webhookId="automation-bench-orders"),
        node("n2", "Is it an order?", "n8n-nodes-base.if", 2.2, [220, 300],
             {"conditions": {
                 "options": {"caseSensitive": True, "leftValue": "", "typeValidation": "strict", "version": 2},
                 "conditions": [{"id": "c1", "leftValue": "={{ $json.body.type }}", "rightValue": "order",
                                 "operator": {"type": "string", "operation": "equals"}}],
                 "combinator": "and"}, "options": {}}),
        node("n3", "Shape the message", "n8n-nodes-base.set", 3.4, [440, 200],
             {"mode": "manual", "includeOtherFields": False, "assignments": {"assignments": [
                 {"id": "a1", "name": "event_id", "value": "={{ $json.body.event_id }}", "type": "string"},
                 {"id": "a2", "name": "customer_id", "value": "={{ $json.body.customer_id }}", "type": "string"},
                 {"id": "a3", "name": "amount", "value": "={{ $json.body.amount }}", "type": "number"},
             ]}, "options": {}}),
        node("n4", "Look up customer", "n8n-nodes-base.httpRequest", 4.2, [660, 200],
             {"method": "GET",
              "url": "=" + MOCK + "/crm/customers/{{ $json.customer_id }}?event_id={{ $json.event_id }}",
              "options": {"timeout": 10000}}, **retry_settings, **err),
        node("n5", "Send the SMS", "n8n-nodes-base.httpRequest", 4.2, [880, 200],
             send_params, **retry_settings, **err),
    ]
    connections = {
        "Order webhook": {"main": [[{"node": "Is it an order?", "type": "main", "index": 0}]]},
        "Is it an order?": {"main": [[{"node": "Shape the message", "type": "main", "index": 0}], []]},
        "Shape the message": {"main": [[{"node": "Look up customer", "type": "main", "index": 0}]]},
        "Look up customer": {"main": [[{"node": "Send the SMS", "type": "main", "index": 0}]]},
    }
    if dlq:
        nodes.append(node("n6", "Park in dead-letter queue", "n8n-nodes-base.httpRequest", 4.2, [1100, 380],
                          {"method": "POST", "url": MOCK + "/queue/dead-letter", "sendBody": True,
                           "contentType": "json", "specifyBody": "keypair",
                           "bodyParameters": {"parameters": [
                               {"name": "event_id", "value": "={{ $('Shape the message').item.json.event_id }}"}]},
                           "options": {}}))
        connections["Look up customer"]["main"].append([{"node": "Park in dead-letter queue", "type": "main", "index": 0}])
        connections["Send the SMS"] = {"main": [[], [{"node": "Park in dead-letter queue", "type": "main", "index": 0}]]}
    names = ["No retry", "Retry everything", "Retry with an idempotency key", "Plus a dead-letter queue"]
    return {"name": "Order SMS - rung %d - %s" % (rung + 1, names[rung]), "nodes": nodes,
            "connections": connections, "active": False,
            "settings": {"executionOrder": "v1"}, "pinData": {}}


workflows = [workflow(r) for r in range(4)]
outdir = ROOT / "assets" / "workflows"
outdir.mkdir(parents=True, exist_ok=True)
for r, wf in enumerate(workflows):
    (outdir / ("rung-%d.json" % (r + 1))).write_text(json.dumps(wf, indent=2) + "\n")

payload = {"seed": SEED, "events": events, "failures": FAILURES, "pricing": PRICING, "workflows": workflows}
(ROOT / "assets" / "wf-day.js").write_text(
    "/* wf-day.js - generated by materials/build-flow-day.py (seed %d). Do not edit by hand. */\n" % SEED
    + "(function (root) {\n  var D = " + json.dumps(payload, separators=(",", ":")) + ";\n"
    + "  if (typeof module !== \"undefined\" && module.exports) module.exports = D;\n"
    + "  else root.WF_DAY = D;\n})(typeof window !== \"undefined\" ? window : this);\n")
(ROOT / "materials" / "wf-day.json").write_text(json.dumps(payload) + "\n")

orders = sum(1 for e in events if e["type"] == "order")
in_outage = sum(1 for e in events if e["type"] == "order" and FAILURES["outageStart"] <= e["ts"] < FAILURES["outageEnd"])
print("events", len(events), "orders", orders, "orders in outage", in_outage)
