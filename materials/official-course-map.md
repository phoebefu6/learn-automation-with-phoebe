# learn-automation-with-phoebe - source map

Internal build document. Not linked from any audience-facing page.

Bucket `prod`, difficulty 3, audience both, 6 sessions, single track, 45 minutes each. Title
"Life & Work Automation". Flips the planned hub card (slug kept). Built 2026-10-05.

Evidence tiers used below:
- **read-at-source** - the page, file or package was opened during this build and the wording or
  number was read there, on the date given.
- **reported** - seen only in a search snippet or a secondary summary; say "reported" on the page,
  or cut it.
- **measured** - computed by the bench engine (`assets/wf-bench.js`) AND the independent Python
  reference (`materials/flow_reference.py`); the two agree on all 128 combinations (4 rungs x
  2 store settings x 16 failure toggles), checked 2026-10-05.
- **constructed** - invented for teaching (the seeded day, the failure mix); always labelled so.

---

## Why this course exists, and what it leaves to its siblings

No-code and low-code automation that does not break: deciding what is worth automating, how a
trigger hands data to an action, what the three big tools charge for, and what happens on the day
a step fails. The un-owned slice is the **failure semantics of a single business workflow** run
by one person or a small team on Zapier, Make or n8n.

Seams (link, never teach):

| Topic | Owner | Link target |
|---|---|---|
| DAGs, Airflow, pipeline retries and idempotency for data teams | `learn-data-orchestration-with-phoebe` (03 retries, 04 idempotency) | https://phoebefu6.github.io/learn-data-orchestration-with-phoebe/ |
| SLOs, error budgets, runbooks, on-call, toil | `learn-data-reliability-with-phoebe` (b4 runbooks, b7 toil, a3 on-call) | https://phoebefu6.github.io/learn-data-reliability-with-phoebe/ |
| AI drafting, triage, LLM steps inside a workflow | `learn-ai-productivity-with-phoebe` (built in parallel) | https://phoebefu6.github.io/learn-ai-productivity-with-phoebe/ |
| WorkBuddy's own automation and scheduling | `learn-workbuddy-with-phoebe` b8 | https://phoebefu6.github.io/learn-workbuddy-with-phoebe/courses/b8-automation.html |
| Agents, and workflows vs agents | `learn-ai-agents-with-phoebe` (a3) | https://phoebefu6.github.io/learn-ai-agents-with-phoebe/courses/a3-workflows-vs-agents.html |
| Weekly review habits for a personal system | `learn-pkm-with-phoebe` 05 | https://phoebefu6.github.io/learn-pkm-with-phoebe/ |

Sibling titles grepped 2026-10-05: orchestration uses "Retries, and what they quietly cost" and
"Rerun-safe by construction"; PKM uses "A system you keep"; many courses use "The X bench". This
course's titles avoid those exact strings.

---

## Sessions

| # | File | Title | Covers |
|---|---|---|---|
| 1 | 01-worth-automating.html | Is it worth the time? | time-saved maths, xkcd 1205, build + upkeep, the SRE counterpoint |
| 2 | 02-triggers-and-actions.html | Triggers, actions and the data between | polling vs instant, items/bundles/fields, expressions, n8n locally |
| 3 | 03-zapier-make-n8n.html | Zapier, Make or n8n | task / credit / execution billing, self-host vs cloud, licence |
| 4 | 04-the-workwf-bench.html | The workflow bench | the four-rung ladder on one seeded day, anti-lever, break button |
| 5 | 05-when-it-fails.html | When a step fails | retries, backoff and jitter, idempotency keys, dead-letter, alerts |
| 6 | 06-leave-it-running.html | Leave it running | owner, runbook, inventory, review cadence, key expiry, retirement |

---

## Verified facts

### Session 1 - worth the time

- **xkcd 1205 "Is It Worth the Time?"**, Randall Munroe, published 2013-04-29. Read at source
  (https://xkcd.com/1205/info.0.json, 2026-10-05). Subtitle: "How long can you work on making a
  routine task more efficient before you're spending more time than you save? (Across five
  years)". Columns: 50/day, 5/day, daily, weekly, monthly, yearly. Rows: 1 s, 5 s, 30 s, 1 min,
  5 min, 30 min, 1 h, 6 h, 1 day. Cells used on pages (read from the transcript): 5 minutes daily
  = **6 days**; 1 hour weekly = **10 days**; 30 seconds 5/day = **3 days**; 1 minute daily =
  **1 day**; 5 seconds 50/day = **5 days**. Licence CC BY-NC 2.5: pages link to the comic and
  quote cells, never embed the image.
