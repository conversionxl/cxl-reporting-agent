# Reporting agent (test build 0.3.0)

A module for the CXL AI Native Marketer cohort, for the Reporting agent workshop (sprint day 3, 12 November 2026). An n8n workflow builds weekly reviews from your store or CRM, GA4 and Customer.io, adds trends and an AI summary, delivers them, and a personal OS command saves them so Claude can read them with you.

Built on Nick Christensen's four-reviews workflow (handoff of 22 October 2026). This test build is for Nick's review: every change to his workflow is listed in [CHANGES-v1.1.md](CHANGES-v1.1.md), with the reason, and any of them can be undone.

## What's in it

| Path | What it is |
|---|---|
| `workflows/four-reviews-demo-v1.0.json` | Nick's original demo, unchanged: four rows on made-up data, no Settings, no Collect, no delivery, no credentials. Import into n8n and run. |
| `workflows/four-reviews-connection-template-v1.2.json` | The full template, built and tested on a live WooCommerce store, Customer.io and GA4: five reviews (executive, marketing sources, products, traffic, email), Settings, INCOMPLETE reports, Collect, trends (30 and 90 days, in code), run history in an n8n Data Table, an AI summary, and delivery (Slack, email, GitHub). Every source, the AI summary and every delivery switched off, no credentials. |
| `workflows/four-reviews-metorik-template-v1.1.json` | The same five reviews, trends, history, AI summary and delivery, with the store reviews and the trends wired for Metorik: for stores whose data lives in Metorik. Shipped switched off, no credentials. |
| `workflows/sample-reports/` | The four reports the demo produces, an INCOMPLETE example, the template's email body, an email review and an INCOMPLETE summary, all on made-up data. |
| `commands/build-reporting-agent.md`, `plugin/setup.sh` | `/reporting-agent:build-reporting-agent`: sets the module up in a personal OS, then coaches step by step from no n8n to your own data. |
| `commands/how-to-build-yourself.md` | `/reporting-agent:how-to-build-yourself`: every node and branch explained, how it was built with Claude and MCP, and help building from scratch or editing one branch. |
| `plugin/to_sdk.py` | Converts a workflow file into n8n SDK code, so Claude can create it through the n8n MCP. |
| `commands/get-email-reports.md` | `/reporting-agent:get-email-reports`: saves each run's reports from email into the OS and reads them. |
| `frameworks/report-contract.md` | The format each review needs, guardrails for switching sources, and the WooCommerce mapping. |
| `frameworks/metric-limits.md` | What the reviews cannot tell you (from Nick's handoff). |
| `tests/` | Checks the demo is Nick's v1.0 byte for byte, rebuilds both templates (Metorik from Nick's export, full from the sanitized export of the live build in `tests/fixtures/full-template-source.json`), and runs every lane locally. `bash tests/run-tests.sh` |
| `NOTES-for-Nick.md` | Proposals for Nick: the ads branch and the Customer.io branch, shipped off, and node groups. |

## The workflows

**Demo (Nick's v1.0):** four rows, each `period → made-up data → check → compose → Markdown file`, standing alone. Start here.

**Full template (v1.2):**

```
Run → Settings → five lanes (Executive, Marketing, Products, Traffic, Email)
      each lane: period → source → convert → compose → Markdown file
      any failed step → that lane writes an INCOMPLETE report instead
   → Collect all reports
   → Trends (30 and 90 days, in code) → run history → AI summary → All reports and summary
   → delivery, each switched off until set up:
       Slack (one formatted message per report and the summary)
       Email (one email: readable reports, exact copies, attachments)
       GitHub (new branch, one commit per file, one pull request; never commits to main)
```

**Metorik template (v1.1):** the same shape, with the store lanes on Metorik and the trends read from four Metorik revenue reports (last 30, prior 30, last 90, prior 90 days).

**Both templates are grouped:** each review, Trends and AI summary, and each delivery is a collapsible n8n canvas group with its explainer note beside it, so collapsed the canvas is about a dozen blocks. Groups need an n8n version with canvas groups; an older one ignores them and shows every node.

## Install

1. In Claude, open **Customize**, then **Browse plugins**, **Personal**, **+**, **Add marketplace from GitHub**. Enter `https://github.com/conversionxl/cxl-reporting-agent`, then add **reporting-agent**. This is its own marketplace, separate from the ones for personal-os, marketing-brain and campaign-engine.
   (Terminal or VS Code instead: `/plugin marketplace add conversionxl/cxl-reporting-agent`, then `/plugin install reporting-agent@cxl-reporting-agent`.)
2. Open your personal OS folder (or an empty folder) in Claude Code and run `/reporting-agent:build-reporting-agent`. It sets the module up, then walks you through n8n one step at a time.

New versions don't install themselves on a personal marketplace. To update: **Plugins → Add → Manage marketplaces → ⋮** next to the marketplace → **Check for updates**. Your folder and saved reports are untouched.

**Just the workflow?** Import `workflows/four-reviews-demo-v1.0.json` into a new n8n workflow (Workflow menu, Import from file) and run it. Open each row's **Create Markdown BEFORE Slack** node: one report each.

## Tested

- `tests/run-tests.sh`: the demo is Nick's v1.0 byte for byte and its reports are identical to his examples; both templates match a fresh build; the full template on made-up WooCommerce orders (a foreign-currency order, a refunded order, an empty week), Customer.io series and a stand-in model, as shipped (every lane INCOMPLETE, no zeros), and with a real failure; public-file checks (no credentials, no store addresses, every source and delivery off); EUR and Europe/Tallinn settings; INCOMPLETE reports for a failed source, a wrong store and a failed GA4 call; delivery payloads for Slack, email and GitHub.
- On n8n Cloud (23 October 2026): clean run, forced failure, Slack to a test channel, email, and a GitHub pull request on a test fork. `/get-email-reports` saved the four reports from the email byte-identical to the workflow output.
- Setup: no folder map, renamed folders, a renamed parent folder, a second run, and without `jq`.

- On n8n Cloud (23 October 2026, 0.3.0): the step 7 walkthrough end to end on a live WooCommerce store, reconciled against Metorik (orders and items equal, net within a few dollars for one week and for 30 days); the trends branch and the AI summary on live data.

- On n8n Cloud (23 October 2026, 0.3.0): the marketing and products reviews on WooCommerce (products matched Metorik product by product), the Customer.io review on a live workspace, and the full template's AI summary.

**Not tested:** GA4 through the service account login on a live run (the key was being re-entered at the time of export), the full template file imported fresh into n8n (it is the sanitized export of the tested workflow, rebuilt by `tests/build.py`), and the walkthrough with a real attendee.
