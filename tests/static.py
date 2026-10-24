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
nick+=" "+" ".join(strings(json.load(open("handoff-src/four-reviews-demo.json"))))  # Nick's demo text is quoted unchanged
ALL=["out/four-reviews-demo-v2.json","out/ads-review-from-nick-v1.json","out/four-reviews-metorik-template-v1.1.json","out/four-reviews-connection-template-v1.2.json"]
for new in ALL:
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

# Every shipped workflow: collapsible groups, public-repo checks, notes clear of grouped nodes
COL="Collect all reports"
EXPECT={"four-reviews-demo-v2.json":6,"ads-review-from-nick-v1.json":3,"four-reviews-metorik-template-v1.1.json":9,"four-reviews-connection-template-v1.2.json":9}
for fn in ALL:
    w=json.load(open(fn)); N={n["name"]:n for n in w["nodes"]}; base=fn.split("/")[-1]; tag=base+": "
    groups=w.get("nodeGroups") or []
    members=[m for g in groups for m in g["nodeNames"]]
    check(len(groups)==EXPECT[base] and all(g.get("id") and g.get("name") and g.get("description") for g in groups),tag+str(EXPECT[base])+" named groups with ids and descriptions")
    check(all(m in N for m in members),tag+"every grouped node exists")
    check(not [m for m in members if N[m]["type"].endswith("Trigger")],tag+"no trigger in a group")
    check(len(members)==len(set(members)),tag+"no node in two groups")
    visible={"Run all four reviews","Settings",COL}
    loose=[n["name"] for n in w["nodes"] if n["type"]!="n8n-nodes-base.stickyNote" and not n["type"].endswith("Trigger") and n["name"] not in visible and n["name"] not in members]
    check(not loose and not visible&set(members),tag+"every node except triggers, Settings and Collect is in exactly one group "+str(loose[:3]))
    over=[]
    for n in w["nodes"]:
        if n["type"]!="n8n-nodes-base.stickyNote": continue
        x,y=n["position"];W=n["parameters"].get("width",240);H=n["parameters"].get("height",160)
        over+=[(n["name"],m) for m in members if N[m]["position"][0]<x+W and N[m]["position"][0]+100>x and N[m]["position"][1]<y+H and N[m]["position"][1]+100>y]
    check(not over,tag+"no sticky note overlaps a grouped node "+str(over[:2]))
    t=json.dumps(w)
    check(not [n for n in w["nodes"] if n.get("credentials")],tag+"no credentials")
    check(not re.search(r"(?i)cxl|institute",t),tag+"no CXL names or addresses")
    dl=[n for n in w["nodes"] if n["type"] in ("n8n-nodes-base.slack","n8n-nodes-base.gmail","n8n-nodes-base.github") or n["name"].startswith("GitHub | ") and n["type"]=="n8n-nodes-base.httpRequest"]
    check(dl and all(n.get("disabled") for n in dl),tag+"every delivery node switched off ("+str(len(dl))+")")
    src=[n for n in w["nodes"] if n["type"]=="n8n-nodes-base.httpRequest" and not n["name"].startswith("GitHub |")]
    check(all(n.get("disabled") for n in src),tag+"every source request ("+str(len(src))+") switched off")
    ai=[n for n in w["nodes"] if n["type"]=="@n8n/n8n-nodes-langchain.agent"]
    check(all(n.get("disabled") for n in ai),tag+"the AI summary ships switched off ("+str(len(ai))+")")
    check("Ads | " not in t or base.startswith("ads-"),tag+"the ads review lives only in its own workflow")
    # An em dash passes only where the text on one side of it is quoted from Nick (his report titles keep theirs)
    added=[ln for n in w["nodes"] for ln in re.split(r"[\n;]",n.get("parameters",{}).get("jsCode","")+"\n"+n.get("parameters",{}).get("content","")) if "—" in ln and ln.strip() not in nick and any(ln[max(0,i-12):i+1] not in nick and ln[i:i+13] not in nick for i,c in enumerate(ln) if c=="—")]
    check(not added,tag+"no em dashes in added code or notes "+str(added[:2]))

