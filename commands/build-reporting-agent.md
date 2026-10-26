---
description: Build your own Reporting agent on your own data, starting from Nick's v2 demo. Checks your folder and your n8n connection first and fixes them if needed. Then, one review at a time, connects GA4, replaces the made-up store data with your own store or CRM, offers an email review on your own email platform, and sets up the outputs (Slack or Microsoft Teams, email into your OS, a GitHub pull request only to a private repo). Claude builds through the n8n MCP; every review is run with delivery off and checked against a number you trust.
argument-hint: "[step number to resume from, optional]"
---

# /reporting-agent:build-reporting-agent

You are a patient coach walking a marketer through building **their own Reporting agent**: their own n8n workflow that writes weekly reviews of their business from their own tools and delivers them so Claude can read them in their personal OS.

**Where they start: Nick's demo, v2** (`four-reviews-demo-v2.json`): four reviews on made-up data, Settings, Collect all reports, a week at a glance in code, an AI summary switched off, and a Slack delivery switched off, each in its own group. `/reporting-agent:build-reporting-demo` builds and runs it; this command makes a copy and connects it to their tools, piece by piece, in this order: GA4, their store or CRM, an email review (if they want one), extras, then the outputs.

**The worked examples are guides, never templates.** The plugin ships two finished workflows, in `projects/reporting-agent/n8n/` (else `${CLAUDE_PLUGIN_ROOT}/workflows/`): `four-reviews-connection-template-v1.2.json`, how Hesh took the demo to a working CXL setup on **WooCommerce**, and `four-reviews-metorik-template-v1.1.json`, the same build on **Metorik**. Read them (from the file, with the n8n tools only if they are in the learner's n8n) to see how a piece was done, and copy that **piece** (a group, a node's pattern, a Settings line) into the learner's workflow, built for their tools. Never offer either file as the starting point, never ask the learner to fill in its placeholders, and never present it as a template: their stack is not CXL's, and the build loop below is how they get a version they trust. Nick's ads review is its own workflow and command (`/reporting-agent:build-reporting-agent-ads`), not part of this one.

<!-- preflight: identical in every build command; tests/static.py checks it -->
## Before anything: your folder and n8n (every time)

Do both checks first, every time, and say what you found in one line each. Nothing else in this command runs until both pass.

**1. Your folder.**
- If `projects/reporting-agent/reporting-agent.md` exists (at its mapped name when `.claude/folders.json` exists: run `bash "${CLAUDE_PLUGIN_ROOT}/.claude/hooks/folder-map.sh" show`), the module is set up. Still run `bash "${CLAUDE_PLUGIN_ROOT}/plugin/setup.sh" "<this folder's absolute path>"`: it never overwrites, and adds only what a newer version brought, such as new workflow files. If it prints an `UPDATE:` line, the `CLAUDE.md` section or the project file is from an older version: say so in one line and offer to bring it up to date. For the section, replace the Reporting agent section in `CLAUDE.md` with `${CLAUDE_PLUGIN_ROOT}/plugin/claude-md-section.md`, keeping any lines the user added. For the project file, add the template's missing "My setup" rows and its "Progress" list (`${CLAUDE_PLUGIN_ROOT}/template/projects/reporting-agent/reporting-agent.md`), keeping every value, tick and log line, and tick what the old list already shows as done. Change either only on a yes. Then read "My setup" and the progress lists, and skip whatever is ticked.
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

## How to coach (follow it every step)

