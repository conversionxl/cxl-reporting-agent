---
type: project
status: active
priority: P2
cadence: Weekly
next_action: "Run /reporting-agent:build-reporting-demo and do the demo task"
tags: [reporting-agent, n8n, weekly-report]
---

# Reporting agent

Weekly reviews built in n8n, from Nick's v2 demo to your own stack one review at a time, and read here: executive, marketing sources, products, website traffic, and optionally email, trends and an AI summary. Nick's ads review runs as its own workflow.

## My setup

Filled in as you go through the build commands. No keys, tokens or passwords here: those live in n8n.

| Setting | Value |
|---|---|
| n8n | Cloud or self-hosted, and its address: |
| n8n connected to Claude (MCP) | yes / not yet |
| Demo task | Slack / email |
| GA4 | property connected / not yet / none |
| Store or CRM | Shopify, WooCommerce, Stripe, HubSpot, Metorik, other, spreadsheet: |
| Currency and timezone | |
| Source label on the reports | |
| Email platform (email review) | Customer.io / Klaviyo / Mailchimp / HubSpot / ActiveCampaign / Brevo / other / none: |
| Extras on | trends / run history / AI summary |
| Outputs | Slack / Microsoft Teams / email / GitHub pull request (private repo only) |
| Ads review | sample data / Meta / Google Ads / other: |

## Progress

**Demo** (`/reporting-agent:build-reporting-demo`)
- [ ] Demo built and run (four reviews and a week at a glance)
- [ ] Demo task done: reviews in Slack, or by email and saved into this OS
- [ ] AI summary switched on (optional)

**Your agent** (`/reporting-agent:build-reporting-agent`)
- [ ] My own copy of the demo
- [ ] GA4 reconciled
- [ ] Executive review on my own store or CRM, reconciled against a number I trust (or a screenshot of where it failed)
- [ ] Sources and products reconciled
- [ ] Email review (optional)
- [ ] Trends, history and AI summary (optional)
- [ ] Outputs set and tested
- [ ] One live run, then outputs off for tests
- [ ] Demo posted for review

**Ads review** (`/reporting-agent:build-reporting-agent-ads`, optional)
- [ ] Ads review built and run on Nick's sample data
- [ ] My ad accounts connected and reconciled
- [ ] Delivered, and the schedule on

## Log

Dated notes on runs, fixes and decisions. Never paste real revenue figures here.
