# Four reviews workflow: v1.1 changes

## 0.5.2 (28 October 2026)

**Ken Fleischer's tips from his demo** ([Circle, 28 October](https://ai-native.cxl.com/c/help-and-demos/reporting-agent-demo-with-email-delivery-and-ai-summary)).

| # | Change | Why |
|---|---|---|
| 47 | `/reporting-agent:setup` and `/reporting-agent:build-reporting-demo` step 4: how to check the AI summary against the reviews (numbers match, no invented cause, guesses labelled, missing costs missing), and why a "rerun traffic so the weeks line up" suggestion is by design: traffic reads the last 7 completed days, the demo's store data has fixed dates. | Ken read his summary line by line and found it honest, plus one suggestion that looked like a fix but wasn't. |
| 48 | Setup says n8n is often already on the member's Claude account: skip every connection step, `claude mcp add` included, when the tools are there. | Ken's was already connected. |
| 49 | Setup and `/reporting-agent:get-email-reports`: retry a Gmail connector error ("service unavailable", "quota exhausted") once before troubleshooting. | Ken's failed twice, then worked on the retry. |
| 50 | Setup, own data: it needs enough history (a few weeks of GA4 and no store data won't say much), and it can run for a client as a weekly brief once they sign off on connecting their data. | Ken held off for that reason, and named the client use. |

## 0.5.1 (28 October 2026)

| # | Change | Why |
|---|---|---|
| 46 | The shared preflight (in setup and every build command) points to "Your own folders" in `/personal-os:setup` instead of `/personal-os:start`. | The personal-os plugin folded `/personal-os:start` into `/personal-os:setup` (0.4.0). |

## 0.5.0 (28 October 2026)

**One place to start: `/reporting-agent:setup`.** The workshop prep on Circle shrinks to installing the plugins; the coaching moves into each plugin's setup command, as in the Marketing Brain, the Campaign Engine and the personal OS.

| # | Change | Why |
|---|---|---|
| 43 | New `/reporting-agent:setup`: the shared preflight (folder and n8n), the limits first, then the demo command's steps 1 to 3 (build, run, deliver to a Slack DM or email, `get-email-reports`), one step per message with the four blocks. It never duplicates a build step; it follows the build commands. | Members need one command to type, and the prep lessons can point to it alone. |
| 44 | After the demo is delivered, setup says plainly that this is all the workshop needs, then offers the AI summary and the learner's own data (`/reporting-agent:build-reporting-agent`) as optional, stoppable at any step. | The workshop customises the agent live; nobody should think they must finish it beforehand. |
| 45 | Setup resumes from the project file's Progress list, and recommends one folder for every module. `tests/static.py` checks that setup carries the same preflight block as the build commands. | Typing setup again always lands on the next step, in the folder the other modules use. |

## 0.4.2 (26 October 2026)

**Slack, the quick way: a direct message to yourself.** Nick asked for the Slack setup to be in the commands; Hesh suggested a DM to yourself first, so most people only sign in, and the Slack app becomes the fallback.

| # | Change | Why |
|---|---|---|
| 40 | `/reporting-agent:build-reporting-demo`, step 3A: first a **Slack OAuth2 API** credential made with n8n's **Connect my account**, the learner's member ID in `slackChannel`, and **Deliver \| Slack** set to OAuth2. Then Nick's steps as the fallback (an app named "Reporting Agent", `chat:write`, install, a **Slack API** credential with the token in Access Token, a test channel with the app invited, the channel ID from its details), for self-hosted n8n, a workspace that blocks the sign-in, or a channel. Then email (B) if Slack is blocked altogether. The troubleshooting list adds the wrong-project login and a node whose authentication doesn't match the credential. | No Slack app, channel or invite for most people, and a DM is private by default, so the same setup suits real reviews. |
| 41 | The same two routes in `/reporting-agent:build-reporting-agent` (step 6a, plus the step 7 destination check and the links table), `/reporting-agent:build-reporting-agent-ads` (step 4) and `/reporting-agent:how-to-build-yourself` (the Slack branch and a "post to a team channel" row). `/reporting-agent:get-email-reports` has no Slack step. | One Slack story in every command. |
| 42 | On every canvas (demo, ads, both worked examples) the Slack note is now the quick route, a DM to yourself, and a new **Slack fallback: your own app** note to its right carries Nick's seven steps. The demo's "Your task" note points to both. The Metorik example's old note, which pointed to a SLACK-SETUP.md that no longer ships, is replaced. No other node changes. | The canvas and the commands say the same thing, and the fallback is there when the sign-in is blocked. |

## 0.4.1 (26 October 2026)

**Aligned with the workshop deck, and existing installs pick up a newer version.**

| # | Change | Why |
|---|---|---|
| 38 | The WooCommerce worked example's **Executive \| Compose review** prints a total the source leaves out (refunds or items from a CRM) as "not available", and its change as N/A, instead of "NaN" or "undefined". The report contract and `/reporting-agent:build-reporting-agent` say to leave such a field out and copy that Compose node for a live executive review. Test T11b covers it. | The deck promises "missing, never zero" for a CRM's refunds; the contract mapped them to 0 and a missing field printed NaN. |
| 39 | `plugin/setup.sh` also runs when the project file already exists. It still never overwrites: it adds the files a newer version brought, and prints an `UPDATE:` line when the Reporting agent section in `CLAUDE.md` lacks a current command or the project file has no Progress list. The preflight in the three build commands then offers to bring either up to date, and changes it only on a yes. | Folders set up with 0.1.0 kept the old command table in `CLAUDE.md`, the old project file and the v1.1 workflow files. |

## 0.4.0 (24 October 2026)

**Three build commands instead of one, and no up-front questions before the demo.** Every build command starts with the same two checks: the folder is set up (the setup script runs if the project file is missing), and n8n is connected to Claude through n8n's MCP connector. Without the connector the command fixes that first and goes no further: there is no manual route any more, so attendees are not asked to choose one.

| # | Change | Why |
|---|---|---|
| 31 | **Nick's demo, v2** (`workflows/four-reviews-demo-v2.json`, built by `build_demo_v2()` in `tests/build.py` from Nick's v1.0 export, which stays in `tests/fixtures/nick-v1.0/`): his four reviews and made-up data unchanged; Settings (store, currency, timezone, locale, Slack channel, n8n address) read by every review; an INCOMPLETE report per review; Collect all reports; a Summary with a **week at a glance** written in code (on: one line quoted from each review, and any review that did not run) and an **AI summary** (an AI Agent with `claude-sonnet-5-5`, 6000 tokens, off: while off it passes through and nothing extra is sent); Slack as the only delivery, off, with the channel from Settings; six groups; a "Your task" note. `workflows/four-reviews-demo-v1.0.json` is removed. | Nick asked for v2 to have the Settings node and the collection of the reports plus a summary only, with Slack as the one output. Summary: both, the AI one switched off, so the demo needs no API key. |
| 32 | `/reporting-agent:build-reporting-demo`: the checks, then Claude creates the v2 demo through the MCP (`to_sdk.py`, then its groups), runs it, shows the reviews and the glance, and gives the task: connect Slack, or swap Slack for the worked example's email delivery and save the reviews with `/reporting-agent:get-email-reports`. Optional: the AI summary with an Anthropic key. | One short path to a working demo, no questionnaire first. |
| 33 | `/reporting-agent:build-reporting-agent` rewritten: the checks, a copy of the v2 demo, then GA4, then their own store or CRM in place of the made-up nodes (one review at a time through the build loop), an optional email review copied from the Customer.io lane and switched to their own email platform, optional trends, history and AI summary, then the outputs one at a time: Slack or Microsoft Teams, email (with how `/reporting-agent:get-email-reports` brings it into the OS), and a GitHub pull request only after the repo is checked to be private. The WooCommerce and Metorik workflows are used as guides to copy pieces from, never offered as templates. The checkpoints table keeps every real failure, plus "a live review still said DEMO". | Hesh: use the full Metorik and WooCommerce workflows only as examples to copy the branches for the extra lanes and outputs. |
| 34 | **Nick's ads review is its own workflow** (`workflows/ads-review-from-nick-v1.json`, `build_ads()`), from his MIT starter: his daily schedule kept as is, plus a manual trigger **Run now** beside it (both start the same chain into Settings, so the n8n MCP can run it in manual mode), two sample-data nodes, merge and Analyze code carried unchanged under a credit header; Settings; a Compose step writing the report contract (`ads-<date>-to-<date>.md`, a daily read of yesterday, labelled SAMPLE DATA while any sample node feeds the merge); an INCOMPLETE path; Slack and email delivery, both off, in place of his webhook and SMTP nodes; three groups and notes on connecting Meta, Google Ads and other channels. `/reporting-agent:build-reporting-agent-ads` builds it, runs Nick's sample, then connects their ad accounts in the same row format. | Hesh: build it as a separate workflow, not as lane 6. |
| 35 | Ads removed from both worked examples: no lane 6, no `adsEnabled`, no skipped-item filters, no sample-data rule in the AI summary's instructions. Collect takes five inputs, nine groups. Reverses items 27 and 28. | Follows from 34. |
| 36 | Email and the GitHub pull request count reviews without the summary or the glance file; Slack titles the glance; `/reporting-agent:get-email-reports` saves `glance-...md` files; the glance has a line for the email review. | The glance is a file like the summary, not a review. |
| 37 | Tests: the v2 demo (Nick's reports from his data, no credentials, Slack only and off, the glance deterministic and listing a failed review, the AI summary only when on, the Slack-to-email swap), the examples without ads, the ads workflow (Nick's code verbatim, the report contract, the sample label and its removal, a failing grade step), one static loop over all four workflows (groups, notes clear of groups, no credentials, no CXL names, every source, delivery and AI summary off), and every build command carrying the same preflight with no manual route. Sample reports regenerated: the dated traffic file replaces `website-traffic-review.md`, plus the glance. | Keep every shipped file reproducible and checked. |

