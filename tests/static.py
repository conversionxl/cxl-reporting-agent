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
sys.exit(1 if fails else 0)
