/* wf-bench.js - the workflow bench for learn-automation-with-phoebe
 *
 * A small workflow runner that executes n8n-format workflow JSON (the same files you can import
 * into n8n: assets/workflows/rung-1.json ... rung-4.json) over one seeded day of 600 incoming
 * webhook events, against deterministic mock endpoints.
 *
 * Node types implemented (a documented subset, with n8n's own semantics):
 *   n8n-nodes-base.webhook      trigger; one execution per incoming event; output {headers, params, query, body}
 *   n8n-nodes-base.if           one string-equals condition; output 0 = true, output 1 = false
 *   n8n-nodes-base.set          manual assignments, includeOtherFields false; type number casts
 *   n8n-nodes-base.httpRequest  GET/POST against the mock endpoints; header and body key-pairs;
 *                               node settings retryOnFail, maxTries (clamped 2..5, default 3),
 *                               waitBetweenTries, onError stopWorkflow | continueErrorOutput.
 *                               The 2..5 clamp and the 5,000 ms wait cap are n8n's own
 *                               (n8n-core 2.41.6, workflow-execute.js, getRetryParams), read at source.
 * Expressions supported: ={{ $json.a.b }} and ={{ $('Node name').item.json.a.b }}, alone or inside text.
 *
 * Mock endpoints (deterministic: every failure is a hash of event, step and attempt number):
 *   GET  /crm/customers/:id   can time out or return 500
 *   POST /sms/send            can return 500 before sending, or SEND and then lose the response
 *                             (the client sees a timeout); returns 503 for every event that arrived
 *                             during the 13:00-13:30 outage; honours Idempotency-Key when its
 *                             store is on (the break button turns the store off)
 *   POST /queue/dead-letter   always accepts; parked events are re-posted once at 23:30 (the redrive)
 *
 * What is MEASURED: every delivery, duplicate, loss, run and unit below is counted from the
 *   executions this file performs. What is DECLARED: the failure mix (in wf-day.js), printed on
 *   the widget. What is MAPPED: which steps each vendor bills, from its pricing page, applied to
 *   this workflow; on Make, whether a failed module run uses a credit is not stated in the docs
 *   read, and the bench assumes it does.
 *
 * materials/flow_reference.py is an independent Python implementation; both must print the same
 * counts for every rung, every failure toggle and both store settings.
 */
