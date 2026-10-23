import json,sys,re,os
HERE=sys.argv[1] if len(sys.argv)>1 else os.path.dirname(os.path.abspath(__file__))
def strings(o):
    if isinstance(o,str): yield o
    elif isinstance(o,dict):
        for v in o.values(): yield from strings(v)
    elif isinstance(o,list):
        for v in o: yield from strings(v)
nick=" ".join(strings(json.load(open("handoff-src/four-reviews-connection-template.json"))))
nick+=" "+open(os.path.join(HERE,"js","slack-format.js")).read()
ads=json.load(open(os.path.join(HERE,"fixtures","nick-ads-starter","starter-workflow.json")))
ads_code={n["name"]:n["parameters"].get("jsCode") for n in ads["nodes"]}
nick+=" "+" ".join(c for c in ads_code.values() if c)  # Nick's ads starter code is quoted unchanged
for new in ["out/four-reviews-metorik-template-v1.1.json","out/four-reviews-connection-template-v1.2.json"]:
    b=json.load(open(new))
    ids=[n["id"] for n in b["nodes"]]; names=[n["name"] for n in b["nodes"]]
    print("==",new,"| nodes",len(b["nodes"]),"| unique ids",len(set(ids))==len(ids),"| unique names",len(set(names))==len(names))
    print("credentials:",[n["name"] for n in b["nodes"] if n.get("credentials")])
    tgt={t["node"] for c in b["connections"].values() for outs in c.values() for o in outs for t in o}|set(b["connections"])
    print("unconnected:",[n["name"] for n in b["nodes"] if n["name"] not in tgt and n["type"]!="n8n-nodes-base.stickyNote"])
    print("disabled:",sorted(n["name"] for n in b["nodes"] if n.get("disabled")))
    added=[ln for s in strings(b) for ln in re.split(r"[\n;]",s) if "—" in ln and ln.strip() not in nick]
    print("em dashes in added text:",added)
    print("secrets scan:",re.findall(r"(xox[bp]-|ghp_|github_pat_|Bearer [A-Za-z0-9]{10}|@cxl\.com)",json.dumps(b)))

# The full template is public: hard checks
full=json.load(open("out/four-reviews-connection-template-v1.2.json"))
src=json.dumps(full)
fails=[]
def check(cond,msg):
    print(("PASS " if cond else "FAIL ")+msg)
    if not cond: fails.append(msg)
check(not [n for n in full["nodes"] if n.get("credentials")],"full template: no credentials")
check(not re.search(r"(?i)cxl|institute",src),"full template: no CXL names or addresses")
check(not re.search(r"\b[A-Za-z0-9]{16}\b(?=\")",json.dumps([n.get("parameters",{}).get("dataTableId") for n in full["nodes"]])),"full template: data table by name, no instance id")
delivery=["Deliver | Slack","Deliver | Email","GitHub | Get base branch","GitHub | Create branch","GitHub | Commit to branch","GitHub | Open pull request"]
nodes={n["name"]:n for n in full["nodes"]}
check(all(nodes[d].get("disabled") for d in delivery),"full template: every delivery node switched off")
sources=[n for n in full["nodes"] if n["type"]=="n8n-nodes-base.httpRequest" and not n["name"].startswith("GitHub |")]
check(all(n.get("disabled") for n in sources),"full template: every source request switched off ("+str(len(sources))+")")
settings=nodes["Settings"]["parameters"]["jsCode"]
check(all(k+":" in settings for k in ["storeUrl","n8nUrl","sourceLabel","refundNote","cioCaptureSegmentId","cioApiUrl"]),"full template: Settings has storeUrl, n8nUrl, sourceLabel, refundNote, cioCaptureSegmentId, cioApiUrl")
added=[ln for n in full["nodes"] for ln in re.split(r"[\n;]",n.get("parameters",{}).get("jsCode","")+"\n"+n.get("parameters",{}).get("content","")) if "—" in ln and ln.strip() not in nick]
check(not added,"full template: no em dashes in added code or notes "+str(added[:2]))
check(nodes["AI | Claude model"]["parameters"]["model"]["value"]=="claude-sonnet-5-5","full template: AI model id claude-sonnet-5-5")
check(nodes["AI | Claude model"]["parameters"]["options"].get("maxTokensToSample")==6000,"full template: summary has room to finish (6000 tokens)")

