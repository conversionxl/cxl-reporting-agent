# Report contract: what each review needs from your data

Each review's code (the "Compose review" node) reads its data from nodes it finds **by name**, and expects one fixed format. The demo's made-up data nodes show that format exactly. To use your own store or CRM, keep each node **name** and make the node output this format. Everything after it (the report, the Markdown file, delivery) then works unchanged.

**The pattern for your own data:** add a node that fetches your data (an app node such as Shopify or HubSpot, or an HTTP Request), rename it to describe your source, then add a Code node right after it that converts the response into the format below. That Code node takes the **original name** (for example `Executive | Current revenue`), because the review code looks it up by that name. `/reporting-agent:build-reporting-agent` step 7 does this with you: you paste a small sample of your data, with names and emails removed, and Claude writes the Code node.

Dates: each lane's `Reporting period` node gives `start`, `end`, `previousStart`, `previousEnd` (ISO dates, last 7 completed days and the 7 before, in the Settings timezone). Fetch exactly those ranges.

If a node fails or returns the wrong shape, that review becomes an INCOMPLETE report that names the step and the reason. That is a valid demo result.

## Switching sources: guardrails

Every one of these came from a real switch (Metorik to WooCommerce, October 2026) that produced wrong numbers **without any error**. They apply to any translation: Shopify, Stripe, HubSpot, a spreadsheet, another store.

1. **Reconcile one week before you trust it.** Put orders, gross, refunds and net next to the same week in the source you trust today. Within about 1% is a pass. A bigger gap has a cause; find it first. A review that runs is not a review that is right.
2. **A zero next to activity is a broken source, not zero sales.** If sales or orders come back 0 while the same response, or another source, shows customers, sessions or sign-ups, treat the source as broken and make the conversion step throw, so the review goes INCOMPLETE.
3. **One currency.** Every amount must be in the Settings currency. Multi-currency stores keep a converted amount per order (WooCommerce plugins store base-currency fields); use the source's own converted amount, never the face value, and throw when it is missing rather than guess a rate.
4. **Decide which states count, and write down how refunds are dated.** Include refunded and partly refunded orders on purpose, or gross and refunds drift from the old source. Say in `refundNote` whether refunds count on the day they happen (refund date) or against the original order (order date); the two give different weeks.
5. **Distrust summary endpoints.** "Reports" and "analytics" endpoints can be stale, disabled, or blind to newer storage, and still answer with a 200. Prefer the raw records (orders, charges, deals) summed in a Code node, with a check that throws when an expected field is missing.
6. **Page through everything, and flag truncation.** Fetch every page until an empty one. If a page limit is hit, say so on the report instead of reporting a partial total.
7. **Ask for the fields you need, nothing more.** Limit the response to money fields and identifiers (`_fields` on WooCommerce). It keeps customer names and emails out of n8n's execution history and keeps runs fast.
8. **The report names the real source.** Set `sourceLabel` (and `refundNote`) in Settings, so no report says "Metorik" when the numbers came from somewhere else. A reader, or the AI summary, will otherwise compare it with the wrong thing.
9. **Totals reconcile across tools; attribution does not.** Orders, gross, refunds and net should match the old source. Sources by order will not: each tool records attribution its own way and covers a different share of orders (WooCommerce's order attribution recorded a source on far more orders than Metorik's source report for the same week). Compare the rows both tools have; never "fix" one tool's attribution to match the other.
10. **Compare like with like.** Group products the way the old source does before comparing (Metorik ranks by parent product, so a per-variation list will not line up), and match its definition of net (tax excluded, refunds taken off).
11. **A switched-off source is not zero.** A disabled request node in n8n passes its input through, which a sum reads as "no orders". Make the conversion step throw when its input is not the source's data, so the review goes INCOMPLETE; keep "Always Output Data" on the request, so a connected store with a genuinely empty week reports a true zero.

## WooCommerce mapping

Read `wc/v3/orders` with statuses `processing,completed,refunded`, `per_page=100`, pagination until empty, and `_fields=id,status,currency,total,total_tax,shipping_total,discount_total,refunds,line_items,meta_data`. Sum in a Code node. Do not use `wc/v3/reports/sales` (returned zeros on a store with the new order storage) or `wc-analytics` (absent when WooCommerce Analytics is off).

| Contract field | WooCommerce, order in the Settings currency | WooCommerce, order in another currency |
|---|---|---|
| `totals.gross` | sum of `total` | sum of meta `_order_total_base_currency` |
| `totals.taxes` | sum of `total_tax` | sum of meta `_order_tax_base_currency` |
| `totals.discounts` | sum of `discount_total` | sum of meta `_cart_discount_base_currency` |
| `totals.refunds` | sum of the absolute `refunds[].total` | the same, times meta `_base_currency_exchange_rate` |
| `totals.orders` | number of orders | same |
| `totals.items` | sum of `line_items[].quantity` | same |
| `totals.net` | gross minus taxes, shipping (`shipping_total`) and refunds | the same, with `_order_shipping_base_currency` |

Refunds then count against the order they belong to (order date): say so in `refundNote`. The meta key names come from the store's multi-currency plugin; check one foreign-currency order before relying on them.

The WooCommerce worked example (`four-reviews-connection-template-v1.2.json`) does this for all three store reviews:

| Review | WooCommerce source | Contract node |
|---|---|---|
| Marketing | the week's orders, `_fields` with `meta_data`: `_wc_order_attribution_utm_source` and `_wc_order_attribution_utm_medium` (medium `(not set)` when absent) | `Marketing \| Order sources` rows per source and medium, net per order as above; orders without a `utm_source` are left out, so the review counts them as not represented |
| Products | the week's orders with `line_items` and `refunds`, then `wc/v3/products?include=<ids>&_fields=id,name,status,type,permalink` | `Products \| Top products`: grouped by parent `product_id`, net sales = line totals (tax excluded) minus each order's refunds shared by line value, converted with the order's exchange rate |
| Trends | every paid or refunded order in the last 180 days, with `date_created` | windows summed in code: last 30 vs prior 30 and last 90 vs prior 90 |

