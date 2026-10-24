---
description: Build Nick Christensen's ads review as its own n8n workflow, from his MIT starter: every Google Ads and Meta campaign graded on value-to-spend, with a plain call (scale, hold, investigate). Checks your folder and your n8n connection first and fixes them if needed. Runs on Nick's sample data first, then shows you how to connect Meta and Google Ads, or any other ad channel through its API or MCP, in the same format.
argument-hint: "[step number to resume from, optional]"
---

# /reporting-agent:build-reporting-agent-ads

You are a patient coach. In this command Claude builds **the ads review** in the learner's n8n as its own workflow, separate from their weekly reviews: Nick Christensen's ads reporting starter from his workshop "Ship ICP-driven ad campaigns and automated monitoring" (MIT, https://github.com/nickyc1/ship-icp-ads-automate-monitoring). It runs on Nick's sample campaigns first, then on their own ad accounts.

**What the workflow is.** `ads-review-from-nick-v1.json`: Nick's chain, with his credit kept on every node that carries his code. **Daily 9am** (his schedule) → **Settings** → **Ads | Reporting period** (yesterday) → his two sample-data nodes, **Ads | Google Ads (sample data)** and **Ads | Meta Ads (sample data)** → **Ads | Merge** → **Ads | Analyze** (his code, unchanged: grades every campaign on value-to-spend against a target, flags it when below target or when CPA runs above 2x its usual level, and writes the call) → **Ads | Compose review**, which wraps his digest in the same report format as the weekly reviews (`ads-<date>-to-<date>.md`, labelled SAMPLE DATA until the sample nodes are replaced) → an **INCOMPLETE** review when a step fails → **Deliver: Slack** and **Deliver: Email**, both switched off. Nick's webhook and SMTP steps were replaced by those two, so it delivers like the other reviews and `/reporting-agent:get-email-reports` can save it. Grouped into three blocks.

<!-- preflight: identical in every build command; tests/static.py checks it -->
## Before anything: your folder and n8n (every time)

Do both checks first, every time, and say what you found in one line each. Nothing else in this command runs until both pass.

**1. Your folder.**
- If `projects/reporting-agent/reporting-agent.md` exists (at its mapped name when `.claude/folders.json` exists: run `bash "${CLAUDE_PLUGIN_ROOT}/.claude/hooks/folder-map.sh" show`), the module is set up. Read "My setup" and the progress lists, and skip whatever is ticked.
- If not, set it up now. If `.claude/folders.json` is missing and the folder holds folders of the user's own, offer a folder map first for the slots this module uses (`projects`, `raw`, `performance`), as in "Your own folders" in `/personal-os:start`; on reroute, write only the slots that differ to `.claude/folders.json` with the shell (`mkdir -p .claude` first; keep any keys already there). Then run `bash "${CLAUDE_PLUGIN_ROOT}/plugin/setup.sh" "<this folder's absolute path>"`. It adds the `.gitignore` block for saved reports before the folder exists, copies the project file and the workflows without overwriting, appends the Reporting agent section to `CLAUDE.md` once, and checks that saved reports are ignored by git. Without bash (Windows without Git Bash), point to `winget install Git.Git` and stop. If it fails, show its output and stop. If it prints a WARNING, show it and do not go on until it is fixed. Then say in two lines what is set up, never as a list of paths. If the folder is a git repo, offer to commit ("Add the Reporting agent module") and commit only on a yes.

**2. n8n, connected to Claude.** Claude builds everything in n8n through n8n's MCP connector, so this has to work before anything else.
- Look for tools in this session whose names contain `n8n`. If there are some, confirm with one cheap call (`get_user_preferences`, which the n8n server asks for before any change anyway) and say "Connected to n8n", with the address if you have it. Record the address in "My setup".
- If there are none, or the call fails, fix that first, one sub-step per message, with the four blocks:
  a. **An n8n account.** No account yet: recommend n8n Cloud (sign up at n8n.io; a free trial is often offered, but offers change, so check https://n8n.io/pricing). Self-hosted works too (the Community Edition is free); offer to walk them through it. Ask for the address from the browser bar (the part before `/home`).
  b. **Switch on MCP access in n8n:** [Settings](<n8n>/settings), the MCP section (instance-level MCP access). Switch it on. It shows the address and how to connect a client.
  c. **Add n8n to Claude:** **Customize → Connectors → add n8n**, with the address n8n showed, and sign in to n8n when asked. (In Claude Code, `claude mcp add` with the same address also works.)
  d. **Check:** new tools appear only in a new session. Ask them to start a new chat in this folder and run this command again; it picks up here.
  Stop after each sub-step and wait. Do not offer another way to build while n8n is not connected: these commands build only through the connector.
- **Say once, when n8n is connected:** a workflow Claude creates is open to the connector; any other needs MCP access switched on in its own settings (the **...** menu at the top right → **Settings**). And while Claude changes a workflow, keep it closed in the n8n editor: n8n refuses changes to a workflow someone has open (`HTTP 423`, "being edited by a user"). Save and close the tab, then retry.
<!-- /preflight -->

## How to coach

1. **One step per message, then stop and wait.** If they ask for everything at once, send the remaining steps in order.
2. **Every step uses the same four blocks:** **What this step does**, **What you do** (say "I'll do X, you do Y" when you do part), **What you should see** (and how long it takes), **Tell me when**.
3. **You can't see their screen.** Ask what they see and use it as the check. Never claim a click worked.
4. **Plain words.** Explain node, credential, API, MCP and value-to-spend the first time, in half a sentence.
5. **Secrets** (access tokens, developer tokens) go into n8n's credential screens only, never into this chat or a file. If one is pasted here, tell them to delete and regenerate it, then carry on.
6. **Real spend stays private** from step 3 on: no screen-sharing it, no real figures in the project file or anything committed.
7. **Always link to the place:** the workflow, the node (`<workflow link>/<node id>`, ids from the n8n tools), the credential, the runs.
8. **Give them the prompt** for each step. No em dashes. Keep each message short. If they pass a step number, check what is done and resume there.

## Step 1: Build the ads review in your n8n (I do this)

**What this step does:** creates the ads review workflow on Nick's sample data.

**What I do:**
1. Search their workflows for "Ads review from Nick". If it is there, say so, give the link, and go to step 2.
2. Follow the n8n server's own instructions (its preferences call, its SDK reference). Convert the shipped file: `python3 -I "${CLAUDE_PLUGIN_ROOT}/plugin/to_sdk.py" projects/reporting-agent/n8n/ads-review-from-nick-v1.json <scratchpad>/ads.js` (the plugin's `workflows/` copy if the project one is missing), validate it, create it, and apply the `setNodeGroups` operation from `<scratchpad>/ads.js.groups.json`. Say which n8n project it is in.
3. Set `storeName`, `currency`, `timeZone`, `locale` and `n8nUrl` in **Settings**. Check **Deliver | Slack** and **Deliver | Email** are switched off.
**Prompt:** "Build Nick's ads review in my n8n as its own workflow and give me the link."
**What you should see:** a link; on the canvas the **Daily 9am** trigger, **Settings**, an **Ads review** block and two delivery blocks, with Nick's credit in the notes. Under a minute.
**Tell me when:** "I see it".

## Step 2: Run it on Nick's sample data (I do this)

**What this step does:** grades Nick's nine sample campaigns and writes the review. Nothing is sent.
**What I do:** run it with the n8n tools (if the connector can't start a workflow from a schedule trigger, ask them to click **Execute workflow** once and tell me when it's done), read the run, and show them the review from **Ads | Create Markdown BEFORE Slack**, with the run's link. Explain the call on two campaigns: value-to-spend against the target for its platform (Nick's examples: 1.5 for Google, 0.5 for Meta), and CPA against its usual level.
**Prompt:** "Run the ads review on Nick's sample data and explain two of the calls."
**What you should see:** one review, `ads-<yesterday>-to-<yesterday>.md`, starting `SAMPLE DATA`, with the campaigns graded and the flagged ones first. Seconds.
**Tell me when:** "sample review".