- Arithmetic check (constructed, reproducible): 5 min x 365 x 5 = 9,125 min = 152.1 h = 6.3
  24-hour days. The chart's "days" are 24-hour days, not working days; in 8-hour working days the
  same budget is 19 days. The chart counts no upkeep.
- **xkcd 1319 "Automation"**, 2014-01-20, read at source (info.0.json). Cited by number and title
  only; its punchline is the planned-vs-actual automation curve. Do not quote the alt text.
- **Google SRE book, ch. 7 "The Evolution of Automation at Google"** (Niall Murphy with John
  Looney and Michael Kacirek, ed. Betsy Beyer), read at source 2026-10-05:
  "For SRE, automation is a force multiplier, not a panacea." and "doing automation
  thoughtlessly can create as many problems as it solves." It lists consistency, a platform,
  faster repairs and time saving as values, and argues that "automation provides more than just
  time saving, so it's worth implementing in more cases than a simple time-expended versus
  time-saved calculation might suggest." **This is the disagreement session 1 teaches**: xkcd
  1205 is a time-only break-even; the SRE chapter says time is not the only return.
- SRE ch. 5 defines toil (manual, repetitive, automatable, tactical, no enduring value, scales
  linearly). Owned by reliability b7; link, do not teach.

### Session 2 - triggers, actions, data

- n8n data: "all data passed between nodes is an array of objects", each item wrapped in `json`
  (docs.n8n.io/build/work-with-data/understand-n8ns-data-structure, read at source).
- n8n webhook node output carries the payload under `body` (alongside headers, params, query):
  observed in the workflows built here; the runner implements it.
- Zapier polling dedupe: "By default, the field with the key `id` is used as the primary key";
  Zapier stores seen ids when a Zap is turned on and clears the list when it is turned off
  (docs.zapier.com/integrations/build/deduplication, read at source).
- Zapier: "Instant triggers do not use deduplication because apps only send new data." (help
  article 8496260269965, updated 2026-05-29, read via fetch). **Pair it with** Stripe: "Webhook
  endpoints might occasionally receive the same event more than once" (docs.stripe.com/webhooks,
  read at source) - teach the gap.
- Make: an operation is "a single module run to process data or check for new data"; a trigger
  check counts once even with no new data (help.make.com/operations, read via fetch).
- n8n local install: docs say "n8n requires a Node.js version between 20.19 and 24.x, inclusive"
  and offer `npx n8n` (docs.n8n.io install-with-npm, read at source). **But** the npm package
  n8n@2.41.6 (dist-tag stable and latest on 2026-10-05) declares `engines: node >=24.0.0`
  (read with `npm view`). On Node 22.6 the current stable does not satisfy its own engines field;
  with Node 24.21.0 it started and answered `/healthz` `{"status":"ok"}` in about 6 s in this
  build. Its own startup log warns "Running n8n outside a container is deprecated." Teach: use
  Node 24, or Docker.

### Session 3 - Zapier, Make, n8n (pricing read 2026-10-05; RE-VERIFY BEFORE DELIVERY)

- **Zapier** (zapier.com/pricing, read at source): Free 100 tasks/month; Professional from
  $29.99/month billed monthly or $19.99/month billed annually, at 750 tasks; Team from $103.50
  monthly / $69 annually at 2,000 tasks. Pay-per-task overage when enabled: 2.5x the base rate on
  monthly self-serve, 1.25x on annual. "A task is any successful action that runs in Zapier. Only
  successful actions count" (help article 8496196837261, updated 2026-08-21): trigger steps,
  Filter, Paths, Formatter, Delay, Looping, Digest, Storage are free; "All action steps that
  error or halt" are free; a full replay re-counts previously successful steps.
- Zapier Autoreplay replays the errored step, Professional and above (help article
  8496241726989, updated 2026-05-29). Schedule not stated on that page.
