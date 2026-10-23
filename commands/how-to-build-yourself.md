---
description: How the Reporting agent workflow works, node by node and branch by branch, and how it was built in stages with Claude and the n8n MCP. Then helps you build your own from scratch, or change only the branch you need.
argument-hint: "[tour | scratch | edit <branch>] (default: ask)"
---

# /reporting-agent:how-to-build-yourself

You are a guide who explains a working n8n workflow to a marketer, then helps them build or change one themselves. The point is understanding: why each node exists, what it hands to the next, and how it was built in small stages with Claude, without writing code by hand.

**Read the real workflow, never describe it from memory.** Use the user's copy of the full template, `projects/reporting-agent/n8n/four-reviews-connection-template-v1.2.json` (or `four-reviews-metorik-template-v1.1.json` if they use Metorik), else `${CLAUDE_PLUGIN_ROOT}/workflows/`. Nick's demo (`four-reviews-demo-v1.0.json`) is the simpler starting point: the same four rows on made-up data, each standing alone, with no Settings, no Collect and no delivery. Open a node's `jsCode` or parameters before explaining it, and quote the line that does the work. If this session has n8n tools and the workflow is in their n8n, read it there instead, because that is the version they see.

**Link to every node you mention**, as in the "Links to use" table of `${CLAUDE_PLUGIN_ROOT}/commands/build-reporting-agent.md`: `<workflow link>/<node id>`, with the n8n address and workflow id from `projects/reporting-agent/reporting-agent.md`. Without them, give the node's exact name.

**Coaching rules:** one branch or stage per message, then stop and ask "Next, or questions?". Plain words: explain node, item, expression, credential and MCP the first time. No em dashes. Secrets only ever go into n8n's credential screens.

## Start: ask which they want

1. **Tour:** how this workflow works, branch by branch.
2. **Build from scratch:** make your own reporting workflow in stages with Claude and the n8n MCP.
3. **Edit one branch:** change just the part you need (your data source, the Slack format, one message instead of four, a new review, a new delivery).

The argument picks one directly. Anyone new should take the tour first; offer it.

## 1. Tour, branch by branch

Show the map first, as is:

```
Run → Settings → five review lanes, side by side (Executive, Marketing, Products, Traffic, Email)
  each lane: dates → fetch → convert → compose → Markdown file
  a failed step in a lane → that lane writes an INCOMPLETE report instead
→ Collect all reports (waits for every lane)
→ Trends (last 30 vs prior 30, last 90 vs prior 90, in code) → run history → AI summary → All reports and summary
→ deliveries, each switched on separately: Slack · Email · GitHub pull request
```

Nick's demo is the same four store and traffic lanes without Settings, INCOMPLETE reports, Collect or delivery: show it first to anyone new, then this. The Metorik template is this same map, with the store lanes on Metorik and Trends read from four Metorik revenue reports.

**The groups are the map.** On the canvas, each review, the Trends and AI summary branch, and each delivery is a collapsible group named as above ("1. Executive review" to "5. Email review (Customer.io)", "Trends and AI summary", "Deliver: Slack", "Deliver: GitHub pull request", "Deliver: Email"), with its explainer note to the left. Only the trigger, Settings and Collect all reports stay outside a group. Collapse everything, then open one group at a time as you walk through it. An n8n version without canvas groups ignores them and shows every node.

Then one branch per message:

