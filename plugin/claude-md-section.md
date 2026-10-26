

---

## Reporting agent

<!-- Added by the reporting-agent plugin. Edit freely. -->

**Weekly reviews, read in this OS.** Your own n8n workflow, built from Nick Christensen's demo one review at a time, writes a report per review each run: executive (sales, refunds, orders), marketing sources (which recorded sources are tied to sales, and how much has no source), products (what sold), website traffic (GA4) and, if you add them, email, trends and an AI summary. It writes them as dated Markdown files, collects them, and delivers them by Slack or Microsoft Teams, email, or a GitHub pull request. Claude reads them here and helps decide what to check next. The numbers come from deterministic code in n8n, not from an AI model. The optional AI summary only narrates numbers the workflow computed. Nick's ads review is a separate workflow that writes its report in the same format.

| Folder | What goes in it |
|---|---|
| `projects/reporting-agent/` | The project file (your settings, your outputs, your build progress) and `n8n/`: Nick's v2 demo on made-up data, where you start; two worked examples of how Hesh took it to a working version (on WooCommerce, and the same build on Metorik), to copy pieces from; and Nick's ads review. Your own workflows live in your n8n. |
| `raw/performance/reporting-agent/` | The saved reports, one file per review per run. Kept out of git, because real reports hold revenue. |

| Command | What it does |
|---|---|
| `/reporting-agent:build-reporting-demo` | Builds Nick's v2 demo in your n8n and runs it on made-up data; your task is to get the reviews to Slack (a message to yourself), or to email and into this OS. |
| `/reporting-agent:build-reporting-agent [step]` | Builds your own version from a copy of the demo: GA4, your store or CRM, an optional email review, extras, then the outputs, each review run with delivery off and reconciled against a number you trust. |
| `/reporting-agent:build-reporting-agent-ads [step]` | Builds Nick's ads review as its own workflow, on his sample data first, then on your ad accounts. |
| `/reporting-agent:get-email-reports [save\|read]` | Saves the reports from the latest emails into `raw/performance/reporting-agent/`, then reads them with you. Also reads reports merged in from a GitHub pull request. |
| `/reporting-agent:how-to-build-yourself [tour\|story\|scratch\|edit]` | Explains every node, tells how the worked examples were built in stages with Claude and the n8n MCP, and helps you build from scratch or change one branch. |

Every build command first checks this folder's setup and that n8n is connected to Claude through n8n's MCP connector, and fixes either before anything else.

**Rules for the reports:**
- **Quote, never recalculate.** A figure in a readout is copied from a report file. Missing data, "unavailable" and INCOMPLETE are never read as zero. A number in the AI summary is checked against its report before it is repeated.
- **Facts, hypotheses and missing data stay apart** in every readout.
- **Real reports stay local.** Do not paste real revenue into chat, a project file, a commit or a screenshot you share. For review, share the made-up demo reports, or a screenshot with figures hidden.
- **Secrets live in n8n only.** API keys, tokens and passwords go into n8n's credential screens, never into chat or a file here.
- **Your own folder names.** If `.claude/folders.json` exists, the folders above are read at their mapped names.
