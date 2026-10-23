# Four reviews workflow: v1.1 changes

## 0.3.0 (23 October 2026)

**The demo is back to Nick's v1.0, unchanged.** `workflows/four-reviews-demo-v1.0.json` is his export byte for byte: four rows on made-up data, no Settings, no Collect, no delivery. It is the simpler thing to learn from. Every change below, and every change in the v1.1 list further down, now lives in the connection template only. The build command was reordered to match: demo (steps 3 and 4), then the template with its Settings (step 5), delivery (6), own data (7), GA4 (8), extras (9).

**Full template (`workflows/four-reviews-connection-template-v1.2.json`), built and tested live on n8n Cloud** against a WooCommerce store, Customer.io and GA4, then exported with credentials, ids and store details removed (`tests/fixtures/full-template-source.json`) and rebuilt by `build_full()` in `tests/build.py`. The 0.2.0 template, on Metorik, is kept as `workflows/four-reviews-metorik-template-v1.1.json`, and now gets the same branches (items 24 to 26).

| # | Change | Why |
|---|---|---|
| 8 | Settings: `sourceLabel` and `refundNote`, printed on the reviews; `storeUrl` for every WooCommerce request; `cioApiUrl` (EU workspaces use `api-eu`); `cioCaptureSegmentId` and `cioCaptureLabel`; `n8nUrl` as in 0.2.0 | The review said "Live Metorik data" when the numbers came from WooCommerce, and the AI summary then told the reader the figures would not match Metorik. |
| 9 | Executive review on WooCommerce: `wc/v3/orders` summed in Code | `wc/v3/reports/sales` returned zero sales with no error on a store with the new order storage; `wc-analytics` returned 404 with Analytics off. |
| 10 | Multi-currency conversion from the order's base-currency fields; INCOMPLETE when they are missing | Orders in another currency were added at face value and inflated gross about three times. |
| 11 | Refunded orders included | Without them, orders, gross and refunds drifted from Metorik. With them, one week and 30 days reconciled within a few dollars. |
| 12 | Trends branch after Collect: last 30 vs prior 30 and last 90 vs prior 90, computed in code from WooCommerce orders | Month and quarter comparisons from the first run, without asking a model to calculate. |
| 13 | Run history in an n8n Data Table (`reporting_agent_history`, found by name; the learner creates it) | Trends across runs, once there are three. |
| 14 | AI summary: AI Agent with an Anthropic model (`claude-sonnet-5-5`), fed only the reports, the computed comparisons and the history; given the number of complete reviews directly, and earlier runs of the same week count once; its file is delivered with the reports through "All reports and summary". Shipped off. | Trends, flags, what is and isn't working, in one read. On the live run it first miscounted the reviews and counted three test reruns of one week as three weeks. |
| 15 | Marketing review on WooCommerce order attribution (`_wc_order_attribution_utm_source` and `_utm_medium`); orders without a `utm_source` are counted as not represented | The same orders fetch as the executive review, no Metorik needed. Coverage differs from Metorik's source report (WooCommerce recorded a source on more orders), which is expected: attribution never reconciles across tools, totals do. |
| 16 | Products review on order line items, grouped by parent product (`product_id`), net of refunds shared by line value; names, status and links from `wc/v3/products` | Grouped by variation name it did not line up with Metorik; by parent product it matched product by product. |
| 17 | Customer.io email review (fifth lane, shipped off): App API `/v1/campaigns`, `/v1/campaigns/{id}/metrics` and `/v1/newsletters/{id}/metrics` with `period=days&steps=15`; the last 7 complete UTC days against the 7 before; `human_opened` and `human_clicked`, `unsubscribed`, `topic_unsubscribed`, bounces and spam; top sends | Campaign performance and unsubscribes next to revenue. |
| 18 | Email capture: net growth of a chosen segment (`/v1/segments/{id}/customer_count`) against the last saved week, stored in the history as `facts_json.leads_email_count` | The App API cannot count people by the date they were created, so a segment does the counting. The first run only takes a reading. |
| 19 | GA4 through a Google Service Account credential (predefined `googleApi` type) with `analytics.readonly` | A Search Console login returned Forbidden; the service account needs no OAuth sign-in. |
| 20 | Slack: Format for Slack also titles the email review and the summary; one message per file; no n8n footer (`includeLinkToWorkflow: false`) | As 0.2.0, extended to the new files. |
| 21 | The INCOMPLETE report's "First run before setup?" line only when the reason says a source is not connected yet (both templates) | It showed on real failures too, where it misleads. |
| 22 | A switched-off WooCommerce node never reads as zero: the conversion steps throw "No order data: the WooCommerce request node is switched off..." (the lane goes INCOMPLETE) and Trends reports itself unavailable; an empty week from a connected store is a true zero | A switched-off node passes its input through, which a sum would otherwise read as no orders. |
| 23 | Collect renamed "Collect all reports" (five inputs) in both templates | Five lanes. |
| 24 | **Collapsible node groups** in both templates (`nodeGroups`, ids derived from the group name so builds are reproducible): "1. Executive review" to "5. Email review (Customer.io)", "Trends and AI summary", "Deliver: Slack", "Deliver: GitHub pull request", "Deliver: Email". The trigger, Settings and Collect stay outside (n8n does not allow a trigger in a group). The coloured lane and delivery frames are gone; each explainer note sits to the left of its group, following Hesh's layout of the live workflow, plus a new "Email review explainer". Verified through the n8n API; **Import from file not yet verified**. An n8n version without canvas groups ignores the key and shows every node. | Collapsed, the canvas is about a dozen blocks, and the workshop can open one block at a time. |
| 25 | Metorik template gets the Customer.io lane, Trends, history, AI summary and All reports and summary, copied from the full template's build so both share one version of the code. Trends there reads four Metorik revenue reports (last 30, prior 30, last 90, prior 90 days) through `.totals` only, the shape the executive review already relies on; a switched-off or failed request makes Trends report itself unavailable. The executive review passes its totals on, for the history and the summary. Settings gains `sourceLabel` (`Metorik`), `refundNote` (refund-date reporting), `cioApiUrl`, `cioCaptureSegmentId`, `cioCaptureLabel`. All shipped switched off. | One template per store source, same features. |
| 26 | AI summary output limit raised to 6000 tokens (both templates); the History `facts_json` expression no longer contains `}}` | The live run cut the summary off mid-sentence at 2000 tokens, and `}}` inside the expression ended it early, so the capture count was not saved. |

