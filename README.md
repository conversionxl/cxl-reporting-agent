# Reporting agent (test build 0.4.2)

A module for the CXL AI Native Marketer cohort, for the Reporting agent workshop (sprint day 3, 12 November 2026). You start from Nick Christensen's demo on made-up data, then build your own n8n workflow on your own GA4, store or CRM, and email platform, one review at a time, with Claude building through the n8n MCP and every review reconciled against a number you trust before the next. It delivers the reviews, and a personal OS command saves them so Claude can read them with you. Nick's ads review is a separate workflow with its own command.

Built on Nick Christensen's four-reviews workflow (handoff of 22 October 2026). This test build is for Nick's review: every change to his workflow is listed in [CHANGES-v1.1.md](CHANGES-v1.1.md), with the reason, and any of them can be undone.

## Commands

Every build command first checks your folder setup and that n8n is connected to Claude through n8n's MCP connector, and fixes either before anything else. Claude builds everything in n8n through that connector.

| Command | What it does |
|---|---|
| `/reporting-agent:build-reporting-demo` | Builds Nick's demo, v2, in your n8n and runs it on made-up data. Your task: connect Slack (quickest: a message to yourself, with only a sign-in), or swap Slack for email and save the reviews into your OS. Optional: switch on the AI summary. |
| `/reporting-agent:build-reporting-agent` | Your own version: a copy of the demo, then GA4, your store or CRM in place of the made-up data, an optional email review on your own email platform, optional trends and AI summary, and the outputs (Slack or Microsoft Teams, email, a GitHub pull request only to a private repo). One build loop for every review: propose, login in the right n8n project, fetch with delivery off, convert, reconcile. |
| `/reporting-agent:build-reporting-agent-ads` | Nick's ads review as its own workflow: runs on his sample campaigns first, then shows how to connect Meta, Google Ads, or any other ad channel in the same format. |
| `/reporting-agent:get-email-reports` | Saves each run's reports from email into your OS and reads them with you. Also reads reports merged in from a GitHub pull request. |
| `/reporting-agent:how-to-build-yourself` | Every node explained, the story of how the worked examples were built from Nick's demo, and help building from scratch or editing one branch. |

## What's in it

