

---

## Reporting agent

<!-- Added by /reporting-agent:build-reporting-agent. Edit freely. -->

**Weekly reviews, read in this OS.** An n8n workflow builds a report per review each run: executive (sales, refunds, orders), marketing sources (which recorded sources are tied to sales, and how much has no source), products (what sold), website traffic (GA4) and, in the full template, email (Customer.io), plus trends and an AI summary. It writes them as dated Markdown files, collects them, and delivers them by email, a GitHub pull request, or Slack. Claude reads them here and helps decide what to check next. The numbers come from deterministic code in n8n, not from an AI model. The optional AI summary only narrates numbers the workflow computed.

| Folder | What goes in it |
|---|---|
| `projects/reporting-agent/` | The project file (your settings, which delivery you use, your demo progress) and `n8n/`, the workflows to import: Nick's demo with made-up data, the full template for your own data (WooCommerce, GA4, Customer.io, trends, AI summary, delivery), and a Metorik template for stores on Metorik. |
| `raw/performance/reporting-agent/` | The saved reports, one file per review per run. Kept out of git, because real reports hold revenue. |

| Command | What it does |
|---|---|
| `/reporting-agent:build-reporting-agent [step]` | Sets the module up, then walks you through n8n one step at a time: import, run the demo, choose a delivery, connect your own store or CRM, GA4. |
| `/reporting-agent:how-to-build-yourself [tour\|scratch\|edit]` | Explains every node and branch, how it was built in stages with Claude and the n8n MCP, and helps you build from scratch or change one branch. |
| `/reporting-agent:get-email-reports [save\|read]` | Saves the reports from the latest emails into `raw/performance/reporting-agent/`, then reads them with you. Also reads reports merged in from a GitHub pull request. |

**Rules for the reports:**
- **Quote, never recalculate.** A figure in a readout is copied from a report file. Missing data, "unavailable" and INCOMPLETE are never read as zero. A number in the AI summary is checked against its report before it is repeated.
- **Facts, hypotheses and missing data stay apart** in every readout.
- **Real reports stay local.** Do not paste real revenue into chat, a project file, a commit or a screenshot you share. For review, share the made-up demo reports, or a screenshot with figures hidden.
- **Secrets live in n8n only.** API keys, tokens and passwords go into n8n's credential screens, never into chat or a file here.
- **Your own folder names.** If `.claude/folders.json` exists, the folders above are read at their mapped names.