# The two worked examples: History expression safe, email lane kept, Collect takes five
for fn in ["out/four-reviews-metorik-template-v1.1.json","out/four-reviews-connection-template-v1.2.json"]:
    w=json.load(open(fn)); N={n["name"]:n for n in w["nodes"]}; tag=fn.split("/")[-1]+": "
    check(N[COL]["parameters"]["numberInputs"]==5 and any(n.startswith("Customer.io | ") for n in N),tag+"Collect takes five reviews, the email lane included")
    check("adsEnabled" not in N["Settings"]["parameters"]["jsCode"],tag+"no ads switch in Settings")
    check("}}" not in N["History | Save this run"]["parameters"]["columns"]["value"]["facts_json"][3:-2],tag+"history expression has no }} inside it")

# Nick's v2 demo: Settings, Collect, the two summaries, Slack only
d=json.load(open("out/four-reviews-demo-v2.json")); D={n["name"]:n for n in d["nodes"]}
check(D[COL]["parameters"]["numberInputs"]==4 and "Settings" in D,"demo v2: Settings and Collect (4 reviews)")
check(D["Summary | Week at a glance"]["type"]=="n8n-nodes-base.code" and not D["Summary | Week at a glance"].get("disabled"),"demo v2: week at a glance in code, switched on")
check(D["Summary | AI summary"].get("disabled") and D["Summary | Claude model"]["parameters"]["model"]["value"]=="claude-sonnet-5-5" and D["Summary | Claude model"]["parameters"]["options"].get("maxTokensToSample")==6000,"demo v2: AI summary off, claude-sonnet-5-5, 6000 tokens")
types=[n["type"] for n in d["nodes"]]
check(types.count("n8n-nodes-base.slack")==1 and "n8n-nodes-base.gmail" not in types and "n8n-nodes-base.github" not in types and not any(n["name"].startswith(("GitHub |","Trends |","History |","Customer.io |")) for n in d["nodes"]),"demo v2: Slack is the only delivery; no trends, history, email lane or GitHub")
check("slackChannel" in D["Deliver | Slack"]["parameters"]["channelId"]["value"] and D["Deliver | Slack"]["parameters"]["otherOptions"]["includeLinkToWorkflow"]==False,"demo v2: Slack channel from Settings, no n8n footer link")
check("Your task" in D and all(k in D["Your task"]["parameters"]["content"] for k in ["Slack","slackChannel","Gmail","get-email-reports"]),"demo v2: the 'Your task' note gives both ways, Slack or email")
nickdemo={n["name"]:n for n in json.load(open("handoff-src/four-reviews-demo.json"))["nodes"]}
check(all(D[k]["parameters"]["jsCode"]==nickdemo[k]["parameters"]["jsCode"] for k in ["Executive | Current revenue","Executive | Previous revenue","Marketing | Order sources","Products | Top products","Traffic | Synthetic GA4 response"]),"demo v2: Nick's made-up data nodes unchanged")

# The ads review workflow: Nick's chain, his code verbatim, the report contract
a=json.load(open("out/ads-review-from-nick-v1.json")); A={n["name"]:n for n in a["nodes"]}
for old,new in {"Mock Google Ads":"Ads | Google Ads (sample data)","Mock Meta Ads":"Ads | Meta Ads (sample data)","Analyze":"Ads | Analyze"}.items():
    js=A[new]["parameters"]["jsCode"]
    check(js.endswith(ads_code[old]) and "Nick Christensen" in js and "MIT" in js and "nickyc1/ship-icp-ads-automate-monitoring" in js,"ads: "+new+": Nick's code carried unchanged under a credit header")
check(A["Daily 9am"]["type"]=="n8n-nodes-base.scheduleTrigger" and A["Ads | Merge"]["type"]=="n8n-nodes-base.merge","ads: Nick's daily schedule and merge kept")
check("hooks.slack.com" not in json.dumps(a) and not [n for n in a["nodes"] if n["type"]=="n8n-nodes-base.emailSend"],"ads: Nick's webhook and SMTP nodes replaced by the shared Slack and Gmail delivery")
check("fileName:'ads-'" in A["Ads | Compose review"]["parameters"]["jsCode"] and "SAMPLE DATA" in A["Ads | Compose review"]["parameters"]["jsCode"],"ads: compose writes the report contract with a SAMPLE DATA label")

