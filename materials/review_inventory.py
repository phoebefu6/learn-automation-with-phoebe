"""Read the automation inventory and print what needs a person this week. Constructed rows."""
import csv
from datetime import date, timedelta

TODAY = date(2026, 10, 5)
rows = list(csv.DictReader(open("inventory.csv")))
for r in rows:
    issues = []
    if not r["owner"]:
        issues.append("no owner")
    if not r["runbook"]:
        issues.append("no runbook")
    if not r["alert_to"]:
        issues.append("fails silently")
    if r["side_effect"] and r["idempotency"] == "none":
        issues.append("a retry can repeat: " + r["side_effect"])
    due = date.fromisoformat(r["last_review"]) + timedelta(days=int(r["review_every_days"]))
    if due < TODAY:
        issues.append(f"review overdue since {due}")
    print(f"{r['name']:<20} {r['tool']:<7} {', '.join(issues) if issues else 'ok'}")
print(f"{sum(1 for r in rows if not r['owner'])} without an owner, "
      f"{sum(1 for r in rows if r['dead_letter'] == 'no')} without a dead-letter list, of {len(rows)}")
