# Metric limits: what the four reviews cannot tell you

From Nick Christensen's workshop handoff (22 October 2026). Read this before explaining any number in a review, and say these limits out loud when they apply.

- **Definitions follow the source.** Gross, net, refund and tax definitions come from your store or CRM. Reconcile them before using another source. Do not subtract discounts twice.
- **Non-renewal revenue is not first-time buyer revenue.**
- **Order-source attribution is not incrementality,** GA4 session attribution or platform ROAS. Orders with no recorded source are not "Direct".
- **Product order counts can overlap** in multi-product baskets. A plan purchase does not tell you which course caused it.
- **Product publication status does not prove that checkout works.**
- **COGS, gross profit, operating income, net profit, marketing spend and MER** stay unavailable until cost and spend sources are added. Missing costs are not zero.
- **GA4:** sessions by source use session attribution. Event counts are not unique customers, and GA4 is not the financial source of truth. Recent days can still be incomplete. Reports flag thresholding, sampling and aggregated rows when GA4 returns them; no flag does not guarantee complete tracking.
- **The interpretation in each report is deterministic code,** not an AI analysis. Claude's readout in your OS comes after, and keeps facts, hypotheses and missing data apart.

## Privacy

Live requests put real financial data into n8n's node outputs and execution history. Hiding or scaling the final report is not enough. Use the made-up demo while screen sharing. For a live demonstration, use a sandbox store with invented orders, or connect privately and return to the demo for teaching.
