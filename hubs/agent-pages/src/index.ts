import { Hono } from 'hono';

type Bindings = {
  D1_OUTREACH: D1Database;
  D1_SPINE: D1Database;
};

const app = new Hono<{ Bindings: Bindings }>();

// ── Agent lookup ──────────────────────────────────────────────
// NOTE: these pages go OUT to the individual servicing agents — an agent must
// never see another agent's page, listing, or even their existence. There is no
// index/listing of agents and no "all agents" link anywhere. Each agent gets
// only their own /agent/sa-00X URL.
const AGENTS: Record<string, { id: string; name: string }> = {
  'sa-001': { id: 'SA-001', name: 'Dave Allan' },
  'sa-002': { id: 'SA-002', name: 'Jeff Mussolino' },
  'sa-003': { id: 'SA-003', name: 'David Vang' },
};

// BAR-417: the MillionVerifier verdict — the truth column, not the loose has_verified_email flag.
const MV_CASE = "CASE WHEN pm.email_verified = 1 AND pm.email_verification_source IN ('MillionVerifier','mv_verified','millionverifier:ok') THEN 1 ELSE 0 END";

function resolveAgent(c: any) {
  const a = AGENTS[String(c.req.param('agentId') || '').toLowerCase()];
  return a || null;
}

// ── Health ────────────────────────────────────────────────────
app.get('/health', (c) => c.json({ status: 'ok', worker: 'agent-pages' }));

// ── Root — deliberately NOT an agent index ────────────────────
app.get('/', (c) =>
  c.html(`<!DOCTYPE html><html><head><meta charset="utf-8"><title>SVG Agency</title>
<style>body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;max-width:480px;margin:80px auto;padding:0 20px;color:#1a1a1a;text-align:center}</style></head>
<body><h1>SVG Agency</h1><p>Use the link you were given to reach your territory page.</p></body></html>`)
);

// ── Helpers: pull this agent's contacts (with MV verdict), optionally filtered ──
async function fetchContacts(db: D1Database, agentId: string, q: string | null, limit: number | null) {
  const like = `%${agentId}%`;
  const filter = q && q.trim()
    ? `AND (sw.canonical_name LIKE ?2 OR sw.company_name LIKE ?2 OR sw.company_domain LIKE ?2)`
    : '';
  const lim = limit && limit > 0 ? `LIMIT ${Math.floor(limit)}` : '';
  const sql = `
    SELECT sw.outreach_id, sw.canonical_name, sw.company_name, sw.company_domain, sw.state, sw.city,
           sw.employees, sw.slot_type, sw.person_first_name, sw.person_last_name, sw.person_email,
           sw.company_phone, sw.hunter_phone, sw.person_linkedin,
           ${MV_CASE} AS mv_verified
    FROM slot_workbench sw
    LEFT JOIN people_people_master pm ON sw.person_unique_id = pm.unique_id
    WHERE sw.service_agents LIKE ?1 AND sw.has_name = 1 AND sw.has_email = 1
      ${filter}
    ORDER BY sw.canonical_name, sw.company_name, sw.slot_type
    ${lim}`;
  const stmt = q && q.trim()
    ? db.prepare(sql).bind(like, `%${q.trim()}%`)
    : db.prepare(sql).bind(like);
  const { results } = await stmt.all<any>();
  return results ?? [];
}

