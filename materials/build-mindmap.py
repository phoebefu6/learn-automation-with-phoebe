"""Writes window.MINDMAP_DATA into index.html with json.dumps. Run from the repo root."""
import json, re
from pathlib import Path
S = [
 ("Is it worth\nthe time?", "01-worth-automating.html", "#34D399", ["The break-even line", "What charts leave out", "Which task goes first"]),
 ("Triggers, actions\nand the data", "02-triggers-and-actions.html", "#FBBF24", ["Instant or polling", "Items, bundles, fields", "One step reads another"]),
 ("Zapier, Make\nor n8n", "03-zapier-make-n8n.html", "#FBBF24", ["Task, credit, execution", "Self-host or cloud", "One flow, three bills"]),
 ("The workflow\nbench", "04-the-workflow-bench.html", "#F87171", ["Red is not lost", "Retry everything doubles", "Store off, key useless"]),
 ("When a step\nfails", "05-when-it-fails.html", "#FB923C", ["Backoff with jitter", "Keys without app support", "Dead letters and alerts"]),
 ("Leave it\nrunning", "06-leave-it-running.html", "#FB923C", ["Owner and runbook", "The inventory", "Review, expire, retire"]),
]
data = {"title": "Life & Work\nAutomation", "centerColor": "#0A4A92", "sessions": [
    {"label": l, "href": "courses/" + h, "color": c, "concepts": [{"label": x, "href": "courses/" + h} for x in cs]} for l, h, c, cs in S]}
p = Path("index.html"); s = p.read_text()
s = re.sub(r"window\.MINDMAP_DATA = .*?;\n</script>", lambda m: "window.MINDMAP_DATA = " + json.dumps(data, indent=1) + ";\n</script>", s, flags=re.S)
p.write_text(s)
print(max(len(x) for _, _, _, cs in S for x in cs))