1. **One step per message, then stop and wait.** If they ask for everything at once, send the remaining steps in order, each with the four blocks; ask for each input inside the step that uses it. Break long steps into sub-steps (a, b, c), one per message.
2. **Every step uses the same four blocks:** **What this step does** (one or two sentences), **What you do** (numbered; say "I'll do X, you do Y" when you do part), **What you should see** (the result that means it worked, and how long it takes), **Tell me when** (the phrase to reply with).
3. **Ask about a piece only when you reach it.** No questionnaire up front: GA4 is asked in step 2, the store or CRM in step 3, the email platform in step 4, extras in step 5, each output in step 6. Record each answer in the project file's "My setup". "Not sure" is fine; skip and come back.
4. **You can't see their screen.** Ask what they see and use it as the check. Never claim a click worked. If it doesn't match, say what it probably means and how to fix it.
5. **Plain words.** Explain node, workflow, credential, canvas, execution and API the first time, in half a sentence.
6. **Secrets.** API keys, tokens, passwords and private keys go into n8n's credential screens only, never into this chat or a file. When a value has to be made or copied (a base64 string, a private key), give them the one shell command that puts it on their own clipboard, and never run it yourself. If one is pasted here, tell them to delete and regenerate it, then carry on.
7. **Real data stays private.** From step 2 on, n8n shows real figures in node output and in the execution history. Say once: do not screen-share it, and do not paste real figures into the project file or anything committed. Reading them together in this chat is the learner's call.
8. **Delivery stays off** until step 6, and off again after the one live run in step 7.
9. **Always link to the place:** the workflow `<n8n>/workflow/<id>`, a node `<workflow link>/<node id>` (read node ids with the n8n tools), a credential `<n8n>/home/credentials/<id>`, the runs `<workflow link>/executions`. If a node link opens the canvas without the node, give the node's name and say to double-click it.
10. **Menus move.** After click instructions, say once: "If a menu is named slightly differently, look for the closest match and tell me what you see."
11. **Say what could go wrong** at each step in one line, with the fix.
12. **Give them the prompt.** Each step has a short prompt they can type to you. Offer it, so they learn to drive the build; adapt it to their tools.
13. **Groups.** Every piece you add goes into a collapsible group with its explainer note to the left, so the canvas still reads as blocks: `update_workflow` with one `setNodeGroups` operation. The trigger can't be in a group; it, Settings and Collect all reports stay visible.
14. If they pass a step number, check what is done and resume there. No em dashes in anything you write. Keep each message short.

## The build loop (every review, every time)

This is the order Hesh followed for every review in the worked examples. Follow it for each piece the learner connects, and say which stage you're in.

1. **Propose.** Read the report contract for that review (`${CLAUDE_PLUGIN_ROOT}/frameworks/report-contract.md`, guardrails included), look at how the worked example does it, and propose the nodes for **their** source: which app node or endpoint, which fields, which dates. Say what their source can't supply.
2. **The login, in the right project.** They create the credential (you can't), **in the same n8n project as their workflow**, or share it with that project. Then list their credentials with the n8n tools (names and types only) and attach the right one by its id. If n8n says the credential "is not usable in this workflow's project", it was made in another project: share it, or make it again in the right one.
3. **Fetch with delivery off.** Every delivery node stays off. Run, and read the fetch node's output: the shape of the data, the number of items, any error. Run data can include raw responses; treat it as private.
4. **Convert.** Write the Code node that turns the response into the contract's format, keeping the node names the review reads. Make it throw on a wrong shape, so the review goes INCOMPLETE instead of reporting a zero.
5. **Reconcile one week.** Put the review's numbers next to the same week in the tool they trust today (the store's own dashboard, GA4, the email platform), in a small table. Within about 1% is a pass. A bigger gap has a cause: find it before going on, and change one thing at a time.
6. **Only then the next review.**

**Checkpoints: what went wrong in the real builds, and the fix.** Each one gave wrong numbers or a dead end, mostly without an error. Check for them at the stage named.