function rowsToCompanies(rows: any[]) {
  const ROLE_ORDER: Record<string, number> = { CEO: 1, CFO: 2, HR: 3 };
  const map = new Map<string, any>();
  for (const r of rows) {
    const k = r.outreach_id as string;
    if (!map.has(k)) {
      map.set(k, {
        name: r.canonical_name || r.company_name || 'Unknown',
        city: r.city || '', state: r.state || '', employees: r.employees || 0,
        company_phone: r.company_phone || '',
        _people: new Map<string, any>(),
      });
    }
    const co = map.get(k)!;
    const fullName = [r.person_first_name, r.person_last_name].filter(Boolean).join(' ').trim();
    const pkey = (r.person_email || '').trim().toLowerCase() || fullName.toLowerCase() || String(r.person_unique_id || '');
    let ct = co._people.get(pkey);
    if (!ct) {
      ct = { roles: [] as string[], name: fullName, email: (r.person_email || '').trim(), mv: false, person_phone: '', linkedin: '' };
      co._people.set(pkey, ct);
    }
    if (r.slot_type && !ct.roles.includes(r.slot_type)) ct.roles.push(r.slot_type);
    if (r.mv_verified) ct.mv = true;
    if (!ct.person_phone && r.hunter_phone && String(r.hunter_phone).trim()) ct.person_phone = String(r.hunter_phone).trim();
    if (!ct.linkedin && r.person_linkedin) ct.linkedin = r.person_linkedin;
  }
  return Array.from(map.values()).map((co) => ({
    name: co.name, city: co.city, state: co.state, employees: co.employees, company_phone: co.company_phone,
    contacts: Array.from(co._people.values())
      .map((ct: any) => {
        ct.roles.sort((a: string, b: string) => (ROLE_ORDER[a] ?? 99) - (ROLE_ORDER[b] ?? 99));
        return { slot: ct.roles.join(' / ') || '—', name: ct.name, email: ct.email, mv: ct.mv, phone: ct.person_phone || co.company_phone || '', linkedin: ct.linkedin };
      })
      .sort((a: any, b: any) => (ROLE_ORDER[a.slot.split(' / ')[0]] ?? 99) - (ROLE_ORDER[b.slot.split(' / ')[0]] ?? 99)),
  })).sort((a, b) => a.name.localeCompare(b.name));
}

const esc = (s: any) => String(s == null ? '' : s).replace(/&/g, '&amp;').replace(/</g, '&lt;');
const csvCell = (s: any) => `"${String(s == null ? '' : s).replace(/"/g, '""')}"`;

// ── JSON data endpoint — the table loads from here (keeps the page tiny) ──
app.get('/agent/:agentId/data', async (c) => {
  const agent = resolveAgent(c);
  if (!agent) return c.json({ error: 'not found' }, 404);
  const q = c.req.query('q') ?? null;
  const rows = await fetchContacts(c.env.D1_OUTREACH, agent.id, q, q && q.trim() ? 800 : 300);
  return c.json({ companies: rowsToCompanies(rows), truncated: rows.length >= (q && q.trim() ? 800 : 300) });
});

// ── CSV export — full list, server-side, paginated internally ──
app.get('/agent/:agentId/export.csv', async (c) => {
  const agent = resolveAgent(c);
  if (!agent) return c.text('not found', 404);
  const verifiedOnly = c.req.query('verified') === '1';
  const rows = await fetchContacts(c.env.D1_OUTREACH, agent.id, null, null); // no limit
  const header = ['Company', 'City', 'State', 'Employees', 'Role(s)', 'Name', 'Email', 'MV Verified', 'Phone', 'LinkedIn'];
  const lines = [header.map(csvCell).join(',')];
  for (const co of rowsToCompanies(rows)) {
    for (const ct of co.contacts) {
      if (verifiedOnly && !ct.mv) continue;
      lines.push([co.name, co.city, co.state, co.employees, ct.slot, ct.name, ct.email, ct.mv ? 'Yes' : 'No', ct.phone, ct.linkedin].map(csvCell).join(','));
    }
  }
  const today = new Date().toISOString().slice(0, 10);
  return new Response(lines.join('\r\n'), {
    headers: {
      'Content-Type': 'text/csv; charset=utf-8',
      'Content-Disposition': `attachment; filename="${agent.id}-${verifiedOnly ? 'mv-verified' : 'all'}-${today}.csv"`,
    },
  });
});