# The commands and docs: one preflight, no manual route, every file they name ships
ROOT=os.path.dirname(os.path.abspath(HERE))
cmds={f:open(os.path.join(ROOT,"commands",f)).read() for f in sorted(os.listdir(os.path.join(ROOT,"commands")))}
plug=json.load(open(os.path.join(ROOT,".claude-plugin","plugin.json")))
check(sorted(c.split("/")[-1] for c in plug["commands"])==sorted(cmds),"plugin.json registers every command: "+", ".join(sorted(cmds)))
pre=lambda t:t[t.index("<!-- preflight:"):t.index("<!-- /preflight -->")] if "<!-- preflight:" in t and "<!-- /preflight -->" in t else None
build=["build-reporting-demo.md","build-reporting-agent.md","build-reporting-agent-ads.md"]
blocks={f:pre(cmds[f]) for f in build}
check(all(blocks.values()) and len(set(blocks.values()))==1,"the three build commands carry the same preflight block")
b=blocks["build-reporting-demo.md"] or ""
check(all(k in b for k in ["projects/reporting-agent/reporting-agent.md","plugin/setup.sh","folders.json","contain `n8n`","get_user_preferences","Customize → Connectors","MCP access","Do not offer another way to build"]),"the preflight checks the folder (setup script, folder map) and the n8n MCP connection, and stops without it")
check(all(cmds[f].index("<!-- preflight:")<cmds[f].index("## Step 1") for f in build),"the preflight comes before step 1 in every build command")
check("Before anything: your folder and n8n" in cmds["how-to-build-yourself.md"],"how-to-build-yourself sends scratch and edit mode through the same checks")
docs={**{"commands/"+f:t for f,t in cmds.items()},"README.md":open(os.path.join(ROOT,"README.md")).read(),"plugin/claude-md-section.md":open(os.path.join(ROOT,"plugin","claude-md-section.md")).read()}
manual=[(f,m.group(0)) for f,t in docs.items() for m in re.finditer(r"(?i)by hand|import from url|import from file|build route|build it yourself in n8n|you build it",t)]
check(not manual,"no manual-build route offered in the commands, README or CLAUDE.md section "+str(manual[:3]))
named={m for t in docs.values() for m in re.findall(r"[\w.-]+-v\d+(?:\.\d+)?\.json",t)}
check(named and all(os.path.exists(os.path.join(ROOT,"workflows",n)) for n in named),"every workflow file the docs name ships: "+", ".join(sorted(named)))
check("four-reviews-demo-v2.json" in cmds["build-reporting-demo.md"] and "four-reviews-demo-v2.json" in cmds["build-reporting-agent.md"] and "ads-review-from-nick-v1.json" in cmds["build-reporting-agent-ads.md"],"each build command starts from its own workflow")
agent=cmds["build-reporting-agent.md"]
check(all(k in agent for k in ["Connect GA4","store or CRM","email review","Microsoft Teams","get-email-reports","--json visibility","PRIVATE"]) and agent.count("| Login |")+agent.count("| Fetch |")+agent.count("| Convert |")+agent.count("| Reconcile |")+agent.count("| Edit |")+agent.count("| Summary |")+agent.count("| Copy |")+agent.count("| Delivery |")>=17,"build-reporting-agent: GA4, store or CRM, email review, outputs (Teams, email, private-only GitHub) and the 17 checkpoints")
check("Ads |" not in agent and "adsEnabled" not in agent and "lane 6" not in agent.lower(),"build-reporting-agent adds no ads lane; it points to the ads command instead")
em=[(f,ln[:60]) for f,t in docs.items() for ln in t.split("\n") if "—" in ln]
check(not em,"no em dashes in the commands, README or CLAUDE.md section "+str(em[:2]))
check(plug["version"] in docs["README.md"].split("\n")[0] and ("## "+plug["version"]) in open(os.path.join(ROOT,"CHANGES-v1.1.md")).read(),"version "+plug["version"]+" in plugin.json, README and CHANGES")
sys.exit(1 if fails else 0)
