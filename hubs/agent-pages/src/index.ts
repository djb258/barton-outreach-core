import { Hono } from 'hono';

type Bindings = {
  D1_OUTREACH: D1Database;
  D1_SPINE: D1Database;
};

const app = new Hono<{ Bindings: Bindings }>();

// ── Agent lookup ──────────────────────────────────────────────
const AGENTS: Record<string, { id: string; name: string; first: string; last: string }> = {
  'sa-001': { id: 'SA-001', name: 'Dave Allan', first: 'Dave', last: 'Allan' },
  'sa-002': { id: 'SA-002', name: 'Jeff Mussolino', first: 'Jeff', last: 'Mussolino' },
  'sa-003': { id: 'SA-003', name: 'David Vang', first: 'David', last: 'Vang' },
};

// BAR-417: the MillionVerifier verdict — the truth column, not the loose has_verified_email flag.
const MV_OK = "pm.email_verified = 1 AND pm.email_verification_source IN ('MillionVerifier','mv_verified','millionverifier:ok')";

// ── Health ────────────────────────────────────────────────────
app.get('/health', (c) => c.json({ status: 'ok', worker: 'agent-pages', agents: Object.keys(AGENTS) }));

// ── Agent listing page ────────────────────────────────────────
app.get('/', (c) => {
  const html = `<!DOCTYPE html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>SVG Agency — Agent Territories</title>
<style>
  body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; max-width: 600px; margin: 40px auto; padding: 0 20px; background: #f8f9fa; color: #1a1a1a; }
  h1 { font-size: 1.5rem; border-bottom: 2px solid #1a1a1a; padding-bottom: 8px; }
  .agent-card { background: white; border-radius: 8px; padding: 20px; margin: 16px 0; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }
  .agent-card h2 { margin: 0 0 8px 0; font-size: 1.2rem; }
  .agent-card a { color: #2563eb; text-decoration: none; font-weight: 500; }
  .agent-card a:hover { text-decoration: underline; }
  .meta { color: #666; font-size: 0.9rem; }
</style></head><body>
<h1>SVG Agency — Agent Territories</h1>
<div class="agent-card"><h2><a href="/agent/sa-001">Dave Allan</a></h2><p class="meta">SA-001 — Western PA / WV</p></div>
<div class="agent-card"><h2><a href="/agent/sa-002">Jeff Mussolino</a></h2><p class="meta">SA-002 — Primary territory</p></div>
<div class="agent-card"><h2><a href="/agent/sa-003">David Vang</a></h2><p class="meta">SA-003 — Expansion territory</p></div>
</body></html>`;
  return c.html(html);
});