- **Make** (make.com/en/pricing, read at source): Free 1,000 credits/month; Core $9, Pro $16,
  Teams $29 per month at 10,000 credits as displayed; "Save 15% or more" annually. Whether the
  displayed figure is the monthly or annual-billing price could not be confirmed from the fetched
  page: say "as displayed" and re-verify. "As of August 27, credits are the billing unit in Make"
  (previously operations); "1 operation equals 1 credit" for non-AI apps; some Make AI modules use
  2 or 10 (help.make.com/credits). Error-handler modules and routers use no credits (pricing FAQ).
  Whether a FAILED module run uses a credit is **not stated** in the pages read. The bench
  assumes it does and says so on the widget.
- Make's error handlers are now named Skip, Retry, Resume, Commit, Rollback (help.make.com/
  error-handlers, read at source). Retry needs "incomplete executions" enabled (help.make.com/
  retry-error-handler). Number-of-attempts range 1-100 and minutes between attempts are
  **reported** (search snippet of the older "Break" page), not read at source.
- **n8n** (n8n.io/pricing, read at source): Starter 20 EUR/month at 2,500 executions, Pro
  50 EUR at 10,000, Business 667 EUR (self-hosted) at 40,000; "17%" annual saving; as with Make,
  monthly vs annual figure not confirmed: "as displayed". "An execution is a single run of your
  entire workflow. It doesn't matter how many steps are in the workflow or how much data it
  processes." Only production executions count; manual runs from the editor do not
  (docs.n8n.io understand-executions, read at source).
- n8n licence: Sustainable Use License 1.0 (github.com/n8n-io/n8n LICENSE.md, read at source):
  use "only for your own internal business purposes or for non-commercial or personal use";
  files with `.ee.` need an enterprise licence. n8n calls this fair-code. Teach it as
  source-available with limits, not as open source in the OSI sense; do not claim more.
  Open Source Definition criterion 6, read at source (opensource.org/osd, 2026-10-05): "The
  license must not restrict anyone from making use of the program in a specific field of
  endeavor."
- Per-unit prices the bench uses (plan price / included units, labelled "mapped" on the widget):
  Zapier $29.99/750 = **$0.0400 a task**; Make $9/10,000 = **$0.0009 a credit**; n8n 20 EUR/2,500
  = **0.0080 EUR an execution**. Real bills are by tier, not by unit; say so.

### Sessions 4 and 5 - failure semantics

- **n8n node retry, read in the engine source** (n8n-core 2.41.6,
  `dist/execution-engine/workflow-execute.js`, `getRetryParams`): with Retry On Fail off, one try;
  on, `maxTries` is clamped to 2..5 (default 3) and `waitBetweenTries` to 0..5,000 ms (default
  1,000). So the longest node-level retry window is 4 waits x 5 s = **20 seconds**. A
  30-minute outage cannot be bridged by node retries. Node settings documented (docs.n8n.io
  work-with-nodes): Retry On Fail; On Error = Stop Workflow / Continue / Continue (using error
  output).
- n8n error workflow: set per workflow in Workflow Settings, must start with Error Trigger, runs
  when an execution fails; cannot be tested with manual runs (docs.n8n.io handle-errors-gracefully,
  errortrigger, read at source). Error data includes `execution.retryOf` for retries.
- n8n Remove Duplicates node, "Remove Items Processed in Previous Executions", Keep Items Where
  Value Is New, default history 10,000 items, scope node or workflow (docs, read at source).
  **Nuance taught in s5:** a dedupe step placed BEFORE the send marks an item as seen before the
  send succeeds; a failed send then retried in a new execution is dropped as "seen". Dedupe at
  the receiver (idempotency key) or mark after success.
- **Stripe idempotent requests** (docs.stripe.com/api/idempotent_requests, read at source):
  `Idempotency-Key` header; Stripe saves "the resulting status code and body of the first request
  made for any given idempotency key, regardless of whether it succeeds or fails. Subsequent
  requests with the same key return the same result, including 500 errors"; keys up to 255
  characters; keys may be pruned after at least 24 hours; results are saved only once endpoint
  execution begins. Teach: provider semantics differ, read them; and a redrive after the key
  window re-sends.
- **Stripe webhooks**: up to three days of automatic retries with exponential backoff in live
  mode; "Webhook endpoints might occasionally receive the same event more than once"; track
  event IDs (docs.stripe.com/webhooks, read at source).
- **GitHub webhooks best practices** (read at source): respond with 2XX within 10 seconds;
  redeliver missed deliveries; a redelivery keeps the same `X-GitHub-Delivery` header.
