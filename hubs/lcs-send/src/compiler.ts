// ═══════════════════════════════════════════════════════════════
// LCS Hub — Compiler (CID → SID → MID)
// ═══════════════════════════════════════════════════════════════
// CID compiles. SID thinks. MID ships.
// This is the WATER flowing through the LCS pipes.
// ═══════════════════════════════════════════════════════════════

import type {
  Env, CompiledCid, DesignedSid, MessagePackage,
  CampaignType, AudiencePath, TargetSlot, SidMessage,
  PipelineJob,
} from './types';
import { mintId, logEvent, logError, isSuppressed, suppress } from './utils';
import { runGateStack, allGatesPassed, type CompanyData, type SignalPresence } from './gates';
import { deliver } from './spokes/delivery';

// ── Stage 1: CID Compilation ────────────────────────────────

export async function compileCid(
  env: Env,
  sovereignCompanyId: string,
  signalIds: string[],
): Promise<CompiledCid | null> {
  const cidId = mintId('CID');

  try {
    // 1. Fetch signals from D1
    const placeholders = signalIds.map(() => '?').join(',');
    const signals = await env.D1.prepare(
      `SELECT * FROM signal_queue WHERE signal_id IN (${placeholders})`
    ).bind(...signalIds).all();

    if (!signals.results || signals.results.length === 0) {
      await logError(env.D1, {
        sovereign_company_id: sovereignCompanyId,
        cid_id: cidId,
        stage: 'cid',
        error_type: 'no_signals',
        error_message: 'No signals found for compilation',
      });
      return null;
    }

    // 2. Fetch company data from Neon vault
    // TODO: Replace with actual Neon query via Hyperdrive when wired
    // For now, build from signal payloads + D1 cache
    const companyData = await fetchCompanyData(env, sovereignCompanyId);
    if (!companyData) {
      await logError(env.D1, {
        sovereign_company_id: sovereignCompanyId,
        cid_id: cidId,
        stage: 'cid',
        error_type: 'company_not_found',
        error_message: `Company ${sovereignCompanyId} not found in vault`,
      });
      return null;
    }

    // 3. Build signal presence for gate evaluation
    const signalPresence: SignalPresence = {
      has_talent_flow_signal: signals.results.some(
        (s: any) => s.worker === 'TALENT_FLOW'
      ),
      has_blog_signal: signals.results.some(
        (s: any) => s.worker === 'BLOG'
      ),
      active_signal_count: signals.results.length,
      signal_types: signals.results.map((s: any) => s.signal_type),
    };

    // 4. Run gate stack
    const gateResults = runGateStack(companyData, signalPresence);

    // 5. Check if company passes gates
    const status = allGatesPassed(gateResults) ? 'compiled' : 'blocked';

    // 6. Compile intelligence layers
    const layers = {
      financial: buildFinancialLayer(companyData),
      personnel: buildPersonnelLayer(companyData),
      behavioral: buildBehavioralLayer(signals.results),
      movement: buildMovementLayer(signals.results),
      engagement: await buildEngagementLayer(env.D1, sovereignCompanyId),
    };

    // 7. Write CID to D1
    const cid: CompiledCid = {
      cid_id: cidId,
      sovereign_company_id: sovereignCompanyId,
      assigned_agent: companyData.assigned_agent,
      signal_ids: signalIds,
      layers,
      gate_results: gateResults,
      status,
    };

    await env.D1.prepare(`
      INSERT INTO cid (cid_id, sovereign_company_id, assigned_agent, signal_ids,
        layer_financial, layer_personnel, layer_behavioral, layer_movement, layer_engagement,
        gate_results, status)
      VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    `).bind(
      cid.cid_id,
      cid.sovereign_company_id,
      cid.assigned_agent,
      JSON.stringify(cid.signal_ids),
      JSON.stringify(cid.layers.financial),
      JSON.stringify(cid.layers.personnel),
      JSON.stringify(cid.layers.behavioral),
      JSON.stringify(cid.layers.movement),
      JSON.stringify(cid.layers.engagement),
      JSON.stringify(cid.gate_results),
      cid.status,
    ).run();

    // 8. Mark signals as compiled
    await env.D1.prepare(
      `UPDATE signal_queue SET status = 'compiled', updated_at = datetime('now') WHERE signal_id IN (${placeholders})`
    ).bind(...signalIds).run();

    // 9. Log event
    await logEvent(env.D1, {
      sovereign_company_id: sovereignCompanyId,
      cid_id: cidId,
      event_type: status === 'compiled' ? 'cid_compiled' : 'cid_failed',
      event_data: {
        signal_count: signalIds.length,
        gates_passed: gateResults.filter(g => g.passed).length,
        gates_total: gateResults.length,
        status,
      },
    });

    // 10. If compiled, queue SID design
    if (status === 'compiled') {
      await env.LCS_QUEUE.send({
        job_type: 'design_sid',
        sovereign_company_id: sovereignCompanyId,
        cid_id: cidId,
      });
    }

    return cid;
  } catch (err) {
    const msg = err instanceof Error ? err.message : String(err);
    await logError(env.D1, {
      sovereign_company_id: sovereignCompanyId,
      cid_id: cidId,
      stage: 'cid',
      error_type: 'compilation_error',
      error_message: msg,
    });
    return null;
  }
}