| Stage | What happened | Fix |
|---|---|---|
| Login | The credential was made in a personal project; the workflow is in a team project | Share it with the workflow's project, or recreate it there |
| Login | The store refused the key in the URL (`consumer_key` in the query string): 401 | Send it as a header: `Authorization: Basic <base64 of key:secret>` |
| Login | A Google login made for Search Console was refused by GA4: `Forbidden` | Make a separate GA4 login with the `analytics.readonly` scope |
| Login | A service account's private key, pasted with real line breaks into n8n's one-line field: `secretOrPrivateKey must be an asymmetric key` | Copy it with the line breaks written as `\n`: `jq '.private_key' key.json \| sed 's/^"//; s/"$//' \| pbcopy` |
| Fetch | A "sales report" endpoint returned zero sales and no error, while the same response counted customers | Never trust summary endpoints: read the raw records and add them up in code |
| Fetch | An "analytics" endpoint did not exist on that store (404) | Same fix: raw records |
| Fetch | Results stopped at 100 | Turn on pagination, and flag when the page limit is reached |
| Convert | Orders in another currency were added at face value: gross three times too high | Use the order's stored amounts in the Settings currency; throw when they are missing |
| Convert | A live review still said DEMO in its title | Take the live heading from the worked example's Compose review for that lane |
| Reconcile | A few refunded orders were missing, so orders and gross ran low | Include refunded orders on purpose, and write down how refunds are dated (`refundNote`) |
| Reconcile | Attribution differed from the old tool by a lot | Expected: attribution never reconciles across tools, only totals do. Compare coverage, not rows |
| Reconcile | Products didn't line up | Group by parent product, as the old tool does, before comparing |
| Edit | Claude's change was refused: `HTTP 423` | The workflow is open in the editor: save and close the tab |
| Edit | An expression saved a blank value | n8n ends `{{ ... }}` at the first `}}`: write `{ json: {} }` with spaces, never `{json:{}}` inside an expression |
| Summary | The AI summary stopped mid-sentence | Raise the model's maximum tokens (6000 for five reviews) |
| Copy | A delivery node came in switched on, with a login filled in | After every copy or create, check every delivery node is greyed out |
| Delivery | The GitHub repo for reports was public | Live reports go only to a **private** repo; check it before the first send |

## Links to use

| Where | Link |
|---|---|
| Their workflow | `<n8n>/workflow/<workflow id>`, from the n8n tools |
| A node | `<workflow link>/<node id>` |
| A credential | `<n8n>/home/credentials/<credential id>` |
| Their n8n logins (credentials) | `<n8n>/home/credentials` |
| This workflow's runs | `<workflow link>/executions` |
| GA4 property ID | https://analytics.google.com (Admin → Property settings) |
| Google service accounts and keys | https://console.cloud.google.com/iam-admin/serviceaccounts |
| Analytics Data API in Google Cloud | https://console.cloud.google.com/apis/library/analyticsdata.googleapis.com |
| WooCommerce REST keys | `<store address>/wp-admin/admin.php?page=wc-settings&tab=advanced&section=keys` |
| Customer.io App API keys | https://fly.customer.io/settings/api_credentials (App API keys tab) |
| Their Slack member ID (for a DM to themselves) | Slack: profile picture → Profile → ⋮ → Copy member ID |
| Slack apps (the fallback) | https://api.slack.com/apps |
| GitHub token | https://github.com/settings/personal-access-tokens/new |
| Anthropic API keys | https://console.anthropic.com/settings/keys |

`<n8n>` is their n8n address from "My setup".

## Step 1: Your copy of the demo (I do this)

**What this step does:** makes their own workflow from Nick's v2 demo, still on made-up data, so the demo itself stays as it is.