| Path | What it is |
|---|---|
| `workflows/four-reviews-demo-v2.json` | **Nick's demo, v2.** His four reviews on made-up data (executive, marketing sources, products, traffic) with the pieces he asked for: one Settings node, Collect all reports, and a Summary (a week at a glance in code, on; an AI summary, off). Slack is the only delivery, switched off. Each review, the Summary and Slack are collapsible groups. No credentials. |
| `workflows/four-reviews-connection-template-v1.2.json` | **Worked example: how Hesh took the demo to a working version**, built and tested on a live WooCommerce store, GA4 and Customer.io: five reviews (executive, marketing sources, products, traffic, email), Settings, INCOMPLETE reports, Collect, trends (30 and 90 days, in code), run history in an n8n Data Table, an AI summary, and delivery (Slack, email, GitHub). A guide to copy pieces from, never a template. Every source, the AI summary and every delivery switched off, no credentials. |
| `workflows/four-reviews-metorik-template-v1.1.json` | **Worked example: the same build on Metorik**, Nick's original source. Shipped switched off, no credentials. |
| `workflows/ads-review-from-nick-v1.json` | **Nick's ads review, its own workflow**, from his MIT starter: his schedule plus a manual "Run now" trigger, sample campaigns, merge and Analyze code unchanged and credited, a Compose step that writes the same report format (labelled SAMPLE DATA until real ad data is connected), an INCOMPLETE path, and Slack and email delivery, both off. |
| `workflows/sample-reports/` | What the workflows write, all on made-up data: the four demo reviews, the week at a glance, an INCOMPLETE review, the email body, an email review, the ads review on Nick's sample data and an INCOMPLETE summary. |
| `commands/` | The five commands above. |
| `plugin/setup.sh` | Adds the module to a personal OS: the `.gitignore` block for saved reports, the project file, the workflows and a CLAUDE.md section. Never overwrites a file. |
| `plugin/to_sdk.py` | Converts a workflow file into n8n SDK code, so Claude can create it through the n8n MCP, plus `<out>.groups.json`, the operation that adds its collapsible groups afterwards. |
| `frameworks/report-contract.md` | The format each review needs, guardrails for switching sources, the WooCommerce mapping, and the ads row format. |
| `frameworks/metric-limits.md` | What the reviews cannot tell you (from Nick's handoff). |
| `tests/` | Rebuilds all four workflows from their sources (Nick's exports in `tests/fixtures/nick-v1.0/` and `tests/fixtures/nick-ads-starter/`, and the sanitized export of the live build in `tests/fixtures/full-template-source.json`), checks each matches the shipped file, and runs every lane locally. `bash tests/run-tests.sh` |
| `NOTES-for-Nick.md` | For Nick: his v2 demo, his ads starter as its own workflow, the email review, and node groups, each to confirm. |
| `tests/fixtures/nick-ads-starter/` | Nick's ads reporting starter (MIT) from his workshop repo, with its license, which the ads workflow is built from. |

## The workflows

**Nick's demo, v2:**

```
Run → Settings → four reviews on made-up data (Executive, Marketing, Products, Traffic)
      each review: period → made-up data → check → compose → Markdown file
      any failed step → that review writes an INCOMPLETE report instead
   → Collect all reports
   → Summary: week at a glance (code, on) · AI summary (off)
   → Deliver: Slack (off)
```

**Worked example on WooCommerce (v1.2):**

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

**Worked example on Metorik (v1.1):** the same shape, with the store lanes on Metorik and the trends read from four Metorik revenue reports (last 30, prior 30, last 90, prior 90 days).

**Ads review (its own workflow):** `Daily 9am or Run now → Settings → yesterday → Google Ads and Meta (sample data) → merge → Nick's Analyze → compose → Slack · Email`.

**Every workflow is grouped:** each review, the summary or trends, and each delivery is a collapsible n8n canvas group with its explainer note beside it. Groups need an n8n version with canvas groups; an older one ignores them and shows every node.

## Install

1. In Claude, open **Customize**, then **Browse plugins**, **Personal**, **+**, **Add marketplace from GitHub**. Enter `https://github.com/conversionxl/cxl-reporting-agent`, then add **reporting-agent**. This is its own marketplace, separate from the ones for personal-os, marketing-brain and campaign-engine.
   (Terminal or VS Code instead: `/plugin marketplace add conversionxl/cxl-reporting-agent`, then `/plugin install reporting-agent@cxl-reporting-agent`.)
2. Open your personal OS folder (or an empty folder) in Claude and run `/reporting-agent:build-reporting-demo`. It sets the module up, connects n8n if needed, and builds the demo.

New versions don't install themselves on a personal marketplace. To update: **Plugins → Add → Manage marketplaces → ⋮** next to the marketplace → **Check for updates**. Your folder and saved reports are untouched.

## Tested

- `tests/run-tests.sh`: all four shipped workflows match a fresh build; Nick's v2 demo writes his example reports from his made-up data, has no credentials, delivers only to Slack (off), writes the week at a glance in code and lists a failed review as missing, adds the AI summary only when switched on, and works with Slack swapped for the worked example's email delivery; both worked examples have five lanes and no ads; the ads workflow carries Nick's code unchanged under a credit header, labels his sample data, goes INCOMPLETE when grading fails, and drops the label once the sample nodes are replaced; the WooCommerce worked example on made-up WooCommerce orders (a foreign-currency order, a refunded order, an empty week), Customer.io series and a stand-in model, as shipped (every lane INCOMPLETE, no zeros), and with a real failure; public-file checks (no credentials, no store addresses, every source and delivery off, the AI summary off); EUR and Europe/Tallinn settings; delivery payloads for Slack, email and GitHub; every build command carries the same folder and n8n check, and none offers a manual route.
- On n8n Cloud (23 October 2026, 0.3.0): clean run, forced failure, Slack to a test channel, email, and a GitHub pull request on a test fork. `/get-email-reports` saved the reports from the email byte-identical to the workflow output.
- On n8n Cloud (23 October 2026, 0.3.0): the executive review on a live WooCommerce store, reconciled against Metorik (orders and items equal, net within a few dollars for one week and for 30 days); marketing and products on WooCommerce (products matched Metorik product by product); the Customer.io review on a live workspace; GA4 through a Google Service Account login, once the private key was pasted with `\n` markers; trends and the AI summary on live data; one live delivery with all five reviews complete: six Slack messages to a private channel and one email.
- Setup: no folder map, renamed folders, a renamed parent folder, a second run, and without `jq`.

**Not tested in n8n yet (0.4.2):** Slack as a direct message to yourself, with a Slack OAuth2 login made through n8n's Connect my account and a member ID in `slackChannel`. **(0.4.0):** the v2 demo and the ads workflow created through the MCP from `to_sdk.py` output with their groups applied, the ads workflow run through the MCP from its Run now trigger, the demo's Slack-to-email swap, the Microsoft Teams output, an email review on a platform other than Customer.io, and the three build commands with a real attendee. Everything above is tested locally.