- **AWS SQS dead-letter queues** (docs.aws.amazon.com SQS developer guide, read at source):
  source queues target DLQs "for messages that are not processed successfully"; `maxReceiveCount`
  = receives before a message moves to the DLQ; redrive moves messages back; DLQ retention should
  be longer than the source queue's; CloudWatch alarms on DLQ messages are documented.
- **Marc Brooker, "Exponential Backoff And Jitter"**, AWS Architecture Blog, 2015-03-04 (read via
  fetch): full jitter had the lowest client work; with 100 contending clients jitter cut the call
  count by more than half. The newer Builders' Library article redirects to a page that did not
  render for fetch: not cited.

### Session 6 - leave it running

- SRE ch. 7 operator-skill warning: "human operators are progressively more relieved of useful
  direct contact with the system as the automation covers more and more daily activities"
  (read at source).
- Stripe key pruning (24 h) and Zapier's seen-id list cleared when a Zap is turned off: both are
  state that a rebuild or a pause silently resets. Read at source above.
- Owner / runbook / inventory / review cadence: practice, not a cited standard. Teach as
  practice; the runbook craft itself is reliability b4's.

---

## The bench: constructed day, real execution (canon, all four failures on)

`assets/wf-day.js`, generated by `materials/build-flow-day.py`, seed 1205: 600 webhook events,
07:00-22:00, 344 orders (60%), signups 25%, refunds 15%; 13 orders arrive in the 13:00-13:30
outage. **Constructed.** Declared failure mix, per attempt: CRM lookup timeout 2%, CRM 500 3%,
SMS 500 3% (nothing sent), SMS ack lost 4% (sent, reply lost), SMS 503 for every send for an
event arriving 13:00-13:30. Dead-letter redrive once at 23:30.

Workflows: `assets/workflows/rung-1.json` .. `rung-4.json`, real n8n JSON (webhook, IF, Set,
two HTTP Request nodes, plus the DLQ HTTP node on rung 3).

| Rung | Texted | Duplicates | Lost | Runs | Red runs | Zapier tasks | Make credits | n8n executions |
|---|---|---|---|---|---|---|---|---|
| 1 No retry | 304 / 344 | 0 | 40 | 600 | 51 | 621 | 1,616 | 600 |
| 2 Retry everything (anti-lever) | 331 / 344 | **11** | 13 | 600 | 13 | 675 | 1,697 | 600 |
| 3 + idempotency key | 331 / 344 | 0 | 13 | 600 | 13 | 675 | 1,697 | 600 |
| 4 + dead-letter queue | **344 / 344** | 0 | **0** | 613 (13 redrives) | 0 | 714 | 1,766 | 613 |
| Break: rung 3, store off | 331 / 344 | 11 | 13 | 600 | 13 | 675 | 1,697 | 600 |
| Break: rung 4, store off | 344 / 344 | **13** | 0 | 613 | 0 | 714 | 1,766 | 613 |

Other measured facts:
- Rung 1: 51 red runs but only 40 lost: **11 runs went red after the customer got the text**
  (ack lost). Red is not the same as lost.
- Anti-lever mechanism: with "ack lost" switched off, rung 2 shows **0** duplicates (331 texted,
  13 lost); the duplicates come entirely from retrying a send whose reply was lost.
- With "outage" off, rung 2: 344 texted, 12 duplicates, 0 lost; rung 3: 344, 0, 0.
- Outage only (other three off): rungs 1 and 2 both text 331 and lose exactly the 13 outage
  orders; no retry can reach past a 30-minute outage. Rung 1 with only the outage off: 317
  texted, 27 lost, 39 red.
- Ack lost only: rung 1 texts 344 of 344 with 12 red runs (all of them delivered); rung 2 texts
  344 with 12 duplicates. The same 12 lost replies, two opposite symptoms.
- All failures off: every rung texts 344 of 344 with 0 duplicates; 688 Zapier tasks (344 x 2),
  1,632 Make credits, 600 n8n executions.
- Cost (mapped), all failures on, per day / per run: rung 1 Zapier $24.83 / $0.0414, Make $1.45 /
  $0.0024, n8n 4.80 EUR / 0.0080 EUR; rung 4 Zapier $28.55 / $0.0466, Make $1.59 / $0.0026,
  n8n 4.90 EUR / 0.0080 EUR. Zapier at 714 tasks a day is about 21,000 a month against a 750-task
  plan: the per-unit figure is a comparison device, not a quote.

