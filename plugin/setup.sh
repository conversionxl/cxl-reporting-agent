#!/usr/bin/env bash
# Adds the Reporting agent module to a personal OS folder (default: the current
# folder): gitignore block first, then the project file and the n8n workflows,
# then the CLAUDE.md section. Never overwrites a file that already exists.
set -e
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TARGET="${1:-$PWD}"
cd "$TARGET"
# A folder map (.claude/folders.json) sends each file to the user's own folder;
# without one, every path below is the standard one.
. "$ROOT/.claude/hooks/lib-folders.sh"
mp() { pos_map_path "$PWD" "$1"; }
project="$(mp projects/reporting-agent)"
reports="$(mp raw/performance/reporting-agent)"

# No personal OS here? Start a minimal CLAUDE.md so the module still works.
if [ ! -f CLAUDE.md ]; then
  printf '# CLAUDE.md\n\nInstructions Claude reads in this folder.\n' > CLAUDE.md
  cm_new="created (no personal OS here; the Reporting agent works on its own)"
fi

# 1. Reports hold revenue: the gitignore block goes in BEFORE the reports folder exists.
touch .gitignore
if ! grep -qx 'raw/performance/\*' .gitignore; then
  printf '\n' >> .gitignore
  cat "$ROOT/plugin/gitignore-block.txt" >> .gitignore
  gi="added"
else
  gi="already there"
fi
# Renamed folders get the same local-only rules, before any file lands in them.
[ -f .claude/folders.json ] && map_gi="$(bash "$ROOT/.claude/hooks/folder-map.sh" gitignore "$PWD")"

# 2. Module files, skipping anything that exists.
created=0; kept=0
copy_file() {
  if [ -e "$2" ]; then kept=$((kept+1)); return; fi
  mkdir -p "$(dirname "$2")"
  cp "$1" "$2"
  created=$((created+1))
}
copy_file "$ROOT/template/projects/reporting-agent/reporting-agent.md" "$project/reporting-agent.md"
for f in "$ROOT"/workflows/*.json; do
  copy_file "$f" "$project/n8n/$(basename "$f")"
done
mkdir -p "$reports"

# 3. The Reporting agent section in CLAUDE.md, once.
if grep -q '^## Reporting agent' CLAUDE.md; then
  cm="already there"
else
  cat "$ROOT/plugin/claude-md-section.md" >> CLAUDE.md
  cm="added"
fi

echo "Folder: $TARGET"
echo ".gitignore block: $gi"
echo "Files created: $created. Existing files kept: $kept."
[ -n "${map_gi:-}" ] && echo "$map_gi"
[ -n "${cm_new:-}" ] && echo "CLAUDE.md: $cm_new"
echo "CLAUDE.md Reporting agent section: $cm"
echo "Project file: ${project#"$PWD"/}/reporting-agent.md"
echo "n8n workflows to import: ${project#"$PWD"/}/n8n/"
echo "Saved reports (stay on this computer): ${reports#"$PWD"/}/"
if git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  probe="$reports/probe-$$.md"; : > "$probe"
  if git check-ignore -q "$probe"; then echo "Check: saved reports are ignored by git."; else echo "WARNING: saved reports would be tracked by git. Check .gitignore before saving real reports."; fi
  rm -f "$probe"
fi
echo
echo "Next: the walkthrough continues with n8n (step 2 of /reporting-agent:build-reporting-agent)."
