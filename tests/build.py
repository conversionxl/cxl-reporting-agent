"""Build every shipped workflow.

Usage: python3 -I build.py <src_dir> <out_dir>
build_demo_v2(): Nick's v2 demo, four-reviews-demo-v2.json, from Nick's v1.0 demo export
(tests/fixtures/nick-v1.0): Settings, the four lanes on made-up data, Collect, the
summaries (week at a glance in code; the AI summary shipped off) and Slack only.
build(): the Metorik worked example, four-reviews-metorik-template-v1.1.json, from
Nick's connection template export.
build_full(): the WooCommerce worked example, four-reviews-connection-template-v1.2.json,
from the sanitized export of the workflow tested live on 23 October 2026
(tests/fixtures/full-template-source.json), plus the plugin edits.
build_ads(): the ads review, ads-review-from-nick-v1.json, its own workflow, from Nick
Christensen's MIT ads starter (tests/fixtures/nick-ads-starter).
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
GROUP_ORDER = [g for _, g in LANE_GROUPS] + ["Summary", "Trends and AI summary", "Ads review", "Deliver: Slack",
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
    if name.startswith("Summary | "):
        return "Summary"
    if name.startswith("Ads | "):
        return "Ads review"
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


def add_groups(wf, template, desc, override=None):
    members = {}
    for n in wf["nodes"]:
        if n["type"] == "n8n-nodes-base.stickyNote" or n["name"] in UNGROUPED or n["type"].endswith("Trigger"):
            continue  # a trigger cannot be in a group
        g = (override or {}).get(n["name"]) or group_of(n["name"])
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


# ---------------------------------------------------------------------------
# The ads review, its own workflow: Nick Christensen's ads reporting starter from his CXL
# workshop "Ship ICP-driven ad campaigns and automated monitoring" (29 June 2026), MIT
# licensed, https://github.com/nickyc1/ship-icp-ads-automate-monitoring (n8n-ads-reporting/).
# His schedule trigger, sample-data nodes, merge and Analyze code are carried unchanged
# (the code under a credit header). His Slack webhook and email nodes are replaced by the
# same Slack and Gmail delivery the other workflows use, both switched off.

ADS_SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fixtures", "nick-ads-starter", "starter-workflow.json")
ADS_CREDIT = ("// From Nick Christensen's ads reporting starter (MIT), workshop \"Ship ICP-driven ad campaigns and automated monitoring\".\n"
              "// Source: https://github.com/nickyc1/ship-icp-ads-automate-monitoring (n8n-ads-reporting/starter-workflow.json).\n"
              "// Carried unchanged below this header.\n")
ADS_FROM = {"Mock Google Ads": "Ads | Google Ads (sample data)", "Mock Meta Ads": "Ads | Meta Ads (sample data)",
            "Merge": "Ads | Merge", "Analyze": "Ads | Analyze"}
ADS_TRIGGER = "Daily 9am"
ADS_RUN_NOW = "Run now"
ADS_SETTINGS = """// Edit these before the first run. Every step reads its settings from here.
return [{json:{
  storeName:'YOUR_BUSINESS',         // printed on the review
  currency:'USD',                    // ISO code, for example EUR or GBP
  timeZone:'America/Chicago',        // reporting timezone, for example Europe/London
  locale:'en-US',                    // number and money format, for example en-GB or de-DE
  slackChannel:'SELECT_YOUR_TEST_CHANNEL', // Slack delivery: the channel ID (right-click the channel, Copy link: the part after /archives/)
  emailTo:'YOU@EXAMPLE.COM',         // Email delivery: where the review goes
  n8nUrl:'https://YOUR-INSTANCE.app.n8n.cloud' // your n8n address, for the workflow links in email and Slack
}}];"""
ADS_PERIOD = """// Yesterday, in the Settings timezone: Nick's digest is a daily read.
const s=$('Settings').first().json;
const d=$now.setZone(s.timeZone).startOf('day').minus({days:1}).toISODate();
return [{json:{start:d,end:d}}];"""
ADS_COMPOSE = """// Wraps the ads digest from Ads | Analyze (Nick Christensen's grading) into the report contract.
const p=$('Ads | Reporting period').first().json, s=$('Settings').first().json;
// A sample node that ran means sample rows reached the grading; once both are replaced (renamed), this is false.
const isSample=n=>{try{const j=$(n).first().json;return !!(j&&j.campaign!==undefined&&j.platform!==undefined);}catch(e){return false;}};
const sample=isSample('Ads | Google Ads (sample data)')||isSample('Ads | Meta Ads (sample data)');
const a=$('Ads | Analyze').first().json;
if(!a||typeof a.digest!=='string'||!a.campaign_count)throw Error('No ad data: Ads | Analyze returned no campaigns. Connect your ad platforms, or keep the two sample nodes switched on.');
if(/NaN|undefined/.test(a.digest))throw Error('Ad rows are missing fields: each row needs campaign, platform, spend, conversions, conversion_value, cpa and historical_cpa.');
const lines=[(sample?'SAMPLE DATA':'PRIVATE LIVE REVIEW')+' | '+s.storeName+' | Ads review (Google Ads and Meta)',p.start+' to '+p.end+' | '+s.currency,
  sample?'Sample data: the example campaigns from Nick Christensen\\'s ads workshop, not your ad accounts. Replace the two sample nodes with your Google Ads and Meta data (same fields) to make this review live.':'Live data from your ad platforms.',
  '',a.digest,'',
  'Campaigns graded: '+a.campaign_count+'; flagged: '+a.flagged+'.',
  'Grades use value-to-spend against the targets at the top of Ads | Analyze. Platform-reported conversion value is not profit: set the targets from your margins.',
  'Review: check the flagged campaigns in the ad platform before changing any budget.'];