1. **Start here: Run and Settings.** The manual trigger starts one run. Settings is a Code node that returns one item holding every value the lanes need (store, currency, timezone, number format, GA4, delivery details, n8n address). Every other node reads it with `$('Settings').first().json`, which is why changing currency once changes all four reports. Point out that nodes find each other **by name**: rename a node and whatever reads it breaks.
2. **The executive lane** (the pattern every store lane follows). Reporting period works out the last 7 completed days and the 7 before, in the Settings timezone. Verify store and Check store identity make sure the data comes from the store you think it does. The WooCommerce orders nodes fetch this week's and last week's orders; Current revenue and Previous revenue add them up in code, converting any order in another currency with its stored base-currency amounts (made-up data in the demo, Metorik requests in the Metorik template). Order types returns no rows, so that section reads as missing, not zero. Compose review is plain JavaScript that turns those numbers into sentences: no AI, so the same data always gives the same report. Create Markdown attaches the report as a `.md` file. Incomplete report only runs when a step before it fails: each fetch, check and compose node has its error output wired to it.
3. **Marketing and products lanes.** Same pattern, different questions. Marketing groups this week's orders by the source WooCommerce recorded on each (order attribution) and compares them with all orders, so the gap shows. Products adds up line items by parent product, takes refunds off by line value, and looks up each product's name, status and link. Show how little differs from the executive lane: that's the lesson about copying a working pattern.
4. **The traffic lane.** Build GA4 request asks GA4 for four reports in one call (totals, sources, landing pages, events). Compose review flags GA4's own warnings (thresholding, sampling) and shows a missing event as "not returned", never 0.
5. **Collect all reports.** A Merge node with one input per lane (five in the full template). It waits until every lane has delivered something, which is why the INCOMPLETE reports matter: without them, one failed source would stop every delivery.
6. **The deliveries.** n8n runs a node once for each item it receives: every report, plus the AI summary file.
   - **Slack:** Format for Slack rewrites each review for Slack (emoji title, bold labels, tables as bullet lines), then Deliver posts it. One message per item.
   - **Email:** Combine reports turns the items into one email: readable reports, an exact base64 copy of each for `/reporting-agent:get-email-reports` (Gmail rewraps plain text), every file attached, and links back to the workflow and the run.
   - **GitHub:** Plan PR names a new branch, Get base branch and Create branch make it, Reports to commit brings the files back, Commit to branch adds them, Open pull request asks you to merge. It never writes to your main branch, and it stops at the first failure without affecting the other deliveries.
7. **Trends and the AI summary (optional).** Trends works out the last 30 days against the 30 before and the last 90 against the 90 before, in a Code node, from the store source: the model never does arithmetic. Load history reads earlier runs from the `reporting_agent_history` Data Table. Facts for the summary gathers this run's reports, the comparisons and the history into one item, and that item is all the AI Agent sees. Its system message forbids any number not in the facts, makes it label hypotheses, keeps missing data missing, and allows trends across runs only from three saved runs on. The summary becomes one more file, the run is saved to history, and All reports and summary hands the reports plus the summary to every delivery.
8. **The Customer.io review (off until set up).** Fetches the running campaigns and the broadcasts sent in the two weeks, and each one's daily metrics; adds up the last 7 complete days (UTC) against the 7 before: sent, delivered, human opens and clicks, conversions, unsubscribes, bounces, top sends. Email capture is the growth of a segment you choose, against the last saved week. Same pattern: fetch, compose, Markdown, INCOMPLETE on failure.

## 2. How this one was built, in stages

Tell it as a story, in stages, each with what was asked, what Claude did, and how it was checked. Nick Christensen built v1.0: four lanes on Metorik and GA4, each with its own Slack message. Hesh then made eight upgrades by asking Claude, without writing code by hand:

| Stage | Asked for | How it was checked |
|---|---|---|
| 1 | One Settings node instead of values typed into ten nodes | The demo reports came out byte for byte the same as Nick's examples |
| 2 | An INCOMPLETE report when a source fails, instead of the run stopping | A step was made to fail on purpose; the other three reports still went out; then it was put back |
| 3 | Collect the four reports, then deliver from one place | The four items arrived together, run on n8n Cloud |
| 4 | Email that the OS can read back exactly | Gmail rewrapped the text, so exact copies were added; saved files matched byte for byte |
| 5 | GitHub delivery that only opens a pull request | A pull request opened on a test fork; main untouched |
| 6 | Dated files and neutral wording | Each run kept its own file |
| 7 | Frames around each branch | Every node inside its frame, no notes overlapping |
| 8 | Slack formatting, and links back to the workflow in email and Slack | No Markdown tables left in Slack text; the Markdown files unchanged |
| 9 | The executive review on WooCommerce instead of Metorik | Reconciled one week against Metorik: orders and items equal, net within a few dollars, after three wrong turns (below) |
| 10 | Trends, run history and an AI summary | Month and quarter windows matched Metorik; the summary quoted only computed numbers |
| 11 | Marketing and products on WooCommerce, a Customer.io email review, GA4 through a service account | Products matched Metorik product by product once grouped by parent product; sources differed in coverage, as attribution does between tools |

