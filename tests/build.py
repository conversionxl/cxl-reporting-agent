"""Build both connection templates.

Usage: python3 -I build.py <src_dir> <out_dir>
build(): the v1.1 edits on Nick's connection template export, written as
four-reviews-metorik-template-v1.1.json (Metorik and GA4).
build_full(): the full template, four-reviews-connection-template-v1.2.json, from the
sanitized export of the workflow tested live on 23 October 2026
(tests/fixtures/full-template-source.json), plus the plugin edits.
The demo ships as Nick's v1.0 export, unchanged (workflows/four-reviews-demo-v1.0.json):
Settings, Collect and delivery belong to the templates only. The demo
branches in build() are kept so the template's edits stay in one place.
Every string replacement asserts the exact number of matches, so a changed
source fails loudly instead of producing a half-edited workflow.
"""
import json, sys, uuid, copy, os

SRC, OUT = sys.argv[1], sys.argv[2]
LANES = ["Executive", "Marketing", "Products"]
SLACK_FORMAT = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "js", "slack-format.js")).read()


def rep(s, old, new, count=1):
    n = s.count(old)
    assert n == count, f"expected {count} of {old!r}, found {n}"
    return s.replace(old, new)


def nid():
    return str(uuid.uuid4())


GH = "{{ $('GitHub | Plan PR').first().json"
PR_PLAN = """const s=$('Settings').first().json,items=$input.all();
const runDate=$now.setZone(s.timeZone).toISODate();
const done=items.filter(i=>!i.json.incomplete).length;
const branch='reports/'+runDate+'-run-'+$execution.id;
const files=items.map(i=>'- '+s.githubFolder+'/'+i.json.fileName+(i.json.incomplete?' (INCOMPLETE)':'')).join('\\n');
return [{json:{owner:s.githubOwner,repo:s.githubRepo,base:s.githubBase,branch,
 title:'Weekly reports '+runDate+(done<items.length?' (incomplete)':''),
 body:'Weekly reports from the n8n reporting workflow, run '+runDate+'. '+done+' of '+items.length+' reviews complete.\\n\\n'+files+'\\n\\nMerge this pull request to add the reports. Nothing was committed to '+s.githubBase+'.'}}];"""


def gh_http(name, method, path, body, pos, notes, execute_once=False, stop_on_error=False):
    p = {"method": method, "url": "=https://api.github.com/repos/" + GH + ".owner }}/" + GH + ".repo }}" + path,
         "authentication": "predefinedCredentialType", "nodeCredentialType": "githubApi",
         "sendHeaders": True, "headerParameters": {"parameters": [{"name": "Accept", "value": "application/vnd.github+json"}]},
         "options": {}}
    if body:
        p.update({"sendBody": True, "specifyBody": "json", "jsonBody": body})
    n = {"parameters": p, "id": nid(), "name": name, "type": "n8n-nodes-base.httpRequest", "typeVersion": 4.2,
         "position": pos, "disabled": True, "onError": "continueErrorOutput" if stop_on_error else "continueRegularOutput",
         "notes": notes, "notesInFlow": True}
    if execute_once:
        n["executeOnce"] = True
    return n


def add_github_pr_chain(wf, conns):
    """Branch + commits + pull request. Never writes to the base branch."""
    y = 700
    chain = [
        {"parameters": {"jsCode": PR_PLAN}, "id": nid(), "name": "GitHub | Plan PR", "type": "n8n-nodes-base.code",
         "typeVersion": 2, "position": [2280, y]},
        gh_http("GitHub | Get base branch", "GET", "/git/ref/heads/" + GH + ".base }}", None, [2500, y],
                "Reads the latest commit on the base branch, so the new branch starts from it.", stop_on_error=True),
        gh_http("GitHub | Create branch", "POST", "/git/refs",
                "={{ JSON.stringify({ref:'refs/heads/'+$('GitHub | Plan PR').first().json.branch, sha:$json.object.sha}) }}",
                [2720, y], "Creates a new branch for this run, for example reports/2026-10-22-run-123.", stop_on_error=True),
        {"parameters": {"jsCode": "return $('Collect all four reports').all();"}, "id": nid(),
         "name": "GitHub | Reports to commit", "type": "n8n-nodes-base.code", "typeVersion": 2, "position": [2940, y]},
        {"parameters": {
            "resource": "file", "operation": "create",
            "owner": {"__rl": True, "mode": "name", "value": "={{ $('Settings').first().json.githubOwner }}"},
            "repository": {"__rl": True, "mode": "name", "value": "={{ $('Settings').first().json.githubRepo }}"},
            "filePath": "={{ $('Settings').first().json.githubFolder }}/{{ $json.fileName }}",
            "binaryData": True, "binaryPropertyName": "report",
            "commitMessage": "=Add report {{ $json.fileName }}",
            "additionalParameters": {"branch": {"branch": "=" + GH + ".branch }}"}}},
         "id": nid(), "name": "GitHub | Commit to branch", "type": "n8n-nodes-base.github", "typeVersion": 1.1,
         "position": [3160, y], "disabled": True, "onError": "continueRegularOutput",
         "notes": "Commits each report to the new branch only.", "notesInFlow": True},
        gh_http("GitHub | Open pull request", "POST", "/pulls",
                "={{ JSON.stringify({title:$('GitHub | Plan PR').first().json.title, head:$('GitHub | Plan PR').first().json.branch, base:$('GitHub | Plan PR').first().json.base, body:$('GitHub | Plan PR').first().json.body}) }}",
                [3380, y], "Opens the pull request. You review and merge it.", execute_once=True),
    ]
    wf["nodes"].extend(chain)
    for a, b in zip(chain, chain[1:]):
        conns[a["name"]] = {"main": [[{"node": b["name"], "type": "main", "index": 0}]]}


