# Notes for Nick (0.3.0)

Three proposals from testing the module end to end. None of them is built into the demo; your v1.0 demo ships unchanged.

1. **Your ad monitoring flow as a branch, shipped switched off.** It would sit in the connection template next to the four reviews, with its own INCOMPLETE path and its own file in Collect, so attendees who run ads can switch it on and everyone else ignores it. Is it worth adding, and which parts would you keep for a workshop?

2. **A Customer.io email branch, also switched off.** Campaign performance (sent, delivered, human opens and clicks, conversions), unsubscribes, and email capture, this week against last, built with the same pattern as the other lanes. Email capture is the net growth of a segment you choose, because Customer.io's App API cannot count people by the date they were created. It is in the full template now (`four-reviews-connection-template-v1.2.json`), off by default, and was tested on a live workspace. Would you keep these measures, or pick others?

3. **Node groups to make the canvas less daunting.** The template has grown (trends, history, AI summary, Customer.io). n8n can group a lane's nodes into one box and collapse it. Collapsed, the canvas would read as a handful of blocks (Settings, the reviews, Collect, Trends and summary, delivery), and the workshop could open one block at a time and explain it step by step. Frames are in place today; groups would replace them once we confirm how n8n exports them.

Also changed in 0.3.0, for your review: the demo is back to your v1.0, and every upgrade lives in the templates only: the full template (v1.2, WooCommerce, Customer.io, GA4, trends and AI summary) and the Metorik template (v1.1). See CHANGES-v1.1.md, section 0.3.0.