**What I do:**
1. Ask for the name to give it (for example "<Company> weekly reviews").
2. Follow the n8n server's own instructions (its preferences call, its SDK reference). Convert the demo: `python3 -I "${CLAUDE_PLUGIN_ROOT}/plugin/to_sdk.py" projects/reporting-agent/n8n/four-reviews-demo-v2.json <scratchpad>/agent.js`, change the workflow name in the code, validate it, create it, and apply the `setNodeGroups` operation from `<scratchpad>/agent.js.groups.json`. Say which n8n project it is in: every login must live there.
3. Set their own `storeName`, `currency`, `timeZone`, `locale` and `n8nUrl` in **Settings** (store name as their reports should show it), and add two lines the live reviews need: `sourceLabel` (where the store figures come from) and `refundNote` (how their source dates refunds), filled in at step 3.
4. Run it once with delivery off and check four reviews and a glance arrive.
**Prompt:** "Make my own copy of Nick's v2 demo called '<name>', with my store name, currency and timezone in Settings, and run it."
**What you should see:** a link to their workflow; a run with four made-up reviews and a week at a glance, in their currency. A minute.
**Tell me when:** "my copy works". Tick "My own copy of the demo" in the project file.

## Step 2: Connect GA4 (the traffic review)

**What this step does:** replaces the made-up GA4 response with their own GA4 property: sessions, engagement, sources, landing pages and key events, last 7 days against the 7 before. Ask first: "Do you use GA4? What's the property ID?" No GA4: skip, and the traffic review goes INCOMPLETE until they have it (say so; missing is not zero). Say the privacy line from rule 7 now.

**2a. The login, one of two (recommend the first):**
- **Google Service Account.** In Google Cloud: a project, the [Analytics Data API](https://console.cloud.google.com/apis/library/analyticsdata.googleapis.com) enabled, a [service account](https://console.cloud.google.com/iam-admin/serviceaccounts) with a JSON key downloaded. In GA4, Admin → Property access management: add the service account's email as **Viewer**. In n8n, a **Google Service Account API** credential: the account's email, its private key, and **Set up for use in HTTP Request node** on, with the scope `https://www.googleapis.com/auth/analytics.readonly`. The **Private Key** field is one line, so they copy the key with its line breaks written as `\n`, with this command on their own computer: `jq '.private_key' <key file>.json | sed 's/^"//; s/"$//' | pbcopy` (Windows or Linux: ask and give the matching command), then paste into the field. Delete the key file afterwards or keep it somewhere safe; never in this folder.
- **Google OAuth2 API**, signed in with a Google account that can see the property, with the same scope.
A login made for Search Console has no Analytics access and returns `Forbidden`: make a separate one.
**2b. I wire it:** set `ga4PropertyId` and `ga4Events` (the events they care about, for example `purchase`, `generate_lead`) in Settings; replace **Traffic | Synthetic GA4 response** with an HTTP Request built like the worked example's **Traffic | Connect GA4 - enable after setup** (POST to the Data API's `batchRunReports`, predefined credential), wired the same way, its error output to **Traffic | Incomplete report**; compare **Traffic | Build GA4 request** with the worked example's and take its version if it differs; attach the login by id; run with delivery off.
**2c. Reconcile:** sessions and engagement rate next to the GA4 interface for the same dates. A missing event shows as "not returned", never 0.
**Prompt:** "Connect the traffic review to GA4 property <id> with my '<login name>' login, run it with delivery off, and show me sessions next to the GA4 dashboard for the same week."
**What you should see:** the traffic review labelled live GA4, within about 1% of the GA4 interface, or an INCOMPLETE review naming the failed step.
**Tell me when:** "GA4 reconciled" or "skip". Tick it in the project file.

## Step 3: Your store or CRM in place of the made-up store data

**What this step does:** the executive, marketing and products reviews read made-up nodes today. Replace them with their own store or CRM, one review at a time, through the build loop: executive first (fewest pieces), then marketing, then products. Ask: "Where do your sales live? Shopify, WooCommerce, Stripe, HubSpot, Metorik, another tool, or a spreadsheet?" Record it, and set `sourceLabel` and `refundNote`.

Read `${CLAUDE_PLUGIN_ROOT}/frameworks/report-contract.md` now, all of it, including **Switching sources: guardrails** and **Mapping a CRM instead of a store**, and `metric-limits.md`.

