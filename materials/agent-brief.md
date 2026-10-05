# Agent brief - shared by every fan-out page of learn-automation-with-phoebe

Internal build document, filled from course-builder's agent-brief.template.md. Never link it from
an audience page.

You are writing ONE static HTML session page. No servers, no npm. **If your target file already
exists on disk, do not write it; report that and stop.** Write the file, return its path and one
line of coverage. No HTML in your reply.

## Read first, in this order

1. The template page. Copy its structure, classes, SVG grammar and quiz markup EXACTLY, including
   how many options each question has (four, A to D):
   - `/Users/phoebe.fu/Documents/Claude_Work/github_repo/learn-automation-with-phoebe/courses/01-worth-automating.html`
   - For rhythm on a page that quotes bench numbers, also skim
     `/Users/phoebe.fu/Documents/Claude_Work/github_repo/learn-automation-with-phoebe/courses/04-the-workflow-bench.html`
2. The source map: every verified number, its evidence tier, per-session coverage, the seams. Use
   ONLY its numbers; never invent a statistic; if a fact is missing, teach the uncertainty.
   `/Users/phoebe.fu/Documents/Claude_Work/github_repo/learn-automation-with-phoebe/materials/official-course-map.md`
3. The real build-along outputs. Every output printed in a code box comes from here, verbatim:
   `/Users/phoebe.fu/Documents/Claude_Work/github_repo/learn-automation-with-phoebe/materials/build-along-outputs.md`
4. The stylesheet `:root` block for the palette tokens (first 30 lines):
   `/Users/phoebe.fu/Documents/Claude_Work/github_repo/learn-automation-with-phoebe/assets/style.css`

## Page skeleton (keep every component)

toolbar (crumb EXACTLY "learn-automation-with-phoebe / Session N of 6", #toggle-all, #zoom-toggle) ·
masthead (eyebrow "Learn Automation with Phoebe · Session N of 6", h1 with one
`<span class="accent">`, .sub, .chip-row with the level chip given in your outline plus two
audience chips and "45 min", .agenda a1-a4) · main.wrap · section#intro (Part 0 "Where we start":
kicker, .lede, .legend pills exactly as the template, .callout.win "★ What you walk out with
tonight.") · 3 Parts, each `section.section#part-N` with section-kicker (klabel "Part N · covers
...", h2, `.tag.concept "N min live"`), a `.lede`, ONE figure, `details.card` accordions (summary:
`.mode.live` or `.mode.self`, title, `.mini`, `.caret ▶`), at least one `.callout.example` with
`span.ex-pill` "Real world" on the page · section#demo-1 Build-along (kicker klabel "Build-along",
`.tag.demo "★ 22 min · everyone builds"`, .lede, ONE figure, `.steps > .step`, each with a `<p>`
then a `.prompt-box.good` carrying a `span.label`; content per your outline) · section#exercise
Homework (ol, 4 items) · section#quiz (3 x `.quiz-q data-answer="0-based"`, `p.qtext`, FOUR
`button.qopt` "A · ..." to "D · ...", `p.qwhy`; one `p.quiz-score` after the last; vary which
letter is correct) · section#official, h2 EXACTLY "What this session teaches, and where it came
from", `.covered > .covered-row` (pill solid ✓ / light ◐ + name + note), then the `.mono` line
EXACTLY "Every fact on this page, and its verification tier, is recorded in the course's source
map." · section.cheat#cheatsheet (h3 "Session N cheat sheet <span>· pin this</span>", .grid-2 of
six .cheat-item) · `.callout.next` with `.nx-pill` "Next session" · footer.pagefoot ·
`<script src="../assets/app.js?v=1"></script>`.

Head: the template's social meta block with this page's own title/description/url;
`<title>Session N · Title - learn automation with phoebe</title>`;
`<link rel="stylesheet" href="../assets/style.css?v=1">`. Nothing else external.

First `details.card` in the FIRST Part is `open`; no other. Sentence case headings. Warm
practitioner voice, concrete, never dry. Inside prompt-boxes escape `&` `<` `>`. 450 to 650 lines
is guidance about depth, never a target: never collapse whitespace, dissolve a list into a
paragraph, or drop a component to fit.

## Hard rules (a violation is rework)

