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


COLLECT = "Collect all reports"

# Collapsible canvas groups. n8n stores them as the workflow's top-level `nodeGroups`
# (id, name, nodeNames, description). A trigger cannot be in a group. The trigger,
# Settings and Collect stay visible, so collapsed the canvas reads: trigger, Settings,
# five review blocks, Collect, Trends and AI summary, three delivery blocks.
GROUP_NS = uuid.UUID("b5f3c9a0-2c1e-4d8e-9a77-3e1f0c5a7d21")
LANE_GROUPS = [("Executive", "1. Executive review"), ("Marketing", "2. Marketing source review"),
               ("Products", "3. Top product review"), ("Traffic", "4. Website traffic review"),
               ("Customer.io", "5. Email review (Customer.io)")]
GROUP_ORDER = [g for _, g in LANE_GROUPS] + ["Trends and AI summary", "Deliver: Slack",
                                             "Deliver: GitHub pull request", "Deliver: Email"]
UNGROUPED = {"Run all four reviews", "Settings", COLLECT}
COMMON_GROUP_DESC = {
    "4. Website traffic review": "GA4 sessions, sources, landing pages and events, last 7 days vs prior 7.",
    "5. Email review (Customer.io)": "Sends, opens, clicks, conversions, unsubscribes and email capture.",
    "Trends and AI summary": "MoM and QoQ computed in code, run history, and the AI summary of all reviews.",
    "Deliver: Slack": "One formatted message per report and one for the summary.",
    "Deliver: GitHub pull request": "A branch and a pull request with every report; never commits to main.",
    "Deliver: Email": "One email with every report in the body and attached.",
}
METORIK_GROUP_DESC = {**COMMON_GROUP_DESC,
    "1. Executive review": "Sales, refunds and orders this week vs last, from Metorik.",
    "2. Marketing source review": "Orders and net sales by recorded UTM source, from Metorik.",
    "3. Top product review": "Top products and plans by net sales, from Metorik."}
FULL_GROUP_DESC = {**COMMON_GROUP_DESC,
    "1. Executive review": "Sales, refunds and orders this week vs last, from WooCommerce orders.",
    "2. Marketing source review": "Orders and net sales by recorded source (WooCommerce order attribution).",
    "3. Top product review": "Net sales by product from order line items, with status and links."}


def group_of(name):
    for lane, g in LANE_GROUPS:
        if name.startswith(lane + " | "):
            return g
    if name.startswith(("Trends | ", "AI | ")) or name in ("History | Save this run", "All reports and summary"):
        return "Trends and AI summary"
    if name in ("Slack | Format for Slack", "Deliver | Slack"):
        return "Deliver: Slack"
    if name.startswith("GitHub | "):
        return "Deliver: GitHub pull request"
    if name in ("Email | Combine reports", "Deliver | Email"):
        return "Deliver: Email"
    return None


def add_groups(wf, template, desc):
    members = {}
    for n in wf["nodes"]:
        if n["type"] == "n8n-nodes-base.stickyNote" or n["name"] in UNGROUPED:
            continue
        assert n["type"] != "n8n-nodes-base.manualTrigger", "a trigger cannot be in a group"
        g = group_of(n["name"])
        assert g, "node without a group: " + n["name"]
        members.setdefault(g, []).append(n["name"])
    wf["nodeGroups"] = [{"id": str(uuid.uuid5(GROUP_NS, template + "/" + g)), "name": g, "nodeNames": members[g],
                         "description": desc[g]} for g in GROUP_ORDER if g in members]


METORIK_TRENDS = [("last30", "last 30 days"), ("prev30", "prior 30 days"), ("last90", "last 90 days"), ("prev90", "prior 90 days")]
METORIK_TRENDS_CODE = """// Last 30 vs prior 30 and last 90 vs prior 90 days, from the totals of four Metorik revenue reports, computed in code.
// A switched-off or failed request has no totals, so trends report themselves unavailable, never zero.
const p=$('Trends | Periods').first().json;
const names=""" + json.dumps({k: f"Trends | Metorik revenue ({label})" for k, label in METORIK_TRENDS}) + """;
const read=n=>{try{const j=$(n).first().json;return j&&j.totals&&Number.isFinite(Number(j.totals.net))?j.totals:null;}catch(e){return null;}};
const windows={},missing=[];
for(const [k,n] of Object.entries(names)){const t=read(n);if(!t){missing.push(n);continue;}windows[k]={...p.windows[k],orders:Number(t.orders),gross:Math.round(Number(t.gross)),net:Math.round(Number(t.net))};}
if(missing.length)return [{json:{available:false,reason:'no Metorik totals from '+missing.join(', ')+' (switched off, or the request failed)'}}];
const pct=(a,b)=>b?Math.round((a-b)/b*1000)/10:null;
return [{json:{available:true,source:'Metorik revenue report',truncated:false,windows,
  mom:{net_pct:pct(windows.last30.net,windows.prev30.net),orders_pct:pct(windows.last30.orders,windows.prev30.orders)},
  qoq:{net_pct:pct(windows.last90.net,windows.prev90.net),orders_pct:pct(windows.last90.orders,windows.prev90.orders)}}}];"""