def relayout(wf):
    """Frame each review lane and each delivery branch, so the canvas reads in blocks.

    Lanes move 640 px apart (they were 480) to leave room for a frame each. The
    lane explainer notes become those frames: same text, sized to sit behind the
    whole lane. Notes always render behind nodes in n8n.
    """
    nodes = {n["name"]: n for n in wf["nodes"]}
    lanes = ["Executive", "Marketing", "Products", "Traffic"]
    explainer = {"Executive": "Executive explainer", "Marketing": "Marketing explainer",
                 "Products": "Products explainer", "Traffic": "Website traffic explainer"}
    for i, lane in enumerate(lanes):
        shift = i * 160
        for n in wf["nodes"]:
            if n["name"].startswith(lane + " | "):
                n["position"] = [n["position"][0], n["position"][1] + shift]
        base = i * 640
        frame = nodes[explainer[lane]]
        frame["position"] = [-60, base - 300]
        frame["parameters"]["width"] = 1720
        frame["parameters"]["height"] = 620
    mid = 960
    nodes["Run all four reviews"]["position"] = [-460, mid]
    nodes["Settings"]["position"] = [-240, mid]
    nodes["Collect all four reports"]["position"] = [1900, mid]
    # Delivery: purple explainer and the Slack setup note side by side at the top,
    # then one frame per branch below them.
    nodes["Delivery explainer"]["position"] = [2160, -680]
    nodes["Delivery explainer"]["parameters"].update({"width": 760, "height": 600})
    nodes["Slack app setup guide"]["position"] = [2960, -680]
    nodes["Slack app setup guide"]["parameters"].update({"width": 640, "height": 600})
    nodes["How to demonstrate"]["parameters"].update({"height": 460})
    nodes["Slack | Format for Slack"]["position"] = [2280, 360]
    nodes["Deliver | Slack"]["position"] = [2520, 360]
    nodes["Email | Combine reports"]["position"] = [2280, 760]
    nodes["Deliver | Email"]["position"] = [2520, 760]
    for k, name in enumerate(["GitHub | Plan PR", "GitHub | Get base branch", "GitHub | Create branch",
                              "GitHub | Reports to commit", "GitHub | Commit to branch", "GitHub | Open pull request"]):
        nodes[name]["position"] = [2280 + 240 * k, 1160]
    frames = [
        ("Slack frame", "## Slack\nOne message per review. Optional, on top of email or GitHub.", [2160, 200], 600, 320),
        ("Email frame", "## Email\nOne email per run: readable reviews, exact copies for `/get-email-reports`, and the four files attached.", [2160, 600], 600, 320),
        ("GitHub frame", "## GitHub pull request\nNew branch each run, four commits, one pull request. Never commits to your main branch: you merge.", [2160, 1000], 1600, 320),
    ]
    frames.append(("Start here", "## Start here\n1. Edit **Settings**.\n2. Click **Execute workflow**.", [-560, 760], 500, 340))
    for name, text, pos, w, h in frames:
        wf["nodes"].append({"parameters": {"content": text, "width": w, "height": h, "color": 6}, "id": nid(),
                            "name": name, "type": "n8n-nodes-base.stickyNote", "typeVersion": 1, "position": pos})


def settings_code(demo):
    store = "Demo Store" if demo else "YOUR_STORE_NAME"
    return f"""// Edit these before the first run. Every lane reads its settings from here.
return [{{json:{{
  storeName:'{store}',          // must match the store name your source returns
  currency:'USD',                    // ISO code, for example EUR or GBP
  timeZone:'America/Chicago',        // reporting timezone, for example Europe/London
  locale:'en-US',                    // number and money format, for example en-GB or de-DE
  ga4PropertyId:'YOUR_GA4_PROPERTY_ID', // numeric GA4 property ID (Traffic lane)
  ga4Events:['purchase','generate_lead'], // events your GA4 property collects
  emailTo:'YOU@EXAMPLE.COM',         // Email delivery: where the reports go
  githubOwner:'YOUR_GITHUB_USERNAME',// GitHub delivery: owner of your personal OS repo
  githubRepo:'YOUR_PERSONAL_OS_REPO',// GitHub delivery: that repo's name
  githubFolder:'projects/reporting-agent/reports', // folder in the repo, no slash at either end
  githubBase:'main',                 // the PR targets this branch; nothing is committed to it
  n8nUrl:'https://YOUR-INSTANCE.app.n8n.cloud' // your n8n address, for the workflow links in email and Slack
}}}}];"""


# Reasons that mean "this source is not connected yet", as opposed to a real failure.
SETUP_REASONS = "/switched off|configure the connection first|did not load: no response|got undefined/"


