// Follow one event through a bench workflow, printing what each node outputs.
// usage: node materials/trace_one.js evt_0001 [rung 1-4]
const path = require("path");
const E = require(path.join(__dirname, "..", "assets", "wf-bench.js"));
const D = require(path.join(__dirname, "..", "assets", "wf-day.js"));
const id = process.argv[2] || "evt_0001";
const rung = parseInt(process.argv[3] || "1", 10);
const ev = D.events.find((e) => e.event_id === id);
const world = E.makeWorld(D, { failures: E.DEFAULT_FAILURES, idemStore: true });
const bill = { zapier: 0, make: 0, n8n: 0, attempts: 0 };
const r = E.execute(D.workflows[rung - 1], ev, world, bill);
console.log("event:", JSON.stringify(ev));
console.log("path: ", r.trace.join(" > "));
Object.keys(r.outputs).forEach((n) => console.log("  " + n.padEnd(18), JSON.stringify(r.outputs[n])));
console.log("status:", r.status, "| texts sent:", world.deliveries.length, "| http tries:", bill.attempts);