const markdown=lines.join('\\n')+'\\n';
return [{json:{markdown,slackText:markdown,fileName:'ads-'+p.start+'-to-'+p.end+'.md',period:p,sample}}];"""
ADS_INCOMPLETE = ("const p=$('Ads | Reporting period').first().json,s=$('Settings').first().json;"
    "const j=$input.first().json,e=j.error??j;"
    "const reason=String(typeof e==='string'?e:(e.message||e.description||JSON.stringify(e))).replace(/[\\r\\n]+/g,' ').slice(0,300);"
    "const markdown=['INCOMPLETE | '+s.storeName+' | Ads review (Google Ads and Meta)',p.start+' to '+p.end+' | '+s.currency,'',"
    "'This review did not run, so it reports no figures this week. Missing figures are not zero.',"
    "'Failed step: '+$prevNode.name,'Reason: '+reason,'',"
    "'Review: fix the connection or setting named above, then run the workflow again.'].join('\\n')+'\\n';"
    "return [{json:{markdown,slackText:markdown,fileName:'ads-'+p.start+'-to-'+p.end+'-incomplete.md',incomplete:true}}];")
ADS_NOTE = """## Ads review (Nick Christensen's starter)
**For:** every Google Ads and Meta campaign graded on value-to-spend, flagged when below target or when CPA runs above 2x its usual level, with a plain call: scale, hold, or investigate. A daily read of yesterday.

**Source:** Nick Christensen's ads reporting starter (MIT), from his workshop "Ship ICP-driven ad campaigns and automated monitoring". It ships with his sample campaigns, labelled SAMPLE DATA, so it runs with nothing connected.

**Make it live:** replace the two sample nodes with your own rows in the same fields: campaign, platform, spend, conversions, conversion_value, cpa, historical_cpa, ctr, clicks, impressions. Then set the targets at the top of Ads | Analyze."""
ADS_CONNECT_NOTE = """## Connect your ad platforms
**Meta:** a Facebook Graph API credential (access token with `ads_read`) on the insights edge of `act_<your ad account id>`, level campaign: one request for yesterday, one for the last 30 days (for historical CPA). Pick the conversion `action_type` your funnel uses (purchase, lead, complete_registration).

**Google Ads:** the Google Ads node, or an HTTP Request to the Google Ads API. Both need a Google Ads developer token as well as the Google login.

**Any other channel:** fetch its campaign report and map each row to the same fields in a Code node.

**Name the replacement nodes** `Ads | Google Ads` and `Ads | Meta Ads` (no "sample data") and wire them into Ads | Merge where the sample nodes were. The SAMPLE DATA label goes away once no sample node runs."""
ADS_SLACK_NOTE = """## Slack setup
1. Create and install a Slack app with the bot scope `chat:write`.
2. Save its token as an n8n Slack credential.
3. Invite the bot to a test channel and put its channel ID in Settings.
4. Select the credential on Deliver | Slack and switch it on. It posts one formatted message.