def incomplete_code(lane, traffic=False, email=False):
    period = f"$('{lane} | Reporting period').first().json"
    if traffic:
        head = (f"const c={period};const p={{start:c.current.start,end:c.current.end}};"
                "const s=$('Settings').first().json;")
        title, slug, meta = "Website traffic review", "traffic", "'GA4 | '+c.timeZone"
    elif email:
        head = f"const p={period};const s=$('Settings').first().json;"
        title, slug, meta = "Email review (Customer.io)", "email", "'Customer.io'"
    else:
        head = f"const p={period};"
        title = {"Executive": "Executive business review", "Marketing": "Marketing source review",
                 "Products": "Top product review"}[lane]
        slug, meta = lane.lower(), "p.currency+' | '+p.timeZone"
    store = "s.storeName" if (traffic or email) else "p.storeName"
    return (head +
            "const j=$input.first().json,e=j.error??j;"
            "const reason=String(typeof e==='string'?e:(e.message||e.description||JSON.stringify(e))).replace(/[\\r\\n]+/g,' ').slice(0,300);"
            f"const setup={SETUP_REASONS}.test(reason);"
            f"const markdown=['INCOMPLETE | '+{store}+' | {title}',p.start+' to '+p.end+' | '+{meta},'',"
            "'This review did not run, so it reports no figures this week. Missing figures are not zero.',"
            "'Failed step: '+$prevNode.name,'Reason: '+reason,'',"
            "...(setup?['First run before setup? The source nodes stay switched off until you connect them, so this is expected.']:[]),"
            "'Review: fix the connection or setting named above, then run the workflow again.'].join('\\n')+'\\n';"
            f"return [{{json:{{markdown,slackText:markdown,fileName:'{slug}-'+p.start+'-to-'+p.end+'-incomplete.md',incomplete:true}}}}];")


EMAIL_COMBINE = """const items=$input.all(),s=$('Settings').first().json;
const runDate=$now.setZone(s.timeZone).toISODate();
const done=items.filter(i=>!i.json.incomplete).length;
const base=String(s.n8nUrl||'').replace(/\\/+$/,''),linked=/^https?:\\/\\//.test(base)&&!base.includes('YOUR-INSTANCE'),wfUrl=linked?base+'/workflow/'+$workflow.id:'';
const body=['Weekly reports, run '+runDate+'. '+done+' of '+items.length+' reviews complete.',...(linked?['Workflow: '+wfUrl,'This run: '+wfUrl+'/executions/'+$execution.id]:[]),'',
 ...items.map(i=>'-----BEGIN REPORT '+i.json.fileName+'-----\\n'+i.json.markdown+'-----END REPORT-----\\n')].join('\\n');
const exact=items.map(i=>'-----BEGIN FILE '+i.json.fileName+'-----\\n'+Buffer.from(i.json.markdown,'utf8').toString('base64').match(/.{1,76}/g).join('\\n')+'\\n-----END FILE-----').join('\\n');
const binary={};items.forEach((i,k)=>{if(i.binary?.report)binary['report_'+k]=i.binary.report;});
return [{json:{subject:'Weekly reports '+runDate+(done<items.length?' (incomplete)':''),body:body+'\\n\\nExact copies for /get-email-reports (base64, do not edit):\\n'+exact+'\\n',attachmentNames:Object.keys(binary).join(',')},binary}];"""

DELIVERY_NOTE = """## Delivery: choose one or more
All four reports are collected first, then sent to every delivery node you switch on. Leave the others off, or delete them.

- **Slack:** one formatted message per report (emoji title, bold labels, tables as bullet lines). See the Slack setup note.
- **GitHub:** opens a pull request to your personal OS repo with the four reports as dated .md files (Settings: githubOwner, githubRepo, githubFolder, githubBase). It creates a new branch each run and never commits to your main branch: you merge the PR. Use a private repo, because reports hold revenue. Needs a GitHub API credential with Contents and Pull requests set to read and write, on the four GitHub nodes.
- **Email:** one email with all four reports in the body and attached (Settings: emailTo).

Set `n8nUrl` in Settings to your n8n address and both email and Slack link back to this workflow and the run.

Incomplete reports are delivered too, so a failed source shows up instead of going quiet."""


