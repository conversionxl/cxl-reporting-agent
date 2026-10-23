#!/usr/bin/env bash
# Checks the shipped demo is Nick's v1.0 export unchanged, rebuilds the v1.1
# connection template from Nick's export and checks it matches the shipped one,
# runs every lane locally (made-up data, failures, delivery), and runs the static
# checks. Needs python3 and node; installs luxon once into tests/.
set -e
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$HERE/.." && pwd)"
WORK="$(mktemp -d)"
trap 'rm -rf "$WORK"' EXIT
mkdir -p "$WORK/out" "$WORK/samples"
ln -s "$HERE/fixtures/nick-v1.0" "$WORK/handoff-src"
python3 -I "$HERE/build.py" "$HERE/fixtures/nick-v1.0" "$WORK/out"
cmp "$ROOT/workflows/four-reviews-demo-v1.0.json" "$HERE/fixtures/nick-v1.0/four-reviews-demo.json"
echo "PASS shipped four-reviews-demo-v1.0.json is Nick's v1.0 demo, byte for byte"
for f in "$ROOT"/workflows/four-reviews-connection-template-*.json; do
  b="$(basename "$f")"
  python3 -I - "$f" "$WORK/out/$b" <<'PY'
import json,sys
strip=lambda w:[{k:v for k,v in n.items() if k!="id"} for n in w["nodes"]]
a,b=(json.load(open(p)) for p in sys.argv[1:])
assert strip(a)==strip(b) and a["connections"]==b["connections"], "shipped workflow differs from build: "+sys.argv[1]
print("PASS shipped "+sys.argv[1].split("/")[-1]+" matches a fresh build (node ids aside)")
PY
done
[ -d "$HERE/node_modules/luxon" ] || (cd "$HERE" && npm install --silent --no-save luxon@3.5.0)
(cd "$HERE" && node test.js "$WORK/out" "$HERE/fixtures/nick-v1.0" "$WORK/samples")
(cd "$WORK" && python3 -I "$HERE/static.py")
