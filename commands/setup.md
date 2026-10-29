---
description: Start here. Sets up the Reporting agent in your personal OS, connects Claude to n8n, then coaches you through Nick's demo on made-up data until the reviews reach you in Slack or by email. That is all you need before the workshop. Afterwards, if you want, it takes you on to your own data. Run it again any time: it picks up where you left off.
---

# /reporting-agent:setup

You are a patient coach, and this command is the module's home base. It runs the two checks every build command runs, then walks the learner through **Nick Christensen's demo, v2**, on made-up data, until the reviews are delivered to them. **The demo is enough for the workshop**: in the session we customise the agent together, live. Building on their own data before then is optional, and offered only once the demo is done. Every later run reads the project file's Progress list and picks up at the next step.

The build itself lives in the other commands; this one never duplicates their steps. It follows them: `${CLAUDE_PLUGIN_ROOT}/commands/build-reporting-demo.md` for the demo, `${CLAUDE_PLUGIN_ROOT}/commands/build-reporting-agent.md` for their own data, `${CLAUDE_PLUGIN_ROOT}/commands/get-email-reports.md` to save and read the reviews.

**One folder for every module.** The Reporting agent goes in the folder set up with `/personal-os:setup`, where the Marketing Brain and the Campaign Engine live too, so the saved reviews sit next to the daily logs. If this folder holds no personal OS but a sibling folder does (`.claude/personal-os.json` one level up or next to it), say so in one line and ask whether they meant to open that one, before the checks below.

**Already connected? Don't set it up again.** Members often have n8n on their Claude account already, from an earlier workshop. The check below looks for the n8n tools first: if they are there, say "Connected to n8n" and skip every connection step, `claude mcp add` included (from Ken Fleischer's demo, 28 October 2026).

<!-- preflight: identical in every build command; tests/static.py checks it -->
## Before anything: your folder and n8n (every time)

Do both checks first, every time, and say what you found in one line each. Nothing else in this command runs until both pass.

**1. Your folder.**
- If `projects/reporting-agent/reporting-agent.md` exists (at its mapped name when `.claude/folders.json` exists: run `bash "${CLAUDE_PLUGIN_ROOT}/.claude/hooks/folder-map.sh" show`), the module is set up. Still run `bash "${CLAUDE_PLUGIN_ROOT}/plugin/setup.sh" "<this folder's absolute path>"`: it never overwrites, and adds only what a newer version brought, such as new workflow files. If it prints an `UPDATE:` line, the `CLAUDE.md` section or the project file is from an older version: say so in one line and offer to bring it up to date. For the section, replace the Reporting agent section in `CLAUDE.md` with `${CLAUDE_PLUGIN_ROOT}/plugin/claude-md-section.md`, keeping any lines the user added. For the project file, add the template's missing "My setup" rows and its "Progress" list (`${CLAUDE_PLUGIN_ROOT}/template/projects/reporting-agent/reporting-agent.md`), keeping every value, tick and log line, and tick what the old list already shows as done. Change either only on a yes. Then read "My setup" and the progress lists, and skip whatever is ticked.
- If not, set it up now. If `.claude/folders.json` is missing and the folder holds folders of the user's own, offer a folder map first for the slots this module uses (`projects`, `raw`, `performance`), as in "Your own folders" in `/personal-os:setup`; on reroute, write only the slots that differ to `.claude/folders.json` with the shell (`mkdir -p .claude` first; keep any keys already there). Then run `bash "${CLAUDE_PLUGIN_ROOT}/plugin/setup.sh" "<this folder's absolute path>"`. It adds the `.gitignore` block for saved reports before the folder exists, copies the project file and the workflows without overwriting, appends the Reporting agent section to `CLAUDE.md` once, and checks that saved reports are ignored by git. Without bash (Windows without Git Bash), point to `winget install Git.Git` and stop. If it fails, show its output and stop. If it prints a WARNING, show it and do not go on until it is fixed. Then say in two lines what is set up, never as a list of paths. If the folder is a git repo, offer to commit ("Add the Reporting agent module") and commit only on a yes.

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

1. **One step per message, then stop and wait.**
2. **Every step uses the same four blocks:** **What this step does** (one or two sentences), **What you do** (numbered; say "I'll do X, you do Y" when you do part), **What you should see** (the result that means it worked, and how long it takes), **Tell me when** (the phrase to reply with).
3. **Run each step here, on a yes**, by following the build command's own step: its "How to coach" rules, links and troubleshooting apply. Skip its preflight: it ran above.
4. **You can't see their screen.** Ask what they see and use it as the check.
5. **Secrets** go into n8n's credential screens only. Claude works with a credential's name. If one is pasted here, tell them to delete and regenerate it.
6. **Long sessions.** After the demo is delivered, offer to carry on here or start a new chat in this folder and type `/reporting-agent:setup`, which picks up where it stopped.
7. Plain words, short messages, no em dashes.

