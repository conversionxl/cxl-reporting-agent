"""Convert an n8n workflow JSON export into n8n Workflow SDK code, one-to-one, so Claude can create it through the n8n MCP connector (validate_workflow, then create_workflow_from_code). Usage: python3 -I to_sdk.py <workflow.json> <out.ts>"""
import json, re, sys

wf = json.load(open(sys.argv[1]))
out_path = sys.argv[2]


def js(v):
    if isinstance(v, str):
        if v.startswith("="):
            return "expr(" + json.dumps(v[1:]) + ")"
        return json.dumps(v)
    if isinstance(v, bool):
        return "true" if v else "false"
    if v is None:
        return "null"
    if isinstance(v, (int, float)):
        return json.dumps(v)
    if isinstance(v, list):
        return "[" + ", ".join(js(x) for x in v) + "]"
    return "{" + ", ".join(json.dumps(k) + ": " + js(x) for k, x in v.items()) + "}"


var = {}
lines = ["import { workflow, node, trigger, sticky, merge, expr } from '@n8n/workflow-sdk';", ""]
for i, n in enumerate(wf["nodes"]):
    v = "n" + str(i)
    var[n["name"]] = v
    cfg = {"name": n["name"], "position": n["position"]}
    if n["type"] == "n8n-nodes-base.stickyNote":
        p = n["parameters"]
        opts = {"name": n["name"], "position": n["position"], "color": p.get("color", 1),
                "width": p.get("width"), "height": p.get("height")}
        lines.append(f"const {v} = sticky({json.dumps(p['content'])}, [], {js(opts)});")
        continue
    cfg["parameters"] = n["parameters"]
    for k in ("disabled", "onError", "retryOnFail", "maxTries", "waitBetweenTries", "notes", "notesInFlow"):
        if k in n:
            cfg[k] = n[k]
    fn = "trigger" if n["type"].endswith("Trigger") else ("merge" if n["type"] == "n8n-nodes-base.merge" else "node")
    if fn == "merge":
        lines.append(f"const {v} = merge({{ version: {n['typeVersion']}, config: {js(cfg)} }});")
    else:
        lines.append(f"const {v} = {fn}({{ type: {json.dumps(n['type'])}, version: {n['typeVersion']}, config: {js(cfg)}, output: [{{}}] }});")

chain = [f"export default workflow('four-reviews-demo-v1-1', {json.dumps(wf['name'])})"]
added = set()
for src, c in wf["connections"].items():
    for out_i, targets in enumerate(c["main"]):
        for t in targets:
            dst = var[t["node"]]
            tn = next(n for n in wf["nodes"] if n["name"] == t["node"])
            dst_expr = f"{dst}.input({t['index']})" if tn["type"] == "n8n-nodes-base.merge" else dst
            if out_i == 0:
                chain.append(f"  .add({var[src]}.to({dst_expr}))")
            else:
                chain.append(f"  .add({var[src]}.onError({dst_expr}))")
            added |= {src, t["node"]}
for n in wf["nodes"]:
    if n["name"] not in added:
        chain.append(f"  .add({var[n['name']]})")
lines.append("")
lines.append("\n".join(chain) + ";")
open(out_path, "w").write("\n".join(lines) + "\n")
print(out_path, len(open(out_path).read()), "chars")