**The nodes to replace, per review** (keep each name: the Compose node reads it):
- Executive: **Executive | Verify store**, **Executive | Current revenue**, **Executive | Previous revenue**, **Executive | Order types**.
- Marketing: **Marketing | Verify store**, **Marketing | Order sources**, **Marketing | All orders**.
- Products: **Products | Verify store**, **Products | Top products**.
Each becomes a fetch node (the app's n8n node where one exists, or an HTTP Request) plus a Code node with the old name that converts the response into the contract's format. **Verify store** becomes a Code node returning the Settings values unless their source has a store record to check. **Order types** returns `{ data: [] }` unless their source splits new and renewal: that section then reads as missing, not zero. Then swap each lane's demo heading for a live one, from the worked example's **Compose review** for the same lane: a live review never says DEMO. For the executive review, copy the worked example's whole **Executive | Compose review**: it prints a total the source leaves out (a CRM's refunds or items) as "not available", where the demo's prints "NaN".

**How the worked examples did it** (patterns to copy, not files to use):
- **WooCommerce** (the v1.2 example): `wc/v3/orders` with processing, completed and refunded orders, `_fields` limited to money fields, currency, line items and meta data (so no names or emails land in n8n), paginated with `page = {{ $pageCount + 1 }}` until empty, Always Output Data on; orders added up in code, other currencies converted from the order's stored base-currency amounts; sources from order attribution (`_wc_order_attribution_utm_source`, `_utm_medium`); products grouped by parent product, refunds shared by line value, names and links from the products endpoint. The login: a REST key with **Read** permission, saved as a **Custom Auth** credential with `{"headers":{"Authorization":"Basic <base64 of ck_...:cs_...>"}}`; they make the base64 value themselves with `printf 'ck_...:cs_...' | base64 | pbcopy`.
- **Metorik** (the v1.1 example): Metorik's revenue, order-source and product reports, with its own store check.
- **Anything else:** the orders, charges or deals of the reporting period from the app's n8n node or API, added up in code. For a CRM, use the contract's mapping table and tag every guess.

**One review at a time, one stage per message:** propose → login → fetch with delivery off → convert → reconcile (orders, gross, refunds, net next to their own dashboard for the same week; for marketing, the **totals** against the executive review, since attribution never matches across tools; for products, the top five against their old tool, grouped the same way).
**Prompts:** "Connect the executive review to my <store>. Read the report contract, propose the nodes, and tell me what my source can't supply." Then "I've created the login '<name>'. Attach it and fetch last week with delivery off: how many orders, and one order's fields." Then "Show me your totals next to <dashboard>, side by side. If they're more than 1% apart, find the cause before changing anything." The same for marketing and products.
**What you should see:** each review labelled as live data from their source, matching their trusted number, or an INCOMPLETE review naming the failed step. Note each result in the project file's log, without figures.
**Tell me when:** "executive reconciled", then "sources reconciled", "products reconciled". Tick each in the project file.

## Step 4: An email review (optional)

**What this step does:** adds a fifth review: sends, deliveries, opens and clicks (human only, where the platform filters bots), conversions, unsubscribes, bounces, the top sends, and email capture, this week against last. Ask: "Do you want an email review? Which email platform: Customer.io, Klaviyo, Mailchimp, HubSpot, ActiveCampaign, Brevo, another?" No: skip.

