#!/usr/bin/env bash
# Rebuilds every shipped workflow from its source (Nick's v2 demo and his ads
# review from his exports, the Metorik example from his export, the full example
# from the sanitized export of the live-tested workflow) and checks each matches
# the shipped file, runs every lane locally (made-up data, failures, delivery),
# and runs the static checks. Needs python3 and node; installs luxon once into tests/.
set -e
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$HERE/.." && pwd)"
WORK="$(mktemp -d)"
trap 'rm -rf "$WORK"' EXIT
mkdir -p "$WORK/out" "$WORK/samples"
ln -s "$HERE/fixtures/nick-v1.0" "$WORK/handoff-src"
python3 -I "$HERE/build.py" "$HERE/fixtures/nick-v1.0" "$WORK/out"
[ "$(ls "$ROOT"/workflows/*.json | wc -l | tr -d ' ')" = 4 ] || { echo "FAIL workflows/ should hold exactly the four built workflows"; exit 1; }
echo "PASS workflows/ holds exactly the four built workflows"
for f in "$ROOT"/workflows/four-reviews-demo-v2.json "$ROOT"/workflows/ads-review-from-nick-v1.json "$ROOT"/workflows/four-reviews-metorik-template-v1.1.json "$ROOT"/workflows/four-reviews-connection-template-v1.2.json; do
  b="$(basename "$f")"
  python3 -I - "$f" "$WORK/out/$b" <<'PY'
import json,sys
strip=lambda w:[{k:v for k,v in n.items() if k!="id"} for n in w["nodes"]]
a,b=(json.load(open(p)) for p in sys.argv[1:])
assert strip(a)==strip(b) and a["connections"]==b["connections"] and a.get("nodeGroups")==b.get("nodeGroups"), "shipped workflow differs from build: "+sys.argv[1]
print("PASS shipped "+sys.argv[1].split("/")[-1]+" matches a fresh build, groups included (node ids aside)")
PY
done
[ -d "$HERE/node_modules/luxon" ] || (cd "$HERE" && npm install --silent --no-save luxon@3.5.0)
(cd "$HERE" && node test.js "$WORK/out" "$HERE/fixtures/nick-v1.0" "$WORK/samples")
(cd "$WORK" && python3 -I "$HERE/static.py" "$HERE")