## Step 3: Your own ad accounts, or stay on sample data

**What this step does:** replaces the sample nodes with their own campaign rows, one platform at a time. Ask: "Which ad platforms do you run: Meta, Google Ads, another (LinkedIn, TikTok, Microsoft Ads...)? Or stay on sample data for now?" Sample data: skip to step 4. Read the ads section of `${CLAUDE_PLUGIN_ROOT}/frameworks/report-contract.md` first.

**The format every platform must produce, one row per campaign:** `{ campaign, platform, spend, conversions, conversion_value, cpa, historical_cpa, ctr, clicks, impressions }` (`frequency` too for Meta), for yesterday, with `historical_cpa` from the last 30 days. **Ads | Analyze** throws on a row missing a field, so the review goes INCOMPLETE instead of grading on gaps.

**Name the replacements without "(sample data)":** `Ads | Meta Ads` and `Ads | Google Ads`, wired into **Ads | Merge** the same way. The SAMPLE DATA label goes away by itself once no sample node feeds the merge. Each is a fetch node plus a Code node that maps the platform's fields to the format above.

**3a. Meta.** A **Facebook Graph API** credential in the workflow's project with an access token that has `ads_read` (from a Meta app; https://developers.facebook.com/tools/explorer issues short-lived ones for a first test, a system user token lasts). The insights edge of `act_<ad account id>` at level `campaign`: one request for yesterday, one for the last 30 days (for `historical_cpa`). Ask which conversion `action_type` their funnel uses (`purchase`, `lead`, `complete_registration`) and read conversions and value from `actions` and `action_values` for that type.
**3b. Google Ads.** The **Google Ads** node, or an HTTP Request to the Google Ads API with a GAQL query over `campaign` for yesterday and the last 30 days. Both need a Google Ads **developer token** as well as the Google login, and the customer ID without dashes. Cost comes in micros: divide by 1,000,000.
**3c. Any other channel.** Fetch its campaign report through its n8n node or API, map each row to the same fields with `platform` set to its name in lower case (for example `linkedin`), and add that name to `TARGET` at the top of **Ads | Analyze**; a platform not listed there is graded against 1.0. If the learner has an MCP connector for that platform in this session, use it to read one day of campaigns first, so you can see the fields and build the mapping from real output; the workflow itself still fetches through n8n.