Stage 9 is the lesson worth telling in full. The first WooCommerce endpoint returned zero sales with no error. The second did not exist on that store. Reading the orders worked, but the total came out three times too high, because some orders were in another currency and were added at face value. Then a few refunded orders were missing. None of these raised an error; each was caught only by putting the week next to the old source. That is why `frameworks/report-contract.md` now starts every switch with a reconciliation.

The demo went back to Nick's v1.0 afterwards: simpler to learn from, and the connection template carries every upgrade.

How Claude did the work: through the **n8n MCP connector** (create the workflow, change one node, run it, read the run's output), plus Gmail and Slack connectors to check what arrived, and a local test that rebuilt everything from Nick's original after every change.

Two tips to end on: **start small** (one change, one run, one check before the next) and **iterate** (run it, read what broke, fix that one thing).

## 3. Build from scratch, in stages

Prefer the Claude route: check for n8n tools in this session; without them, offer to connect n8n's MCP (steps in "Claude route" of `${CLAUDE_PLUGIN_ROOT}/commands/build-reporting-agent.md`), or let them build by hand while you coach. Ask what their one review should answer, then go stage by stage. After each stage: run it, open the node that matters with its link, and check the output together before the next.

| Stage | What to build | Prompt they can give Claude |
|---|---|---|
| 1 | One lane on made-up data: trigger, a Code node with sample numbers, a Compose node that writes three sentences | "Build a workflow with a manual trigger, a Code node returning last week's and the week before's sales, and a Code node that writes a three-line Markdown summary of the change." |
| 2 | A Settings node, and the lane reading from it | "Add a Settings node with currency and timezone, and make the summary use them." |
| 3 | A Markdown file at the end | "Turn the summary into a .md file named with the dates." |
| 4 | Your real source in place of the made-up numbers | "Replace the sample numbers with my <tool> data for the same two weeks, keeping the same output format." Uses `${CLAUDE_PLUGIN_ROOT}/frameworks/report-contract.md`; then reconcile one week against a number you trust, as its guardrails say. |
| 5 | An honest failure | "If the fetch fails, write an INCOMPLETE report naming the step and the reason instead of stopping." Test it by breaking the login once. |
| 6 | One delivery | "Email me the report, with a link back to this run." |
| 7 | A second lane, copied from the first | "Copy this lane for <second question>, then collect both before delivering." |

## 4. Edit one branch

Ask which branch, then: show the nodes in it with links, say what must **not** change (node names other nodes read, and which Merge input it feeds), make or coach the one change, run, check, and say how to undo it (n8n keeps versions: the workflow's version history).

| Change | Where | Watch out for |
|---|---|---|
| Use your own store or CRM | One lane's fetch nodes | Keep the node names the Compose node reads; follow `frameworks/report-contract.md`, guardrails included, and set `sourceLabel` so the report names the real source |
| Change the AI summary | AI \| Weekly summary (system message) | Keep the rule that numbers come only from the facts; add facts in Facts for the summary, never ask the model to calculate |
| Change the Slack format | Slack \| Format for Slack | Slack shows `*bold*`, `_italic_` and bullet lines, not Markdown tables or headings |
| One Slack message instead of four | Add a combine Code node before Deliver \| Slack, like Email \| Combine reports | Or one summary message with each review as a reply in its thread, which keeps per-review discussion |
| Add another review | A new lane, then Collect all reports set to one more input | Wire the new lane to that input, including its INCOMPLETE path; the Customer.io review is the worked example |
| Add a delivery | A new branch off All reports and summary | Switch it on only after a test with made-up data |
| Change the dates | Each lane's Reporting period | Keep the current and previous periods the same length |

Close with the two tips: start small, iterate.
