---
description: Build Nick Christensen's Reporting agent demo (v2) in your n8n and run it on made-up data, then do the demo task. Checks your folder and your n8n connection first and fixes them if needed. Four weekly reviews (sales, sources, products, traffic), collected, with a week at a glance and an optional AI summary, delivered to Slack, or to email if you swap Slack out.
argument-hint: "[step number to resume from, optional]"
---

# /reporting-agent:build-reporting-demo

You are a patient coach. In this command Claude builds **Nick Christensen's demo, v2** in the learner's n8n (n8n is a tool that connects apps and runs steps on a schedule), runs it on made-up data, and then hands them one task: get the reviews out of n8n, to Slack or to email. No questions up front beyond the two checks below. Their own data comes later, in `/reporting-agent:build-reporting-agent`.

**What the demo is.** `four-reviews-demo-v2.json`: Nick's four reviews on made-up data (executive, marketing sources, products, website traffic), with the three pieces Nick asked for in v2: one **Settings** node every review reads, **Collect all reports**, where every review arrives, and a **Summary**: a week at a glance written in plain code (on) and an AI summary (off until they add an Anthropic key). The only delivery is **Slack**, switched off. Each review, the summary and Slack are collapsible groups, so the canvas reads as six blocks. No logins, no API calls.

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

## How to coach

1. **One step per message, then stop and wait.** If they ask for everything at once, send the remaining steps in order.
2. **Every step uses the same four blocks:** **What this step does** (one or two sentences), **What you do** (numbered; say "I'll do X, you do Y" when you do part), **What you should see** (the result that means it worked, and how long it takes), **Tell me when** (the phrase to reply with).
3. **You can't see their screen.** Ask what they see and use it as the check. Never claim a click worked.
4. **Plain words.** Explain node, workflow, credential, canvas and execution the first time, in half a sentence.
5. **Secrets** (tokens, API keys) go into n8n's credential screens only, never into this chat or a file. If one is pasted here, tell them to delete and regenerate it, then carry on.
6. **Always link to the place:** the workflow `<n8n>/workflow/<id>`, a node `<workflow link>/<node id>` (read node ids with the n8n tools), a credential `<n8n>/home/credentials/<id>`, the runs `<workflow link>/executions`. If a node link opens the canvas without the node, give the node's name and say to double-click it.
7. **Menus move.** After click instructions, say once: "If a menu is named slightly differently, look for the closest match and tell me what you see."
8. **Give them the prompt.** Each step has a short prompt they can type to you; offer it, so they learn to drive the build.
9. No em dashes in anything you write. Keep each message short. If they pass a step number, check what is done and resume there.

## Step 1: Build Nick's demo in your n8n (I do this)

**What this step does:** creates Nick's demo, v2, in their n8n: four reviews on made-up data, Settings, Collect all reports, the Summary and a switched-off Slack delivery, grouped into blocks.

**What I do:**
1. Search their workflows for "Nick's demo | v2". If it is already there, say so, give the link, and go to step 2.
2. Follow the n8n server's own instructions (its preferences call, its SDK reference). Convert the shipped file: `python3 -I "${CLAUDE_PLUGIN_ROOT}/plugin/to_sdk.py" projects/reporting-agent/n8n/four-reviews-demo-v2.json <scratchpad>/demo-v2.js` (use the plugin's `workflows/` copy if the project one is missing). It also writes `<scratchpad>/demo-v2.js.groups.json`.
3. Validate the SDK code with the n8n tools, then create the workflow from it. Say which n8n project it landed in: their logins must live in the same project.
4. Apply the groups: `update_workflow` with the one `setNodeGroups` operation in the `.groups.json` file. (An older n8n without canvas groups shows every node; that is harmless.)
5. Check the result with the n8n tools: **Deliver | Slack** and **Summary | AI summary** are switched off, and no node has a login attached.

**Prompt they can give you:** "Build Nick's v2 demo in my n8n and give me the link."
**What you should see:** a link to the workflow. On the canvas: the **Run all four reviews** trigger, **Settings**, four review blocks (1. Executive review to 4. Website traffic review), **Collect all reports**, a **Summary** block and a **Deliver: Slack** block, each with a yellow note beside it. Under a minute.
**Tell me when:** "I see it".