Prefer email? Switch on Deliver | Email instead, with a Gmail credential and `emailTo` in Settings."""


def build_ads():
    """Nick's ads starter as its own workflow: Settings, his chain, the report contract, Slack and email (both off)."""
    starter = json.load(open(ADS_SRC))
    by = {n["name"]: n for n in starter["nodes"]}
    nodes, conns = {}, {}
    wf = {"name": "Workshop | Ads review from Nick Christensen's starter | v1", "nodes": [], "connections": conns,
          "settings": {"executionOrder": "v1"}}

    def add(node):
        node.setdefault("id", nid())
        node.setdefault("position", [0, 0])
        wf["nodes"].append(node)
        nodes[node["name"]] = node
        return node

    t = copy.deepcopy(by[ADS_TRIGGER])
    t.pop("id", None)
    add(t)
    # A manual trigger beside Nick's schedule, so the n8n MCP can run it on demand; both start the same chain
    add({"parameters": {}, "name": ADS_RUN_NOW, "type": "n8n-nodes-base.manualTrigger", "typeVersion": 1})
    add({"parameters": {"jsCode": ADS_SETTINGS}, "name": "Settings", "type": "n8n-nodes-base.code", "typeVersion": 2,
         "notes": "Edit before the first run: business name, currency, timezone and delivery.", "notesInFlow": True})
    add({"parameters": {"jsCode": ADS_PERIOD}, "name": "Ads | Reporting period", "type": "n8n-nodes-base.code", "typeVersion": 2})
    for old, new in ADS_FROM.items():
        n = copy.deepcopy(by[old])
        n.pop("id", None)
        n.update({"name": new, "position": [0, 0]})
        if "jsCode" in n["parameters"]:
            n["parameters"]["jsCode"] = ADS_CREDIT + n["parameters"]["jsCode"]
        add(n)
    nodes["Ads | Analyze"]["onError"] = "continueErrorOutput"
    add({"parameters": {"jsCode": ADS_COMPOSE}, "name": "Ads | Compose review", "type": "n8n-nodes-base.code", "typeVersion": 2,
         "onError": "continueErrorOutput"})
    add({"parameters": {"jsCode": ADS_INCOMPLETE}, "name": "Ads | Incomplete report", "type": "n8n-nodes-base.code", "typeVersion": 2,
         "notes": "Runs only when a step fails. Writes an INCOMPLETE review instead of stopping the run.", "notesInFlow": True})
    add({"parameters": {"jsCode": MARKDOWN_CODE}, "name": "Ads | Create Markdown BEFORE Slack", "type": "n8n-nodes-base.code", "typeVersion": 2})
    add({"parameters": {"jsCode": SLACK_FORMAT}, "name": "Slack | Format for Slack", "type": "n8n-nodes-base.code", "typeVersion": 2,
         "notes": "Rewrites the review for Slack: emoji title, bold labels.", "notesInFlow": True})
    add(slack_node("One formatted message with the review. Select your Slack credential, set slackChannel in Settings, then switch on."))
    add({"parameters": {"jsCode": EMAIL_COMBINE}, "name": "Email | Combine reports", "type": "n8n-nodes-base.code", "typeVersion": 2})
    add(gmail_node("One email with the review in the body and attached. Set emailTo in Settings, select a Gmail credential, then switch on."))
    m = lambda target, index=0: {"node": target, "type": "main", "index": index}
    conns[ADS_TRIGGER] = {"main": [[m("Settings")]]}
    conns[ADS_RUN_NOW] = {"main": [[m("Settings")]]}
    conns["Settings"] = {"main": [[m("Ads | Reporting period")]]}
    conns["Ads | Reporting period"] = {"main": [[m("Ads | Google Ads (sample data)"), m("Ads | Meta Ads (sample data)")]]}
    conns["Ads | Google Ads (sample data)"] = {"main": [[m("Ads | Merge", 0)]]}
    conns["Ads | Meta Ads (sample data)"] = {"main": [[m("Ads | Merge", 1)]]}
    conns["Ads | Merge"] = {"main": [[m("Ads | Analyze")]]}
    conns["Ads | Analyze"] = {"main": [[m("Ads | Compose review")], [m("Ads | Incomplete report")]]}
    conns["Ads | Compose review"] = {"main": [[m("Ads | Create Markdown BEFORE Slack")], [m("Ads | Incomplete report")]]}
    conns["Ads | Incomplete report"] = {"main": [[m("Ads | Create Markdown BEFORE Slack")]]}
    conns["Ads | Create Markdown BEFORE Slack"] = {"main": [[m("Slack | Format for Slack"), m("Email | Combine reports")]]}
    conns["Slack | Format for Slack"] = {"main": [[m("Deliver | Slack")]]}
    conns["Email | Combine reports"] = {"main": [[m("Deliver | Email")]]}
    # Layout: one row, notes above it, delivery to the right
    chain = ["Ads | Reporting period", "Ads | Google Ads (sample data)", "Ads | Merge", "Ads | Analyze", "Ads | Compose review",
             "Ads | Create Markdown BEFORE Slack"]
    x0, y0, step = 704, 400, 224
    nodes[ADS_TRIGGER]["position"] = [256, y0]
    nodes[ADS_RUN_NOW]["position"] = [256, y0 + 192]
    nodes["Settings"]["position"] = [480, y0]
    for k, name in enumerate(chain):
        nodes[name]["position"] = [x0 + k * step, y0]
    nodes["Ads | Meta Ads (sample data)"]["position"] = [x0 + step, y0 + 192]
    nodes["Ads | Incomplete report"]["position"] = [x0 + 4 * step, y0 + 192]
    dx = x0 + len(chain) * step + 224
    nodes["Slack | Format for Slack"]["position"] = [dx, y0]
    nodes["Deliver | Slack"]["position"] = [dx + step, y0]
    nodes["Email | Combine reports"]["position"] = [dx, y0 + 256]
    nodes["Deliver | Email"]["position"] = [dx + step, y0 + 256]
    for name, text, pos, w, h, color in [
            ("Ads review explainer", ADS_NOTE, [x0 - 64, y0 - 380], 760, 340, 1),
            ("Connect your ad platforms", ADS_CONNECT_NOTE, [x0 + 3 * step + 64, y0 - 380], 700, 340, 4),
            ("Slack setup guide", ADS_SLACK_NOTE, [dx - 64, y0 - 400], 560, 360, 4)]:
        add({"parameters": {"content": text, "width": w, "height": h, "color": color}, "name": name, "position": pos,
             "type": "n8n-nodes-base.stickyNote", "typeVersion": 1})
    add_groups(wf, "ads", ADS_GROUP_DESC, override={"Slack | Format for Slack": "Deliver: Slack"})
    out = f"{OUT}/ads-review-from-nick-v1.json"
    json.dump(wf, open(out, "w"), indent=2, ensure_ascii=False)
    print("wrote", out, len(wf["nodes"]), "nodes")