// ── Stage 2: SID Design ─────────────────────────────────────

export async function designSid(
  env: Env,
  cidId: string,
): Promise<DesignedSid | null> {
  const sidId = mintId('SID');

  try {
    // 1. Read the compiled CID
    const cidRow = await env.D1.prepare('SELECT * FROM cid WHERE cid_id = ?')
      .bind(cidId).first<any>();

    if (!cidRow || cidRow.status !== 'compiled') {
      await logError(env.D1, {
        cid_id: cidId,
        stage: 'sid',
        error_type: 'invalid_cid',
        error_message: `CID ${cidId} not found or not compiled`,
      });
      return null;
    }

    const personnel = JSON.parse(cidRow.layer_personnel || '{}');
    const movement = JSON.parse(cidRow.layer_movement || '{}');
    const financial = JSON.parse(cidRow.layer_financial || '{}');
    const signals = JSON.parse(cidRow.signal_ids || '[]');
    const engagement = JSON.parse(cidRow.layer_engagement || '{}');

    // 2. Determine campaign type from signal combination
    const campaignType = determineCampaignType(movement, financial, signals);

    // 3. Route to audience — pick the target slot
    const { path, slot, name, email, linkedin } = pickAudience(personnel, campaignType);

    // 4. Check suppression
    if (email && await isSuppressed(env.D1, 'email', email)) {
      await logEvent(env.D1, {
        sovereign_company_id: cidRow.sovereign_company_id,
        cid_id: cidId,
        sid_id: sidId,
        event_type: 'suppressed',
        event_data: { email, reason: 'suppression_list' },
      });
      return null;
    }

    // 5. Query svg-brain for relevant content
    const contentSources = await querySvgBrain(env, campaignType, path);

    // 6. Build message sequence
    const messages = buildMessageSequence(campaignType, path, {
      company_name: personnel.company_name ?? 'your company',
      target_name: name,
      financial,
      movement,
      content: contentSources,
    });

    // 7. Write SID to D1
    const sid: DesignedSid = {
      sid_id: sidId,
      cid_id: cidId,
      sovereign_company_id: cidRow.sovereign_company_id,
      campaign_type: campaignType,
      audience_path: path,
      target_slot: slot,
      target_name: name,
      target_email: email,
      target_linkedin: linkedin,
      messages,
      content_sources: contentSources.map((c: any) => c.chunk_id ?? c.title ?? 'unknown'),
      monte_carlo_ref: null,  // TODO: wire Monte Carlo
    };

    await env.D1.prepare(`
      INSERT INTO sid (sid_id, cid_id, sovereign_company_id, campaign_type, audience_path,
        target_slot, target_name, target_email, target_linkedin,
        message_count, messages, content_sources, monte_carlo_ref, status)
      VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'designed')
    `).bind(
      sid.sid_id,
      sid.cid_id,
      sid.sovereign_company_id,
      sid.campaign_type,
      sid.audience_path,
      sid.target_slot,
      sid.target_name,
      sid.target_email,
      sid.target_linkedin,
      sid.messages.length,
      JSON.stringify(sid.messages),
      JSON.stringify(sid.content_sources),
      null,
    ).run();

    // 8. Log event
    await logEvent(env.D1, {
      sovereign_company_id: cidRow.sovereign_company_id,
      cid_id: cidId,
      sid_id: sidId,
      event_type: 'sid_designed',
      event_data: {
        campaign_type: campaignType,
        audience_path: path,
        target_slot: slot,
        message_count: messages.length,
      },
    });

    // 9. Queue first MID for delivery
    await env.LCS_QUEUE.send({
      job_type: 'deliver_mid',
      sovereign_company_id: cidRow.sovereign_company_id,
      sid_id: sidId,
      cid_id: cidId,
    });

    return sid;
  } catch (err) {
    const msg = err instanceof Error ? err.message : String(err);
    await logError(env.D1, {
      cid_id: cidId,
      sid_id: sidId,
      stage: 'sid',
      error_type: 'design_error',
      error_message: msg,
    });
    return null;
  }
}

