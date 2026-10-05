# Learn Automation with Phoebe

Six 45-minute sessions on no-code and low-code automation that does not break: what is worth
automating, how a trigger hands data to an action, what Zapier, Make and n8n actually bill, and
what happens on the day a step fails.

1. Is it worth the time?
2. Triggers, actions and the data between
3. Zapier, Make or n8n
4. The workflow bench
5. When a step fails
6. Leave it running

The bench in session 4 executes real n8n-format workflow JSON (`assets/workflows/rung-1.json` to
`rung-4.json`) over one seeded day of 600 webhook events, with timeouts, 500 errors, lost replies
and a 30-minute outage, and counts texts sent, duplicates, losses, runs and cost per run. The same
workflows were run on n8n 2.41.6 against `materials/mock_server.py` and matched the bench on every
run checked. `materials/flow_reference.py` is an independent Python implementation that agrees with
the browser on every count.

Prices were read from each vendor's pages on 5 October 2026. Re-verify before relying on them.

Static HTML, no build step. Open `index.html`, or serve the folder with any static server.

By Phoebe Fu.