def build(fn, demo):
    wf = json.load(open(f"{SRC}/{fn}"))
    nodes = {n["name"]: n for n in wf["nodes"]}
    conns = wf["connections"]

    def code(name):
        return nodes[name]["parameters"]["jsCode"]

    def set_code(name, value):
        nodes[name]["parameters"]["jsCode"] = value

    def note(name, old, new, count=1):
        p = nodes[name]["parameters"]
        p["content"] = rep(p["content"], old, new, count)

    # 1. Settings node between the trigger and the four lanes
    nodes["Run all four reviews"]["position"] = [-460, 480]
    wf["nodes"].append({"parameters": {"jsCode": settings_code(demo)}, "id": nid(), "name": "Settings",
                        "type": "n8n-nodes-base.code", "typeVersion": 2, "position": [-240, 480],
                        "notes": "Edit before the first run: store, currency, timezone, GA4 and delivery settings.",
                        "notesInFlow": True})
    conns["Settings"] = conns.pop("Run all four reviews")
    conns["Run all four reviews"] = {"main": [[{"node": "Settings", "type": "main", "index": 0}]]}

    for lane in LANES:
        rp = f"{lane} | Reporting period"
        s = code(rp)
        if demo:
            s = rep(s, '"currency": "USD"}}];',
                    '"currency": s.currency, "timeZone": s.timeZone, "locale": s.locale, "storeName": s.storeName}}];')
            set_code(rp, "const s=$('Settings').first().json;" + s)
        else:
            s = rep(s, "$now.setZone('America/Chicago')", "$now.setZone(s.timeZone)")
            s = rep(s, "currency:'USD'}}];", "currency:s.currency,timeZone:s.timeZone,locale:s.locale,storeName:s.storeName}}];")
            set_code(rp, "const s=$('Settings').first().json;" + s)

        chk = f"{lane} | Check store identity"
        expected = "'Demo Store'" if demo else "'YOUR_STORE_NAME'"
        s = code(chk)
        s = rep(s, "const s=$input.first().json;", f"const s=$input.first().json,p=$('{rp}').first().json;")
        s = rep(s, f"if(s.name!=={expected}||s.currency!=='USD'||s.timezone!=='America/Chicago')throw Error('Wrong store/currency/timezone');",
                "if(s.name!==p.storeName||s.currency!==p.currency||s.timezone!==p.timeZone)throw Error('Wrong store/currency/timezone: expected '+p.storeName+', '+p.currency+', '+p.timeZone+'; got '+s.name+', '+s.currency+', '+s.timezone);")
        set_code(chk, s)

        if demo:  # the demo store fixture follows Settings, so the demo runs in any currency
            vs = f"{lane} | Verify store"
            set_code(vs, rep(code(vs), 'return [{json:{"name": "Demo Store", "currency": "USD", "timezone": "America/Chicago"}}];',
                             f"const p=$('{rp}').first().json;return [{{json:{{name:p.storeName,currency:p.currency,timezone:p.timeZone}}}}];"))

        cmp_ = f"{lane} | Compose review"
        s = code(cmp_)
        s = rep(s, "new Intl.NumberFormat('en-US',{style:'currency',currency:'USD',", "new Intl.NumberFormat(p.locale,{style:'currency',currency:p.currency,")
        s = rep(s, "' | USD | America/Chicago'", "' | '+p.currency+' | '+p.timeZone")
        if not demo:
            s = rep(s, "'PRIVATE LIVE REVIEW | Your Store — ", "'PRIVATE LIVE REVIEW | '+p.storeName+' — ")
        set_code(cmp_, s)

        note(f"{lane} explainer", " • America/Chicago • USD", " • timezone and currency from Settings")
        note(f"{lane} explainer", "→ Markdown → optional Slack", "→ Markdown → collected with the other reports → delivery")

    # Traffic lane
    s = code("Traffic | Reporting period")
    s = rep(s, "const timeZone='America/Chicago';", "const s=$('Settings').first().json,timeZone=s.timeZone;")
    s = rep(s, "propertyId:'YOUR_GA4_PROPERTY_ID'", "propertyId:s.ga4PropertyId")
    s = rep(s, "events:['purchase','generate_lead']", "events:s.ga4Events")
    set_code("Traffic | Reporting period", s)
    s = code("Traffic | Compose review")
    s = rep(s, "Metorik remains the revenue source.", "Your store or CRM remains the revenue source.")
    s = rep(s, "fileName:'website-traffic-review.md'", "fileName:'traffic-'+c.current.start+'-to-'+c.current.end+'.md'")
    set_code("Traffic | Compose review", s)
    note("Website traffic explainer", "→ optional Slack (disabled)", "→ collected with the other reports → delivery (switched off)")
    note("Website traffic explainer", "property ID in the connection template. Revenue stays in Metorik.",
         "property ID in Settings (connection template). Revenue stays in your store or CRM.")

    # 2. Incomplete reports: source and check failures go to an error output instead of stopping the run
    traffic_source = "Traffic | Synthetic GA4 response" if demo else "Traffic | Connect GA4 - enable after setup"
    guarded = {
        "Executive": ["Executive | Verify store", "Executive | Check store identity", "Executive | Current revenue",
                      "Executive | Previous revenue", "Executive | Order types", "Executive | Compose review"],
        "Marketing": ["Marketing | Verify store", "Marketing | Check store identity", "Marketing | Order sources",
                      "Marketing | All orders", "Marketing | Compose review"],
        "Products": ["Products | Verify store", "Products | Check store identity", "Products | Top products",
                     "Products | Compose review"],
        "Traffic": [traffic_source, "Traffic | Compose review"],
    }
    for lane, names in guarded.items():
        inc = f"{lane} | Incomplete report"
        cx, cy = nodes[f"{lane} | Compose review"]["position"]
        wf["nodes"].append({"parameters": {"jsCode": incomplete_code(lane, lane == "Traffic")}, "id": nid(), "name": inc,
                            "type": "n8n-nodes-base.code", "typeVersion": 2, "position": [cx, cy + 200],
                            "notes": "Runs only when a step in this lane fails. Writes an INCOMPLETE report so the other reviews still go out.",
                            "notesInFlow": True})
        for name in names:
            nodes[name]["onError"] = "continueErrorOutput"
            main = conns[name]["main"]
            assert len(main) == 1, name
            main.append([{"node": inc, "type": "main", "index": 0}])
        conns[inc] = {"main": [[{"node": f"{lane} | Create Markdown BEFORE Slack", "type": "main", "index": 0}]]}

    # 3. Collect all four reports, then one branch per delivery destination
    slack_template = None
    for i, lane in enumerate(LANES + ["Traffic"]):
        slack = nodes.pop(f"{lane} | Optional Slack delivery")
        wf["nodes"].remove(slack)
        slack_template = slack_template or slack
        conns[f"{lane} | Create Markdown BEFORE Slack"] = {
            "main": [[{"node": "Collect all four reports", "type": "main", "index": i}]]}
    wf["nodes"].append({"parameters": {"numberInputs": 4}, "id": nid(), "name": "Collect all four reports",
                        "type": "n8n-nodes-base.merge", "typeVersion": 3.2, "position": [2000, 700]})
    slack = copy.deepcopy(slack_template)
    slack.update({"id": nid(), "name": "Deliver | Slack", "position": [2280, 460],
                  "notes": "One message per report. Setup: see the Slack setup note. Select your credential and Channel By ID, then switch on."})
    slack["parameters"]["otherOptions"]["includeLinkToWorkflow"] = False
    wf["nodes"].append(slack)
    wf["nodes"].append({"parameters": {"jsCode": SLACK_FORMAT}, "id": nid(), "name": "Slack | Format for Slack",
                        "type": "n8n-nodes-base.code", "typeVersion": 2, "position": [2280, 460],
                        "notes": "Rewrites each review for Slack: emoji title, bold labels, tables as bullet lines.",
                        "notesInFlow": True})
    conns["Slack | Format for Slack"] = {"main": [[{"node": "Deliver | Slack", "type": "main", "index": 0}]]}
    add_github_pr_chain(wf, conns)
    wf["nodes"].append({"parameters": {"jsCode": EMAIL_COMBINE}, "id": nid(), "name": "Email | Combine reports",
                        "type": "n8n-nodes-base.code", "typeVersion": 2, "position": [2280, 940]})
    wf["nodes"].append({"parameters": {
        "resource": "message", "operation": "send",
        "sendTo": "={{ $('Settings').first().json.emailTo }}",
        "subject": "={{ $json.subject }}", "emailType": "text", "message": "={{ $json.body }}",
        "options": {"appendAttribution": False,
                    "attachmentsUi": {"attachmentsBinary": [{"property": "={{ $json.attachmentNames }}"}]}}},
        "id": nid(), "name": "Deliver | Email", "type": "n8n-nodes-base.gmail", "typeVersion": 2.2,
        "position": [2500, 940], "disabled": True,
        "notes": "One email with all four reports. Set emailTo in Settings, select a Gmail credential, then switch on.",
        "notesInFlow": True})
    conns["Collect all four reports"] = {"main": [[
        {"node": "Slack | Format for Slack", "type": "main", "index": 0},
        {"node": "GitHub | Plan PR", "type": "main", "index": 0},
        {"node": "Email | Combine reports", "type": "main", "index": 0}]]}
    conns["Email | Combine reports"] = {"main": [[{"node": "Deliver | Email", "type": "main", "index": 0}]]}
    wf["nodes"].append({"parameters": {"content": DELIVERY_NOTE, "height": 430, "width": 520, "color": 6},
                        "id": nid(), "name": "Delivery explainer", "type": "n8n-nodes-base.stickyNote",
                        "typeVersion": 1, "position": [2240, -20]})

    note("Slack app setup guide", "4. Select credential + channel By ID on each Slack node.\n5. Review Markdown, enable one Slack node, test, then enable all four.",
         "4. Select credential + channel By ID on the Deliver | Slack node.\n5. Review the Markdown, then switch on Deliver | Slack. It posts one formatted message per report.")
    if demo:
        note("How to demonstrate", "Slack is disabled and has no destination or credential.",
             "All four reports are then collected. The delivery nodes (Slack, GitHub, Email) are switched off and have no destination or credential.")
    else:
        note("How to demonstrate", "All HTTP and Slack nodes are disabled; credentials removed. Configure credentials, store identity and report settings before enabling HTTP nodes.",
             "All HTTP and delivery nodes are disabled; credentials removed. Fill in the Settings node and credentials before enabling HTTP nodes. Until a source is connected, its lane writes an INCOMPLETE report instead of stopping the run.")
        note("How to demonstrate", "Enable Slack only after choosing your own test destination and reviewing the report.",
             "Switch on a delivery node only after choosing your own destination and reviewing the reports.")

    relayout(wf)
    wf["name"] = wf["name"] + " | v1.1"
    out = f"{OUT}/four-reviews-metorik-template-v1.1.json"
    json.dump(wf, open(out, "w"), indent=2, ensure_ascii=False)
    print("wrote", out, len(wf["nodes"]), "nodes")