**Coaching changes from the live test:** credentials must be created in, or shared with, the workflow's n8n project; WooCommerce auth by a Basic header (the `qs` method was refused); a Search Console Google login has no Analytics scope (403), so GA4 needs its own; check that the GitHub delivery repo is private before a live run; check after every import that delivery nodes are switched off (one import came in with Slack on and a login filled in); reconcile one week against the old source before trusting a new one; a GA4 service-account key must be pasted with its line breaks as literal `\n` markers, because n8n's Private Key field is a single line: `jq '.private_key' <key file> | sed 's/^"//; s/"$//' | pbcopy` (pasting real line breaks gives `secretOrPrivateKey must be an asymmetric key`). The general rules are in `frameworks/report-contract.md`, "Switching sources: guardrails".

---

Proposed edits to Nick's handoff of 22 October 2026, and the plugin built around them, for Nick's review before anything is final. Since 0.3.0 these changes apply to the templates only (`workflows/four-reviews-metorik-template-v1.1.json`, Metorik and GA4, and through it the full template); the demo ships as Nick's v1.0. The report code and the made-up data are unchanged, apart from the lines listed below.

## What changed

| # | Change | Why | Nodes |
|---|---|---|---|
| 1 | **Settings node** after the trigger: store name, currency, timezone, number format, GA4 property ID and events, plus the email and GitHub delivery settings | USD, America/Chicago and the store name were typed into about 10 nodes. Attendees outside the US now edit one node. | 1 new. The 4 Reporting period nodes, 3 Check store identity nodes and 3 Compose review nodes now read from it. |
| 2 | **Incomplete reports.** When a source request or check fails, that lane writes an `INCOMPLETE` report naming the failed step and the reason, and the run carries on | Without this, one failure stops the run, and the Merge in change 3 waits forever. It also matches the workshop page: "Label a run incomplete when a source fails, instead of sending stale numbers". | 1 new Code node per lane. "On error: continue (using error output)" on each request, check and compose node. |
| 3 | **Collect all four reports** in one Merge node, then one branch per delivery: Slack, GitHub, Email | Attendees pick the delivery they want and switch the others off. The four per-lane Slack nodes are replaced by one, which still posts one message per report. | 1 Merge, 1 Slack, 1 Email (Gmail) with a Code node that combines the four reports into one email, and a 6-node GitHub chain (below). The 4 old Slack nodes are removed. |
| 4 | **Dated traffic file:** `traffic-<start>-to-<end>.md` | It was always `website-traffic-review.md`, so each run overwrote the last. | Traffic, Compose review: 1 line |
| 5 | **Neutral revenue source:** "Your store or CRM remains the revenue source." | Attendees without Metorik | Traffic, Compose review: 1 line. Sticky notes updated to match. |
| 6 | **Framed layout:** each review and each delivery branch sits in its own coloured frame; lanes are spaced further apart; the Slack setup note sits next to the delivery note | Less overwhelming on first open. Positions and notes only, no logic. n8n's collapsible canvas groups (2.28 and later) are the next step once their export format is confirmed | 4 new notes, positions |
| 7 | **Slack formatting and workflow links:** a Format for Slack step rewrites each review for Slack (emoji title, bold labels, dashed separators, tables as bullet lines) and Slack's own n8n footer is off; with `n8nUrl` set in Settings, email and Slack link to the workflow and the run | Slack showed raw Markdown tables and headings. The Markdown files are unchanged | 1 new Code node, Settings, Email combine |