METORIK_TRENDS_NOTE = """## Trends and AI summary
**Trends:** last 30 against the prior 30 days and last 90 against the prior 90, computed in code from the totals of four Metorik revenue reports. Switch the four Metorik trend requests on with your Metorik login.

**History:** every run is saved to the n8n Data Table `reporting_agent_history`. Create it first, with columns run_date, period_start, period_end (string), reviews_complete, reviews_total, exec_net, exec_orders (number) and facts_json (string).

**AI summary:** switched off until you add an Anthropic credential to AI | Claude model. It only explains numbers the workflow computed, labels hypotheses, and keeps missing data missing. Its file goes out with the reports."""
EXTRA_NODES = ["Trends | Periods", "Trends | Load history", "Trends | Facts for the summary", "AI | Weekly summary",
               "AI | Claude model", "AI | Summary report", "History | Save this run", "All reports and summary"]


def add_metorik_extras(wf, full):
    """Customer.io lane, Trends on Metorik, history, AI summary: copied from the built full template,
    so both templates share one version of that code."""
    nodes = {n["name"]: n for n in wf["nodes"]}
    conns = wf["connections"]
    fconns = full["connections"]
    for n in full["nodes"]:
        name = n["name"]
        if name.startswith("Customer.io ") or name in EXTRA_NODES:
            c = copy.deepcopy(n)
            c["id"] = nid()
            wf["nodes"].append(c)
            nodes[name] = c
            if name in fconns and n["type"] != "n8n-nodes-base.stickyNote":
                conns[name] = copy.deepcopy(fconns[name])
    conns["Settings"]["main"][0].append({"node": "Customer.io | Reporting period", "type": "main", "index": 0})
    conns["Collect all four reports"] = {"main": [[{"node": "Trends | Periods", "type": "main", "index": 0}]]}
    nodes["Collect all four reports"]["parameters"]["numberInputs"] = 5

    # Trends on Metorik: four revenue reports read only through .totals, the shape the executive review relies on
    src = nodes["Executive | Current revenue"]
    prev = "Trends | Periods"
    for key, label in METORIK_TRENDS:
        t = copy.deepcopy(src)
        name = f"Trends | Metorik revenue ({label})"
        t.update({"id": nid(), "name": name, "disabled": True, "onError": "continueRegularOutput", "alwaysOutputData": True,
                  "notes": f"Read-only. Metorik revenue totals for the {label}.", "notesInFlow": True})
        win = "$('Trends | Periods').first().json.windows." + key
        t["parameters"]["queryParameters"]["parameters"] = [
            {"name": "start_date", "value": "={{ " + win + ".start }}"},
            {"name": "end_date", "value": "={{ " + win + ".end }}"},
            {"name": "group_by", "value": "day"}]
        wf["nodes"].append(t)
        nodes[name] = t
        conns[prev] = {"main": [[{"node": name, "type": "main", "index": 0}]]}
        prev = name
    wf["nodes"].append({"parameters": {"jsCode": METORIK_TRENDS_CODE}, "id": nid(), "name": "Trends | Revenue by period",
                        "type": "n8n-nodes-base.code", "typeVersion": 2, "position": [0, 0], "onError": "continueRegularOutput"})
    nodes["Trends | Revenue by period"] = wf["nodes"][-1]
    conns[prev] = {"main": [[{"node": "Trends | Revenue by period", "type": "main", "index": 0}]]}
    conns["Trends | Revenue by period"] = {"main": [[{"node": "Trends | Load history", "type": "main", "index": 0}]]}
    wf["nodes"].append({"parameters": {"content": METORIK_TRENDS_NOTE, "width": 400, "height": 260, "color": 6}, "id": nid(),
                        "name": "Trends and summary explainer", "type": "n8n-nodes-base.stickyNote", "typeVersion": 1, "position": [0, 0]})
    nodes["Trends and summary explainer"] = wf["nodes"][-1]

    # Deliveries go out from All reports and summary; the summary is not counted as a review
    nodes["GitHub | Reports to commit"]["parameters"]["jsCode"] = "return $('All reports and summary').all();"
    nodes["Email | Combine reports"]["parameters"]["jsCode"] = count_reviews(EMAIL_COMBINE)
    nodes["GitHub | Plan PR"]["parameters"]["jsCode"] = count_reviews(PR_PLAN)
    nodes["Delivery explainer"]["parameters"]["content"] = full_delivery_note()
    nodes["Deliver | Email"]["notes"] = "One email with all the reports and the summary. Set emailTo in Settings, select a Gmail credential, then switch on."
    nodes["Deliver | Slack"]["notes"] = "One message per report and one for the summary. Setup: see the Slack setup note. Select your credential and Channel By ID, then switch on."


