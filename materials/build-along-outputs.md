# Real build-along outputs (captured 2026-10-05 in this build)

Internal build document. Every output a session page prints in a code box must come from this file
(or be re-run by the page author). Never invent an output. Paths are relative to the repo root;
on a session page link scripts as `../materials/<file>` and workflows as `../assets/workflows/<file>`.

## Session 2 - n8n locally, the mock endpoints, one order traced

Node requirement (read at source): n8n's docs say "n8n requires a Node.js version between 20.19
and 24.x, inclusive". The npm package n8n@2.41.6 (stable and latest on 2026-10-05) declares
`engines: { node: '>=24.0.0' }`. Teach: install Node 24 (or use Docker). On Node 22.6 this build
could not use the current stable.

```
$ node --version
v24.21.0
$ npx n8n            # first run downloads n8n; the editor is then at http://localhost:5678
$ curl -s http://localhost:5678/healthz
{"status":"ok"}
```
(In this build n8n ran on port 5679 via N8N_PORT because 5678 was reserved; the healthz answer is
the real one. Its log also printed: "Running n8n outside a container is deprecated. Future versions
will require running n8n via the official Docker image.")

Import from the command line (real output):
```
$ n8n import:workflow --input=rung-1.json
Importing 1 workflows...
Successfully imported 1 workflow.
```
Or in the editor: open a new workflow and paste/import the JSON file (no output to paste).

Mock endpoints (real output):
```
$ python3 materials/mock_server.py
mock endpoints on http://127.0.0.1:8787  (idempotency store ON)

$ curl -s "http://127.0.0.1:8787/crm/customers/c_071?event_id=evt_0002"
{"customer_id": "c_071", "phone": "+1555010071", "name": "Customer 071"}

$ curl -s -X POST http://127.0.0.1:8787/sms/send -H 'Content-Type: application/json' \
    -H 'Idempotency-Key: evt_0002' -d '{"event_id":"evt_0002","to":"+1555010071","text":"Order evt_0002 confirmed"}'
{"status": "sent", "message_id": "msg_1"}
$ (the same command again)
{"status": "duplicate-suppressed", "message_id": "msg_1"}
$ curl -s http://127.0.0.1:8787/log
{"deliveries": [{"event_id": "evt_0002", "message_id": "msg_1", "phase": "main"}], "deadLetter": []}
```

One event traced through the same workflow by the bench runner (real output of
`node materials/trace_one.js evt_0002 1`; needs only Node, no n8n):
```
event: {"event_id":"evt_0002","ts":25328,"type":"order","customer_id":"c_071","amount":147}
path:  Order webhook > Is it an order? > Shape the message > Look up customer > Send the SMS
  Order webhook      {"headers":{},"params":{},"query":{},"body":{"event_id":"evt_0002","ts":25328,"type":"order","customer_id":"c_071","amount":147}}
  Is it an order?    {"headers":{},"params":{},"query":{},"body":{"event_id":"evt_0002","ts":25328,"type":"order","customer_id":"c_071","amount":147}}
  Shape the message  {"event_id":"evt_0002","customer_id":"c_071","amount":147}
  Look up customer   {"customer_id":"c_071","phone":"+1555010071","name":"Customer 071"}
  Send the SMS       {"status":"sent","message_id":"msg_1"}
status: success | texts sent: 1 | http tries: 2
```
`node materials/trace_one.js evt_0001 1` (a signup, stops at the IF):
```
event: {"event_id":"evt_0001","ts":25289,"type":"signup","customer_id":"c_187","amount":0}
path:  Order webhook > Is it an order?
status: success | texts sent: 0 | http tries: 0
```
(the per-node lines print too; for evt_0001 only "Order webhook" and "Is it an order?" appear)

Key data-between-steps facts visible above: the webhook wraps the payload in `body`; the Set node
replaces the item with three fields (includeOtherFields off), so the event's `ts` and `type` are
gone after it; the HTTP lookup REPLACES the item with the CRM's answer, so the send step must
reach back with `$('Shape the message').item.json.event_id` to find the event id.

Expressions used in rung-1.json (exact):
- IF left value: `={{ $json.body.type }}` equals `order`
- Set: `event_id` = `={{ $json.body.event_id }}`, `customer_id` = `={{ $json.body.customer_id }}`, `amount` = `={{ $json.body.amount }}` (number)
- Lookup URL: `=http://127.0.0.1:8787/crm/customers/{{ $json.customer_id }}?event_id={{ $json.event_id }}`
- Send body: `to` = `={{ $json.phone }}`, `event_id` = `={{ $('Shape the message').item.json.event_id }}`,
  `text` = `=Order {{ $('Shape the message').item.json.event_id }} confirmed, {{ $('Shape the message').item.json.amount }} paid. Thank you.`

## Session 3 - one workflow priced three ways

`python3 materials/price_three_ways.py` (real output):
```
   500 runs:  1,000 tasks,  2,000 credits,    500 executions | Zapier Professional over, Make Core fits, n8n Starter fits, n8n Pro fits
 3,000 runs:  6,000 tasks, 12,000 credits,  3,000 executions | Zapier Professional over, Make Core over, n8n Starter over, n8n Pro fits
18,000 runs: 36,000 tasks, 72,000 credits, 18,000 executions | Zapier Professional over, Make Core over, n8n Starter over, n8n Pro over
```
The in-page calculator (`data-fn="price"`, input "runs a month, action steps per run") prints
units and per-unit money for the three tools; e.g. input `3000 2` gives 6,000 Zapier tasks ·
$239.92, 9,000 Make credits · $8.10, 3,000 n8n executions · €24.00 (per-unit device: plan price /
included units; the Make count there is runs x (steps + 1) for the trigger).

## Session 5 - backoff, keys, dead letters, alerts

`python3 materials/backoff.py` (real output, seeded):
```
attempt  ceiling  full-jitter wait (s)
      0        1      0.32
      1        2      0.30
      2        4      2.60
      3        8      0.58
      4       16      8.57
      5       32     11.70
      6       60      3.48
worst case before giving up: 123 s
```
Real n8n 2.41.6 runs (manual-trigger variants of the bench workflows, against mock_server.py):
- rung 1 (no retry), evt_0101, the reply is lost: execution status `error`; n8n's error text
  "The connection was aborted, perhaps the server is offline" and "timeout of 10000ms exceeded";
  last node executed "Send the SMS"; mock delivery log: 1 message. (Red run, customer texted.)
- rung 2 (retry everything), evt_0101: status `success`; delivery log: 2 messages, msg_1 and msg_2.
- rung 3 (+ key), evt_0101: status `success`; delivery log: 1 message.
- rung 4 (+ dead-letter), evt_0251 (outage): status `success`; last node "Park in dead-letter
  queue"; 0 messages; dead-letter list ["evt_0251"]; started 06:13:00.577Z, stopped 06:13:10.683Z.
- store off (`python3 materials/mock_server.py --no-store`), rungs 3 and 4, evt_0101: 2 messages each.
24 of 24 runs matched the bench runner.

What the rung-3 send node carries (from assets/workflows/rung-3.json):
```
"retryOnFail": true, "maxTries": 3, "waitBetweenTries": 5000,
"sendHeaders": true,
"headerParameters": {"parameters": [{"name": "Idempotency-Key",
   "value": "={{ $('Shape the message').item.json.event_id }}"}]}
```
Rung 4 adds `"onError": "continueErrorOutput"` on both HTTP nodes and wires output 1 of each to
"Park in dead-letter queue" (POST http://127.0.0.1:8787/queue/dead-letter with event_id).

## Session 6 - the inventory

`materials/inventory.csv` (constructed, five automations) and `python3 materials/review_inventory.py`
(real output, TODAY fixed at 2026-10-05):
```
Order SMS            n8n     ok
Leads into CRM       Zapier  no runbook, review overdue since 2026-05-31
Invoice filing       Make    no owner, no runbook, fails silently, review overdue since 2026-05-19
Monday status email  Zapier  a retry can repeat: sends email
Weekly sales number  n8n     no runbook, a retry can repeat: posts message, review overdue since 2026-09-29
1 without an owner, 4 without a dead-letter list, of 5
```
CSV columns: name, tool, owner, trigger, side_effect, idempotency, dead_letter, alert_to, runbook,
last_review, review_every_days, units_month.