// ── Agent detail page ─────────────────────────────────────────
app.get('/agent/:agentId', async (c) => {
  const agentKey = c.req.param('agentId').toLowerCase();
  const agent = AGENTS[agentKey];
  if (!agent) return c.text('Agent not found', 404);

  // ── Contacts in this territory — MV verdict joined in (BAR-417) ──
  const { results: companies } = await c.env.D1_OUTREACH.prepare(`
    SELECT sw.outreach_id, sw.canonical_name, sw.company_name, sw.company_domain, sw.state, sw.city,
           sw.employees, sw.slot_type, sw.person_first_name, sw.person_last_name, sw.person_email,
           sw.company_phone, sw.hunter_phone, sw.readiness_tier, sw.person_linkedin,
           CASE WHEN ${MV_OK} THEN 1 ELSE 0 END AS mv_verified,
           pm.email_verification_source AS mv_source
    FROM slot_workbench sw
    LEFT JOIN people_people_master pm ON sw.person_unique_id = pm.unique_id
    WHERE sw.service_agents LIKE ? AND sw.has_name = 1 AND sw.has_email = 1
    ORDER BY sw.canonical_name, sw.company_name, sw.slot_type
  `).bind(`%${agent.id}%`).all();

  // ── Sent / delivered / bounced for this agent ──
  // lcs_mid_sequence_state (spine) → lcs_cid (communication_id) → lcs_signal_queue (agent_number)
  let sentStats: Record<string, number> = {};
  try {
    const { results: midRows } = await c.env.D1_SPINE.prepare(`
      SELECT m.delivery_status AS status, COUNT(*) AS n
      FROM lcs_mid_sequence_state m
      JOIN lcs_cid c ON c.communication_id = m.communication_id
      JOIN lcs_signal_queue s ON s.id = c.signal_queue_id
      WHERE s.agent_number = ?
      GROUP BY m.delivery_status
    `).bind(agent.id).all<{ status: string; n: number }>();
    for (const r of midRows ?? []) sentStats[String(r.status)] = Number(r.n);
  } catch {
    // non-blocking — if the join schema shifts, show zeros rather than 500
  }
  const delivered = sentStats['DELIVERED'] ?? 0;
  const bounced = sentStats['BOUNCED'] ?? 0;
  const sentOnly = sentStats['SENT'] ?? 0;
  const scheduled = sentStats['SCHEDULED'] ?? 0;
  const totalTouched = delivered + bounced + sentOnly;
  const bounceRate = totalTouched > 0 ? ((bounced / totalTouched) * 100).toFixed(1) : '0.0';

  // Group contacts by company
  const companyMap = new Map<string, any>();
  for (const row of companies) {
    const key = row.outreach_id as string;
    if (!companyMap.has(key)) {
      companyMap.set(key, {
        outreach_id: key,
        name: row.canonical_name || row.company_name || 'Unknown',
        domain: row.company_domain || '',
        state: row.state || '',
        city: row.city || '',
        employees: row.employees || 0,
        company_phone: row.company_phone || '',
        contacts: [],
      });
    }
    companyMap.get(key)!.contacts.push({
      slot: row.slot_type,
      first: row.person_first_name,
      last: row.person_last_name,
      email: row.person_email,
      mv_verified: !!row.mv_verified,
      mv_source: row.mv_source || '',
      person_phone: row.hunter_phone || '',
      linkedin: row.person_linkedin || '',
      tier: row.readiness_tier,
    });
  }

  const companyList = Array.from(companyMap.values()).sort((a, b) => a.name.localeCompare(b.name));
  const totalContacts = companyList.reduce((sum, co) => sum + co.contacts.length, 0);
  const verifiedContacts = companyList.reduce((sum, co) => sum + co.contacts.filter((ct: any) => ct.mv_verified).length, 0);

  const html = `<!DOCTYPE html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>${agent.name} — Outreach Territory</title>
<style>
  body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; max-width: 1280px; margin: 0 auto; padding: 20px; background: #f8f9fa; color: #1a1a1a; }
  h1 { font-size: 1.5rem; border-bottom: 2px solid #1a1a1a; padding-bottom: 8px; }
  h2.section { font-size: 1rem; color: #666; text-transform: uppercase; letter-spacing: 0.05em; margin: 28px 0 8px; }
  .stats { display: flex; gap: 16px; margin: 16px 0; flex-wrap: wrap; }
  .stat { background: white; border-radius: 8px; padding: 14px 22px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); min-width: 110px; }
  .stat .num { font-size: 1.8rem; font-weight: 700; color: #2563eb; }
  .stat.good .num { color: #16a34a; }
  .stat.warn .num { color: #d97706; }
  .stat.bad .num { color: #dc2626; }
  .stat .label { color: #666; font-size: 0.8rem; }
  .controls { margin: 18px 0; display: flex; gap: 12px; align-items: center; flex-wrap: wrap; }
  .btn { background: #2563eb; color: white; border: none; padding: 10px 20px; border-radius: 6px; cursor: pointer; font-size: 0.9rem; font-weight: 500; }
  .btn:hover { background: #1d4ed8; }
  .btn-outline { background: white; color: #2563eb; border: 1px solid #2563eb; }
  input[type=search] { padding: 10px 16px; border: 1px solid #d1d5db; border-radius: 6px; font-size: 0.9rem; width: 300px; }
  table { width: 100%; border-collapse: collapse; background: white; border-radius: 8px; overflow: hidden; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }
  th { background: #1a1a1a; color: white; padding: 10px 12px; text-align: left; font-size: 0.78rem; text-transform: uppercase; letter-spacing: 0.04em; }
  td { padding: 8px 12px; border-bottom: 1px solid #eee; font-size: 0.85rem; }
  tr:hover td { background: #f1f5f9; }
  .verified { color: #16a34a; font-weight: 600; }
  .unverified { color: #dc2626; }
  a { color: #2563eb; text-decoration: none; }
  a:hover { text-decoration: underline; }
  .back { margin-bottom: 16px; display: inline-block; }
</style></head><body>
<a href="/" class="back">&larr; All Agents</a>
<h1>${agent.name} — Outreach Territory (${agent.id})</h1>

<h2 class="section">Outreach sent (this agent's territory)</h2>
<div class="stats">
  <div class="stat"><div class="num">${totalTouched}</div><div class="label">Messages out</div></div>
  <div class="stat good"><div class="num">${delivered}</div><div class="label">Delivered</div></div>
  <div class="stat warn"><div class="num">${sentOnly}</div><div class="label">Sent (pending)</div></div>
  <div class="stat warn"><div class="num">${scheduled}</div><div class="label">Scheduled</div></div>
  <div class="stat ${Number(bounceRate) > 2 ? 'bad' : 'good'}"><div class="num">${bounced}</div><div class="label">Bounced (${bounceRate}%)</div></div>
</div>

<h2 class="section">Contacts to work</h2>
<div class="stats">
  <div class="stat"><div class="num">${companyList.length}</div><div class="label">Companies</div></div>
  <div class="stat"><div class="num">${totalContacts}</div><div class="label">Contacts</div></div>
  <div class="stat good"><div class="num">${verifiedContacts}</div><div class="label">MV-verified</div></div>
</div>
<div class="controls">
  <input type="search" id="search" placeholder="Search companies..." onkeyup="filterTable()">
  <button class="btn" onclick="exportCSV(false)">Export All (CSV)</button>
  <button class="btn btn-outline" onclick="exportCSV(true)">Export MV-Verified Only</button>
</div>
<table id="data">
<thead><tr><th>Company</th><th>City</th><th>State</th><th>Emp</th><th>Role</th><th>Name</th><th>Email</th><th>MV&nbsp;Verified</th><th>Person&nbsp;Phone</th><th>Company&nbsp;Phone</th><th>LinkedIn</th></tr></thead>
<tbody>
${companyList.map(co => co.contacts.map((ct: any, i: number) => `<tr data-company="${co.name.toLowerCase()}" data-verified="${ct.mv_verified ? 1 : 0}">
  <td>${i === 0 ? co.name : ''}</td>
  <td>${i === 0 ? co.city : ''}</td>
  <td>${i === 0 ? co.state : ''}</td>
  <td>${i === 0 ? co.employees : ''}</td>
  <td>${ct.slot ?? ''}</td>
  <td>${(ct.first ?? '')} ${(ct.last ?? '')}</td>
  <td><a href="mailto:${ct.email ?? ''}">${ct.email ?? ''}</a></td>
  <td class="${ct.mv_verified ? 'verified' : 'unverified'}">${ct.mv_verified ? 'Yes' : 'No'}</td>
  <td>${ct.person_phone ?? ''}</td>
  <td>${i === 0 ? (co.company_phone ?? '') : ''}</td>
  <td>${ct.linkedin ? `<a href="${ct.linkedin}" target="_blank">profile</a>` : ''}</td>
</tr>`).join('')).join('')}
</tbody></table>

<script>
function filterTable() {
  const q = document.getElementById('search').value.toLowerCase();
  document.querySelectorAll('#data tbody tr').forEach(r => {
    r.style.display = r.dataset.company.includes(q) ? '' : 'none';
  });
}

function exportCSV(verifiedOnly) {
  const rows = [['Company','City','State','Employees','Role','First Name','Last Name','Email','MV Verified','MV Source','Person Phone','Company Phone','LinkedIn']];
  const data = ${JSON.stringify(companyList)};
  data.forEach(co => co.contacts.forEach(ct => {
    if (verifiedOnly && !ct.mv_verified) return;
    rows.push([co.name, co.city, co.state, co.employees, ct.slot, ct.first, ct.last, ct.email, ct.mv_verified ? 'Yes' : 'No', ct.mv_source || '', ct.person_phone || '', co.company_phone || '', ct.linkedin || '']);
  }));
  const csv = rows.map(r => r.map(v => '"' + String(v == null ? '' : v).replace(/"/g, '""') + '"').join(',')).join('\\n');
  const blob = new Blob([csv], { type: 'text/csv' });
  const a = document.createElement('a');
  a.href = URL.createObjectURL(blob);
  a.download = '${agent.id}-' + (verifiedOnly ? 'mv-verified' : 'all') + '-' + new Date().toISOString().slice(0,10) + '.csv';
  a.click();
}
</script>
</body></html>`;
  return c.html(html);
});

export default app;