// ── Agent detail page — small shell; table fetched from /data ──
app.get('/agent/:agentId', async (c) => {
  const agent = resolveAgent(c);
  if (!agent) return c.text('Agent not found', 404);

  // counts (cheap)
  const cnt = await c.env.D1_OUTREACH.prepare(`
    SELECT COUNT(DISTINCT sw.outreach_id) companies,
           COUNT(*) contacts,
           SUM(${MV_CASE}) mv_verified,
           COUNT(DISTINCT CASE WHEN (sw.company_phone IS NOT NULL AND TRIM(sw.company_phone)!='')
                              OR (sw.hunter_phone IS NOT NULL AND TRIM(sw.hunter_phone)!='') THEN sw.outreach_id END) with_phone
    FROM slot_workbench sw
    LEFT JOIN people_people_master pm ON sw.person_unique_id = pm.unique_id
    WHERE sw.service_agents LIKE ? AND sw.has_name = 1 AND sw.has_email = 1
  `).bind(`%${agent.id}%`).first<any>();

  // sent / delivered / bounced for this agent (lcs_mid -> lcs_cid -> lcs_signal_queue.agent_number)
  let sent: Record<string, number> = {};
  try {
    const { results } = await c.env.D1_SPINE.prepare(`
      SELECT m.delivery_status AS status, COUNT(*) AS n
      FROM lcs_mid_sequence_state m
      JOIN lcs_cid ci ON ci.communication_id = m.communication_id
      JOIN lcs_signal_queue s ON s.id = ci.signal_queue_id
      WHERE s.agent_number = ?
      GROUP BY m.delivery_status
    `).bind(agent.id).all<{ status: string; n: number }>();
    for (const r of results ?? []) sent[String(r.status)] = Number(r.n);
  } catch { /* non-blocking */ }
  const delivered = sent['DELIVERED'] ?? 0, bounced = sent['BOUNCED'] ?? 0, sentPending = sent['SENT'] ?? 0, scheduled = sent['SCHEDULED'] ?? 0;
  const touched = delivered + bounced + sentPending;
  const bounceRate = touched > 0 ? ((bounced / touched) * 100).toFixed(1) : '0.0';

  const companies = Number(cnt?.companies ?? 0), contacts = Number(cnt?.contacts ?? 0), mv = Number(cnt?.mv_verified ?? 0), withPhone = Number(cnt?.with_phone ?? 0);

  const html = `<!DOCTYPE html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>${esc(agent.name)} — Outreach Territory</title>
<style>
  body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;max-width:1280px;margin:0 auto;padding:20px;background:#f8f9fa;color:#1a1a1a}
  h1{font-size:1.5rem;border-bottom:2px solid #1a1a1a;padding-bottom:8px}
  h2.section{font-size:.95rem;color:#666;text-transform:uppercase;letter-spacing:.05em;margin:26px 0 8px}
  .stats{display:flex;gap:14px;margin:14px 0;flex-wrap:wrap}
  .stat{background:#fff;border-radius:8px;padding:13px 20px;box-shadow:0 1px 3px rgba(0,0,0,.1);min-width:104px}
  .stat .num{font-size:1.7rem;font-weight:700;color:#2563eb}
  .stat.good .num{color:#16a34a}.stat.warn .num{color:#d97706}.stat.bad .num{color:#dc2626}
  .stat .label{color:#666;font-size:.78rem}
  .controls{margin:16px 0;display:flex;gap:12px;align-items:center;flex-wrap:wrap}
  .btn{background:#2563eb;color:#fff;border:none;padding:9px 18px;border-radius:6px;cursor:pointer;font-size:.88rem;font-weight:500;text-decoration:none;display:inline-block}
  .btn:hover{background:#1d4ed8}.btn-outline{background:#fff;color:#2563eb;border:1px solid #2563eb}
  input[type=search]{padding:9px 14px;border:1px solid #d1d5db;border-radius:6px;font-size:.9rem;width:320px}
  table{width:100%;border-collapse:collapse;background:#fff;border-radius:8px;overflow:hidden;box-shadow:0 1px 3px rgba(0,0,0,.1)}
  th{background:#1a1a1a;color:#fff;padding:9px 11px;text-align:left;font-size:.75rem;text-transform:uppercase;letter-spacing:.04em}
  td{padding:7px 11px;border-bottom:1px solid #eee;font-size:.84rem}
  tr:hover td{background:#f1f5f9}
  .verified{color:#16a34a;font-weight:600}.unverified{color:#dc2626}
  a{color:#2563eb}.muted{color:#888;font-size:.85rem;margin:8px 0}
</style></head><body>
<h1>${esc(agent.name)} — Outreach Territory</h1>

<h2 class="section">Outreach sent</h2>
<div class="stats">
  <div class="stat"><div class="num">${touched}</div><div class="label">Messages out</div></div>
  <div class="stat good"><div class="num">${delivered}</div><div class="label">Delivered</div></div>
  <div class="stat warn"><div class="num">${sentPending}</div><div class="label">Sent (pending)</div></div>
  <div class="stat warn"><div class="num">${scheduled}</div><div class="label">Scheduled</div></div>
  <div class="stat ${Number(bounceRate) > 2 ? 'bad' : 'good'}"><div class="num">${bounced}</div><div class="label">Bounced (${bounceRate}%)</div></div>
</div>

<h2 class="section">Contacts to work</h2>
<div class="stats">
  <div class="stat"><div class="num">${companies.toLocaleString()}</div><div class="label">Companies</div></div>
  <div class="stat"><div class="num">${contacts.toLocaleString()}</div><div class="label">Contacts</div></div>
  <div class="stat good"><div class="num">${mv.toLocaleString()}</div><div class="label">MV-verified</div></div>
  <div class="stat"><div class="num">${withPhone.toLocaleString()}</div><div class="label">With a phone</div></div>
</div>
<div class="controls">
  <input type="search" id="q" placeholder="Search company or domain…">
  <a class="btn" href="/agent/${esc(c.req.param('agentId'))}/export.csv">Download Full List (CSV)</a>
  <a class="btn btn-outline" href="/agent/${esc(c.req.param('agentId'))}/export.csv?verified=1">Download MV-Verified Only</a>
</div>
<p class="muted" id="note">Showing the first results — type to search your whole territory, or download the full list above.</p>
<table><thead><tr><th>Company</th><th>City</th><th>St</th><th>Emp</th><th>Role(s)</th><th>Name</th><th>Email</th><th>MV</th><th>Phone</th><th>LinkedIn</th></tr></thead>
<tbody id="rows"><tr><td colspan="10" style="text-align:center;color:#888;padding:20px">loading…</td></tr></tbody></table>

<script>
const agentPath = ${JSON.stringify('/agent/' + String(c.req.param('agentId')))};
let timer = null;
async function load(q) {
  const tb = document.getElementById('rows');
  tb.innerHTML = '<tr><td colspan="10" style="text-align:center;color:#888;padding:20px">loading…</td></tr>';
  let data;
  try { data = await (await fetch(agentPath + '/data' + (q ? ('?q=' + encodeURIComponent(q)) : ''))).json(); }
  catch (e) { tb.innerHTML = '<tr><td colspan="10" style="color:#dc2626;padding:20px">load failed — retry</td></tr>'; return; }
  const cos = data.companies || [];
  document.getElementById('note').textContent = (q ? ('Matches for "' + q + '": ' + cos.length + ' companies') : 'First ' + cos.length + ' companies — type to search, or download the full list above.') + (data.truncated ? ' (more — narrow the search or download)' : '');
  const out = [];
  for (const co of cos) for (let i = 0; i < co.contacts.length; i++) {
    const ct = co.contacts[i], first = i === 0;
    out.push('<tr><td>' + (first ? esc(co.name) : '') + '</td><td>' + (first ? esc(co.city) : '') + '</td><td>' + (first ? esc(co.state) : '') + '</td><td>' + (first ? esc(co.employees) : '') + '</td><td>' + esc(ct.slot) + '</td><td>' + esc(ct.name) + '</td><td><a href="mailto:' + esc(ct.email) + '">' + esc(ct.email) + '</a></td><td class="' + (ct.mv ? 'verified">Yes' : 'unverified">No') + '</td><td>' + esc(ct.phone) + '</td><td>' + (ct.linkedin ? '<a href="' + esc(ct.linkedin) + '" target="_blank">profile</a>' : '') + '</td></tr>');
  }
  tb.innerHTML = out.length ? out.join('') : '<tr><td colspan="10" style="text-align:center;color:#888;padding:20px">no matches</td></tr>';
}
function esc(s){ return String(s==null?'':s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;'); }
document.getElementById('q').addEventListener('input', e => { clearTimeout(timer); timer = setTimeout(() => load(e.target.value.trim()), 350); });
load('');
</script>
</body></html>`;
  return c.html(html);
});

export default app;