// ── Stage 3: MID Delivery ───────────────────────────────────

export async function deliverMid(
  env: Env,
  sidId: string,
): Promise<void> {
  try {
    // 1. Read the SID
    const sidRow = await env.D1.prepare('SELECT * FROM sid WHERE sid_id = ?')
      .bind(sidId).first<any>();

    if (!sidRow || sidRow.status === 'completed' || sidRow.status === 'stopped') {
      return;
    }

    const messages: SidMessage[] = JSON.parse(sidRow.messages || '[]');

    // 2. Find the next message to send (check what's already been delivered)
    const deliveredCount = await env.D1.prepare(
      "SELECT COUNT(*) as cnt FROM mid WHERE sid_id = ? AND delivery_status NOT IN ('failed')"
    ).bind(sidId).first<{ cnt: number }>();

    const nextSeq = (deliveredCount?.cnt ?? 0) + 1;
    const nextMessage = messages.find(m => m.sequence_num === nextSeq);

    if (!nextMessage) {
      // Campaign complete — all messages sent
      await env.D1.prepare(
        "UPDATE sid SET status = 'completed', updated_at = datetime('now') WHERE sid_id = ?"
      ).bind(sidId).run();
      await logEvent(env.D1, {
        sovereign_company_id: sidRow.sovereign_company_id,
        sid_id: sidId,
        event_type: 'campaign_completed',
      });
      return;
    }

    // 3. Build message package
    const midId = `MID-${sidId.slice(4)}-${String(nextSeq).padStart(2, '0')}-${nextMessage.channel}`;
    const pkg: MessagePackage = {
      mid_id: midId,
      sid_id: sidId,
      cid_id: sidRow.cid_id,
      sovereign_company_id: sidRow.sovereign_company_id,
      sequence_num: nextSeq,
      channel: nextMessage.channel,
      path_type: determinPathType(sidRow),
      recipient_email: sidRow.target_email,
      recipient_linkedin: sidRow.target_linkedin,
      subject: nextMessage.subject,
      body_plain: nextMessage.body_plain,
      body_html: nextMessage.body_html,
    };

    // 4. Write MID record (queued)
    await env.D1.prepare(`
      INSERT INTO mid (mid_id, sid_id, cid_id, sovereign_company_id, sequence_num,
        channel, path_type, recipient_email, recipient_linkedin,
        subject, body_plain, body_html, delivery_status)
      VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'queued')
    `).bind(
      pkg.mid_id, pkg.sid_id, pkg.cid_id, pkg.sovereign_company_id,
      pkg.sequence_num, pkg.channel, pkg.path_type,
      pkg.recipient_email, pkg.recipient_linkedin,
      pkg.subject, pkg.body_plain, pkg.body_html,
    ).run();

    // 5. Deliver
    const result = await deliver(env, pkg);

    // 6. Update MID status
    const newStatus = result.success ? 'sent' : 'failed';
    await env.D1.prepare(
      `UPDATE mid SET delivery_status = ?, sent_at = datetime('now'), updated_at = datetime('now') WHERE mid_id = ?`
    ).bind(newStatus, midId).run();

    // 7. If failed, check strike count
    if (!result.success) {
      const strikes = await env.D1.prepare(
        "SELECT COUNT(*) as cnt FROM err0 WHERE sovereign_company_id = ? AND stage = 'mid'"
      ).bind(pkg.sovereign_company_id).first<{ cnt: number }>();

      const strikeCount = (strikes?.cnt ?? 0);
      if (strikeCount >= 3) {
        // Strike 3 — suppress
        if (pkg.recipient_email) {
          await suppress(env.D1, {
            sovereign_company_id: pkg.sovereign_company_id,
            entity_type: 'email',
            entity_value: pkg.recipient_email,
            reason: 'strike_3',
          });
        }
        await env.D1.prepare(
          "UPDATE sid SET status = 'stopped', updated_at = datetime('now') WHERE sid_id = ?"
        ).bind(sidId).run();
        await logEvent(env.D1, {
          sovereign_company_id: pkg.sovereign_company_id,
          sid_id: sidId,
          mid_id: midId,
          event_type: 'strike_3',
          event_data: { strike_count: strikeCount, suppressed: pkg.recipient_email },
        });
      }
    }
  } catch (err) {
    const msg = err instanceof Error ? err.message : String(err);
    await logError(env.D1, {
      sid_id: sidId,
      stage: 'mid',
      error_type: 'delivery_error',
      error_message: msg,
    });
  }
}