(function (root) {
  "use strict";

  /* ---------- deterministic draws ---------- */
  var imul = Math.imul;
  function fmix(x) {
    x = (x ^ (x >>> 16)) >>> 0;
    x = imul(x, 0x85EBCA6B) >>> 0;
    x = (x ^ (x >>> 13)) >>> 0;
    x = imul(x, 0xC2B2AE35) >>> 0;
    x = (x ^ (x >>> 16)) >>> 0;
    return x;
  }
  function draw(seed, evNum, step, attempt) {
    var h = (imul(evNum, 0x9E3779B1) ^ imul(step + 1, 0x85EBCA77) ^ imul(attempt + 1, 0xC2B2AE3D) ^ seed) >>> 0;
    return fmix(h) / 4294967296;
  }

  /* ---------- expressions ---------- */
  function getPath(obj, path) {
    var parts = path.split(".");
    for (var i = 0; i < parts.length; i++) {
      if (obj === null || obj === undefined) return undefined;
      obj = obj[parts[i]];
    }
    return obj;
  }
  function evalExpr(expr, ctx) {
    expr = expr.trim();
    var m = /^\$json\.(.+)$/.exec(expr);
    if (m) return getPath(ctx.json, m[1]);
    m = /^\$\('([^']+)'\)\.item\.json\.(.+)$/.exec(expr);
    if (m) {
      var out = ctx.outputs[m[1]];
      if (!out) throw new Error("Node '" + m[1] + "' has not run in this execution");
      return getPath(out, m[2]);
    }
    throw new Error("Unsupported expression: " + expr);
  }
  function resolve(value, ctx) {
    if (typeof value !== "string" || value.charAt(0) !== "=") return value;
    var body = value.slice(1);
    var whole = /^\{\{([^}]*)\}\}$/.exec(body.trim());
    if (whole) return evalExpr(whole[1], ctx);
    return body.replace(/\{\{([^}]*)\}\}/g, function (_, e) {
      var v = evalExpr(e, ctx);
      return v === undefined || v === null ? "" : String(v);
    });
  }

  /* ---------- the mock world ---------- */
  var STEP = { lookup: 1, send: 2 };

  function makeWorld(day, opts) {
    var F = day.failures;
    var on = opts.failures;
    return {
      phase: "main",
      attempts: {},
      store: {},
      deliveries: [],
      deadLetter: [],
      call: function (method, url, headers, body, ev) {
        var evNum = parseInt(ev.event_id.slice(4), 10);
        var path = url.replace(/^https?:\/\/[^/]+/, "").split("?")[0];
        if (method === "GET" && path.indexOf("/crm/customers/") === 0) {
          var ka = ev.event_id + ":lookup";
          var n = this.attempts[ka] || 0; this.attempts[ka] = n + 1;
          var u = draw(day.seed, evNum, STEP.lookup, n);
          if (on.timeouts && u < F.lookupTimeout) return { ok: false, error: "timeout" };
          if (on.errors5xx && u >= F.lookupTimeout && u < F.lookupTimeout + F.lookup5xx) return { ok: false, error: "500" };
          var cid = path.split("/").pop();
          return { ok: true, json: { customer_id: cid, phone: "+1555010" + cid.slice(2), name: "Customer " + cid.slice(2) } };
        }
        if (method === "POST" && path === "/sms/send") {
          var ks = ev.event_id + ":send";
          var k = this.attempts[ks] || 0; this.attempts[ks] = k + 1;
          if (on.outage && this.phase === "main" && ev.ts >= F.outageStart && ev.ts < F.outageEnd) return { ok: false, error: "503" };
          var v = draw(day.seed, evNum, STEP.send, k);
          if (on.errors5xx && v < F.send5xx) return { ok: false, error: "500" };
          var key = headers["Idempotency-Key"];
          var resp;
          if (key && opts.idemStore && this.store[key]) {
            resp = { status: "duplicate-suppressed", message_id: this.store[key] };
          } else {
            var mid = "msg_" + (this.deliveries.length + 1);
            this.deliveries.push({ event_id: body.event_id, to: body.to, message_id: mid, phase: this.phase });
            if (key && opts.idemStore) this.store[key] = mid;
            resp = { status: "sent", message_id: mid };
          }
          if (on.ackLost && v >= F.send5xx && v < F.send5xx + F.ackLost) return { ok: false, error: "timeout (sent, response lost)" };
          return { ok: true, json: resp };
        }
        if (method === "POST" && path === "/queue/dead-letter") {
          this.deadLetter.push({ event_id: body.event_id, ev: ev });
          return { ok: true, json: { queued: true } };
        }
        return { ok: false, error: "404 " + method + " " + path };
      }
    };
  }

  /* ---------- the runner ---------- */
  function retryParams(node) {
    if (!node.retryOnFail) return [1, 0];
    return [Math.min(5, Math.max(2, node.maxTries || 3)), Math.min(5000, Math.max(0, node.waitBetweenTries || 1000))];
  }
  function kvList(list, ctx) {
    var o = {};
    (list || []).forEach(function (p) { o[p.name] = resolve(p.value, ctx); });
    return o;
  }

  function runNode(node, json, ctx, world, ev, bill) {
    var p = node.parameters;
    if (node.type === "n8n-nodes-base.if") {
      var c = p.conditions.conditions[0];
      var left = resolve(c.leftValue, ctx);
      var pass = c.operator.type === "string" && c.operator.operation === "equals" && String(left) === String(c.rightValue);
      return { outputs: pass ? [[json], []] : [[], [json]] };
    }
    if (node.type === "n8n-nodes-base.set") {
      var o = {};
      p.assignments.assignments.forEach(function (a) {
        var v = resolve(a.value, ctx);
        o[a.name] = a.type === "number" ? Number(v) : v;
      });
      bill.make += 1;
      return { outputs: [[o]] };
    }
    if (node.type === "n8n-nodes-base.httpRequest") {
      var url = resolve(p.url, ctx);
      var headers = p.sendHeaders ? kvList(p.headerParameters.parameters, ctx) : {};
      var body = p.sendBody ? kvList(p.bodyParameters.parameters, ctx) : null;
      var rp = retryParams(node), last = null;
      for (var t = 0; t < rp[0]; t++) {
        var r = world.call(p.method || "GET", url, headers, body, ev);
        bill.make += 1;
        bill.attempts += 1;
        if (r.ok) { bill.zapier += 1; return { outputs: [[r.json]], tries: t + 1 }; }
        last = r.error;
      }
      if (node.onError === "continueErrorOutput") {
        return { outputs: [[], [{ error: { message: last, node: node.name } }]], tries: rp[0], erroredToOutput: true };
      }
      return { error: last, tries: rp[0] };
    }
    throw new Error("Node type not implemented by the bench runner: " + node.type);
  }

  function execute(wf, ev, world, bill) {
    var byName = {};
    wf.nodes.forEach(function (n) { byName[n.name] = n; });
    var trigger = wf.nodes.filter(function (n) { return n.type === "n8n-nodes-base.webhook"; })[0];
    var outputs = {};
    var first = { headers: {}, params: {}, query: {}, body: JSON.parse(JSON.stringify(ev)) };
    outputs[trigger.name] = first;
    bill.make += 1; // the instant trigger reads the webhook: one credit
    var queue = [];
    function fanOut(fromName, outs) {
      var conns = (wf.connections[fromName] || {}).main || [];
      outs.forEach(function (items, idx) {
        (conns[idx] || []).forEach(function (c) {
          items.forEach(function (it) { queue.push({ node: byName[c.node], json: it }); });
        });
      });
    }
    fanOut(trigger.name, [[first]]);
    var trace = [trigger.name];
    while (queue.length) {
      var job = queue.shift();
      var ctx = { json: job.json, outputs: outputs };
      var res = runNode(job.node, job.json, ctx, world, ev, bill);
      trace.push(job.node.name + (res.tries > 1 ? " x" + res.tries : "") + (res.error ? " (failed: " + res.error + ")" : "") + (res.erroredToOutput ? " (error output)" : ""));
      if (res.error) return { status: "error", trace: trace, error: res.error, failedNode: job.node.name, outputs: outputs };
      var firstOut = res.outputs[0] && res.outputs[0][0];
      if (firstOut) outputs[job.node.name] = firstOut;
      fanOut(job.node.name, res.outputs);
    }
    return { status: "success", trace: trace, outputs: outputs };
  }

  var DEFAULT_FAILURES = { timeouts: true, errors5xx: true, ackLost: true, outage: true };

  function runDay(day, wf, opts) {
    opts = opts || {};
    var o = {
      failures: opts.failures || DEFAULT_FAILURES,
      idemStore: opts.idemStore !== false
    };
    var world = makeWorld(day, o);
    var bill = { zapier: 0, make: 0, n8n: 0, attempts: 0 };
    var runs = 0, failedRuns = 0, redriveRuns = 0, samples = [];
    day.events.forEach(function (ev) {
      var r = execute(wf, ev, world, bill);
      runs += 1; bill.n8n += 1;
      if (r.status === "error") { failedRuns += 1; if (samples.length < 6) samples.push({ event_id: ev.event_id, trace: r.trace }); }
    });
    // the redrive: every parked event is re-posted to the webhook once, after the outage has ended
    var parkedBefore = world.deadLetter.length;
    if (parkedBefore) {
      var parked = world.deadLetter.slice();
      world.deadLetter = [];
      world.phase = "redrive";
      parked.forEach(function (item) {
        var r = execute(wf, item.ev, world, bill);
        runs += 1; redriveRuns += 1; bill.n8n += 1;
        if (r.status === "error") failedRuns += 1;
      });
    }
    var eligible = day.events.filter(function (e) { return e.type === "order"; }).length;
    var perEvent = {};
    world.deliveries.forEach(function (d) { perEvent[d.event_id] = (perEvent[d.event_id] || 0) + 1; });
    var delivered = Object.keys(perEvent).length;
    var duplicates = world.deliveries.length - delivered;
    var stillParked = world.deadLetter.filter(function (d) { return !perEvent[d.event_id]; }).length;
    var lost = eligible - delivered - stillParked;
    var dupEvents = Object.keys(perEvent).filter(function (k) { return perEvent[k] > 1; }).sort();
    return {
      workflow: wf.name,
      events: day.events.length,
      eligible: eligible,
      delivered: delivered,
      deliveries: world.deliveries.length,
      duplicates: duplicates,
      duplicateEvents: dupEvents,
      lost: lost,
      parkedAfterRedrive: stillParked,
      parkedDuringDay: parkedBefore,
      runs: runs,
      failedRuns: failedRuns,
      redriveRuns: redriveRuns,
      httpAttempts: bill.attempts,
      units: { zapier: bill.zapier, make: bill.make, n8n: bill.n8n },
      samples: samples
    };
  }

  function cost(result, pricing, platform) {
    var p = pricing[platform];
    var unitPrice = p.price / p.units;
    var units = result.units[platform];
    return { units: units, unitPrice: unitPrice, perDay: units * unitPrice, perRun: units * unitPrice / result.runs, currency: p.currency, unit: p.unit };
  }

  /* ---------- UI ---------- */
  function esc(s) {
    return String(s).replace(/[&<>"]/g, function (c) { return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]; });
  }
  function metric(label, value, unit, kind) {
    return '<div class="mb-metric"><span class="mb-mlabel">' + esc(label) + "</span>" +
      '<span class="mb-mvalue">' + esc(value) + "</span>" +
      '<span class="mb-munit">' + esc(unit) + "</span>" +
      '<span class="mb-mkind is-' + (kind === "measured" ? "measured" : "heuristic") + '">' + esc(kind) + "</span></div>";
  }
  function money(x, cur) {
    var sym = cur === "EUR" ? "€" : "$";
    return sym + (x < 1 ? x.toFixed(4) : x.toFixed(2));
  }

  var RUNGS = [
    { label: "No retry", note: "Every step gets one try. A failed step stops the run." },
    { label: "Retry everything", note: "Retry On Fail, 3 tries, 5 s apart, on both HTTP steps. No key.", anti: true },
    { label: "Retry with an idempotency key", note: "Same retries, plus an Idempotency-Key header set to the event id." },
    { label: "Plus a dead-letter queue", note: "Same, plus On Error: continue to an error output that parks the event; redriven at 23:30." }
  ];
  var FAILS = [
    ["timeouts", "CRM lookup times out, 2% of tries"],
    ["errors5xx", "500 errors: CRM 3%, SMS 3% of tries"],
    ["ackLost", "SMS sent but the reply is lost, 4% of tries"],
    ["outage", "SMS provider down 13:00-13:30 (503)"]
  ];

  var state = { rung: 0, platform: "n8n", idemStore: true, failures: { timeouts: true, errors5xx: true, ackLost: true, outage: true } };
  var day, rootEl, readout, detail, jsonBox, rungBtns = [], storeBtn;

  function grade(r) {
    if (r.duplicates > 0 && !state.idemStore && state.rung >= 2) {
      return ["bad", "The idempotency store is off, so the key protects nothing: " + r.duplicates + " duplicate texts went out. The fix lives in the receiver, not in the header."];
    }
    if (r.duplicates > 0) {
      return ["bad", r.duplicates + " duplicate texts. Retrying a step whose reply was lost sends the message again, because nothing tells the provider it is the same message."];
    }
    if (r.lost > 0) {
      return ["ok", r.lost + " orders never got their text and nothing records which ones. No duplicates."];
    }
    if (r.parkedAfterRedrive > 0) {
      return ["ok", "Nothing lost silently: " + r.parkedAfterRedrive + " events still parked on the dead-letter list, waiting for a person."];
    }
    return ["good", "Every order texted exactly once: " + r.delivered + " of " + r.eligible + ". Failures were retried, parked and redriven, and the key made every repeat harmless."];
  }

  function render() {
    var wf = day.workflows[state.rung];
    var r = runDay(day, wf, { failures: state.failures, idemStore: state.idemStore });
    var c = cost(r, day.pricing, state.platform);
    var g = grade(r);
    root.WF_BENCH.last = r;
    readout.innerHTML =
      '<div class="mb-verdict is-' + g[0] + '">' + esc(g[1]) + ' <span class="mb-mkind is-measured">measured</span></div>' +
      '<div class="mb-metrics">' +
        metric("Orders texted", r.delivered + " / " + r.eligible, "of the day's orders reached a customer", "measured") +
        metric("Duplicate texts", r.duplicates, "extra messages a customer received", "measured") +
        metric("Orders lost", r.lost, "never texted, and on no list", "measured") +
        metric("Runs", r.runs, r.failedRuns + " ended red, " + r.redriveRuns + " were redrives", "measured") +
        metric("Units used", c.units + " " + c.unit + (c.units === 1 ? "" : "s"), "for the day, on " + day.pricing[state.platform].label, "mapped") +
        metric("Cost per run", money(c.perRun, c.currency), money(c.perDay, c.currency) + " for the day at " + money(c.unitPrice, c.currency) + " a unit", "mapped") +
      "</div>";
    var parts = [];
    parts.push("<p><strong>Where the day went.</strong> " + r.events + " webhook events, " + r.eligible + " of them orders. " +
      r.deliveries + " messages left the provider for " + r.delivered + " distinct orders. " +
      "Dead-letter list: " + r.parkedDuringDay + " parked during the day, " + r.parkedAfterRedrive + " still there after the redrive. " +
      "HTTP attempts: " + r.httpAttempts + ".</p>");
    if (r.duplicateEvents.length) {
      parts.push("<p><strong>Texted twice:</strong> " + r.duplicateEvents.slice(0, 8).map(esc).join(", ") +
        (r.duplicateEvents.length > 8 ? " and " + (r.duplicateEvents.length - 8) + " more" : "") + ".</p>");
    }
    if (r.samples.length) {
      parts.push("<p><strong>First red runs, as the executions list would show them:</strong></p><ul>" +
        r.samples.slice(0, 4).map(function (s) { return "<li><code>" + esc(s.event_id) + "</code> " + esc(s.trace.join(" > ")) + "</li>"; }).join("") + "</ul>");
    }
    parts.push('<p class="mb-hint">Billing is mapped, not metered: Zapier counts successful action steps (trigger, filter and formatter free); ' +
      "Make counts every module run including the trigger, and the bench assumes a failed run still uses a credit, which Make's docs read here do not state; " +
      "n8n counts one execution per run, however many steps or retries it holds. Per-unit price = plan price / included units, read 2026-10-05. Re-verify before delivery.</p>");
    detail.innerHTML = parts.join("");
    jsonBox.textContent = JSON.stringify(wf.nodes.filter(function (n) { return n.type === "n8n-nodes-base.httpRequest"; }).map(function (n) {
      var o = { name: n.name };
      ["retryOnFail", "maxTries", "waitBetweenTries", "onError"].forEach(function (k) { if (n[k] !== undefined) o[k] = n[k]; });
      if (n.parameters.sendHeaders) o.headers = n.parameters.headerParameters.parameters;
      return o;
    }), null, 2);
    rungBtns.forEach(function (b, i) { b.classList.toggle("is-on", i === state.rung); var inp = b.querySelector("input"); if (inp) inp.checked = i === state.rung; });
    storeBtn.textContent = state.idemStore ? "Break it: switch the idempotency store off" : "Mend it: switch the idempotency store back on";
    storeBtn.classList.toggle("is-broken", !state.idemStore);
  }

  function buildUI() {
    var panel = document.createElement("div");
    panel.className = "mb-presets";
    RUNGS.forEach(function (p, i) {
      var lab = document.createElement("label");
      lab.className = "mb-preset" + (p.anti ? " is-anti" : "");
      lab.innerHTML = '<input type="radio" name="wb-rung" value="' + i + '">' +
        '<span class="mb-pname">' + (i + 1) + " · " + esc(p.label) + (p.anti ? ' <em class="mb-anti">the anti-lever</em>' : "") + "</span>" +
        '<span class="mb-pnote">' + esc(p.note) + "</span>";
      lab.querySelector("input").addEventListener("change", function () { state.rung = i; render(); });
      rungBtns.push(lab);
      panel.appendChild(lab);
    });

    var ctl = document.createElement("div");
    ctl.className = "wb-controls";
    var fails = '<fieldset class="wb-group"><legend>Failures injected (declared mix)</legend>' +
      FAILS.map(function (f) {
        return '<label class="wb-check"><input type="checkbox" data-fail="' + f[0] + '" checked> ' + esc(f[1]) + "</label>";
      }).join("") + "</fieldset>";
    var plats = '<fieldset class="wb-group"><legend>Price it as</legend>' +
      ["zapier", "make", "n8n"].map(function (k) {
        var p = day.pricing[k];
        return '<label class="wb-check"><input type="radio" name="wb-plat" value="' + k + '"' + (k === state.platform ? " checked" : "") + "> " +
          esc(p.label) + " <span class=\"wb-dim\">" + esc(p.plan) + ", " + (p.currency === "EUR" ? "€" : "$") + p.price.toFixed(2) + "</span></label>";
      }).join("") + "</fieldset>";
    ctl.innerHTML = fails + plats;
    ctl.querySelectorAll("[data-fail]").forEach(function (cb) {
      cb.addEventListener("change", function () { state.failures[cb.getAttribute("data-fail")] = cb.checked; render(); });
    });
    ctl.querySelectorAll("[name=wb-plat]").forEach(function (rb) {
      rb.addEventListener("change", function () { state.platform = rb.value; render(); });
    });

    storeBtn = document.createElement("button");
    storeBtn.type = "button";
    storeBtn.className = "wb-break";
    storeBtn.addEventListener("click", function () { state.idemStore = !state.idemStore; render(); });

    var hint = document.createElement("p");
    hint.className = "mb-hint";
    hint.textContent = "One seeded day: " + day.events.length + " webhook events between 07:00 and 22:00, seed " + day.seed +
      ". Every failure is decided by a hash of the event, the step and the attempt number, so the same day replays identically. " +
      "The workflows are real n8n JSON; the endpoints are mocks that behave like a CRM, an SMS provider and a queue.";

    readout = document.createElement("div"); readout.className = "mb-readout";
    detail = document.createElement("div"); detail.className = "wb-detail";
    var jwrap = document.createElement("details");
    jwrap.className = "wb-json";
    jwrap.innerHTML = "<summary>The settings that differ between rungs, read from the workflow JSON</summary>";
    jsonBox = document.createElement("pre");
    jwrap.appendChild(jsonBox);

    rootEl.appendChild(panel);
    rootEl.appendChild(ctl);
    rootEl.appendChild(storeBtn);
    rootEl.appendChild(hint);
    rootEl.appendChild(readout);
    rootEl.appendChild(detail);
    rootEl.appendChild(jwrap);
    render();
  }

  function init() {
    rootEl = document.getElementById("wf-bench");
    day = root.WF_DAY;
    if (!rootEl || !day) return;
    root.WF_BENCH = {
      state: state,
      runDay: function (rung, o) { return runDay(day, day.workflows[rung], o); },
      set: function (patch) { Object.keys(patch).forEach(function (k) { state[k] = patch[k]; }); render(); return root.WF_BENCH.last; },
      last: null
    };
    buildUI();
  }

  var api = { runDay: runDay, cost: cost, draw: draw, resolve: resolve, execute: execute, makeWorld: makeWorld, DEFAULT_FAILURES: DEFAULT_FAILURES };
  if (typeof module !== "undefined" && module.exports) module.exports = api;
  if (typeof document !== "undefined") {
    if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", init);
    else init();
  }
})(typeof window !== "undefined" ? window : this);