ADS_GROUP_DESC = {
    "Ads review": "Google Ads and Meta campaigns graded on value-to-spend, from Nick Christensen's starter (sample data until connected).",
    "Deliver: Slack": "One formatted message with the review.",
    "Deliver: Email": "One email with the review in the body and attached.",
}
MARKDOWN_CODE = "const d=$input.first().json;return [{json:d,binary:{report:{data:Buffer.from(d.markdown,'utf8').toString('base64'),mimeType:'text/markdown',fileExtension:'md',fileName:d.fileName}}}];"


def slack_node(notes):
    """The n8n Slack node every workflow delivers through: channel by ID from Settings, no n8n footer link."""
    return {"parameters": {"select": "channel",
                           "channelId": {"__rl": True, "value": "={{ $('Settings').first().json.slackChannel }}", "mode": "id"},
                           "text": "={{ $json.slackText }}",
                           "otherOptions": {"unfurl_links": False, "unfurl_media": False, "includeLinkToWorkflow": False}},
            "name": "Deliver | Slack", "type": "n8n-nodes-base.slack", "typeVersion": 2.3, "disabled": True,
            "webhookId": str(uuid.uuid5(GROUP_NS, "slack-webhook")), "notes": notes, "notesInFlow": True}


def gmail_node(notes):
    return {"parameters": {
        "resource": "message", "operation": "send",
        "sendTo": "={{ $('Settings').first().json.emailTo }}",
        "subject": "={{ $json.subject }}", "emailType": "text", "message": "={{ $json.body }}",
        "options": {"appendAttribution": False,
                    "attachmentsUi": {"attachmentsBinary": [{"property": "={{ $json.attachmentNames }}"}]}}},
        "name": "Deliver | Email", "type": "n8n-nodes-base.gmail", "typeVersion": 2.2, "disabled": True,
        "notes": notes, "notesInFlow": True}