// ── Helper Functions ────────────────────────────────────────

async function fetchCompanyData(env: Env, sovereignCompanyId: string): Promise<CompanyData | null> {
  // Read from D1 workspace — company data seeded from Neon vault
  // Neon is the vault. D1 is the workspace. All processing on D1.
  const row = await env.D1.prepare(
    'SELECT * FROM company WHERE sovereign_company_id = ?'
  ).bind(sovereignCompanyId).first<any>();

  if (!row) return null;

  return {
    sovereign_company_id: row.sovereign_company_id,
    company_name: row.company_name,
    state: row.state,
    zip: row.zip,
    employee_count: row.employee_count,
    assigned_agent: row.assigned_agent,
    has_5500_filing: row.has_5500_filing === 1,
    renewal_month: row.renewal_month,
    premium_current: row.premium_current,
    premium_prior: row.premium_prior,
    carrier_current: row.carrier_current,
    carrier_prior: row.carrier_prior,
    broker_current: row.broker_current,
    broker_prior: row.broker_prior,
    ceo_name: row.ceo_name,
    ceo_email: row.ceo_email,
    cfo_name: row.cfo_name,
    cfo_email: row.cfo_email,
    hr_name: row.hr_name,
    hr_email: row.hr_email,
  };
}

function buildFinancialLayer(company: CompanyData): Record<string, unknown> {
  return {
    has_5500: company.has_5500_filing,
    renewal_month: company.renewal_month,
    premium_current: company.premium_current,
    premium_prior: company.premium_prior,
    carrier_current: company.carrier_current,
    broker_current: company.broker_current,
    employee_count: company.employee_count,
  };
}

function buildPersonnelLayer(company: CompanyData): Record<string, unknown> {
  return {
    company_name: company.company_name,
    ceo: { name: company.ceo_name, email: company.ceo_email },
    cfo: { name: company.cfo_name, email: company.cfo_email },
    hr: { name: company.hr_name, email: company.hr_email },
  };
}

function buildBehavioralLayer(signals: any[]): Record<string, unknown> {
  const blogSignals = signals.filter((s: any) => s.worker === 'BLOG');
  return {
    signals: blogSignals.map((s: any) => ({
      type: s.signal_type,
      magnitude: s.magnitude,
      created_at: s.created_at,
    })),
  };
}

function buildMovementLayer(signals: any[]): Record<string, unknown> {
  const tfSignals = signals.filter((s: any) => s.worker === 'TALENT_FLOW');
  const peopleSignals = signals.filter((s: any) => s.worker === 'PEOPLE');
  return {
    talent_flow: tfSignals.map((s: any) => ({
      type: s.signal_type,
      magnitude: s.magnitude,
    })),
    people: peopleSignals.map((s: any) => ({
      type: s.signal_type,
    })),
  };
}