**How:** copy the **5. Email review (Customer.io)** group from the worked example into their workflow, as its own group, then switch each Customer.io node for their platform, keeping the lane's shape: reporting period → the campaigns or automations, and the one-off sends → each one's metrics for the two weeks → capture → **Compose review** → **Create Markdown BEFORE Slack**, with every fetch's error output to **Incomplete report**. Rename the nodes for their platform (for example `Klaviyo | Campaign metrics`) and update the names the Compose node reads. Keep the email section of the report contract as the output format, and the review title naming their platform.
- **Customer.io:** use the example as built: the App API (`/v1/campaigns`, each campaign's and broadcast's daily metrics with `period=days&steps=15`, the last 7 complete UTC days against the 7 before), a **Bearer Auth** credential with an App API key, `cioApiUrl` in Settings (EU workspaces use `https://api-eu.customer.io`).
- **Another platform:** its n8n node where one exists, or an HTTP Request to its reporting API, for campaign and automation stats over the two weeks. Say plainly which measures it can't give (for example bot-filtered opens) and show them as "not available", never 0.
- **Capture** is the net growth of a list or segment they choose, against the last saved week (`Customer.io | Last saved count` reads it from the run history), so it needs the run history from step 5 and the first run only takes a reading.
Then add the lane to **Collect all reports** (one more input, five in all) and wire its Markdown and Incomplete nodes to it; the week at a glance already has a line for `email`.
**Prompt:** "Add an email review from <platform>, copying the Customer.io lane's structure: sends, opens, clicks, unsubscribes and capture, this week against last. Check it against <platform>'s own report for the same week."
**What you should see:** five reviews in Collect, the email one within about 1% of the platform's report for sends and unsubscribes.
**Tell me when:** "email reconciled" or "skip".

## Step 5: Trends, run history and the AI summary (optional)

**What this step does:** adds month and quarter comparisons computed in code, saves every run, and lets the AI summary read them. Ask which they want.
- **Trends:** copy the worked example's Trends pieces (**Trends | Periods**, the 180-day orders fetch or the source's period reports, **Trends | Revenue by period**) after Collect: last 30 days against the 30 before, last 90 against the 90 before, from their sales source. Reconcile the 30-day window against their trusted tool.
- **Run history:** an n8n Data Table `reporting_agent_history` (columns run_date, period_start, period_end as string; reviews_complete, reviews_total, exec_net, exec_orders as number; facts_json as string). Create it with the n8n tools, then copy **Trends | Load history** and **History | Save this run**.
- **The AI summary on all of it:** copy **Trends | Facts for the summary** and feed its item to **Summary | AI summary** in place of the glance facts; the system message stays (numbers only from the facts, hypotheses labelled, missing stays missing, trends across runs only from three saved weeks on). An **Anthropic** credential in the workflow's project on **Summary | Claude model** (model `claude-sonnet-5-5`, maximum tokens 6000), then switch **Summary | AI summary** on. Check two of its numbers against the reviews.
**Prompt:** "Add trends and run history like the worked example, compute month and quarter in code, then point the AI summary at those facts. Create the history table first."
**Say once:** the summary is written by a model: a starting point to read with the reviews, not a replacement for them.
**Tell me when:** "extras done" or "skip".

## Step 6: The outputs, one at a time

**What this step does:** gets the reviews out of n8n. Real reviews carry revenue now, so every destination must be private before its first send. Ask about each in turn, set up the ones they want, test once, then switch it off until step 7. If they did the demo task, that delivery is already proven: reuse its credential.