# Both templates: collapsible groups, hard public-repo checks, notes clear of grouped nodes
COL="Collect all reports"
for fn in ["out/four-reviews-metorik-template-v1.1.json","out/four-reviews-connection-template-v1.2.json"]:
    w=json.load(open(fn)); N={n["name"]:n for n in w["nodes"]}; tag=fn.split("/")[-1]+": "
    groups=w.get("nodeGroups") or []
    members=[m for g in groups for m in g["nodeNames"]]
    check(len(groups)==10 and all(g.get("id") and g.get("name") and g.get("description") for g in groups),tag+"10 named groups with ids and descriptions")
    check("6. Ads review" in [g["name"] for g in groups],tag+"the Ads review has its own group")
    for old,new in {"Mock Google Ads":"Ads | Google Ads (sample data)","Mock Meta Ads":"Ads | Meta Ads (sample data)","Analyze":"Ads | Analyze"}.items():
        js=N[new]["parameters"]["jsCode"]
        check(js.endswith(ads_code[old]) and "Nick Christensen" in js and "MIT" in js and "nickyc1/ship-icp-ads-automate-monitoring" in js,tag+new+": Nick's code carried unchanged under a credit header")
    check("adsEnabled:false" in N["Settings"]["parameters"]["jsCode"],tag+"Ads review ships switched off (adsEnabled:false)")
    check(N[COL]["parameters"]["numberInputs"]==6 and any(t["node"]==COL and t["index"]==5 for o in w["connections"]["Ads | Create Markdown BEFORE Slack"]["main"] for t in o),tag+"Collect takes the Ads review as its sixth input")
    check(not [n for n in w["nodes"] if n["type"] in ("n8n-nodes-base.scheduleTrigger","n8n-nodes-base.emailSend")] and "hooks.slack.com" not in json.dumps(w),tag+"the starter's own trigger, webhook and email node are left out")
    check(all(m in N for m in members),tag+"every grouped node exists")
    check(not [m for m in members if N[m]["type"]=="n8n-nodes-base.manualTrigger"],tag+"no trigger in a group")
    check(len(members)==len(set(members)),tag+"no node in two groups")
    visible={"Run all four reviews","Settings","Collect all reports"}
    loose=[n["name"] for n in w["nodes"] if n["type"]!="n8n-nodes-base.stickyNote" and n["name"] not in visible and n["name"] not in members]
    check(not loose and visible<=set(N) and not visible&set(members),tag+"every node except trigger, Settings and Collect is in exactly one group "+str(loose[:3]))
    over=[]
    for n in w["nodes"]:
        if n["type"]!="n8n-nodes-base.stickyNote": continue
        x,y=n["position"];W=n["parameters"].get("width",240);H=n["parameters"].get("height",160)
        over+=[(n["name"],m) for m in members if N[m]["position"][0]<x+W and N[m]["position"][0]+100>x and N[m]["position"][1]<y+H and N[m]["position"][1]+100>y]
    check(not over,tag+"no sticky note overlaps a grouped node "+str(over[:2]))
    t=json.dumps(w)
    check(not [n for n in w["nodes"] if n.get("credentials")],tag+"no credentials")
    check(not re.search(r"(?i)cxl|institute",t),tag+"no CXL names or addresses")
    check(all(N[d].get("disabled") for d in delivery),tag+"every delivery node switched off")
    src=[n for n in w["nodes"] if n["type"]=="n8n-nodes-base.httpRequest" and not n["name"].startswith("GitHub |")]
    check(all(n.get("disabled") for n in src) and N["AI | Weekly summary"].get("disabled"),tag+"every source request ("+str(len(src))+") and the AI summary switched off")
    check("}}" not in N["History | Save this run"]["parameters"]["columns"]["value"]["facts_json"][3:-2],tag+"history expression has no }} inside it")
sys.exit(1 if fails else 0)