def core(wf, demo, settings_js):
    """Settings, Settings-driven lanes, INCOMPLETE reports, Collect, and the formatted Slack delivery.
    Shared by Nick's v2 demo and the Metorik worked example."""
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
    wf["nodes"].append({"parameters": {"jsCode": settings_js}, "id": nid(), "name": "Settings",
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
    return nodes, conns, code, set_code, note


def build(fn, demo, full):
    wf = json.load(open(f"{SRC}/{fn}"))
    nodes, conns, code, set_code, note = core(wf, demo, settings_code(demo))
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
# Nick's v2 demo: what Nick asked for on top of his v1.0 demo. Settings, the four lanes on his
# made-up data, Collect, a summary, and Slack as the only delivery. The week-at-a-glance summary
# is plain code (no API key); the AI summary sits beside it, switched off.

DEMO_SETTINGS = """// Edit these before the first run. Every lane reads its settings from here.
return [{json:{
  storeName:'Demo Store',            // the made-up store; keep it for the demo
  currency:'USD',                    // ISO code, for example EUR or GBP
  timeZone:'America/Chicago',        // reporting timezone, for example Europe/London
  locale:'en-US',                    // number and money format, for example en-GB or de-DE
  ga4PropertyId:'NOT_NEEDED_FOR_THE_DEMO', // the demo's traffic data is made up
  ga4Events:['purchase','generate_lead'], // events the traffic review lists
  slackChannel:'SELECT_YOUR_TEST_CHANNEL', // Slack delivery: the channel ID (right-click the channel, Copy link: the part after /archives/)
  emailTo:'YOU@EXAMPLE.COM',         // only if you swap Slack for email
  n8nUrl:'https://YOUR-INSTANCE.app.n8n.cloud' // your n8n address, for the workflow links in Slack
}}];"""
GLANCE_CODE = """// Week at a glance: one line per review, quoted from its report, and the reviews that did not run.
// Plain code, no AI and no new arithmetic: every figure here is copied from a review.
const items=$('Collect all reports').all(), s=$('Settings').first().json, p=$('Executive | Reporting period').first().json;
const lines=md=>String(md||'').split('\\n').map(x=>x.trim());
const pick={executive:/^\\u2022 Net revenue:/,marketing:/^\\u2022 Source report represents/,products:/^1\\. /,traffic:/^Sessions:/,email:/^\\u2022 Emails sent:/};
const label={executive:'Sales',marketing:'Sources',products:'Top product',traffic:'Traffic',email:'Email'}; // add a lane here when you add a review
const lane=i=>String(i.json.fileName).split('-')[0];
const done=items.filter(i=>!i.json.incomplete), missing=items.filter(i=>i.json.incomplete);
const out=['# Week at a glance',p.start+' to '+p.end+' | '+s.storeName+' | '+done.length+' of '+items.length+' reviews complete',''];
for(const i of done){const l=lines(i.json.markdown).find(x=>(pick[lane(i)]||/^\\u2022/).test(x));out.push('\\u2022 '+(label[lane(i)]||lane(i))+': '+(l?l.replace(/^\\u2022\\s*/,''):'see the review'));}
if(missing.length){out.push('','Did not run (missing, not zero):');for(const i of missing){const f=lines(i.json.markdown).find(x=>/^Failed step:/.test(x));out.push('\\u2022 '+(label[lane(i)]||lane(i))+': '+(f||'see the review'));}}
out.push('','Every figure above is quoted from its review. The reviews follow.');
const markdown=out.join('\\n')+'\\n', fileName='glance-'+p.start+'-to-'+p.end+'.md';
const facts={period:{start:p.start,end:p.end,previousStart:p.previousStart,previousEnd:p.previousEnd},currency:s.currency,
  reviews:{complete:done.map(i=>i.json.fileName),incomplete:missing.map(i=>i.json.fileName),complete_count:done.length,total_count:items.length},
  reports:items.map(i=>({file:i.json.fileName,incomplete:!!i.json.incomplete,markdown:i.json.markdown}))};
return [{json:{markdown,slackText:markdown,fileName,facts},binary:{report:{data:Buffer.from(markdown,'utf8').toString('base64'),mimeType:'text/markdown',fileExtension:'md',fileName}}}];"""
DEMO_AI_SYSTEM = """You write a short weekly summary for a marketing team from the facts you are given, and nothing else.

Rules:
1. Every number you write must appear in the facts. You may round to whole numbers. Never calculate a new number.
2. How many reviews ran comes only from reviews.complete_count and reviews.total_count. Name the incomplete ones from reviews.incomplete.
3. A report marked incomplete, or a value that is missing or null, is missing data, not zero. Say it is missing and name the failed step.
4. Keep facts, hypotheses and missing data apart. Label every hypothesis as a hypothesis.
5. If the reports say DEMO or SYNTHETIC DATA, say once, first, that the figures are made up.
6. Order sources are not incrementality, event counts are not unique people, and non-renewal revenue is not first-time buyer revenue.
7. Plain US English, short lines, no em dashes, no all caps.

Output Markdown with exactly these sections:
## Headline (two lines)
## Flags
## Working
## Not working
## Missing data
## Check next (at most three items, each tied to a line in a report)"""
DEMO_AI_REPORT = """// The AI summary as one more file. While the AI node is switched off it passes the glance through,
// so this step marks the summary skipped and nothing extra is delivered.
const j=$input.first().json, p=$('Summary | Week at a glance').first().json.facts.period;
if(!j.output&&!j.error)return [{json:{skipped:true,fileName:'summary-'+p.start+'-to-'+p.end+'-skipped.md',markdown:'',slackText:''}}];
const ok=!j.error&&j.output;
const body=ok?String(j.output).replace(/\\s*\\u2014\\s*/g,', '):'INCOMPLETE: the AI summary did not run, so there is no AI summary this week. The reviews are unaffected.\\nReason: '+String(j.error?.message||j.error||'no output').slice(0,300);
const fileName='summary-'+p.start+'-to-'+p.end+(ok?'':'-incomplete')+'.md';
const markdown='# Weekly summary\\n'+p.start+' to '+p.end+'\\nWritten by an AI model from this run\\'s reviews. Check a number against its review before acting on it.\\n\\n'+body+'\\n';
return [{json:{markdown,slackText:markdown,fileName,incomplete:!ok},binary:{report:{data:Buffer.from(markdown,'utf8').toString('base64'),mimeType:'text/markdown',fileExtension:'md',fileName}}}];"""
DEMO_ALL = """// The four reviews, the week at a glance and, when it is switched on, the AI summary.
return [...$('Collect all reports').all(), $('Summary | Week at a glance').first(), ...$('Summary | AI summary report').all().filter(i => !i.json.skipped)];"""
DEMO_INTRO_NOTE = """## Nick's demo, v2
Four weekly reviews on made-up data: no logins, no API calls. **Settings** holds the store, currency and timezone. Each review is a group: open one block at a time.

After the four lanes, **Collect all reports** gathers them, **Summary** writes a week at a glance (plain code, every figure quoted), and **Deliver: Slack** posts them, switched off until you connect Slack.

Every number is invented and fixed. The store reviews show a fixed example week; traffic uses the last 7 days."""
DEMO_TASK_NOTE = """## Your task
Get the reviews out of n8n, one of two ways:

**A. Slack:** create a Slack app with the bot scope `chat:write`, save its token as an n8n Slack credential, invite the bot to a test channel, put the channel ID in Settings (`slackChannel`), select the credential on Deliver | Slack, switch it on, run.

**B. Email instead:** replace Deliver | Slack with a Gmail node that sends the reports (ask Claude to swap it), set `emailTo` in Settings, run, then `/reporting-agent:get-email-reports` saves them into your OS."""
DEMO_SUMMARY_NOTE = """## Summary
**Week at a glance** (on): one line per review, quoted from the review, and any review that did not run. Plain code, no API key.

**AI summary** (off): an AI Agent with a Claude model reads the reviews and writes flags, what is working and what to check. It may not invent a number. To switch it on: add an Anthropic credential to Summary | Claude model, then switch on Summary | AI summary."""
DEMO_SLACK_NOTE = """## Slack setup
1. Create and install a Slack app with the bot scope `chat:write`.
2. Save its token as an n8n Slack credential.
3. Invite the bot to a test channel.
4. Put the channel ID in Settings (`slackChannel`).
5. Select the credential on Deliver | Slack and switch it on. It posts one formatted message per review and one for the summary.

App installation may need workspace approval."""
DEMO_GROUP_DESC = {
    "1. Executive review": "Sales, refunds and orders this week vs last, on made-up data.",
    "2. Marketing source review": "Orders and net sales by recorded source, on made-up data.",
    "3. Top product review": "Top products and plans by net sales, on made-up data.",
    "4. Website traffic review": "Sessions, sources, landing pages and events, on a made-up GA4 response.",
    "Summary": "Week at a glance in code (on) and the AI summary (off), then every report together.",
    "Deliver: Slack": "One formatted message per review and one for the summary.",
}
DEMO_CHAINS = {
    "Executive": ["Reporting period", "Verify store", "Check store identity", "Current revenue", "Previous revenue",
                  "Order types", "Compose review", "Create Markdown BEFORE Slack"],
    "Marketing": ["Reporting period", "Verify store", "Check store identity", "Order sources", "All orders",
                  "Compose review", "Create Markdown BEFORE Slack"],
    "Products": ["Reporting period", "Verify store", "Check store identity", "Top products", "Compose review",
                 "Create Markdown BEFORE Slack"],
    "Traffic": ["Reporting period", "Build GA4 request", "Synthetic GA4 response", "Compose review", "Create Markdown BEFORE Slack"],
}


def build_demo_v2(full):
    wf = json.load(open(f"{SRC}/four-reviews-demo.json"))
    nodes, conns, code, set_code, note = core(wf, True, DEMO_SETTINGS)
    txt = json.dumps(wf, ensure_ascii=False)
    wf = json.loads(rep(txt, "Collect all four reports", COLLECT, txt.count("Collect all four reports")))
    nodes = {n["name"]: n for n in wf["nodes"]}
    nodes["Settings"]["notes"] = "Edit before the first run: currency, timezone, number format and the Slack channel."
    conns = wf["connections"]
    fn = {n["name"]: n for n in full["nodes"]}

    def add(node):
        node.setdefault("id", nid())
        node.setdefault("position", [0, 0])
        wf["nodes"].append(node)
        nodes[node["name"]] = node
        return node

    # Slack: channel from Settings
    nodes["Deliver | Slack"]["parameters"]["channelId"] = {"__rl": True, "value": "={{ $('Settings').first().json.slackChannel }}", "mode": "id"}
    nodes["Deliver | Slack"]["notes"] = "One formatted message per review and one for the summary. Select your Slack credential, set slackChannel in Settings, then switch on."
    # Summary: week at a glance (on), AI summary (off)
    add({"parameters": {"jsCode": GLANCE_CODE}, "name": "Summary | Week at a glance", "type": "n8n-nodes-base.code", "typeVersion": 2,
         "notes": "One line per review, quoted. No AI.", "notesInFlow": True})
    agent = copy.deepcopy(fn["AI | Weekly summary"])
    agent.pop("id", None)
    agent["name"] = "Summary | AI summary"
    agent["disabled"] = True
    agent["parameters"]["text"] = "={{ 'Facts (JSON):\\n' + JSON.stringify($json.facts, null, 1) }}"
    agent["parameters"]["options"]["systemMessage"] = DEMO_AI_SYSTEM
    add(agent)
    model = copy.deepcopy(fn["AI | Claude model"])
    model.pop("id", None)
    model.pop("credentials", None)
    model["name"] = "Summary | Claude model"
    add(model)
    add({"parameters": {"jsCode": DEMO_AI_REPORT}, "name": "Summary | AI summary report", "type": "n8n-nodes-base.code", "typeVersion": 2})
    add({"parameters": {"jsCode": DEMO_ALL}, "name": "All reports and summary", "type": "n8n-nodes-base.code", "typeVersion": 2})
    m = lambda target, index=0: {"node": target, "type": "main", "index": index}
    conns[COLLECT] = {"main": [[m("Summary | Week at a glance")]]}
    conns["Summary | Week at a glance"] = {"main": [[m("Summary | AI summary")]]}
    conns["Summary | Claude model"] = {"ai_languageModel": [[{"node": "Summary | AI summary", "type": "ai_languageModel", "index": 0}]]}
    conns["Summary | AI summary"] = {"main": [[m("Summary | AI summary report")]]}
    conns["Summary | AI summary report"] = {"main": [[m("All reports and summary")]]}
    conns["All reports and summary"] = {"main": [[m("Slack | Format for Slack")]]}

    # Notes
    nodes["How to demonstrate"]["parameters"]["content"] = DEMO_INTRO_NOTE
    nodes["Slack app setup guide"]["parameters"]["content"] = DEMO_SLACK_NOTE
    for name, text in [("Summary explainer", DEMO_SUMMARY_NOTE), ("Your task", DEMO_TASK_NOTE)]:
        add({"parameters": {"content": text}, "name": name, "type": "n8n-nodes-base.stickyNote", "typeVersion": 1})

    # Layout: Hesh's pattern. Lane explainers left of each lane group, summary and Slack to the right.
    x0, step, y0, gap = 704, 224, 304, 480
    for i, (lane, chain) in enumerate(DEMO_CHAINS.items()):
        y = y0 + i * gap
        for k, short in enumerate(chain):
            nodes[f"{lane} | {short}"]["position"] = [x0 + k * step, y]
        nodes[f"{lane} | Incomplete report"]["position"] = [x0 + chain.index("Compose review") * step, y + 192]
        note_name, w, h, color = LANE_NOTES[lane]
        nodes[note_name]["position"] = [x0 - 848, y - 192]
        nodes[note_name]["parameters"].update({"width": w, "height": h, "color": color})
    nodes["Run all four reviews"]["position"] = [-64, 920]
    nodes["Settings"]["position"] = [160, 920]
    nodes["How to demonstrate"]["position"] = [-816, -128]
    nodes["How to demonstrate"]["parameters"].update({"width": 480, "height": 400, "color": 2})
    right = x0 + max(len(c) for c in DEMO_CHAINS.values()) * step + 256
    nodes[COLLECT]["position"] = [right, y0 + gap]
    sx, sy = right + 224, y0 + gap
    row = ["Summary | Week at a glance", "Summary | AI summary", "Summary | AI summary report", "All reports and summary",
           "Slack | Format for Slack", "Deliver | Slack"]
    for k, name in enumerate(row):
        nodes[name]["position"] = [sx + k * step + (224 if k >= 4 else 0), sy]
    nodes["Summary | Claude model"]["position"] = [sx + step, sy + 224]
    nodes["Summary explainer"]["position"] = [sx - 64, sy - 340]
    nodes["Summary explainer"]["parameters"].update({"width": 4 * step + 64, "height": 300, "color": 6})
    slack_x = sx + 4 * step + 224
    nodes["Slack app setup guide"]["position"] = [slack_x - 64, sy - 480]
    nodes["Slack app setup guide"]["parameters"].update({"width": 520, "height": 440, "color": 4})
    nodes["Your task"]["position"] = [slack_x - 64, sy + 200]
    nodes["Your task"]["parameters"].update({"width": 520, "height": 470, "color": 3})
    add_groups(wf, "demo-v2", DEMO_GROUP_DESC, override={"All reports and summary": "Summary"})
    wf["name"] = "Workshop | Four reviews | Nick's demo | v2"
    out = f"{OUT}/four-reviews-demo-v2.json"
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
    """Email and the pull request count the reviews, not the summary or week-at-a-glance file."""
    js = rep(js, "const done=items.filter(i=>!i.json.incomplete).length;",
             "const reviews=items.filter(i=>!/^(summary|glance)-/.test(String(i.json.fileName))),done=reviews.filter(i=>!i.json.incomplete).length;")
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

    # Executive review: a total the source can't supply (a CRM has no refunds or items) reads as missing, never NaN or 0
    js = code("Executive | Compose review")
    js = rep(js, "const money=v=>new Intl.NumberFormat(", "const na=v=>v===undefined||v===null||v==='';const money=v=>na(v)?'not available':new Intl.NumberFormat(")
    js = rep(js, "const pct=(a,b)=>b?", "const pct=(a,b)=>na(a)||na(b)?'N/A':b?")
    js = rep(js, "'• Orders: '+c.orders+' ('+pct(c.orders,b.orders)+'); items: '+c.items+'.'",
             "'• Orders: '+(na(c.orders)?'not available':c.orders)+' ('+pct(c.orders,b.orders)+'); items: '+(na(c.items)?'not available':c.items)+'.'")
    set_code("Executive | Compose review", js)

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
build_demo_v2(full_wf)
build_ads()