All three delivery nodes are switched off, with no credentials and placeholder destinations.

- **GitHub** never commits to the main branch. Each run reads the base branch (`githubBase`, default `main`), creates a branch `reports/<date>-run-<execution id>`, commits the four reports to `<githubFolder>/<fileName>` on that branch, and opens one pull request that the attendee merges. The GitHub nodes use "continue on error", so a GitHub failure doesn't stop Slack or email. The credential needs Contents and Pull requests set to read and write. Note: a token belonging to a repo admin can still push to a protected main through other tools; the workflow itself only ever opens a PR.
- **Email** sends one plain-text message. Each report sits between `-----BEGIN REPORT <file>-----` and `-----END REPORT-----` for reading, and is also attached. Gmail hard-wraps long lines in plain text, and the Claude Gmail connector cannot download attachments, so the email also carries an exact base64 copy of each report between `-----BEGIN FILE <file>-----` and `-----END FILE-----`. The `/get-email-reports` command decodes those; the test confirms they come out byte-identical after wrapping.

**One former demo-only change (until 0.2.0):** the made-up "Verify store" data echoed the Settings values, so the demo ran in any currency. Since 0.3.0 the demo is Nick's v1.0 again; the tests reuse that echo when they run the template on made-up data in another currency.

## The plugin around it (new, for review too)

| Piece | What it does |
|---|---|
| `/reporting-agent:build-reporting-agent` | One command. Sets up the attendee's personal OS first (a project file, the two workflows to import, a local-only folder for saved reports), then coaches step by step: n8n, import, Settings, first run, delivery, then the exercise: swap one review (executive first) onto their own store or CRM. Claude writes the conversion Code node from a sample of their data with personal details removed. |
| `/reporting-agent:get-email-reports` | Saves the reports from the email into the OS and gives a readout: what changed, facts vs hypotheses vs missing data, what to check next. |
| `/reporting-agent:how-to-build-yourself` | Explains every node and branch, how this was built in stages with Claude and the n8n MCP, and helps build from scratch or edit one branch. |
| `frameworks/report-contract.md` | The format each review needs, including a first draft of how CRM fields map onto the store fields. Please check the CRM mapping. |

**The workshop demo:** a finished run on the made-up data passes. One review on their own store or CRM data, complete or a screenshot of where it failed, gets the fuller review from you and Hesh. Email and ads lanes come after you approve this version.

## If you want something back the way it was