async function buildEngagementLayer(
  d1: D1Database,
  sovereignCompanyId: string,
): Promise<Record<string, unknown>> {
  // Check previous campaigns
  const prevSids = await d1.prepare(
    "SELECT sid_id, campaign_type, status, created_at FROM sid WHERE sovereign_company_id = ? ORDER BY created_at DESC LIMIT 10"
  ).bind(sovereignCompanyId).all();

  const prevMids = await d1.prepare(
    "SELECT mid_id, delivery_status, channel, created_at FROM mid WHERE sovereign_company_id = ? ORDER BY created_at DESC LIMIT 20"
  ).bind(sovereignCompanyId).all();

  return {
    previous_campaigns: prevSids.results ?? [],
    previous_deliveries: prevMids.results ?? [],
    total_campaigns: prevSids.results?.length ?? 0,
    total_deliveries: prevMids.results?.length ?? 0,
  };
}

function determineCampaignType(
  movement: Record<string, unknown>,
  financial: Record<string, unknown>,
  signalIds: string[],
): CampaignType {
  const tf = (movement.talent_flow as any[]) ?? [];
  const hasDolSignal = financial.renewal_month !== null || financial.premium_current !== null;

  // Multiple signals = priority (hot company)
  if (signalIds.length >= 3) return 'priority';
  // Talent flow = exec change
  if (tf.length > 0) return 'exec_change';
  // DOL = renewal
  if (hasDolSignal) return 'renewal';
  // Blog or other = activity
  if (signalIds.length > 0) return 'activity';
  // No signals = monthly touch
  return 'monthly_touch';
}

function pickAudience(
  personnel: Record<string, unknown>,
  campaignType: CampaignType,
): { path: AudiencePath; slot: TargetSlot; name: string | null; email: string | null; linkedin: string | null } {
  const cfo = personnel.cfo as any;
  const ceo = personnel.ceo as any;
  const hr = personnel.hr as any;

  // Default: money path for CFO/CEO, workload path for HR
  // Priority: CFO first (money person), then CEO, then HR
  if (cfo?.email) {
    return { path: 'cfo_ceo_money', slot: 'CFO', name: cfo.name, email: cfo.email, linkedin: null };
  }
  if (ceo?.email) {
    return { path: 'cfo_ceo_money', slot: 'CEO', name: ceo.name, email: ceo.email, linkedin: null };
  }
  if (hr?.email) {
    return { path: 'hr_workload', slot: 'HR', name: hr.name, email: hr.email, linkedin: null };
  }

  // No email — try LinkedIn
  if (cfo?.linkedin) {
    return { path: 'cfo_ceo_money', slot: 'CFO', name: cfo.name, email: null, linkedin: cfo.linkedin };
  }

  // Last resort
  return { path: 'cfo_ceo_money', slot: 'CFO', name: null, email: null, linkedin: null };
}

async function querySvgBrain(
  env: Env,
  campaignType: CampaignType,
  audiencePath: AudiencePath,
): Promise<any[]> {
  const queryMap: Record<string, string> = {
    renewal: 'renewal cost savings premium increase employer group benefits strategy',
    exec_change: 'new executive leadership change benefits review onboarding',
    activity: 'company growth expansion benefits consulting',
    priority: 'cost savings insurance informatics 10 percent high cost management',
    monthly_touch: 'benefits consulting value proposition introduction',
  };

  const query = queryMap[campaignType] ?? queryMap.monthly_touch;

  try {
    const resp = await fetch(`${env.SVG_BRAIN_URL}/query`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${env.SVG_BRAIN_API_KEY}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        query,
        domain: audiencePath === 'cfo_ceo_money' ? 'fin' : 'client',
        top_k: 5,
      }),
    });

    if (!resp.ok) return [];
    const data = await resp.json<{ results: any[] }>();
    return data.results ?? [];
  } catch {
    return [];
  }
}