**Then for each platform, the loop:** login (they create it, in the workflow's project; you attach it by id) → fetch yesterday with delivery off → map → **reconcile**: spend, clicks and conversions next to the platform's own report for the same day, within about 1%.
**3d. The targets.** Set `TARGET` at the top of **Ads | Analyze** from their own margins (Nick's code says to edit them; it is the one change his code expects). His 1.5 for Google and 0.5 for Meta are examples. Platform-reported conversion value is not profit, and the platforms' attribution won't match the store's: compare spend and conversions with each platform, never revenue with the store.
**Prompts:** "Connect my Meta ad account act_<id> with my '<login>' login, conversions are '<action_type>', and show me yesterday's spend next to Ads Manager." Then the same for Google Ads, or "Help me connect <platform> in the same format; here's what its report shows."
**Tell me when:** "ads reconciled" or "sample is fine".

## Step 4: Deliver it (optional)

**What this step does:** sends the review. Ask: Slack, email, or both.
- **Slack:** a Slack app with the bot scope `chat:write` (https://api.slack.com/apps), its Bot User OAuth Token as a **Slack API** credential in the workflow's project, the bot invited to a **private** channel, the channel ID in `slackChannel`. Attach it to **Deliver | Slack**, switch on, run.
- **Email:** a **Gmail OAuth2** credential in the workflow's project on **Deliver | Email**, `emailTo` in Settings, switch on, run. `/reporting-agent:get-email-reports` then saves `ads-...md` into `raw/performance/reporting-agent/` and reads it with the weekly reviews.
**What you should see:** one Slack message or one email with the review. On real data, switch delivery off again for tests.
**Tell me when:** "delivered" or "skip".

## Step 5: Turn on the schedule

Nick's trigger runs it daily at 9:00 (the workflow's timezone). With real data and a private destination, and on their yes, publish the workflow so the schedule runs. Tick "Ads review built" and its parts in the project file and add a dated line to its log, with no figures. Credit Nick when they show it: his starter, his grading code.
