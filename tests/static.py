import json,sys,re
for old,new in [("handoff-src/four-reviews-demo.json","out/four-reviews-demo-v1.1.json"),("handoff-src/four-reviews-connection-template.json","out/four-reviews-connection-template-v1.1.json")]:
    a=json.load(open(old)); b=json.load(open(new))
    ids=[n["id"] for n in b["nodes"]]; names=[n["name"] for n in b["nodes"]]
    print("==",new,"| nodes",len(b["nodes"]),"| unique ids",len(set(ids))==len(ids),"| unique names",len(set(names))==len(names))
    print("credentials:",[n["name"] for n in b["nodes"] if n.get("credentials")])
    tgt={t["node"] for c in b["connections"].values() for o in c["main"] for t in o}|set(b["connections"])
    print("unconnected:",[n["name"] for n in b["nodes"] if n["name"] not in tgt and n["type"]!="n8n-nodes-base.stickyNote"])
    print("disabled:",sorted(n["name"] for n in b["nodes"] if n.get("disabled")))
    def strings(o):
        if isinstance(o,str): yield o
        elif isinstance(o,dict):
            for v in o.values(): yield from strings(v)
        elif isinstance(o,list):
            for v in o: yield from strings(v)
    olds=" ".join(strings(a))
    added=[ln for s in strings(b) for ln in re.split(r"[\n;]",s) if "—" in ln and ln.strip() not in olds]
    print("em dashes in added text:",added)
    print("secrets scan:",re.findall(r"(xox[bp]-|ghp_|github_pat_|Bearer [A-Za-z0-9]{10}|@cxl\.com)",json.dumps(b)))
