"""Count one workflow's monthly units on Zapier, Make and n8n, and check them against the entry plans
read on 2026-10-05. Re-verify every plan on the vendors' pricing pages before you buy."""
RUNS_PER_MONTH = [500, 3_000, 18_000]   # 18,000 is roughly the bench day (600 runs) x 30
ACTIONS_PER_RUN = 2   # Zapier: look up customer + send SMS; trigger, filter and formatter steps are free
MODULES_PER_RUN = 4   # Make: webhook trigger + Set + 2 HTTP modules; the IF becomes a filter, free
PLANS = {"Zapier Professional": 750, "Make Core": 10_000, "n8n Starter": 2_500, "n8n Pro": 10_000}

for runs in RUNS_PER_MONTH:
    units = {"Zapier Professional": runs * ACTIONS_PER_RUN, "Make Core": runs * MODULES_PER_RUN,
             "n8n Starter": runs, "n8n Pro": runs}
    fits = ", ".join(f"{p} {'fits' if units[p] <= cap else 'over'}" for p, cap in PLANS.items())
    print(f"{runs:>6,} runs: {units['Zapier Professional']:>6,} tasks, {units['Make Core']:>6,} credits, "
          f"{runs:>6,} executions | {fits}")