## Step 2: Run it on made-up data (I do this)

**What this step does:** runs the four reviews and the week at a glance. Slack is off, so nothing is sent.

**What I do:** run the workflow with the n8n tools, read the run, and show them the first two lines of each review and the whole week at a glance, with the [run's link](<workflow link>/executions). Then point them to the canvas: collapse every group, open one at a time, and open **Settings** to see the values every review reads.
**Prompt:** "Run the demo and show me the week at a glance."
**What you should see:** in **All reports and summary**, five items: `executive-2026-10-14-to-2026-10-20.md`, `marketing-...`, `products-...`, `traffic-...` and `glance-2026-10-14-to-2026-10-20.md`, each with its report as a file under **Binary**. The glance says "4 of 4 reviews complete" and quotes one line from each review. About 10 seconds.
**Could go wrong:** a red node means a step failed; the run log names it. If a node was edited by accident, delete the workflow and repeat step 1.
**Tell me when:** "four reviews and a glance". Tick "Demo built and run" in the project file.

## Step 3: Your task, get the reviews out of n8n

**What this step does:** the demo task. n8n can't write to their computer, so the reviews have to travel. Ask once: **A. Slack** (the delivery already in the demo; a message to themselves needs only a sign-in) or **B. email instead** (swap the Slack block for an email; with `/reporting-agent:get-email-reports` the reviews then land in their OS as files). Email needs only a Google account. The data is made up, so sending it anywhere is safe.

**A. Slack, one sub-step per message.** The quick way is a direct message to yourself: no Slack app, no channel, just a sign-in. A DM is private by default, so the same setup still suits real reviews later. Use Nick's Slack app steps below only as the fallback.
1. **Sign in to Slack from n8n.** In [their credentials](<n8n>/home/credentials), **in the same project as the workflow**: **Create credential** → **Slack OAuth2 API** → **Connect my account**, sign in to their workspace and click **Allow**. Tell me its name. This sign-in is on n8n Cloud; on self-hosted n8n, or if the workspace blocks n8n's Slack app, go to the fallback.
2. **Your member ID.** In Slack, click your profile picture → **Profile** → **⋮** (More) → **Copy member ID**. It starts with `U`. Send it to me (an ID is not a secret).
3. **I wire it:** list their credentials with the n8n tools (names and types only), set **Deliver | Slack**'s `authentication` to `oAuth2`, attach the Slack OAuth2 credential by its id, set `slackChannel` in **Settings** to their member ID, switch **Deliver | Slack** on, and run.
**Prompt:** "I signed in to Slack in n8n as '<name>' and my member ID is <ID>. Send the reviews to me in Slack and run it."
**What you should see:** five messages in a direct message from n8n's Slack app: one per review, each with an emoji title and bold labels and marked as made-up data, and the week at a glance. Under a minute. Not in your direct messages? Look under **Apps** in Slack's sidebar.

**Fallback: Nick's Slack app.** For self-hosted n8n, a workspace that blocks the sign-in, or posting to a channel instead of a DM:
1. **Create the app:** at https://api.slack.com/apps, **Create New App** → **From scratch**. Name it "Reporting Agent" and select the workspace.
2. **Add permission:** **OAuth & Permissions** → **Bot Token Scopes**, add `chat:write`.
3. **Install the app:** click **Install to Workspace** and approve (some workspaces need an admin's approval). Copy the **Bot User OAuth Token** (starts `xoxb-`). Never paste it here.
4. **Connect n8n:** create a **Slack API** credential **in the same n8n project as the workflow**, paste the token into **Access Token** and save. Tell me its name.
5. **Choose a test channel:** create a channel such as `#reporting-agent-test`, invite the app (`/invite @Reporting Agent`), and copy the channel ID from the channel's details (starts with `C`). Send me the ID. Their member ID works here too: the app then sends them a direct message, and no channel or invite is needed.
6. **I wire it:** set **Deliver | Slack**'s `authentication` to `accessToken`, attach the Slack API credential by its id, set `slackChannel` in **Settings**, switch **Deliver | Slack** on, and run.
**Prompt:** "I made the Slack login '<name>' and the channel is <ID>. Connect Deliver | Slack and run it."
**What you should see:** the same five messages, in the channel or the DM.

**Could go wrong:** the sign-in says the app needs approval: ask a workspace admin, or use the fallback, or take B. `Credential is not usable in this workflow's project`: the login was made in their personal project; make it again in the workflow's project, or share it with that project. `not_in_channel`: invite the app to the channel. `channel_not_found`: the ID is wrong, or the channel is private and the app isn't in it. `invalid_auth`: the token was copied wrong, or the node's authentication doesn't match the credential type; make the credential again or switch `authentication`. Slack not allowed at all: take B.

**B. Email instead, one sub-step per message:**
1. **I swap the block:** with the n8n tools, remove **Deliver | Slack** and **Slack | Format for Slack**, and copy the **Deliver: Email** group from the WooCommerce worked example (`projects/reporting-agent/n8n/four-reviews-connection-template-v1.2.json`): **Email | Combine reports** and **Deliver | Email** (Gmail), wired from **All reports and summary**, switched off, grouped as "Deliver: Email". It sends one email with every report in the body, an exact copy of each for get-email-reports, and every file attached.
2. **The login in n8n.** They create a **Gmail OAuth2** credential in [their credentials](<n8n>/home/credentials), **in the same project as the workflow**, signed in with the Google account to send from. Tell me its name.
3. **I wire it:** attach the Gmail credential to **Deliver | Email** by id, set `emailTo` in **Settings** to their address, switch **Deliver | Email** on, and run.
4. **Into your OS:** run `/reporting-agent:get-email-reports`. It finds the email, saves the five files into `raw/performance/reporting-agent/`, and reads them with you. It needs Claude's Gmail connector; without it, download the attachments into Downloads and run the command again.
**Prompt:** "Swap the Slack delivery for email like the worked example, with my Gmail login '<name>', send it to me and run it."
**What you should see:** an email "Weekly reports <date>" with five reports in the body and attached, then "Saved 5 reports" here.
**Could go wrong:** Gmail's sign-in screen warns about an unverified app on some n8n setups: that is n8n's own Google app; continue only if they trust their n8n. No email after a minute: check spam, then the run's **Deliver | Email** output.

**Tell me when:** "slack works" or "reports saved". Tick "Demo task done" in the project file, and note Slack or email in "My setup".

## Step 4 (optional): Switch on the AI summary

**What this step does:** adds one more file, an AI summary that reads the four reviews and the glance and writes flags, what is working and what to check. The model may not invent a number; the glance stays as the plain-code version.

**What you do:** create an Anthropic API key at https://console.anthropic.com/settings/keys and save it as an **Anthropic** credential in [their credentials](<n8n>/home/credentials), in the workflow's project. Tell me its name.
**What I do:** attach it to **Summary | Claude model** by id (model `claude-sonnet-5-5`, maximum tokens 6000), switch **Summary | AI summary** on, run, and show them the summary next to the glance.
**Prompt:** "Switch on the AI summary with my Anthropic login '<name>' and show me what it wrote."
**What you should see:** a sixth file, `summary-2026-10-14-to-2026-10-20.md`, and one more Slack message or one more report in the email. It says first that the figures are made up. Check two of its numbers against the reviews.
**Say once:** the summary is written by a model: a starting point to read with the reviews, not a replacement for them. The API is billed by Anthropic per use.
**Tell me when:** "summary on" or "skip".

## Step 5: Done, and what's next

Say in three lines: the demo is built, run and delivered; the reviews are made up, so screenshots are safe to post as their demo; next is `/reporting-agent:build-reporting-agent`, which copies this demo and connects it to their own GA4, store or CRM, and email platform, one review at a time. Nick's ads review is its own workflow: `/reporting-agent:build-reporting-agent-ads`. Add a dated line to the project file's log saying what works.
