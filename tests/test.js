const fs = require('fs');
const { run } = require('./run');
const [OUT, SRC, SAMPLES] = process.argv.slice(2);
const demo = `${OUT}/four-reviews-demo-v1.1.json`, tmpl = `${OUT}/four-reviews-connection-template-v1.1.json`;
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

  console.log('\n== T1 demo, default settings: output matches Nick\'s examples');
  let r = await run(demo, { deliver: true });
  ok(!r.errors.length, 'no errors ' + r.errors.join('; '));
  ok(r.merged.length === 4, 'merge collected 4 reports');
  const m = byName(r.merged);
  ok(JSON.stringify(Object.keys(m)) === JSON.stringify(['executive-2026-10-14-to-2026-10-20.md', 'marketing-2026-10-14-to-2026-10-20.md', 'products-2026-10-14-to-2026-10-20.md', 'traffic-2026-10-14-to-2026-10-20.md']), 'dated file names: ' + Object.keys(m).join(', '));
  for (const lane of ['executive', 'marketing', 'products']) {
    const nick = fs.readFileSync(`${SRC}/${lane}-example.md`, 'utf8');
    ok(m[`${lane}-2026-10-14-to-2026-10-20.md`] === nick, `${lane} report identical to Nick's example`);
  }
  const nickT = fs.readFileSync(`${SRC}/traffic-example.md`, 'utf8').replace('Metorik remains the revenue source.', 'Your store or CRM remains the revenue source.');
  ok(m['traffic-2026-10-14-to-2026-10-20.md'] === nickT, 'traffic report identical to Nick\'s example apart from the revenue-source line');
  ok(r.merged.every(i => decoded(i) === i.json.markdown), 'binary report matches markdown for all 4');
  ok(r.delivered.slack.length === 4 && r.delivered.slack.every(s => s.channel === 'SELECT_YOUR_TEST_CHANNEL'), 'Slack would post 4 messages to the placeholder channel');
  const sl = r.delivered.slack;
  ok(sl[0].text.startsWith('📊 *Executive business review*') && sl[3].text.startsWith('🌐 *Website traffic review*'), 'Slack titles carry an emoji and bold');
  ok(sl.every(m => !m.text.split('\n').some(l => l.startsWith('|') || l.startsWith('#'))), 'no Markdown tables or headings left in Slack text');
  ok(sl.every(m => m.text.includes('------------------------------')) && sl[0].text.includes('• *Net revenue:* $24,000'), 'dashed separators and bold labels');
  ok(sl[3].text.includes('• *google / organic* · Sessions 5000 · Previous 4200 · Change 19.0% · Engagement 65.0%'), 'traffic table rows become bullet lines');
  ok(!sl[0].text.includes('Open the workflow') && !r.delivered.email[0].body.includes('Workflow:'), 'no workflow links while n8nUrl is the placeholder');
  console.log(sl[3].text.split('\n').slice(0, 12).join('\n'));
  ok(r.delivered.github.length === 4 && r.delivered.github[0].path === 'projects/reporting-agent/reports/executive-2026-10-14-to-2026-10-20.md' && r.delivered.github[0].owner === 'YOUR_GITHUB_USERNAME', 'GitHub paths and owner from Settings: ' + r.delivered.github[0].path);
  ok(r.delivered.github.every((g, i) => g.bytes === r.merged[i].json.markdown), 'GitHub commits the exact report text');
  const api = r.delivered.api, br = 'reports/2026-10-21-run-8200';
  ok(api.length === 3 && api[0].method === 'GET' && api[0].url === 'https://api.github.com/repos/YOUR_GITHUB_USERNAME/YOUR_PERSONAL_OS_REPO/git/ref/heads/main', 'reads base branch: ' + (api[0] && api[0].url));
  ok(api[1].url.endsWith('/git/refs') && api[1].body.ref === 'refs/heads/' + br && api[1].body.sha === 'abc123', 'creates branch ' + api[1].body.ref);
  ok(r.delivered.github.every(g => g.branch === br), 'all 4 commits go to the new branch, none to main');
  ok(api[2].url.endsWith('/pulls') && api[2].body.head === br && api[2].body.base === 'main' && api[2].body.title === 'Weekly reports 2026-10-21', 'opens one PR into main: ' + api[2].body.title);
  console.log(api[2].body.body);
  const em = r.delivered.email;
  ok(em.length === 1 && em[0].to === 'YOU@EXAMPLE.COM' && em[0].attachments.length === 4, 'one email, 4 attachments: ' + (em[0] && em[0].subject));
  ok((em[0].body.match(/-----BEGIN REPORT /g) || []).length === 4 && em[0].body.includes(m['executive-2026-10-14-to-2026-10-20.md']), 'email body holds all 4 reports between markers');
  const wrapped = em[0].body.replace(/(.{60})/g, '$1\n');  // simulate Gmail hard-wrapping every line
  const files = [...wrapped.matchAll(/-----BEGIN FILE ([^\n]+?)-----\n([\s\S]*?)-----END FILE-----/g)];
  ok(files.length === 4 && files.every(f => Buffer.from(f[2].replace(/\s+/g, ''), 'base64').toString('utf8') === m[f[1].replace(/\s+/g, '')]), 'exact copies decode byte-identical even after line wrapping');
  fs.mkdirSync(SAMPLES, { recursive: true });
  for (const [f, md] of Object.entries(m)) fs.writeFileSync(`${SAMPLES}/${f}`, md);
  fs.writeFileSync(`${SAMPLES}/email-body-example.txt`, `Subject: ${em[0].subject}\n\n${em[0].body}`);

  console.log('\n== T1b links when n8nUrl is set');
  r = await run(demo, { deliver: true, settings: { n8nUrl: 'https://acme.app.n8n.cloud/' } });
  ok(r.delivered.email[0].body.includes('Workflow: https://acme.app.n8n.cloud/workflow/wf123\nThis run: https://acme.app.n8n.cloud/workflow/wf123/executions/8200'), 'email links to the workflow and the run');
  ok(r.delivered.slack[0].text.endsWith('<https://acme.app.n8n.cloud/workflow/wf123|Open the workflow> · <https://acme.app.n8n.cloud/workflow/wf123/executions/8200|This run>'), 'Slack links to the workflow and the run');
  ok(r.merged.every(i => i.json.markdown === m[i.json.fileName]), 'the Markdown reports are unchanged by the Slack formatting');
  console.log(r.delivered.slack[0].text);

  console.log('\n== T2 demo with EUR, Europe/Tallinn, de-DE');
  r = await run(demo, { settings: { currency: 'EUR', timeZone: 'Europe/Tallinn', locale: 'de-DE' } });
  ok(!r.errors.length && r.merged.length === 4 && !r.merged.some(i => i.json.incomplete), 'all 4 complete');
  const ex = byName(r.merged)['executive-2026-10-14-to-2026-10-20.md'];
  ok(ex.replace(/\u00a0/g,' ').includes('24.000 €') && ex.includes('| EUR | Europe/Tallinn'), 'euro formatting and labels: ' + ex.split('\n').slice(1, 5).join(' / '));
  ok(byName(r.merged)['traffic-2026-10-14-to-2026-10-20.md'].includes('(Europe/Tallinn)'), 'traffic uses the Settings timezone');

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

  console.log(failures ? `\n${failures} FAILED` : '\nALL PASSED');
  process.exit(failures ? 1 : 0);
})().catch(e => { console.error(e); process.exit(2); });