## 0.3.0 (23 October 2026)

**The demo is back to Nick's v1.0, unchanged.** `workflows/four-reviews-demo-v1.0.json` is his export byte for byte: four rows on made-up data, no Settings, no Collect, no delivery. It is the simpler thing to learn from. Every change below, and every change in the v1.1 list further down, now lives in the connection template only. The build command was rebuilt around it (item 30): demo (steps 3 and 4), your own copy with Settings and Collect (5), delivery tested on made-up data (6), your sales review (7), the other reviews (8), extras (9), one live run (10).

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
| 27 | **Ads review, lane 6, from Nick's ads reporting starter** (MIT, `nickyc1/ship-icp-ads-automate-monitoring`, `n8n-ads-reporting/starter-workflow.json`, kept as `tests/fixtures/nick-ads-starter/` with its license) in both worked examples: his two sample-data nodes, merge and Analyze code carried unchanged under a credit header; his trigger, Slack webhook and email node left out; a Compose step wraps the digest into the report contract (`ads-<start>-to-<end>.md`), labelled SAMPLE DATA while the sample nodes are in place; an INCOMPLETE path; group "6. Ads review" and an explainer note with the Meta setup (ad account id, Graph API token with `ads_read`, conversion `action_type`). Collect takes six inputs. | Nick's proposal 1: one collection report for every review, ads included. |
| 28 | `adsEnabled:false` in Settings: while off, the ads lane sends a **skipped** item, so Collect never waits; the summary facts, the history row, Slack, email and GitHub all leave it out. When on, the summary facts list it in `sample_data` and the model's instructions say sample data is not the business's. | An optional lane must not pollute live runs, and Collect waits for every input. |
| 29 | `plugin/to_sdk.py` also writes `<out>.groups.json`: the `setNodeGroups` operation to apply after creating a workflow from SDK code | The SDK code does not carry canvas groups, so the Claude route lost them. |
| 30 | **The two templates are now worked examples, not templates.** `/reporting-agent:build-reporting-agent` starts every attendee from Nick's demo, makes their own copy with Settings, INCOMPLETE reports and Collect, tests delivery on made-up data, then connects each review on their own tools through one build loop (propose, login in the right n8n project, fetch with delivery off, convert, reconcile one week), with a copy-paste prompt per step, the real failure modes as checkpoints, and one live run at the end. `/reporting-agent:how-to-build-yourself` gains the build story stage by stage. Import from URL link for Nick's demo. | Hesh: the examples show how he iterated from the dummy to a working version; attendees should do the same on their own stack, not fill in his file. |

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