# ---------------------------------------------------------------------------
# Full template (v1.2): the workflow tested live on a WooCommerce store, Customer.io
# and GA4 on 23 October 2026, exported with credentials, ids and store details
# removed (tests/fixtures/full-template-source.json), plus the plugin edits below.

FULL_SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fixtures", "full-template-source.json")
COLLECT = "Collect all reports"

FULL_SETTINGS = """// Edit these before the first run. Every lane reads its settings from here.
return [{json:{
  storeName:'YOUR_STORE_NAME',       // printed on the reports
  storeUrl:'https://YOUR-STORE.com', // your WooCommerce site, no slash at the end
  currency:'USD',                    // ISO code, for example EUR or GBP
  timeZone:'America/Chicago',        // reporting timezone, for example Europe/London
  locale:'en-US',                    // number and money format, for example en-GB or de-DE
  sourceLabel:'WooCommerce orders',  // where the store figures come from, printed on the reports
  refundNote:'Refunds count against the order they belong to, so a refund on an older order is not in this week.', // how your source dates refunds
  ga4PropertyId:'YOUR_GA4_PROPERTY_ID', // numeric GA4 property ID (Traffic lane)
  ga4Events:['purchase','generate_lead'], // events your GA4 property collects
  cioApiUrl:'https://api.customer.io', // Customer.io App API; EU workspaces use https://api-eu.customer.io
  cioCaptureSegmentId:'',            // Customer.io segment whose growth counts as email capture; empty = not set up
  cioCaptureLabel:'',                // that segment's name, printed on the email review
  emailTo:'YOU@EXAMPLE.COM',         // Email delivery: where the reports go
  githubOwner:'YOUR_GITHUB_USERNAME',// GitHub delivery: owner of your personal OS repo
  githubRepo:'YOUR_PERSONAL_OS_REPO',// GitHub delivery: that repo's name
  githubFolder:'projects/reporting-agent/reports', // folder in the repo, no slash at either end
  githubBase:'main',                 // the PR targets this branch; nothing is committed to it
  n8nUrl:'https://YOUR-INSTANCE.app.n8n.cloud' // your n8n address, for the workflow links in email and Slack
}}];"""

# A switched-off request node passes its input through, so the next step sees something that is not orders.
WOO_OFF = ("if({src}.some(i=>i.json&&Object.keys(i.json).length&&i.json.id===undefined&&!i.json.error))"
           "throw Error('No order data: the WooCommerce request node is switched off, or returned something that is not orders. Connect your store and switch it on.');\n")