- NEVER an em dash or en dash, anywhere (prose, code, aria-labels, comments). Hyphen only.
- No meta text: never "this course", "in this course", "the course teaches", "banned here". State
  the professional norm directly with its reason. The two exact estate phrases above are the only
  self-references; "session 5" cross-references are fine.
- Attribution "by Phoebe Fu". Never "built with" a tool.
- Every number comes from the map or build-along-outputs.md, or is labelled constructed. Never
  print an output that is not in build-along-outputs.md. If a step has no captured output, show
  the command and say what to look for, without a fake output.
- Pricing: every price carries "read 5 October 2026" (or "as read on 5 October 2026") and a
  "re-verify before you buy" reminder on the page; Make and n8n prices are "as displayed" (monthly
  vs annual toggle not confirmed). Make's unit is now the credit (formerly operation).
- Contested or missing evidence: teach the disagreement; never resolve what the sources have not.
  Known gaps to state honestly: whether Make bills a failed module run (not stated); Make's retry
  attempt range (reported only); Zapier Autoreplay schedule (not stated).
- Citations in the exact form of the map's appendix.
- NEVER "lottery" or "lotteries"; say the mechanism.
- Default to the English word. No Chinese terms needed on these pages.
- Titles, widget ids and class names must not collide with siblings. Do not use these titles:
  "Retries, and what they quietly cost", "Rerun-safe by construction", "Run it like production",
  "A system you keep", "From cron to DAG". Do not create new widget ids; the only widgets allowed
  are the app.js tryrow (`<div class="tryrow" data-fn="..." ...>`, see session 1) and plain HTML.
- Rung numbering is 1 to 4 everywhere: 1 no retry, 2 retry everything, 3 + idempotency key,
  4 + dead-letter queue. Workflow files: `../assets/workflows/rung-1.json` ... `rung-4.json`.
  Scripts: `../materials/mock_server.py`, `../materials/trace_one.js`,
  `../materials/price_three_ways.py`, `../materials/backoff.py`, `../materials/inventory.csv`,
  `../materials/review_inventory.py`. Link them with those relative paths.
- Light surfaces only. Do not add dark panels; the existing `.prompt-box` style is the one
  exception.

## Figure grammar (hand-drawn, every figure)

Palette, ONLY these hexes (no invented greys): ink `#11233B` · muted `#4D5D74` · accent `#0A64C4`
· deep `#0A4A92` · soft `#B9D5F4` · accent-50 `#EBF3FD` · faint `#C7D4E5` · hairline `#DCE5F0` ·
contrast (rust) `#B5480C` · contrast-ink `#8A3509` · contrast-50 `#FDEEE4` · `#FFFFFF` · universal
reds `#991B1B` `#FEF2F2` `#FCA5A5` only for a wrong-way panel.

- `<figure class="zoomable">` > `<svg viewBox="0 0 880 H" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="the data, not the
  shape">` > `<defs>` + `<style>` + content, then `<figcaption>🔍 Click to zoom - takeaway</figcaption>`.
  Grow H, never W.
- Prefix unique per figure, used for every class and id: `sNx` where N is the session number and
  x is a, b, c, d in page order (e.g. `s2aSk`, `s2aHc`, `s2aAr`, `.s2aH`).
- `<defs>` holds three things with the figure prefix P: a wobble filter `id="PSk"`
  (`feTurbulence type="fractalNoise" baseFrequency="0.02" numOctaves="2" seed="<int>"` +
  `feDisplacementMap scale="2.4" xChannelSelector="R" yChannelSelector="G"`, `x="-3%" y="-3%"
  width="106%" height="106%"`), a hachure pattern `id="PHc"` (7x7 userSpaceOnUse, rotate(-38), one
  accent line, opacity .5), an open arrowhead `id="PAr"` (path `M1 1 L9 5 L1 9`, fill none, ink
  stroke 1.6). ALL shapes sit inside ONE `<g filter="url(#PSk)" fill="none" stroke="#11233B"
  stroke-width="2" stroke-linecap="round" stroke-linejoin="round">`; rects carry a tiny rotation
  (-4 to 4 degrees for hand-placed items, under 1 for panels). Fills: white, accent-50, the hachure
  for "the pile" or "the data", and the contrast colour ONLY for the one thing the figure is about.
  One doodle anchor per figure, simple strokes, never a mascot. Text classes: `.PH` 800 12px ink
  heading · `.PL` 600 12px ink label · `.PS` 400 11px muted · `.PB` 800 11px contrast-ink · `.PV`
  800 16-20px deep value · `.PW` 800 12px white on a fill · `.PA` 700 11px accent axis caption ·
  `.PN` 400 12px muted note. Hand-stacked items must not overlap as painted rects.
