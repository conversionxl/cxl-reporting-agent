# Source of this fixture

`starter-workflow.json` is Nick Christensen's ads reporting starter from his CXL workshop "Ship ICP-driven ad campaigns and automated monitoring" (29 June 2026), copied unchanged from:

https://github.com/nickyc1/ship-icp-ads-automate-monitoring/blob/8ae3c7c7748103e9a22d154c19bcbbc42ebccf9d/n8n-ads-reporting/starter-workflow.json

It is MIT licensed (see `LICENSE` in this folder, copied from the same repository). `tests/build.py` turns it into lane 6, the Ads review, in both example workflows: the two sample-data nodes, the merge and the Analyze code are carried unchanged under a credit header; the schedule trigger, the Slack webhook and the email node are left out because the collection report delivers instead.
