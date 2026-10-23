# Report contract: what each review needs from your data

Each review's code (the "Compose review" node) reads its data from nodes it finds **by name**, and expects one fixed format. The demo's made-up data nodes show that format exactly. To use your own store or CRM, keep each node **name** and make the node output this format. Everything after it (the report, the Markdown file, delivery) then works unchanged.

**The pattern for your own data:** add a node that fetches your data (an app node such as Shopify or HubSpot, or an HTTP Request), rename it to describe your source, then add a Code node right after it that converts the response into the format below. That Code node takes the **original name** (for example `Executive | Current revenue`), because the review code looks it up by that name. `/reporting-agent:build-reporting-agent` step 7 does this with you: you paste a small sample of your data, with names and emails removed, and Claude writes the Code node.

Dates: each lane's `Reporting period` node gives `start`, `end`, `previousStart`, `previousEnd` (ISO dates, last 7 completed days and the 7 before, in the Settings timezone). Fetch exactly those ranges.

If a node fails or returns the wrong shape, that review becomes an INCOMPLETE report that names the step and the reason. That is a valid demo result.

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

The traffic lane uses the GA4 Data API response as it comes (`batchRunReports`, four reports: totals, source and medium, landing pages, events). Connect GA4 in the connection template; no conversion step is needed.

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