In the Metorik template, Trends reads four Metorik revenue reports instead (`revenue-by-date` for the last 30, prior 30, last 90 and prior 90 days), through `.totals.net` and `.totals.orders` only. Any missing total makes Trends report itself unavailable, never zero.

## Executive review

| Node name (keep it) | Output (one item) | Notes |
|---|---|---|
| `Executive \| Verify store` | `{ name, currency, timezone }` | Checked against Settings `storeName`, `currency`, `timeZone`. Without a store record, return the Settings values from a Code node. |
| `Executive \| Current revenue` | `{ totals: { net, gross, refunds, taxes, orders, items, discounts } }` | Numbers, for the current 7 days. `net` is required. The report prints all seven fields, so a missing one shows as "NaN": include each, with 0 only when 0 is true. |
| `Executive \| Previous revenue` | same shape | For the previous 7 days. |
| `Executive \| Order types` | `{ data: [ { grouped_by, net } ] }` | One row per order type. `grouped_by: null` is shown as "Non-renewal orders". |

## Marketing source review

| Node name (keep it) | Output (one item) | Notes |
|---|---|---|
| `Marketing \| Verify store` | `{ name, currency, timezone }` | As above. |
| `Marketing \| Order sources` | `{ data: [ { utm_source, utm_medium, count, net } ] }` | One row per recorded source and medium, current 7 days. Orders with no source are left out: the report counts them as "not represented". |
| `Marketing \| All orders` | `{ totals: { orders, net } }` | All orders in the current 7 days, so the report can show how much has no source. |

## Top product review

| Node name (keep it) | Output (one item) | Notes |
|---|---|---|
| `Products \| Verify store` | `{ name, currency, timezone }` | As above. |
| `Products \| Top products` | `{ data: [ { title, net_sales, net_orders, net_items_sold, status, type, permalink } ] }` | Sorted by `net_sales`, highest first, up to 10 rows. `status`, `type` and `permalink` may be empty. |

## Website traffic review

The traffic lane uses the GA4 Data API response as it comes (`batchRunReports`, four reports: totals, source and medium, landing pages, events). Connect GA4 on the traffic lane's request node; no conversion step is needed. A Google Service Account credential (predefined type `googleApi`, scope `analytics.readonly`, its email a Viewer on the property) is the simplest login; a Search Console login has no Analytics access.

## Email review (Customer.io, both worked examples)

The Customer.io App API (`cioApiUrl` in Settings) gives each running campaign's and each recent broadcast's daily metrics (`/v1/campaigns/{id}/metrics`, `/v1/newsletters/{id}/metrics`, `period=days&steps=15`). The series end with today, which is partial: the review sums the 7 complete days before it against the 7 before those, in UTC. Fields used: `sent`, `delivered`, `human_opened`, `human_clicked`, `converted`, `unsubscribed`, `topic_unsubscribed`, `bounced`, `spammed`. Counts are messages, not people. Email capture is a segment's size (`/v1/segments/{id}/customer_count`, the segment set in `cioCaptureSegmentId`) against the last saved week in the history table, so it is net growth; the App API cannot count people by the date they were created.

## Ads review (its own workflow, from Nick Christensen's ads starter)

The ads review is not a lane of the weekly reviews: it is its own workflow, `ads-review-from-nick-v1.json` (`/reporting-agent:build-reporting-agent-ads`), a daily read of yesterday that writes `ads-<date>-to-<date>.md` in the same report format. Each ad row, one per campaign, from any platform: `{ campaign, platform, spend, conversions, conversion_value, cpa, historical_cpa, ctr, clicks, impressions }` (`frequency` too for Meta). `platform` is `google`, `meta` or another platform's name in lower case, and picks the target in `TARGET` at the top of **Ads | Analyze** (Google 1.5x and Meta 0.5x value-to-spend in Nick's example, 1.0 for a platform not listed: set them from your margins). Analyze returns `{ digest, campaign_count, flagged }`; Compose review wraps the digest into the report. The two sample nodes, `Ads | Google Ads (sample data)` and `Ads | Meta Ads (sample data)`, emit Nick's example rows; replace them with your own nodes, named `Ads | Google Ads` and `Ads | Meta Ads` (any name without "(sample data)"), producing the same fields, and the SAMPLE DATA label goes away by itself. A row missing a field throws, so the review goes INCOMPLETE instead of grading on gaps. Platform-reported conversion value is not profit, and the platforms' attribution won't match your store's: reconcile spend and conversions against each ad platform, not revenue against the store.

## Mapping a CRM instead of a store

The reports say "orders" and "products". For a B2B CRM the closest mapping is below. These labels are a starting point to agree with Nick, not a standard. **(inferred)**

| Contract field | Store meaning | CRM meaning (for example HubSpot) |
|---|---|---|
| `totals.net` | Net sales | Closed-won amount in the period |
| `totals.orders` | Orders | Deals won |
| `totals.refunds` | Refunds | 0, or lost or churned amount if you track it; say which in the log |
| Order types `grouped_by` | Renewal vs new | Deal type: new business vs renewal or expansion |
| Order sources | UTM source and medium on the order | Original source on the contact or deal |
| Top products | Products by net sales | Products or line items on won deals, or deal pipelines |

Never fill a field with a made-up number to make the report run. Leave it out, or return 0 only when 0 is true, and note it in the project file's log.