- ALL `<text>` outside any filtered group, font family "Inter, sans-serif", never below 10.5px.
- Fit: max chars ≈ (box width - 20) / 7 at 12px, 6.4px/char at 11px; full-width note under 110
  chars; 40px between neighbouring point labels; bottom note 22px below the last row, H clears it
  by 8px. When in doubt, shorten.
- **No line, arrow, curve or axis may cross any text label** (the gate flags line-through-text).
  Keep labels in clear space beside lines; a deliberate strike-through carries `data-strike` on its
  path. Text must stay inside its box.
- Floor: one figure per Part plus one in the build-along. Draw the MECHANISM (what travels between
  two steps, where the data is replaced, which billing unit ticks at which node, where a retry
  waits, where an event is parked), never a metaphor literally, never decoration.

## Voice and honesty

Every Part gets a real-world story: use the documented behaviours in the map (Stripe webhooks
deliver more than once; Zapier says instant triggers do not deduplicate; GitHub's 10-second rule;
Make renamed operations to credits on 27 August; n8n's current stable needs Node 24 while its docs
say 20.19 to 24.x; Stripe prunes idempotency keys after at least 24 hours) or a clearly constructed
scenario labelled "constructed" (or phrased "a common pattern"). Never invent a named company
incident. The bench's day and the inventory rows are constructed.

## Cross-links (absolute URLs)

- Data Orchestration (DAGs, pipeline retries/idempotency): https://phoebefu6.github.io/learn-data-orchestration-with-phoebe/
- Data Reliability (runbooks b4, toil b7, on-call a3): https://phoebefu6.github.io/learn-data-reliability-with-phoebe/courses/b4-runbooks.html
- AI-Powered Productivity (AI drafting, triage): https://phoebefu6.github.io/learn-ai-productivity-with-phoebe/
- WorkBuddy automation: https://phoebefu6.github.io/learn-workbuddy-with-phoebe/courses/b8-automation.html
- AI Agents, workflows vs agents: https://phoebefu6.github.io/learn-ai-agents-with-phoebe/courses/a3-workflows-vs-agents.html
- PKM (weekly review habit): https://phoebefu6.github.io/learn-pkm-with-phoebe/
- Hub: https://phoebefu6.github.io/learn-with-phoebe/

## Footer chain and session titles

Footer left: "Session N of 6 · learn-automation-with-phoebe · by Phoebe Fu &nbsp;·&nbsp; 📚 <a href="https://phoebefu6.github.io/learn-with-phoebe/">Learn with Phoebe ↗</a>"
Footer right: `<a href="PREV.html">← Prev: Title</a> &nbsp;·&nbsp; <a href="NEXT.html">Next: Title →</a>`
(session 6: "← Prev: When a step fails" and `<a href="../index.html">Course home</a>`).

Session titles (exact; h1 carries one accent span):
1. `01-worth-automating.html` · Is it worth the time?
2. `02-triggers-and-actions.html` · Triggers, actions and the data between
3. `03-zapier-make-n8n.html` · Zapier, Make or n8n
4. `04-the-workflow-bench.html` · The workflow bench
5. `05-when-it-fails.html` · When a step fails
6. `06-leave-it-running.html` · Leave it running

Bench canon (all four failures on), quote only these: rung 1 texted 304/344, 0 duplicates, 40
lost, 600 runs, 51 red; rung 2 331/344, 11 duplicates, 13 lost, 13 red; rung 3 331/344, 0, 13;
rung 4 344/344, 0, 0, 613 runs (13 redrives), 0 red; store off on rung 4: 13 duplicates; store off
on rung 3: 11. With "reply lost" off, rung 2: 0 duplicates. Units per day: Zapier 621 / 675 / 675
/ 714 tasks; Make 1,616 / 1,697 / 1,697 / 1,766 credits; n8n 600 / 600 / 600 / 613 executions.
Cost per run (mapped): rung 1 $0.0414 Zapier, $0.0024 Make, €0.0080 n8n; rung 4 $0.0466, $0.0026,
€0.0080. Per day rung 1 $24.83 / $1.45 / €4.80; rung 4 $28.55 / $1.59 / €4.90.
