// Minimal local runner for the four-reviews workflows: Code, Merge, disabled
// pass-through, error outputs (both kinds), alwaysOutputData, Data Table rows
// (from opts.history, inserts recorded), the AI Agent (opts.ai stands in for the
// model), and the three delivery nodes (recorded, not sent).
const fs = require('fs');
const vm = require('vm');
const { DateTime } = require('luxon');

function makeDate(fixedIso) {
  const Real = Date;
  const fixed = new Real(fixedIso).getTime();
  class FixedDate extends Real {
    constructor(...a) { if (a.length) super(...a); else super(fixed); }
    static now() { return fixed; }
  }
  return FixedDate;
}

async function run(path, opts = {}) {
  const wf = JSON.parse(fs.readFileSync(path, 'utf8'));
  const nodes = Object.fromEntries(wf.nodes.map(n => [n.name, n]));
  const conns = wf.connections;
  for (const [from, c] of Object.entries(conns)) {
    if (!nodes[from]) throw Error('connection from missing node ' + from);
    for (const outs of Object.values(c)) for (const out of outs) for (const t of out) if (!nodes[t.node]) throw Error('connection to missing node ' + t.node);
  }
  const fixedNow = opts.now || '2026-10-21T17:00:00Z';
  const FixedDate = makeDate(fixedNow);
  const demoFixtures = opts.fixtures || {};
  const runData = {}, delivered = { slack: [], github: [], email: [], api: [], history: [] }, mergeBuf = {}, errors = [], ran = [];

  const ref = name => {
    if (!runData[name]) throw Error(`Node '${name}' has not run`);
    const items = runData[name];
    return { first: () => items[0], all: () => items, last: () => items[items.length - 1] };
  };

  async function runCode(code, items, prev) {
    const ctx = vm.createContext({
      $input: { first: () => items[0], all: () => items, last: () => items[items.length - 1] },
      $: ref, $now: DateTime.fromISO(fixedNow), $prevNode: { name: prev }, $execution: { id: '8200' }, $workflow: { id: 'wf123' },
      Buffer, Date: FixedDate, Intl, console,
    });
    return await vm.runInContext(`(async()=>{${code}\n})()`, ctx);
  }

  function evalExpr(v, item) {
    if (v && typeof v === 'object' && v.__rl) return evalExpr(v.value, item);
    if (typeof v !== 'string' || !v.startsWith('=')) return v;
    return v.slice(1).replace(/\{\{([\s\S]+?)\}\}/g, (_, e) => {
      const ctx = vm.createContext({ $json: item.json, $binary: item.binary || {}, $: ref, JSON, Object, String, Math, $now: DateTime.fromISO(fixedNow), $execution: { id: '8200' } });
      return String(vm.runInContext(e, ctx));
    });
  }

  async function exec(name, items, inputIndex, prev) {
    const n = nodes[name];
    if (n.type === 'n8n-nodes-base.merge') {
      const k = n.parameters.numberInputs || 2;
      mergeBuf[name] = mergeBuf[name] || {};
      if (mergeBuf[name][inputIndex]) throw Error(`merge input ${inputIndex} received twice`);
      mergeBuf[name][inputIndex] = items;
      if (Object.keys(mergeBuf[name]).length < k) return;
      items = [...Array(k).keys()].flatMap(i => mergeBuf[name][i]);
      return emit(name, [items]);
    }
    ran.push(name);
    const delivery = { 'n8n-nodes-base.slack': 'slack', 'n8n-nodes-base.github': 'github', 'n8n-nodes-base.gmail': 'email' }[n.type];
    if (delivery && opts.deliver) {
      const p = n.parameters;
      for (const it of items) {
        if (delivery === 'slack') delivered.slack.push({ channel: evalExpr(p.channelId, it), text: evalExpr(p.text, it) });
        if (delivery === 'github') delivered.github.push({ owner: evalExpr(p.owner, it), repo: evalExpr(p.repository, it), path: evalExpr(p.filePath, it), message: evalExpr(p.commitMessage, it), branch: evalExpr(p.additionalParameters?.branch?.branch, it), bytes: Buffer.from(it.binary[p.binaryPropertyName].data, 'base64').toString('utf8') });
        if (delivery === 'email') delivered.email.push({ to: evalExpr(p.sendTo, it), subject: evalExpr(p.subject, it), body: evalExpr(p.message, it), attachments: evalExpr(p.options.attachmentsUi.attachmentsBinary[0].property, it).split(',').map(a => it.binary[a].fileName) });
      }
      return emit(name, [items]);
    }
    if (n.type === 'n8n-nodes-base.httpRequest' && opts.deliver && name.startsWith('GitHub |')) {
      const p = n.parameters, it = items[0];
      const call = { node: name, method: p.method, url: evalExpr(p.url, it), body: p.jsonBody ? JSON.parse(evalExpr(p.jsonBody, it)) : null };
      delivered.api.push(call);
      const stub = name.includes('Get base') ? { object: { sha: 'abc123' } } : name.includes('Create branch') ? { ref: call.body.ref } : { html_url: 'https://github.com/x/y/pull/1' };
      return emit(name, [[{ json: stub }]]);
    }
    if (n.disabled) return emit(name, [items]);
    let out;
    try {
      if (opts.fail && opts.fail[name]) throw Error(opts.fail[name]);
      if (n.type === 'n8n-nodes-base.manualTrigger') out = [{ json: {} }];
      else if (n.type === 'n8n-nodes-base.httpRequest') throw Error('HTTP node enabled without fixture: ' + name);
      else if (n.type === 'n8n-nodes-base.dataTable') {
        if (n.parameters.operation === 'insert') {
          const row = Object.fromEntries(Object.entries(n.parameters.columns.value).map(([k, v]) => [k, evalExpr(v, items[0])]));
          delivered.history.push(row);
          out = [{ json: { ...row, id: delivered.history.length } }];
        } else out = (opts.history || []).map(h => ({ json: h }));
      } else if (n.type === '@n8n/n8n-nodes-langchain.agent') {
        if (!opts.ai) throw Error('No model credential');
        out = [{ json: { output: opts.ai(items[0].json) } }];
      }
      else if (n.type === 'n8n-nodes-base.code') {
        out = await runCode(n.parameters.jsCode, items, prev);
        if (name === 'Settings' && opts.settings) out = out.map(i => ({ json: { ...i.json, ...opts.settings } }));
      } else throw Error('unsupported node ' + n.type);
    } catch (e) {
      if (n.onError === 'continueErrorOutput') {
        const err = opts.errorShape === 'string' ? { error: e.message } : { error: { message: e.message, description: null } };
        runData[name] = [];
        return emit(name, [[], [{ json: err }]]);
      }
      if (n.onError === 'continueRegularOutput') return emit(name, [[{ json: { error: { message: e.message } } }]]);
      errors.push(`${name}: ${e.message}`);
      return;
    }
    if (!out.length && n.alwaysOutputData) out = [{ json: {} }];
    return emit(name, [out]);
  }

  async function emit(name, outputs) {
    runData[name] = outputs[0];
    const c = conns[name];
    if (!c) return;
    for (const [i, items] of outputs.entries()) {
      if (!items.length || !c.main[i]) continue;
      for (const t of c.main[i]) await exec(t.node, items.map(x => ({ ...x })), t.index, name);
    }
  }

  // Template runs with enabled sources use the demo's fixture code under the same node name.
  if (opts.ai) for (const n of wf.nodes) if (n.type === '@n8n/n8n-nodes-langchain.agent') n.disabled = false;
  for (const [name, code] of Object.entries(demoFixtures)) {
    nodes[name].disabled = false;
    nodes[name].type = 'n8n-nodes-base.code';
    nodes[name].parameters = { jsCode: code };
  }
  const trigger = wf.nodes.find(n => n.type === 'n8n-nodes-base.manualTrigger').name;
  await exec(trigger, [{ json: {} }], 0, null);
  const merged = runData['Collect all four reports'] || runData['Collect all reports'] || [];
  return { runData, merged, delivered, errors, ran, nodes };
}

module.exports = { run };