**Real n8n check (2026-10-05).** n8n 2.41.6 on Node 24.21.0, local, against
`materials/mock_server.py` on 127.0.0.1:8787. Six events (evt_0101 and evt_0112 ack lost on the
first send, evt_0095 and evt_0134 lookup timeout first, evt_0024 SMS 500 first, evt_0251 in the
outage) x four rungs, run with `n8n execute` on manual-trigger variants of the same workflows
(the webhook node replaced by a Set node named "Order webhook" producing the same `body`). See
results below; the runner must match real n8n on every one.

**Result: 24 of 24 match** the runner's prediction on execution status, number of SMS
deliveries and dead-letter entries, plus 2 of 2 with the idempotency store off (rungs 3 and 4 on
evt_0101: 2 deliveries each, as predicted). Real outputs worth quoting (from the run logs):
- rung 1, evt_0101 (reply lost): execution status `error`, n8n's message "The connection was
  aborted, perhaps the server is offline" / "timeout of 10000ms exceeded", lastNodeExecuted
  "Send the SMS", and the mock's delivery log holds **one** message. Red run, customer texted.
- rung 2, evt_0101: status `success`, delivery log holds **two** messages (msg_1, msg_2).
- rung 4, evt_0251 (outage): status `success`, lastNodeExecuted "Park in dead-letter queue",
  0 deliveries, dead-letter list ["evt_0251"].
- One retry window on real n8n: evt_0251 rung 4 started 06:13:00.577Z, stopped 06:13:10.683Z
  (3 tries 5 s apart).
Not checked on real n8n: the 23:30 redrive (the runner re-posts parked events; on n8n this is a
second workflow), the webhook trigger itself (replaced by a Set node for CLI execution), and the
billing counts.

---

## Not covered (honest list)

- Vendor certifications and official academies (Zapier Learn, Make Academy, n8n courses): linked
  as self-study, not reproduced.
- Make's exact retry schedule and whether failed modules bill a credit: not stated in the pages
  read.
- Zapier Autoreplay's retry schedule: not stated on the page read.
- AI steps inside workflows: AI Productivity's.
- Pipeline orchestration, backfills, SLOs, on-call: orchestration and reliability siblings.
- Security of credentials and webhook signature verification: named in s5/s6, not taught in
  depth.
- Real costs of any learner's account: the bench maps list prices; bills depend on tiers,
  currency, tax and discounts.

---

## Citation appendix (exact forms for pages)

- Munroe, R. "Is It Worth the Time?" xkcd 1205, 29 April 2013. https://xkcd.com/1205/
- Munroe, R. "Automation." xkcd 1319, 20 January 2014. https://xkcd.com/1319/
- Murphy, N., Looney, J., Kacirek, M. "The Evolution of Automation at Google." Site Reliability
  Engineering, ch. 7, ed. B. Beyer et al., O'Reilly 2016. https://sre.google/sre-book/automation-at-google/
- Zapier pricing, read 2026-10-05. https://zapier.com/pricing
- Zapier Help, "How is task usage measured in Zapier", updated 2026-08-21.
- Zapier Help, "How Zapier handles duplicate data in Zaps", updated 2026-05-29.
- Zapier Platform docs, "Deduplication". https://docs.zapier.com/integrations/build/deduplication
- Make pricing, read 2026-10-05. https://www.make.com/en/pricing ; Make Help, "Credits",
  "Operations", "Error handlers", "Retry error handler".
- n8n pricing, read 2026-10-05. https://n8n.io/pricing/ ; n8n docs: understand executions,
  work with nodes, handle errors gracefully, Error Trigger, Remove Duplicates, data structure,
  install with npm. https://docs.n8n.io/
- n8n source: n8n-core 2.41.6, workflow-execute.js, getRetryParams (npm package, read 2026-10-05).
- n8n Sustainable Use License 1.0. https://github.com/n8n-io/n8n/blob/master/LICENSE.md
- Stripe API docs, "Idempotent requests". https://docs.stripe.com/api/idempotent_requests
- Stripe docs, "Webhooks". https://docs.stripe.com/webhooks
- GitHub Docs, "Best practices for using webhooks".
- AWS, "Using dead-letter queues in Amazon SQS". https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/sqs-dead-letter-queues.html
- Brooker, M. "Exponential Backoff And Jitter." AWS Architecture Blog, 4 March 2015.
  https://aws.amazon.com/blogs/architecture/exponential-backoff-and-jitter/