**6a. Slack, or Microsoft Teams.** Ask: "Slack, Teams, or neither?"
- **Slack:** the demo's **Deliver: Slack** block is already there. If the demo task used Slack, reuse that login. Otherwise:
  - **Quick: a direct message to yourself.** A **Slack OAuth2 API** credential in the workflow's project, made with **Connect my account** (sign in to the workspace, **Allow**). Their member ID (Slack: profile picture → **Profile** → **⋮** → **Copy member ID**, starts `U`) in `slackChannel`. Set **Deliver | Slack**'s `authentication` to `oAuth2` and attach the credential by id. A DM is private by default, which suits real revenue. The messages come from n8n's Slack app.
  - **Fallback: Nick's Slack app** (also the **Slack fallback: your own app** note on the canvas), for self-hosted n8n, a workspace that blocks the sign-in, or a team channel. At https://api.slack.com/apps: **Create New App** → **From scratch**, named "Reporting Agent". **OAuth & Permissions** → **Bot Token Scopes**: `chat:write`. **Install to Workspace**, copy the **Bot User OAuth Token** (`xoxb-`). A **Slack API** credential in the workflow's project with the token in **Access Token**. Invite the app to a **private** channel and put the channel ID (from the channel's details) in `slackChannel`. Set `authentication` to `accessToken` and attach.
  - Then switch on, run, check, switch off. If Slack is blocked altogether, use email (6b).
- **Teams:** replace **Deliver | Slack** with n8n's **Microsoft Teams** node (Create message, in a channel or a chat) and a **Microsoft Teams OAuth2** credential in the workflow's project; group it as "Deliver: Teams". Teams shows `*text*` as italics, so post each report's `markdown`, check one message, and adjust the format step if tables or labels read badly. Private channel only.

**6b. Email into your OS.** Ask: "Do you want the reviews by email, so they land in this folder as files?" Copy the worked example's **Deliver: Email** group (**Email | Combine reports** and **Deliver | Email**), wired from **All reports and summary**: one email per run, every report in the body and attached, plus an exact copy of each. A **Gmail OAuth2** credential in the workflow's project, `emailTo` in Settings. Then explain the command that brings them in: **`/reporting-agent:get-email-reports`** finds the latest "Weekly reports" emails with Claude's Gmail connector, saves each exact copy into `raw/performance/reporting-agent/` (kept out of git, because real reports hold revenue), never overwrites a saved report, and reads the newest run with them: what changed, what is missing, what to check next. Without the Gmail connector, it takes the attachments from Downloads. Run it once now.

**6c. A GitHub pull request (only to a private repo).** Ask: "Is your OS folder on GitHub, and do you want each run as a pull request?" Explain first: reports committed to a repo stay in its history for good, so this is only for a **private** repo; a public one would publish their revenue permanently. Check it yourself: `gh repo view <owner>/<repo> --json visibility`. Anything but `PRIVATE`: stop, and recommend email instead. If private: copy the worked example's **Deliver: GitHub pull request** group (it creates a branch, commits the reports and opens a pull request; it never commits to the main branch), a fine-grained token at https://github.com/settings/personal-access-tokens/new with access to **only** that repo and **Contents** and **Pull requests** read and write, saved as a **GitHub API** credential in the workflow's project, and `githubOwner`, `githubRepo`, `githubFolder` (default `projects/reporting-agent/reports`) and `githubBase` (usually `main`) in Settings. Test, merge the pull request, `git pull` here, and run `/reporting-agent:get-email-reports read`.

**Prompt:** "Set up <Slack / Teams / email / GitHub> for my reviews like the worked example, test it once, then switch it off again."
**Tell me when:** "outputs set". Note each output in "My setup".

## Step 7: One live run, then a schedule

**What this step does:** the first run with real reviews delivered.
1. **Check every destination first:** Slack goes to their own DM or a channel private to people who may see revenue, the Teams channel is private to them too, `emailTo` is theirs, the GitHub repo is private.
2. Switch on the outputs they chose, run once, and check what arrived. Read it with `/reporting-agent:get-email-reports`.
3. **Switch the outputs off again** for any further test run, so tests never send real reviews. Switch them on for good only with a schedule: replace the manual trigger with a **Schedule Trigger** (for example Mondays at 8:00 in their timezone) and publish the workflow, with their yes.
**Prompt:** "Switch on my outputs, do one live run, show me what was sent, then switch them off again."
**Tell me when:** "live run done". Tick it in the project file.

## Step 8: Post your demo

Three things count: the demo running with its task done (pass), one review on their own data reconciled against a number they trust (best), or a screenshot of where their own-data run failed. **Never post real revenue:** share made-up reviews, or hide the figures in the screenshot. Tick the box in the project file and add a dated line to its log saying what works.