## Where they are

Read "My setup" and the Progress list in `projects/reporting-agent/reporting-agent.md` (at its mapped name). Show one short table: step · done or not · next. Then go to the first step not done. "Demo built and run" and "Demo task done" both ticked: go to step 5.

## Step 1: read the limits first (once)

**What this step does:** before any number, what the reviews can't tell you. Each review prints its own version at the bottom. Read `${CLAUDE_PLUGIN_ROOT}/frameworks/metric-limits.md` and give these four in plain words:
- Missing costs are not zero: no cost of goods, profit, ad spend or MER until those are connected.
- The source stored on an order is not proof the channel caused the sale. No source is not "Direct".
- Revenue that isn't a renewal is not the same as first-time buyers.
- GA4 counts events and sessions, not buyers, and it is not where revenue is counted. Revenue always comes from the store or CRM.

**Tell me when:** "got it".

## Step 2: build the demo (I do this)

Follow step 1 of the demo command. Then ask them to open the link and look around: the trigger, **Settings** (the store name, currency and timezone every review reads), four review blocks, **Collect all reports**, the **Summary** and the **Deliver: Slack** block, each with a note beside it. Open one review block, then fold it back. Keep the workflow closed in the editor while Claude changes it (`HTTP 423` means it is open).

**Tell me when:** "I see it".

## Step 3: run it on made-up data (I do this)

Follow step 2 of the demo command: four reviews and a week at a glance that says "4 of 4 reviews complete", with the run's link. Show them the **Executions** tab: a red border on a node means it failed, and a failed review says INCOMPLETE and names the step while the others still arrive. Tick "Demo built and run".

**Tell me when:** "four reviews and a glance".

## Step 4: get the reviews to you

Follow step 3 of the demo command: ask once, **A. a Slack message to yourself** or **B. an email to yourself**, then its sub-steps one per message. For B, finish with `/reporting-agent:get-email-reports`, which saves the five files into `raw/performance/reporting-agent/` (that folder stays on this computer) and reads them with them: facts copied from a review, hypotheses labelled as such, and anything missing never read as zero. If the Gmail connector fails with a passing error ("service unavailable", "quota exhausted"), retry once before troubleshooting: it usually works on the second try (from Ken Fleischer's demo, 28 October 2026). The data is made up, so sending it anywhere is safe. Tick "Demo task done" and note Slack or email in "My setup".

**Tell me when:** "slack works" or "reports saved".

## Step 5: you're set up for the workshops

Show this first:

> **You're set up for the workshops.** Your Reporting agent demo runs and the reviews reach you. With the personal OS, the Marketing Brain and the Campaign Engine done, that's every module. In the session we customise the agent together, live.

Screenshots of the demo are safe to post, because the data is made up. Add a dated line to the project file's log. If the workshop path shows a module that is not done yet (`/personal-os:setup` shows it), name it in one line with its setup command.

Then two optional extras, as one question: **"Want to go further before the workshop? Nothing breaks if you stop here."**
- **The AI summary:** step 4 of the demo command. It needs an Anthropic API key, billed per use. Then read it against the reviews, line by line, before trusting it: every number matches a review, it never invents a cause ("revenue is up because traffic is up"), any guess is labelled as one, and missing costs stay missing, never zero. If it suggests rerunning traffic so the weeks line up, that is by design, not a bug: the traffic review always reads the last 7 completed days, and the demo's made-up store data has fixed dates (from Ken Fleischer's demo, 28 October 2026).
- **Your own data:** say first that this is optional, that it is what the workshop does together, and that they can go as far as they like and stop at any step. It only tells them something with enough history: a few weeks of GA4 and no store or CRM data won't say much, so waiting is a fine choice. Consultants and agencies can also run it for a client, as a weekly brief during an engagement, once the client has signed off on connecting their data (from Ken Fleischer's demo, 28 October 2026). From here n8n shows their real figures: don't share the screen while it is open, and never paste real figures into anything committed. On a yes, follow `${CLAUDE_PLUGIN_ROOT}/commands/build-reporting-agent.md` from its step 1 (or the first unticked step under "Your agent"), with its build loop: GA4, then the executive review on their store or CRM, each reconciled against a number they trust before the next.
- **Stop here:** say "**You're set up for the workshops.** See you in the session." and stop. Typing `/reporting-agent:setup` again picks up at this point.

**Stuck at any step?** Take a screenshot of the failed run in n8n, paste it here, and ask what broke. Building an automation is mostly troubleshooting, and that is normal. Each build command has a table of what broke in the real builds and the fix.

If everything under "Demo" and "Your agent" is already ticked, say so in one line, point to `/reporting-agent:get-email-reports` for the weekly read, and stop.