LANE_CHAINS = {
    "Executive": ["Reporting period", "Verify store", "Check store identity", "WooCommerce orders (current)", "Current revenue",
                  "WooCommerce orders (previous)", "Previous revenue", "Order types", "Compose review", "Create Markdown BEFORE Slack"],
    "Marketing": ["Reporting period", "Verify store", "Check store identity", "WooCommerce orders (current)", "Order sources",
                  "All orders", "Compose review", "Create Markdown BEFORE Slack"],
    "Products": ["Reporting period", "Verify store", "Check store identity", "WooCommerce orders (current)", "Sales by product",
                 "WooCommerce product details", "Top products", "Compose review", "Create Markdown BEFORE Slack"],
    "Traffic": ["Reporting period", "Build GA4 request", "Connect GA4 - enable after setup", "Compose review", "Create Markdown BEFORE Slack"],
    "Customer.io": ["Reporting period", "Campaigns", "Running campaigns", "Campaign metrics", "Broadcasts", "Sent broadcasts",
                    "Broadcast metrics", "Capture count", "Last saved count", "Compose review", "Create Markdown BEFORE Slack"],
}
TRENDS_CHAIN = ["Trends | Periods", "Trends | WooCommerce orders (180 days)", "Trends | Revenue by period", "Trends | Load history",
                "Trends | Facts for the summary", "AI | Weekly summary", "AI | Summary report", "History | Save this run",
                "All reports and summary"]
SOURCES_OFF = ["Executive | WooCommerce orders (current)", "Executive | WooCommerce orders (previous)",
               "Marketing | WooCommerce orders (current)", "Products | WooCommerce orders (current)",
               "Products | WooCommerce product details", "Trends | WooCommerce orders (180 days)",
               "Traffic | Connect GA4 - enable after setup", "Customer.io | Campaigns", "Customer.io | Campaign metrics",
               "Customer.io | Broadcasts", "Customer.io | Broadcast metrics", "Customer.io | Capture count", "AI | Weekly summary"]

FULL_NOTES = {
    "Executive explainer": """## 1. Business performance
**For:** net and gross sales, refunds, orders and items, against the week before.

**Source:** WooCommerce orders (`wc/v3/orders`: processing, completed and refunded), summed in code. Orders in another currency use the order's stored base-currency amounts. Switch on the two WooCommerce nodes once your store login exists.

Last 7 completed days • timezone and currency from Settings""",
    "Marketing explainer": """## 2. Where sales come from
**For:** net sales and orders by the source recorded on each order, and how many orders have none.

**Source:** WooCommerce order attribution (`_wc_order_attribution_utm_source` and `_utm_medium`). Orders without a recorded source are counted as not represented, never as Direct. Store attribution, not GA4 channels or ad ROAS.

Last 7 completed days • timezone and currency from Settings""",
    "Products explainer": """## 3. What is selling
**For:** the top products by net sales (tax excluded, refunds shared by line value), with orders, units, status and link.

**Source:** line items on WooCommerce orders, grouped by parent product, plus `wc/v3/products` for names, status and links. Published status does not prove checkout works.

Last 7 completed days • timezone and currency from Settings""",
    "Website traffic explainer": """## 4. Website traffic (GA4)
**For:** sessions, engagement, sources, landing pages and your key events. Last 7 completed days against the 7 before.

**Source:** GA4 Data API (`batchRunReports`). Easiest login: a Google Service Account credential with the scope `https://www.googleapis.com/auth/analytics.readonly`, its email added as a Viewer on the property. A Search Console login does not include Analytics. Set `ga4PropertyId` in Settings, then switch on the GA4 node.""",
}
EXTRA_NOTES = [
    ("Customer.io explainer", """## 5. Email (Customer.io)
**For:** emails sent and delivered, human opens and clicks, conversions, unsubscribes, bounces, the top sends, and email capture.

**Source:** Customer.io App API (`cioApiUrl` in Settings). Create a Bearer Auth credential with an App API key, select it on the five Customer.io request nodes, switch them on. Metrics are daily in UTC: the last 7 complete days against the 7 before. Email capture is the growth of the segment you set in `cioCaptureSegmentId`, against the last saved week.""", 5),
    ("Trends and summary explainer", """## Trends and AI summary
**Trends:** last 30 against the prior 30 days and last 90 against the prior 90, computed in code from WooCommerce orders.

**History:** every run is saved to the n8n Data Table `reporting_agent_history`. Create it first, with columns run_date, period_start, period_end (string), reviews_complete, reviews_total, exec_net, exec_orders (number) and facts_json (string).

**AI summary:** switched off until you add an Anthropic credential to AI | Claude model. It only explains numbers the workflow computed, labels hypotheses, and keeps missing data missing. Its file goes out with the reports.""", 6),
]
FULL_DEMO_NOTE = """## PRIVATE CONNECTION TEMPLATE
Every source, the AI summary and every delivery are switched off, and there are no credentials. Fill in **Settings**, create your logins, then switch on one lane at a time. Until a source is connected, its lane writes an INCOMPLETE report instead of stopping the run.

Real requests put real data in the execution history. Do not run this on a shared screen; use the demo for the workshop.

Switch on a delivery node only after choosing your own destination and reviewing the reports."""
SLACK_NOTE = """## Slack setup, before delivery
1. Create and install a Slack app with the bot scope `chat:write`.
2. Save its token as an n8n Slack credential.
3. Invite the bot to a private test channel. Live reports hold revenue.
4. Select the credential and the channel By ID on Deliver | Slack.
5. Review the reports, then switch on Deliver | Slack. It posts one formatted message per report and one for the summary.

App installation may need workspace approval."""