Each change is a separate step in `tests/build.py`, so any one of them can be removed and the workflows rebuilt and retested with `bash tests/run-tests.sh`. For example: back to four Slack messages per lane, no Merge node, or no INCOMPLETE reports.

## How it was tested

The workflow was run locally with a small runner that copies n8n's behaviour for Code nodes, switched-off nodes, error outputs and Merge. Delivery nodes were recorded, not sent. 30 checks, all passed (`tests/test.js`):

- **Demo with default settings:** the executive, marketing and products reports are byte-identical to your example files. Traffic is identical apart from change 5. All four are collected. Slack gets 4 messages, and email 1 message with 4 attachments. GitHub reads `main`, creates one branch, commits 4 files with the exact report text to that branch only, and opens one PR into `main`.
- **Demo in EUR, Europe/Tallinn, de-DE:** all four complete, formatted as `24.000 €`.
- **Template before setup:** 4 INCOMPLETE reports, and the run doesn't stop (sample: `sample-reports/executive-incomplete-example.md`).
- **Template with sources connected,** using your made-up data as stand-in API responses: all four complete, with the store name in the header.
- **One Metorik request fails (503):** executive is INCOMPLETE and names the step and reason. The other three are complete, and all four are delivered.
- **Wrong store name:** the 3 store lanes are INCOMPLETE and show the expected and actual store. Traffic completes.
- **GA4 fails:** traffic is INCOMPLETE.

**Tested on n8n Cloud (23 October 2026), demo workflow:**
- **Clean run:** succeeded. All four reports were collected, and the executive, marketing and products reports are byte-identical to the local run. Traffic matched too, apart from its live dates (15 to 21 October on the run date).
- **Failure run:** "Executive | Previous revenue" was made to throw. The run still succeeded, executive came out INCOMPLETE naming the step and reason, and the email read "3 of 4 reviews complete" with "(incomplete)" in the subject. n8n sends the error as `{error: "<message>"}`, which the Incomplete code handles. The node was then restored and a clean run confirmed.

**Live delivery tests (23 October 2026):**
- **Slack:** 4 messages posted to a test channel, one per report. Two issues to discuss: Slack does not render the traffic report's Markdown tables and headings, and n8n appends "Automated with this n8n workflow" plus a link to each message unless that option is switched off on the node.
- **Email:** one email sent through Gmail with all four reports in the body and attached.
- **GitHub:** run against a test fork. The workflow read `main`, created `reports/2026-10-22-run-8143`, committed the 4 reports to that branch, and opened PR #1 (4 commits, 4 files, 87 additions). `main` was not changed. Base-branch and branch-creation failures now stop the GitHub steps at the first error without affecting Slack or email. An earlier run against a repo the login could not access showed why: without this, each later GitHub step failed with its own error.

**Not tested yet:**
- Importing the JSON file through the n8n editor. The workflow was created through the n8n API from the same definition, not by file import.
- The Metorik template in n8n, and a live Metorik run
- The full template file imported fresh (it is the sanitized export of the tested workflow), and its GA4 lane on a live run

## Questions for Nick

1. **Combined or separate reports?** v1.1 collects all four, then delivers them together. Combined: fewer nodes (one per delivery instead of four), one email and one pull request per run, an INCOMPLETE review shows up in one place, and a summary across all four becomes possible. Separate (your v1.0): each report can be its own thread in Slack or email, so replies stay on topic and can go to different owners, and each lane stays fully independent. Which do you want? Slack currently still posts one message per report either way.
2. Before v1.1, when one source failed, did the other lanes still run on your canvas, or did n8n stop the whole run?
3. Should the three identical "Verify store" calls stay separate (each lane independent), or share one call?
4. In the demo, the three store lanes are fixed to 14 to 20 October, but the traffic lane uses the real last 7 days. Should traffic be fixed to the same week?
5. Slack does not render the traffic report's Markdown tables. Send a shorter Slack version and keep the full report for the file and email?
6. For attendees without Metorik: does it work if Claude writes one Code node that converts their Shopify or CRM data into the same format your made-up data nodes use?
7. Is the first draft of the CRM mapping in `frameworks/report-contract.md` right, or would you map deals differently?
