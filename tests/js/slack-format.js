// Turns each review's Markdown into a Slack message: an emoji title, bold labels,
// a dashed rule between parts, and table rows as bullet lines (Slack can't show
// Markdown tables). The Markdown file itself is unchanged; only slackText is rewritten.
const s = $('Settings').first().json;
const base = String(s.n8nUrl || '').replace(/\/+$/, '');
const linked = /^https?:\/\//.test(base) && !base.includes('YOUR-INSTANCE');
const wfUrl = linked ? base + '/workflow/' + $workflow.id : '';
const icon = { executive: '📊', marketing: '📣', products: '🛍️', traffic: '🌐', email: '✉️', ads: '🎯', summary: '🧠' };
const title = { executive: 'Executive business review', marketing: 'Marketing source review', products: 'Top product review', traffic: 'Website traffic review', email: 'Email review (Customer.io)', ads: 'Ads review (Google Ads and Meta)', summary: 'Weekly summary' };
const rule = '------------------------------';
const esc = t => String(t).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
const isContext = l => /^(DEMO|PRIVATE LIVE|SYNTHETIC DATA|SAMPLE DATA|LIVE GA4|INCOMPLETE \|)/.test(l) || /^\d{4}-\d{2}-\d{2}/.test(l) || /^(Synthetic example data|Sample data:|Live Metorik data|Live data from|Written by an AI model)/.test(l);
const cells = l => l.replace(/^\|/, '').replace(/\|\s*$/, '').split('|').map(c => c.trim());

return $input.all().map(item => {
  const j = item.json;
  const lane = String(j.fileName || '').split('-')[0];
  const head = (j.incomplete ? '⚠️' : (icon[lane] || '📄')) + ' *' + (title[lane] || esc(j.fileName || 'Review')) + (j.incomplete ? ': incomplete' : '') + '*';
  const context = [], body = [];
  let header = null;
  for (const raw of String(j.markdown || '').split('\n')) {
    const l = raw.trim();
    if (!l) { if (body.length && body[body.length - 1] !== '') body.push(''); continue; }
    if (l.startsWith('# ')) continue;
    if (!body.length && isContext(l)) { context.push('_' + esc(l.replace(/\s*\|\s*/g, ' · ')) + '_'); continue; }
    if (l.startsWith('## ')) { if (body.length && body[body.length - 1] !== '') body.push(''); body.push('*' + esc(l.slice(3)) + '*'); header = null; continue; }
    if (l.startsWith('|')) {
      const c = cells(l);
      if (c.every(x => /^:?-+:?$/.test(x))) continue;
      if (!header) { header = c; continue; }
      body.push('• *' + esc(c[0]) + '*' + c.slice(1).map((v, k) => ' · ' + esc(header[k + 1]) + ' ' + esc(v)).join(''));
      continue;
    }
    header = null;
    let m;
    if ((m = l.match(/^Review:\s*(.*)$/))) { body.push('👉 *Review:* ' + esc(m[1])); continue; }
    if ((m = l.match(/^([•-])\s+([^:]{1,45}):\s+(.*)$/))) { body.push('• *' + esc(m[2]) + ':* ' + esc(m[3]).replace(/\s*\|\s*/g, ' · ')); continue; }
    if ((m = l.match(/^(\d+)\.\s+(.+?)\s+—\s+(.*)$/))) { body.push(m[1] + '. *' + esc(m[2]) + '* · ' + esc(m[3]).replace(/\s*\|\s*/g, ' · ')); continue; }
    if ((m = l.match(/^(Failed step|Reason):\s*(.*)$/))) { body.push('*' + m[1] + ':* ' + esc(m[2])); continue; }
    if (/^[^:]{3,60}:$/.test(l)) { body.push('*' + esc(l) + '*'); continue; }
    body.push(esc(l).replace(/\s*\|\s*/g, ' · '));
  }
  while (body.length && body[body.length - 1] === '') body.pop();
  const parts = [head, ...context, rule, ...body];
  if (linked) parts.push(rule, '<' + wfUrl + '|Open the workflow> · <' + wfUrl + '/executions/' + $execution.id + '|This run>');
  return { json: { ...j, slackText: parts.join('\n') }, binary: item.binary };
});