EMAIL_NOTE = """## 5. Email review (Customer.io)
**For:** emails sent and delivered, human opens and clicks, conversions, unsubscribes, bounces and the top sends, this week against last, plus email capture.
**Connection pattern:** Customer.io App API (running automations, broadcasts and their daily metrics; one segment count for capture) → review → Markdown file → collected with the other reports → delivery.
**Setup:** a Bearer Auth credential with an App API key on the five request nodes; set cioCaptureSegmentId and cioCaptureLabel in Settings. Days are UTC; counts are messages, not people."""

# Hesh's note placement from the grouped live workflow: each lane explainer sits to the left
# of its lane group, about 190 px above the lane's first row; delivery notes top right, above
# the delivery groups. Lanes start at x 704 and sit 480 apart. Notes never overlap a grouped node.
LANE_NOTES = {"Executive": ("Executive explainer", 760, 230, 3), "Marketing": ("Marketing explainer", 760, 230, 4),
              "Products": ("Products explainer", 760, 230, 5), "Traffic": ("Website traffic explainer", 758, 224, 5),
              "Customer.io": ("Email review explainer", 758, 240, 7)}
DROPPED_NOTES = {"Slack frame", "Email frame", "GitHub frame", "Start here", "Customer.io explainer"}


def group_layout(wf, chains, trends_row):
    wf["nodes"] = [n for n in wf["nodes"] if n["name"] not in DROPPED_NOTES]
    wf["nodes"].append({"parameters": {"content": EMAIL_NOTE, "width": 758, "height": 240, "color": 7}, "id": nid(),
                        "name": "Email review explainer", "type": "n8n-nodes-base.stickyNote", "typeVersion": 1, "position": [0, 0]})
    nodes = {n["name"]: n for n in wf["nodes"]}
    placed = set()

    def put(name, x, y):
        nodes[name]["position"] = [x, y]
        placed.add(name)

    x0, step, y0, gap = 704, 224, 304, 480
    for i, (lane, chain) in enumerate(chains.items()):
        y = y0 + i * gap
        for k, short in enumerate(chain):
            put(f"{lane} | {short}", x0 + k * step, y)
        put(f"{lane} | Incomplete report", x0 + chain.index("Compose review") * step, y + 192)
        note, w, h, color = LANE_NOTES[lane]
        nodes[note]["position"] = [x0 - 848, y - 192]
        nodes[note]["parameters"].update({"width": w, "height": h, "color": color})
    put("Run all four reviews", -64, 920)
    put("Settings", 160, 920)
    nodes["How to demonstrate"]["position"] = [-816, -128]
    nodes["How to demonstrate"]["parameters"].update({"width": 480, "height": 400, "color": 2})
    right = x0 + max(len(c) for c in chains.values()) * step + 256
    collect = next(n for n in nodes if n.startswith("Collect all"))
    put(collect, right, y0 + 2 * gap)
    dx = right + 224
    put("Slack | Format for Slack", dx, 304)
    put("Deliver | Slack", dx + 224, 304)
    put("Email | Combine reports", dx, 560)
    put("Deliver | Email", dx + 224, 560)
    for k, name in enumerate(["GitHub | Plan PR", "GitHub | Get base branch", "GitHub | Create branch",
                              "GitHub | Reports to commit", "GitHub | Commit to branch", "GitHub | Open pull request"]):
        put(name, dx + 224 * k, 816)
    nodes["Delivery explainer"]["position"] = [dx - 64, -400]
    nodes["Delivery explainer"]["parameters"].update({"width": 520, "height": 430, "color": 6})
    nodes["Slack app setup guide"]["position"] = [dx + 480, -400]
    nodes["Slack app setup guide"]["parameters"].update({"width": 550, "height": 420, "color": 4})
    ty = y0 + 2 * gap
    for k, name in enumerate(trends_row):
        put(name, dx + k * step, ty)
    put("AI | Claude model", dx + trends_row.index("AI | Weekly summary") * step, ty + 224)
    t = nodes["Trends and summary explainer"]
    t["position"] = [dx - 64, ty - 300]
    t["parameters"].update({"width": len(trends_row) * step + 64, "height": 230, "color": 6})
    missing = [n["name"] for n in wf["nodes"] if n["type"] != "n8n-nodes-base.stickyNote" and n["name"] not in placed]
    assert not missing, "nodes without a place in the layout: " + ", ".join(missing)



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
  sourceLabel:'Metorik',             // where the store figures come from, printed in the summary facts
  refundNote:'Net revenue uses refund-date reporting: a refund counts in the week it happens, even on an older order.', // how your source dates refunds
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