function buildMessageSequence(
  campaignType: CampaignType,
  path: AudiencePath,
  context: {
    company_name: string;
    target_name: string | null;
    financial: Record<string, unknown>;
    movement: Record<string, unknown>;
    content: any[];
  },
): SidMessage[] {
  const name = context.target_name ?? 'there';
  const company = context.company_name;

  // Patton tone. Authority. Data-led. No begging.
  if (campaignType === 'monthly_touch') {
    return [{
      sequence_num: 1,
      channel: 'MG',
      subject: `${company} — quick data point`,
      body_plain: `${name},\n\nDave Barton here. I run insurance informatics — the intersection of 25 years in benefits and the data infrastructure to actually manage it.\n\nMost brokers sell products. I manage the 10% of your population that drives 85% of your cost. Nobody else does this because nobody else has the system.\n\nIf that's interesting, I'll show you the dashboard. If not, no sweat.\n\nDave Barton\nSVG Agency`,
      body_html: '',
      condition: null,
    }];
  }

  // Campaign messages — expandable
  const touchCount = campaignType === 'priority' ? 5
    : campaignType === 'renewal' ? 4
    : campaignType === 'exec_change' ? 3
    : 3;

  const messages: SidMessage[] = [];
  for (let i = 1; i <= touchCount; i++) {
    messages.push({
      sequence_num: i,
      channel: i <= 3 ? 'MG' : 'HR',  // First 3 email, then LinkedIn
      subject: `${company} — ${getCampaignSubject(campaignType, i)}`,
      body_plain: getCampaignBody(campaignType, path, i, name, context),
      body_html: '',
      condition: i > 1 ? `if message ${i - 1} delivered but no CTA click` : null,
    });
  }

  return messages;
}

function getCampaignSubject(type: CampaignType, seq: number): string {
  const subjects: Record<string, string[]> = {
    renewal: ['your renewal data', 'the 10% problem', 'what your broker won\'t show you', 'last look'],
    exec_change: ['new role, new data', 'what the last guy didn\'t fix', 'the system'],
    activity: ['saw your news', 'data behind the growth', 'the 10% question'],
    priority: ['your numbers', 'the 85% you\'re ignoring', 'what I built', 'the dashboard', 'last chance to look'],
  };
  const list = subjects[type] ?? subjects.activity;
  return list[Math.min(seq - 1, list.length - 1)];
}

function getCampaignBody(
  type: CampaignType,
  path: AudiencePath,
  seq: number,
  name: string,
  context: any,
): string {
  // Message 1 — always the opener
  if (seq === 1) {
    if (path === 'cfo_ceo_money') {
      return `${name},\n\nDave Barton. I do insurance informatics — 25 years in benefits plus the data systems to actually manage cost.\n\n10% of your employees cause 85% of your claims cost. Your broker manages products. I manage that 10%.\n\nI built a system that watches your data 365 days a year. Not once at renewal. Every day.\n\nIf you want to see it, I'll show you the dashboard. Takes 15 minutes.\n\nDave Barton\nSVG Agency`;
    }
    return `${name},\n\nDave Barton. I run insurance informatics at SVG Agency.\n\nI built a system that handles enrollment, vendor management, tickets, and renewals — so HR doesn't have to. Your team gets a portal. I handle the 10% of employees that cause 85% of the headaches.\n\nIf that sounds useful, I'll show you what the portal looks like. 15 minutes.\n\nDave Barton\nSVG Agency`;
  }

  // Subsequent messages — shorter, different angle
  if (path === 'cfo_ceo_money') {
    return `${name},\n\nFollowing up. The data on your group is worth looking at — most employers in your size range are overpaying because nobody's managing the 10% that drives 85% of cost.\n\nI'm not selling a product. I manage the problem. Lead, follow, or get out of the way.\n\n15 minutes. That's all I need.\n\nDave Barton\nSVG Agency`;
  }
  return `${name},\n\nQuick follow-up. The system I built takes benefits admin off HR's plate completely — enrollment, tickets, vendor exports, renewal tracking. All in one portal.\n\nYour current broker isn't doing this. Nobody is. I built it because it didn't exist.\n\n15 minutes to see it.\n\nDave Barton\nSVG Agency`;
}

function determinPathType(sidRow: any): 'WARM' | 'COLD' {
  // TODO: Determine from CID reachability layer (SocialSweep data)
  // For now, default to COLD
  return 'COLD';
}