def full_delivery_note():
    s = DELIVERY_NOTE
    s = rep(s, "All four reports are collected first", "All the reports and the AI summary are collected first")
    s = rep(s, "with the four reports as dated .md files", "with the reports as dated .md files")
    s = rep(s, "one email with all four reports in the body", "one email with all the reports in the body")
    return s


def count_reviews(js):
    """Email and the pull request count the reviews, not the summary file."""
    js = rep(js, "const done=items.filter(i=>!i.json.incomplete).length;",
             "const reviews=items.filter(i=>!String(i.json.fileName).startsWith('summary-')),done=reviews.filter(i=>!i.json.incomplete).length;")
    js = rep(js, "done<items.length", "done<reviews.length")
    js = rep(js, "done+' of '+items.length+' reviews complete.", "done+' of '+reviews.length+' reviews complete.")
    return js


def build_full():
    wf = json.load(open(FULL_SRC))
    txt = json.dumps(wf, ensure_ascii=False)
    txt = rep(txt, "Collect all four reports", COLLECT, txt.count("Collect all four reports"))
    wf = json.loads(txt)
    nodes = {n["name"]: n for n in wf["nodes"]}
    conns = wf["connections"]
    code = lambda name: nodes[name]["parameters"]["jsCode"]

    def set_code(name, value):
        nodes[name]["parameters"]["jsCode"] = value

    # Settings: store address, Customer.io region, n8n address
    set_code("Settings", FULL_SETTINGS)

    # Request addresses come from Settings
    for n in wf["nodes"]:
        p = n.get("parameters", {})
        url = p.get("url")
        if isinstance(url, str) and url.startswith("https://YOUR-STORE.com"):
            p["url"] = "={{ $('Settings').first().json.storeUrl }}" + url[len("https://YOUR-STORE.com"):]
        elif isinstance(url, str) and "https://api.customer.io" in url:
            p["url"] = "={{ $('Settings').first().json.cioApiUrl }}" + url.lstrip("=")[len("https://api.customer.io"):]

    # Source nodes and the AI summary ship switched off; a switched-off source must never read as zero
    for name in SOURCES_OFF:
        nodes[name]["disabled"] = True
    for name in ["Executive | Current revenue", "Executive | Previous revenue"]:
        js = rep(code(name), "(wc/v3/orders, processing and completed)", "(wc/v3/orders: processing, completed and refunded)")
        set_code(name, rep(js, "const orders=$input.all()", WOO_OFF.format(src="$input.all()") + "const orders=$input.all()"))
    set_code("Marketing | Order sources", rep(code("Marketing | Order sources"), "const orders=$('Marketing | WooCommerce orders (current)')",
             WOO_OFF.format(src="$('Marketing | WooCommerce orders (current)').all()") + "const orders=$('Marketing | WooCommerce orders (current)')"))
    set_code("Products | Sales by product", rep(code("Products | Sales by product"), "const orders=$input.all()",
             WOO_OFF.format(src="$input.all()") + "const orders=$input.all()"))
    set_code("Trends | Revenue by period", rep(code("Trends | Revenue by period"), "const num=v=>Number(v)||0;",
             "if(raw.some(o=>o&&Object.keys(o).length&&o.id===undefined))return [{json:{available:false,reason:'the WooCommerce request node is switched off, or returned something that is not orders'}}];\nconst num=v=>Number(v)||0;"))

    # History: no "}}" inside an expression, which would end it early
    hv = nodes["History | Save this run"]["parameters"]["columns"]["value"]
    hv["facts_json"] = rep(hv["facts_json"], "|| {json:{}}).json", "|| { json: {} }).json")

    # AI summary: no em dash in code, clearer reason when the model is off
    js = code("AI | Summary report")
    js = rep(js, "// Wraps the AI text as a fifth report file,", "// Wraps the AI text as one more report file,")
    js = rep(js, "replace(/\\s*—\\s*/g,', ')", "replace(/\\s*\\u2014\\s*/g,', ')")
    js = rep(js, "The four reports are unaffected.", "The reviews are unaffected.")
    js = rep(js, "String(j.error?.message||j.error||'no output')", "String(j.error?.message||j.error||'the AI node is switched off or returned nothing')")
    set_code("AI | Summary report", js)

    # INCOMPLETE reports: the setup hint only when a source is not connected yet
    for lane in ["Executive", "Marketing", "Products"]:
        set_code(f"{lane} | Incomplete report", incomplete_code(lane))
    set_code("Traffic | Incomplete report", incomplete_code("Traffic", traffic=True))
    set_code("Customer.io | Incomplete report", incomplete_code("Customer.io", email=True))

    # Delivery: the 0.2.0 Slack formatting and workflow links, reviews counted without the summary
    nodes["Deliver | Slack"]["notes"] = "One message per report and one for the summary. Setup: see the Slack setup note. Select your credential and Channel By ID, then switch on."
    wf["nodes"].append({"parameters": {"jsCode": SLACK_FORMAT}, "id": nid(), "name": "Slack | Format for Slack",
                        "type": "n8n-nodes-base.code", "typeVersion": 2, "position": [0, 0],
                        "notes": "Rewrites each review for Slack: emoji title, bold labels, tables as bullet lines.",
                        "notesInFlow": True})
    nodes["Slack | Format for Slack"] = wf["nodes"][-1]
    conns["All reports and summary"]["main"][0] = [
        {"node": "Slack | Format for Slack", "type": "main", "index": 0},
        {"node": "GitHub | Plan PR", "type": "main", "index": 0},
        {"node": "Email | Combine reports", "type": "main", "index": 0}]
    conns["Slack | Format for Slack"] = {"main": [[{"node": "Deliver | Slack", "type": "main", "index": 0}]]}
    set_code("Email | Combine reports", count_reviews(EMAIL_COMBINE))
    set_code("GitHub | Plan PR", count_reviews(code("GitHub | Plan PR")))
    for name in ["Deliver | Slack", "Deliver | Email", "GitHub | Get base branch", "GitHub | Create branch",
                 "GitHub | Commit to branch", "GitHub | Open pull request"]:
        nodes[name]["disabled"] = True
    nodes["Deliver | Email"]["notes"] = "One email with all the reports and the summary. Set emailTo in Settings, select a Gmail credential, then switch on."

    # Notes
    for name, text in FULL_NOTES.items():
        nodes[name]["parameters"]["content"] = text
    nodes["How to demonstrate"]["parameters"]["content"] = FULL_DEMO_NOTE
    nodes["Slack app setup guide"]["parameters"]["content"] = SLACK_NOTE
    nodes["Delivery explainer"]["parameters"]["content"] = full_delivery_note()
    for name, text, color in EXTRA_NOTES:
        wf["nodes"].append({"parameters": {"content": text, "width": 400, "height": 300, "color": color}, "id": nid(),
                            "name": name, "type": "n8n-nodes-base.stickyNote", "typeVersion": 1, "position": [0, 0]})
        nodes[name] = wf["nodes"][-1]

    # Layout: one framed row per lane, the trends and summary row after Collect, delivery frames on the right
    explainer = {"Executive": "Executive explainer", "Marketing": "Marketing explainer", "Products": "Products explainer",
                 "Traffic": "Website traffic explainer", "Customer.io": "Customer.io explainer"}
    step, gap = 220, 640
    for i, (lane, chain) in enumerate(LANE_CHAINS.items()):
        y = i * gap
        for k, short in enumerate(chain):
            nodes[f"{lane} | {short}"]["position"] = [k * step, y]
        cx = chain.index("Compose review") * step
        nodes[f"{lane} | Incomplete report"]["position"] = [cx, y + 200]
        frame = nodes[explainer[lane]]
        frame["position"] = [-60, y - 300]
        frame["parameters"].update({"width": len(chain) * step + 100, "height": 620})
    mid = 2 * gap
    nodes["Run all four reviews"]["position"] = [-460, mid]
    nodes["Settings"]["position"] = [-240, mid]
    nodes[COLLECT]["position"] = [2700, mid]
    tx = 2960
    for k, name in enumerate(TRENDS_CHAIN):
        nodes[name]["position"] = [tx + k * step, mid]
    nodes["AI | Claude model"]["position"] = [tx + TRENDS_CHAIN.index("AI | Weekly summary") * step, mid + 220]
    t = nodes["Trends and summary explainer"]
    t["position"] = [tx - 60, mid - 340]
    t["parameters"].update({"width": len(TRENDS_CHAIN) * step + 100, "height": 700})
    dx = tx + len(TRENDS_CHAIN) * step + 200
    nodes["Delivery explainer"]["position"] = [dx - 120, -680]
    nodes["Delivery explainer"]["parameters"].update({"width": 760, "height": 600})
    nodes["Slack app setup guide"]["position"] = [dx + 680, -680]
    nodes["Slack app setup guide"]["parameters"].update({"width": 640, "height": 600})
    nodes["How to demonstrate"]["position"] = [-560, -300]
    nodes["How to demonstrate"]["parameters"].update({"width": 460, "height": 520})
    nodes["Slack | Format for Slack"]["position"] = [dx, 360]
    nodes["Deliver | Slack"]["position"] = [dx + 240, 360]
    nodes["Email | Combine reports"]["position"] = [dx, 760]
    nodes["Deliver | Email"]["position"] = [dx + 240, 760]
    for k, name in enumerate(["GitHub | Plan PR", "GitHub | Get base branch", "GitHub | Create branch",
                              "GitHub | Reports to commit", "GitHub | Commit to branch", "GitHub | Open pull request"]):
        nodes[name]["position"] = [dx + 240 * k, 1160]
    frames = [
        ("Slack frame", "## Slack\nOne formatted message per report and one for the summary. Optional, on top of email or GitHub.", [dx - 120, 200], 600, 320),
        ("Email frame", "## Email\nOne email per run: readable reports, exact copies for `/get-email-reports`, and every file attached.", [dx - 120, 600], 600, 320),
        ("GitHub frame", "## GitHub pull request\nNew branch each run, one commit per file, one pull request. Never commits to your main branch: you merge. Use a private repo.", [dx - 120, 1000], 1600, 320),
        ("Start here", "## Start here\n1. Edit **Settings**.\n2. Click **Execute workflow**: every lane writes an INCOMPLETE report until you connect it.\n3. Connect one lane at a time.", [-560, mid - 200], 500, 400),
    ]
    for name, text, pos, w, h in frames:
        wf["nodes"].append({"parameters": {"content": text, "width": w, "height": h, "color": 6}, "id": nid(),
                            "name": name, "type": "n8n-nodes-base.stickyNote", "typeVersion": 1, "position": pos})

    wf["name"] = "Workshop | Weekly business reviews | full template | v1.2"
    out = f"{OUT}/four-reviews-connection-template-v1.2.json"
    json.dump(wf, open(out, "w"), indent=2, ensure_ascii=False)
    print("wrote", out, len(wf["nodes"]), "nodes")



build("four-reviews-connection-template.json", False)
build_full()