def build(fn, demo, full):
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
            if lane == "Executive":  # the totals travel with the report, for the history and the summary
                s = rep(s, "period:p}}];", "period:p,totals:c,previousTotals:b}}];")
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
    add_metorik_extras(wf, full)
    txt = json.dumps(wf, ensure_ascii=False)
    wf = json.loads(rep(txt, "Collect all four reports", COLLECT, txt.count("Collect all four reports")))
    group_layout(wf, METORIK_CHAINS, METORIK_TRENDS_ROW)
    add_groups(wf, "metorik", METORIK_GROUP_DESC)
    wf["name"] = wf["name"] + " | v1.1"
    out = f"{OUT}/four-reviews-metorik-template-v1.1.json"
    json.dump(wf, open(out, "w"), indent=2, ensure_ascii=False)
    print("wrote", out, len(wf["nodes"]), "nodes")


# ---------------------------------------------------------------------------
# Full template (v1.2): the workflow tested live on a WooCommerce store, Customer.io
# and GA4 on 23 October 2026, exported with credentials, ids and store details
# removed (tests/fixtures/full-template-source.json), plus the plugin edits below.

FULL_SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fixtures", "full-template-source.json")

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

    # Layout and collapsible groups (shared with the Metorik template)
    nodes["AI | Claude model"]["parameters"]["options"]["maxTokensToSample"] = 6000
    group_layout(wf, LANE_CHAINS, TRENDS_CHAIN)
    add_groups(wf, "full", FULL_GROUP_DESC)

    wf["name"] = "Workshop | Weekly business reviews | full template | v1.2"
    out = f"{OUT}/four-reviews-connection-template-v1.2.json"
    json.dump(wf, open(out, "w"), indent=2, ensure_ascii=False)
    print("wrote", out, len(wf["nodes"]), "nodes")
    return wf


METORIK_CHAINS = {
    "Executive": ["Reporting period", "Verify store", "Check store identity", "Current revenue", "Previous revenue",
                  "Order types", "Compose review", "Create Markdown BEFORE Slack"],
    "Marketing": ["Reporting period", "Verify store", "Check store identity", "Order sources", "All orders",
                  "Compose review", "Create Markdown BEFORE Slack"],
    "Products": ["Reporting period", "Verify store", "Check store identity", "Top products", "Compose review",
                 "Create Markdown BEFORE Slack"],
    "Traffic": ["Reporting period", "Build GA4 request", "Connect GA4 - enable after setup", "Compose review",
                "Create Markdown BEFORE Slack"],
    "Customer.io": LANE_CHAINS["Customer.io"],
}
METORIK_TRENDS_ROW = ["Trends | Periods"] + [f"Trends | Metorik revenue ({label})" for _, label in METORIK_TRENDS] + \
    ["Trends | Revenue by period", "Trends | Load history", "Trends | Facts for the summary", "AI | Weekly summary",
     "AI | Summary report", "History | Save this run", "All reports and summary"]

full_wf = build_full()
build("four-reviews-connection-template.json", False, full_wf)
