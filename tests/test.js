const fs = require('fs');
const { run } = require('./run');
const [OUT, SRC, SAMPLES] = process.argv.slice(2);
const demo = `${__dirname}/../workflows/four-reviews-demo-v1.0.json`, tmpl = `${OUT}/four-reviews-metorik-template-v1.1.json`, full = `${OUT}/four-reviews-connection-template-v1.2.json`;
let failures = 0;
const ok = (cond, msg) => { console.log((cond ? 'PASS ' : 'FAIL ') + msg); if (!cond) failures++; };
const byName = items => Object.fromEntries(items.map(i => [i.json.fileName, i.json.markdown]));
const decoded = i => Buffer.from(i.binary.report.data, 'base64').toString('utf8');

(async () => {
  const demoWf = JSON.parse(fs.readFileSync(`${SRC}/four-reviews-demo.json`, "utf8")); // Nick's original fixtures as stand-in API responses
  const fixtureNames = ['Executive | Verify store', 'Executive | Current revenue', 'Executive | Previous revenue', 'Executive | Order types',
    'Marketing | Verify store', 'Marketing | Order sources', 'Marketing | All orders', 'Products | Verify store', 'Products | Top products'];
  const fixtures = Object.fromEntries(fixtureNames.map(n => [n, demoWf.nodes.find(x => x.name === n).parameters.jsCode]));
  fixtures['Traffic | Connect GA4 - enable after setup'] = demoWf.nodes.find(x => x.name === 'Traffic | Synthetic GA4 response').parameters.jsCode;

  // Template runs with the demo's made-up data standing in for the API responses, Verify store echoing Settings
  const echoStore = lane => `const p=$('${lane} | Reporting period').first().json;return [{json:{name:p.storeName,currency:p.currency,timezone:p.timeZone}}];`;
  const anyStore = { ...fixtures, 'Executive | Verify store': echoStore('Executive'), 'Marketing | Verify store': echoStore('Marketing'), 'Products | Verify store': echoStore('Products') };

  console.log('\n== T1 demo (Nick\'s v1.0, unchanged): each lane matches Nick\'s examples');
  let r = await run(demo);
  ok(!r.errors.length, 'no errors ' + r.errors.join('; '));
  const lanes = ['Executive', 'Marketing', 'Products', 'Traffic'].map(l => r.runData[`${l} | Create Markdown BEFORE Slack`]?.[0]);
  ok(lanes.every(Boolean), 'all four lanes wrote a Markdown file');
  ok(!r.nodes['Settings'] && !r.nodes['Collect all four reports'] && !Object.values(r.nodes).some(n => n.name.startsWith('Deliver |')), 'no Settings, no Collect, no delivery branch');
  ok(Object.values(r.nodes).filter(n => n.type === 'n8n-nodes-base.slack').every(n => n.disabled), 'the per-lane Slack nodes ship switched off');
  const m = Object.fromEntries(lanes.map(i => [i.json.fileName, i.json.markdown]));
  for (const lane of ['executive', 'marketing', 'products']) {
    const nick = fs.readFileSync(`${SRC}/${lane}-example.md`, 'utf8');
    ok(m[`${lane}-2026-10-14-to-2026-10-20.md`] === nick, `${lane} report identical to Nick's example`);
  }
  ok(m['website-traffic-review.md'] === fs.readFileSync(`${SRC}/traffic-example.md`, 'utf8'), 'traffic report identical to Nick\'s example');
  ok(lanes.every(i => decoded(i) === i.json.markdown), 'binary report matches markdown for all 4');
  fs.mkdirSync(SAMPLES, { recursive: true });
  for (const [f, md] of Object.entries(m)) fs.writeFileSync(`${SAMPLES}/${f}`, md);

  console.log('\n== T1c template, sources connected, deliveries recorded');
  r = await run(tmpl, { deliver: true, fixtures, settings: { storeName: 'Demo Store' } });
  ok(!r.errors.length, 'no errors ' + r.errors.join('; '));
  ok(r.merged.length === 4 && !r.merged.some(i => i.json.incomplete), 'merge collected 4 complete reports');
  const tm = byName(r.merged);
  ok(JSON.stringify(Object.keys(tm)) === JSON.stringify(['executive-2026-10-14-to-2026-10-20.md', 'marketing-2026-10-14-to-2026-10-20.md', 'products-2026-10-14-to-2026-10-20.md', 'traffic-2026-10-14-to-2026-10-20.md']), 'dated file names: ' + Object.keys(tm).join(', '));
  ok(r.merged.every(i => decoded(i) === i.json.markdown), 'binary report matches markdown for all 4');
  ok(r.delivered.slack.length === 4 && r.delivered.slack.every(s => s.channel === 'SELECT_YOUR_TEST_CHANNEL'), 'Slack would post 4 messages to the placeholder channel');
  const sl = r.delivered.slack;
  ok(sl[0].text.includes('*Executive business review*') && sl[3].text.startsWith('🌐 *Website traffic review*'), 'Slack titles carry an emoji and bold');
  ok(sl.every(m => !m.text.split('\n').some(l => l.startsWith('|') || l.startsWith('#'))), 'no Markdown tables or headings left in Slack text');
  ok(sl.every(m => m.text.includes('------------------------------')) && sl[0].text.includes('• *Net revenue:* $24,000'), 'dashed separators and bold labels');
  ok(sl[3].text.includes('• *google / organic* · Sessions 5000 · Previous 4200 · Change 19.0% · Engagement 65.0%'), 'traffic table rows become bullet lines');
  ok(!sl[0].text.includes('Open the workflow') && !r.delivered.email[0].body.includes('Workflow:'), 'no workflow links while n8nUrl is the placeholder');
  ok(r.nodes['Deliver | Slack'].parameters.otherOptions.includeLinkToWorkflow === false, 'Slack\'s own n8n attribution link is off');
  ok(r.delivered.github.length === 4 && r.delivered.github[0].path === 'projects/reporting-agent/reports/executive-2026-10-14-to-2026-10-20.md' && r.delivered.github[0].owner === 'YOUR_GITHUB_USERNAME', 'GitHub paths and owner from Settings: ' + r.delivered.github[0].path);
  ok(r.delivered.github.every((g, i) => g.bytes === r.merged[i].json.markdown), 'GitHub commits the exact report text');
  const api = r.delivered.api, br = 'reports/2026-10-21-run-8200';
  ok(api.length === 3 && api[0].method === 'GET' && api[0].url === 'https://api.github.com/repos/YOUR_GITHUB_USERNAME/YOUR_PERSONAL_OS_REPO/git/ref/heads/main', 'reads base branch: ' + (api[0] && api[0].url));
  ok(api[1].url.endsWith('/git/refs') && api[1].body.ref === 'refs/heads/' + br && api[1].body.sha === 'abc123', 'creates branch ' + api[1].body.ref);
  ok(r.delivered.github.every(g => g.branch === br), 'all 4 commits go to the new branch, none to main');
  ok(api[2].url.endsWith('/pulls') && api[2].body.head === br && api[2].body.base === 'main' && api[2].body.title === 'Weekly reports 2026-10-21', 'opens one PR into main: ' + api[2].body.title);
  const em = r.delivered.email;
  ok(em.length === 1 && em[0].to === 'YOU@EXAMPLE.COM' && em[0].attachments.length === 4, 'one email, 4 attachments: ' + (em[0] && em[0].subject));
  ok((em[0].body.match(/-----BEGIN REPORT /g) || []).length === 4 && em[0].body.includes(tm['executive-2026-10-14-to-2026-10-20.md']), 'email body holds all 4 reports between markers');
  const wrapped = em[0].body.replace(/(.{60})/g, '$1\n');  // simulate Gmail hard-wrapping every line
  const files = [...wrapped.matchAll(/-----BEGIN FILE ([^\n]+?)-----\n([\s\S]*?)-----END FILE-----/g)];
  ok(files.length === 4 && files.every(f => Buffer.from(f[2].replace(/\s+/g, ''), 'base64').toString('utf8') === tm[f[1].replace(/\s+/g, '')]), 'exact copies decode byte-identical even after line wrapping');
  fs.writeFileSync(`${SAMPLES}/email-body-example.txt`, `Subject: ${em[0].subject}\n\n${em[0].body}`);

  console.log('\n== T1b links when n8nUrl is set');
  r = await run(tmpl, { deliver: true, fixtures, settings: { storeName: 'Demo Store', n8nUrl: 'https://acme.app.n8n.cloud/' } });
  ok(r.delivered.email[0].body.includes('Workflow: https://acme.app.n8n.cloud/workflow/wf123\nThis run: https://acme.app.n8n.cloud/workflow/wf123/executions/8200'), 'email links to the workflow and the run');
  ok(r.delivered.slack[0].text.endsWith('<https://acme.app.n8n.cloud/workflow/wf123|Open the workflow> · <https://acme.app.n8n.cloud/workflow/wf123/executions/8200|This run>'), 'Slack links to the workflow and the run');
  ok(r.merged.every(i => i.json.markdown === tm[i.json.fileName]), 'the Markdown reports are unchanged by the Slack formatting');

  console.log('\n== T2 template with EUR, Europe/Tallinn, de-DE');
  r = await run(tmpl, { fixtures: anyStore, settings: { storeName: 'Demo Store', currency: 'EUR', timeZone: 'Europe/Tallinn', locale: 'de-DE' } });
  ok(!r.errors.length && r.merged.length === 4 && !r.merged.some(i => i.json.incomplete), 'all 4 complete');
  const ex = r.merged[0].json.markdown;
  ok(ex.replace(/\u00a0/g,' ').includes('24.000 €') && ex.includes('| EUR | Europe/Tallinn'), 'euro formatting and labels: ' + ex.split('\n').slice(1, 5).join(' / '));
  ok(r.merged[3].json.markdown.includes('(Europe/Tallinn)'), 'traffic uses the Settings timezone');

  console.log('\n== T3 template before setup (sources switched off)');
  r = await run(tmpl, { deliver: true });
  ok(!r.errors.length, 'run does not stop ' + r.errors.join('; '));
  ok(r.merged.length === 4 && r.merged.every(i => i.json.incomplete), '4 INCOMPLETE reports collected');
  ok(r.merged.every(i => /-incomplete\.md$/.test(i.json.fileName)), 'incomplete file names: ' + r.merged.map(i => i.json.fileName).join(', '));
  fs.writeFileSync(`${SAMPLES}/executive-incomplete-example.md`, r.merged[0].json.markdown);
  console.log(r.merged[0].json.markdown); console.log(r.merged[3].json.markdown);
  ok(r.delivered.email[0].subject.endsWith('(incomplete)'), 'email subject flags incomplete');

  console.log('\n== T4 template with sources connected (demo data as stand-in API responses)');
  r = await run(tmpl, { fixtures, settings: { storeName: 'Demo Store' } });
  ok(!r.errors.length && r.merged.length === 4 && !r.merged.some(i => i.json.incomplete), 'all 4 complete');
  console.log(r.merged[0].json.markdown.split('\n').slice(0, 3).join('\n'));
  ok(r.merged[0].json.markdown.startsWith('PRIVATE LIVE REVIEW | Demo Store — Executive'), 'store name from Settings in the live header');

  console.log('\n== T5 template, one source fails, both error shapes');
  for (const shape of ['object', 'string']) {
    r = await run(tmpl, { fixtures, settings: { storeName: 'Demo Store' }, fail: { 'Executive | Previous revenue': 'HTTP 503 Service Unavailable' }, errorShape: shape, deliver: true });
    const inc = r.merged.filter(i => i.json.incomplete);
    ok(!r.errors.length && r.merged.length === 4 && inc.length === 1 && inc[0].json.fileName.startsWith('executive-'), `${shape}: 1 incomplete (executive), 3 complete`);
    ok(inc[0].json.markdown.includes('Failed step: Executive | Previous revenue') && inc[0].json.markdown.includes('Reason: HTTP 503'), `${shape}: names the failed step and reason`);
    ok(r.delivered.slack.length === 4, `${shape}: all 4 still delivered`);
  }

  console.log('\n== T6 wrong store name');
  r = await run(tmpl, { fixtures, settings: { storeName: 'Another Store' } });
  ok(r.merged.length === 4 && r.merged.filter(i => i.json.incomplete).length === 3, '3 store lanes incomplete, traffic complete');
  console.log(r.merged[1].json.markdown.split('\n').slice(4, 6).join('\n'));

  console.log('\n== T7 GA4 fails');
  r = await run(tmpl, { fixtures, settings: { storeName: 'Demo Store' }, fail: { 'Traffic | Connect GA4 - enable after setup': 'invalid_grant' } });
  ok(r.merged[3].json.incomplete && r.merged[3].json.fileName === 'traffic-2026-10-14-to-2026-10-20-incomplete.md', 'traffic incomplete: ' + r.merged[3].json.fileName);

  // ---- Full template (v1.2): made-up WooCommerce orders, Customer.io series and GA4 response stand in for the APIs
  const meta = o => Object.entries(o).map(([key, value]) => ({ key, value }));
  const o1 = { id: 101, status: 'completed', currency: 'USD', date_created: '2026-10-15T10:00:00', total: '1000.00', total_tax: '0.00', shipping_total: '0.00', discount_total: '50.00', refunds: [],
    line_items: [{ product_id: 11, name: 'Annual plan - Yearly', quantity: 1, total: '1000.00' }], meta_data: meta({ _wc_order_attribution_utm_source: 'google', _wc_order_attribution_utm_medium: 'organic' }) };
  const o2 = { id: 102, status: 'completed', currency: 'ALL', date_created: '2026-10-16T10:00:00', total: '50000.00', total_tax: '0.00', shipping_total: '0.00', discount_total: '0.00', refunds: [],
    line_items: [{ product_id: 12, name: 'Quarterly plan - Quarterly', quantity: 2, total: '50000.00' }],
    meta_data: meta({ _order_total_base_currency: '618.650000', _order_tax_base_currency: '0', _order_shipping_base_currency: '0', _cart_discount_base_currency: '0', _base_currency_exchange_rate: '0.012373', _wc_order_attribution_utm_source: '(direct)' }) };
  const o3 = { id: 103, status: 'refunded', currency: 'USD', date_created: '2026-10-16T11:00:00', total: '500.00', total_tax: '0.00', shipping_total: '0.00', discount_total: '0.00', refunds: [{ id: 1, total: '-500.00' }],
    line_items: [{ product_id: 11, name: 'Annual plan - Yearly', quantity: 1, total: '500.00' }], meta_data: [] };
  const o4 = { id: 104, status: 'completed', currency: 'USD', date_created: '2026-10-09T10:00:00', total: '800.00', total_tax: '0.00', shipping_total: '0.00', discount_total: '0.00', refunds: [], line_items: [], meta_data: [] };
  const o5 = { ...o4, id: 105, date_created: '2026-09-01T10:00:00', total: '400.00' }, o6 = { ...o4, id: 106, date_created: '2026-06-01T10:00:00', total: '300.00' };
  const ret = list => `return ${JSON.stringify(list)}.map(json=>({json}));`;
  const series = (prev, cur) => [999, ...prev, ...cur, 999];
  const flat = (v, n = 7) => Array(n).fill(v);
  const cio = (sentPrev, sentCur, openPrev, openCur, unsubPrev, unsubCur) => JSON.stringify({ metric: { series: {
    sent: series(sentPrev, sentCur), delivered: series(sentPrev, sentCur), human_opened: series(openPrev, openCur), human_clicked: series(flat(0), flat(0)),
    converted: series(flat(0), flat(0)), unsubscribed: series(unsubPrev, unsubCur), topic_unsubscribed: series(flat(0), flat(0)), bounced: series(flat(0), flat(0)), spammed: series(flat(0), flat(0)) } } });
  const sentAt = Date.parse('2026-10-16T12:00:00Z') / 1000;
  const fullFixtures = {
    'Executive | WooCommerce orders (current)': ret([o1, o2, o3]),
    'Executive | WooCommerce orders (previous)': ret([o4]),
    'Marketing | WooCommerce orders (current)': ret([o1, o2, o3]),
    'Products | WooCommerce orders (current)': ret([o1, o2, o3]),
    'Products | WooCommerce product details': ret([{ id: 11, name: 'Annual plan', status: 'publish', type: 'subscription', permalink: 'https://example.com/annual' },
      { id: 12, name: 'Quarterly plan', status: 'publish', type: 'subscription', permalink: 'https://example.com/quarterly' }]),
    'Trends | WooCommerce orders (180 days)': ret([o1, o3, o5, o6]),
    'Traffic | Connect GA4 - enable after setup': fixtures['Traffic | Connect GA4 - enable after setup'],
    'Customer.io | Campaigns': ret([{ campaigns: [{ id: 1, name: 'Welcome series', state: 'running', active: true, type: 'segment' }, { id: 2, name: 'Old flow', state: 'archived', active: false }] }]),
    'Customer.io | Campaign metrics': `return $input.all().map(()=>({json:${cio(flat(10), flat(20), flat(1), flat(2), [0, 0, 0, 0, 0, 0, 1], [0, 0, 0, 0, 0, 1, 1])}}));`,
    'Customer.io | Broadcasts': ret([{ newsletters: [{ id: 5, name: 'October newsletter', sent_at: sentAt }, { id: 6, name: 'Summer newsletter', sent_at: Date.parse('2026-08-01T12:00:00Z') / 1000 }] }]),
    'Customer.io | Broadcast metrics': `return $input.all().map(()=>({json:${cio(flat(0), [0, 100, 0, 0, 0, 0, 0], flat(0), [0, 30, 0, 0, 0, 0, 0], flat(0), flat(0))}}));`,
    'Customer.io | Capture count': ret([{ count: 1200 }]),
  };
  const lastWeek = [{ run_date: '2026-10-14', period_start: '2026-10-07', period_end: '2026-10-13', reviews_complete: 5, reviews_total: 5, exec_net: 800, exec_orders: 1, facts_json: JSON.stringify({ leads_email_count: 1150 }) }];
  const ai = f => `## Headline\nTest summary: ${f.reviews.complete_count} of ${f.reviews.total_count} reviews ran; history weeks ${f.history_weeks}.`;
  const fullSettings = { storeName: 'Demo Store', cioCaptureSegmentId: '42', cioCaptureLabel: 'Newsletter' };

  console.log('\n== T8 full template, every source connected (made-up data), deliveries recorded');
  r = await run(full, { deliver: true, fixtures: fullFixtures, history: lastWeek, ai, settings: fullSettings });
  ok(!r.errors.length, 'no errors ' + r.errors.join('; '));
  ok(r.merged.length === 5 && !r.merged.some(i => i.json.incomplete), 'Collect all reports holds 5 complete reviews: ' + r.merged.map(i => i.json.fileName).join(', '));
  const fm = byName(r.merged);
  const exe = fm['executive-2026-10-14-to-2026-10-20.md'];
  ok(exe.includes('• Net revenue: $1,619 (102.3% vs prior week).') && exe.includes('• Gross revenue: $2,119; refunds: $500; sales taxes: $0.') && exe.includes('• Orders: 3 (200.0%); items: 4.'),
    'executive: foreign-currency order converted from its base amount, refunded order counted in gross and refunds');
  const tot = r.runData['Executive | Current revenue'][0].json.totals;
  ok(Math.abs(tot.gross - 2118.65) < 1e-6 && Math.abs(tot.net - 1618.65) < 1e-6 && tot.refunds === 500 && tot.discounts === 50, 'executive totals: ' + JSON.stringify(tot));
  ok(exe.includes('Live data from WooCommerce orders.') && exe.includes('Not available from this source. Missing, not zero.'), 'executive names its source and leaves order types missing, not zero');
  const mk = fm['marketing-2026-10-14-to-2026-10-20.md'];
  ok(mk.includes('• Source report represents 2 orders (66.7%) and $1,619 net sales.') && mk.includes('• 1 orders are not represented') && mk.includes('• google / organic → 1 → $1,000') && mk.includes('• (direct) / (not set) → 1 → $619'),
    'marketing: sources from order attribution, the order without one is not represented');
  const pr = fm['products-2026-10-14-to-2026-10-20.md'];
  ok(pr.includes('1. Annual plan | $1,000 | 2 orders | 2 units') && pr.includes('2. Quarterly plan | $619 | 1 orders | 2 units') && pr.includes('https://example.com/annual'),
    'products: grouped by parent product, refund taken off its line, names and links from the product lookup');
  const emr = fm['email-2026-10-14-to-2026-10-20.md'];
  ok(emr.includes('• Emails sent: 240 (242.9% vs prior week); delivered: 240.') && emr.includes('• Unsubscribes: 2 (0.8% of delivered) vs 1 (1.4%)'),
    'email: the last 7 complete days against the 7 before, today and the oldest day left out');
  ok(emr.includes('• Broadcast: October newsletter → 100 → 30.0%') && !emr.includes('Summer newsletter') && !emr.includes('Old flow'), 'email: only running automations and broadcasts sent in the two weeks');
  ok(emr.includes('Email capture (Newsletter segment, net growth): 1,200 people now, +50 since the run for 2026-10-07 to 2026-10-13.'), 'email capture: growth against the last saved week');
  const tr = r.runData['Trends | Revenue by period'][0].json;
  ok(tr.available && tr.windows.last30.net === 1000 && tr.windows.prev30.net === 400 && tr.windows.last90.net === 1400 && tr.windows.prev90.net === 300 && tr.mom.net_pct === 150 && tr.qoq.net_pct === 366.7,
    'trends: 30 and 90 day windows and MoM/QoQ computed in code: ' + JSON.stringify({ mom: tr.mom, qoq: tr.qoq }));
  const facts = r.runData['Trends | Facts for the summary'][0].json;
  ok(facts.reviews.complete_count === 5 && facts.reviews.total_count === 5 && facts.history_weeks === 1 && facts.exec_totals.orders === 3, 'summary facts: review counts, one history week, executive totals');
  const sum = r.runData['AI | Summary report'][0].json;
  ok(!sum.incomplete && sum.fileName === 'summary-2026-10-14-to-2026-10-20.md' && sum.markdown.includes('Test summary: 5 of 5 reviews ran; history weeks 1.'), 'AI summary file written from the facts');
  ok(r.delivered.slack.length === 6 && r.delivered.slack[4].text.startsWith('✉️ *Email review (Customer.io)*') && r.delivered.slack[5].text.startsWith('🧠 *Weekly summary*'), 'Slack: 6 formatted messages, email and summary titled');
  const fe = r.delivered.email[0];
  ok(fe.attachments.length === 6 && fe.body.startsWith('Weekly reports, run 2026-10-21. 5 of 5 reviews complete.') && fe.subject === 'Weekly reports 2026-10-21', 'email: 6 files attached, the summary not counted as a review');
  ok(r.delivered.github.length === 6 && r.delivered.github[5].path.endsWith('summary-2026-10-14-to-2026-10-20.md'), 'GitHub commits the summary with the reports');
  const h = r.delivered.history[0];
  ok(h && h.exec_net === '1619' && h.exec_orders === '3' && h.reviews_complete === '5' && JSON.parse(h.facts_json).leads_email_count === 1200, 'history row saved: ' + JSON.stringify({ exec_net: h && h.exec_net, reviews: h && h.reviews_complete }));
  fs.writeFileSync(`${SAMPLES}/email-2026-10-14-to-2026-10-20.md`, emr);

  console.log('\n== T9 full template as shipped (every source switched off)');
  r = await run(full, { deliver: true });
  ok(!r.errors.length, 'run does not stop ' + r.errors.join('; '));
  ok(r.merged.length === 5 && r.merged.every(i => i.json.incomplete), '5 INCOMPLETE reviews: ' + r.merged.map(i => i.json.fileName).join(', '));
  ok(r.merged.every(i => i.json.markdown.includes('First run before setup?')), 'each one says the source is not connected yet, none shows a zero');
  ok(!r.merged.some(i => /\$0\b/.test(i.json.markdown)), 'no $0 anywhere');
  const s9 = r.runData['AI | Summary report'][0].json;
  ok(s9.incomplete && s9.markdown.includes('the AI node is switched off or returned nothing'), 'AI summary INCOMPLETE while its node is off');
  ok(r.runData['Trends | Revenue by period'][0].json.available === false, 'trends unavailable, not zero, while the store is not connected');
  ok(r.delivered.email[0].subject === 'Weekly reports 2026-10-21 (incomplete)' && r.delivered.email[0].body.includes('0 of 5 reviews complete.'), 'email flags the run incomplete');
  fs.writeFileSync(`${SAMPLES}/summary-incomplete-example.md`, s9.markdown);
  console.log(r.merged[4].json.markdown);

  console.log('\n== T10 full template, one source fails for real');
  r = await run(full, { fixtures: fullFixtures, history: lastWeek, ai, settings: fullSettings, fail: { 'Executive | Previous revenue': 'HTTP 503 Service Unavailable' } });
  const inc10 = r.merged.filter(i => i.json.incomplete);
  ok(!r.errors.length && inc10.length === 1 && inc10[0].json.fileName.startsWith('executive-'), '1 incomplete (executive), 4 complete');
  ok(inc10[0].json.markdown.includes('Reason: HTTP 503') && !inc10[0].json.markdown.includes('First run before setup?'), 'a real failure does not get the setup hint');

  console.log('\n== T11 full template, a week with no orders');
  r = await run(full, { fixtures: { ...fullFixtures, 'Executive | WooCommerce orders (current)': 'return [];' }, history: lastWeek, ai, settings: fullSettings });
  const e11 = r.merged.find(i => i.json.fileName.startsWith('executive-'));
  ok(e11 && !e11.json.incomplete && e11.json.markdown.includes('• Orders: 0 ('), 'an empty week is a true zero, reported as complete');

  console.log(failures ? `\n${failures} FAILED` : '\nALL PASSED');
  process.exit(failures ? 1 : 0);
})().catch(e => { console.error(e); process.exit(2); });
