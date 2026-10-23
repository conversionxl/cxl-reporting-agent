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
- **The AI summary narrates; it does not calculate.** Month over month and quarter over quarter are computed in a Code node from the store source and handed to the model with the reports. The model may only repeat those numbers, must label hypotheses, and must call missing data missing. Trends across runs need at least three saved runs. Check a number in the summary against its report before acting on it.
- **Month and quarter windows are rolling 30 and 90 days**, not calendar months or quarters, and they come from the same source and rules as the executive review.
- **Customer.io metrics are message events,** not people: opens are inflated by privacy features, and email capture counts new profiles with an email, not new customers.

## Privacy

Live requests put real financial data into n8n's node outputs and execution history. Hiding or scaling the final report is not enough. Use the made-up demo while screen sharing. For a live demonstration, use a sandbox store with invented orders, or connect privately and return to the demo for teaching.
