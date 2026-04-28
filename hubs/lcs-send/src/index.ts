/**
 * LCS Hub — Main Entry Point
 *
 * The plumbing. Hub-spoke architecture.
 * All logic in the hub. Spokes are dumb transport.
 *
 * Three handlers:
 *   scheduled() — PRODUCER: cron trigger, scans for pending signals, queues jobs
 *   queue()     — CONSUMER: processes pipeline jobs (CID → SID → MID)
 *   fetch()     — HTTP API: signal ingestion, webhook receivers, health/status
 *
 * D1 = workspace (edge). Neon = vault (source of truth).
 * All integrations through Composio.
 */

import type { Env, PipelineJob } from './types';
import { ingestSignal, ingestSignalBatch } from './spokes/signal-intake';
import { compileCid, constructSid, deliverMid, runPipeline, isSequenceConditionMet } from './compiler-v2';
import { isBounceRateHealthy, nextWarmupCap } from './deliverability';
import { discoverDolSchema, seedDolForEin, fullDolDump, fullCompanyDump, seedDolToD1, batchSeedAllCompanies, seedFixPeopleMaster, seedFixMissingSlots, seedFixAgentAssignment, seedFixMatchPeopleToSlots, seedFullPeopleMaster, seedGlobalZipCodes, seedClean } from './seed';
import { logEvent } from './utils';

export default {
  // ── Cron Trigger (Producer) ──────────────────────────────
  // Scans for pending signals, groups by company, queues compilation jobs.

  async scheduled(
    _controller: ScheduledController,
    env: Env,
    _ctx: ExecutionContext,
  ): Promise<void> {
    console.log('[scheduled] LCS Hub — cron triggered');

    try {
      // ── Domain Warmup Ramp Logic ────────────────────────────
      // Runs BEFORE daily reset so we can check yesterday's bounce rates.

      // 1. Auto-pause: any domain with bounce_count_24h > 5% of sent_today
      const domainsForBounceCheck = await env.D1.prepare(
        "SELECT domain, sent_today, bounce_count_24h FROM lcs_domain_rotation WHERE sent_today > 0 AND is_paused = 0"
      ).all<{ domain: string; sent_today: number; bounce_count_24h: number }>();

      for (const d of domainsForBounceCheck.results ?? []) {
        const bounceRate = d.bounce_count_24h / d.sent_today;
        if (!isBounceRateHealthy(d.sent_today, d.bounce_count_24h)) {
          await env.D1.prepare(
            "UPDATE lcs_domain_rotation SET is_paused = 1, pause_reason = 'bounce_threshold_exceeded', updated_at = datetime('now') WHERE domain = ?"
          ).bind(d.domain).run();
          console.log(`[scheduled] PAUSED domain ${d.domain} — bounce rate ${(bounceRate * 100).toFixed(1)}% (${d.bounce_count_24h}/${d.sent_today})`);
        }
      }

      // 2. Weekly warmup progression — Mondays only
      const today = new Date();
      if (today.getUTCDay() === 1) { // Monday
        const allDomains = await env.D1.prepare(
          "SELECT domain, warmup_week, sent_today, bounce_count_24h, is_paused FROM lcs_domain_rotation"
        ).all<{ domain: string; warmup_week: number; sent_today: number; bounce_count_24h: number; is_paused: number }>();

        for (const d of allDomains.results ?? []) {
          // Skip paused domains — they need manual review before advancing
          if (d.is_paused) continue;

          // Only advance if bounce rate was < 5% (safe sender reputation)
          // For domains that sent nothing, allow advancement (no negative signal)
          const safe = d.sent_today === 0 || isBounceRateHealthy(d.sent_today, d.bounce_count_24h);
          if (!safe) {
            console.log(`[scheduled] Domain ${d.domain} week ${d.warmup_week} — NOT advancing, bounce rate too high`);
            continue;
          }

          const nextWeek = d.warmup_week + 1;
          const newCap = nextWarmupCap(nextWeek);

          await env.D1.prepare(
            "UPDATE lcs_domain_rotation SET warmup_week = ?, daily_cap = ?, updated_at = datetime('now') WHERE domain = ?"
          ).bind(nextWeek, newCap, d.domain).run();
          console.log(`[scheduled] Domain ${d.domain} advanced to week ${nextWeek}, daily_cap = ${newCap}`);
        }
      }

      // 3. Reset daily send counts for domain rotation (AFTER bounce check)
      await env.D1.prepare(
        "UPDATE lcs_domain_rotation SET sent_today = 0, bounce_count_24h = 0, updated_at = datetime('now')"
      ).run();
      console.log('[scheduled] Domain rotation daily counts reset');

      // ── BAR-308: Campaign Scheduler ─────────────────────────
      // Scans lcs_contact_sequence_state for contacts whose next step is due.
      // For each, looks up the step in lcs_sequence_def, checks condition,
      // and inserts a signal into lcs_signal_queue if condition met.

      // 3a. Check domain capacity before scheduling — if all domains at cap, skip
      const domainCapacity = await env.D1.prepare(
        "SELECT SUM(daily_cap - sent_today) as remaining FROM lcs_domain_rotation WHERE is_paused = 0 AND sent_today < daily_cap"
      ).first<{ remaining: number }>();

      // BAR-308 fix: Subtract already-queued SEQUENCE_STEP signals from available capacity
      const pendingSignals = await env.D1.prepare(
        "SELECT COUNT(*) as cnt FROM lcs_signal_queue WHERE signal_category = 'SEQUENCE_STEP' AND status = 'pending'"
      ).first<{cnt: number}>();
      const pendingCount = pendingSignals?.cnt ?? 0;

      const hasCapacity = ((domainCapacity?.remaining ?? 0) - pendingCount) > 0;

      if (hasCapacity) {
        // 3b. Query contacts with due sequence steps (limit 50 per cron run)
        const dueContacts = await env.D1.prepare(`
          SELECT id, sovereign_company_id, contact_email, sequence_id, current_step, last_engagement
          FROM lcs_contact_sequence_state
          WHERE status = 'active'
            AND next_step_after IS NOT NULL
            AND next_step_after <= datetime('now')
          ORDER BY next_step_after ASC
          LIMIT 50
        `).all<{
          id: string;
          sovereign_company_id: string;
          contact_email: string;
          sequence_id: string;
          current_step: number;
          last_engagement: string | null;
        }>();

        let scheduled = 0;
        let skipped = 0;
        let completed = 0;

        for (const contact of dueContacts.results ?? []) {
          // Re-check domain capacity each iteration
          const capCheck = await env.D1.prepare(
            "SELECT COUNT(*) as avail FROM lcs_domain_rotation WHERE is_paused = 0 AND sent_today < daily_cap"
          ).first<{ avail: number }>();
          if ((capCheck?.avail ?? 0) === 0) {
            console.log('[scheduler] All domains at cap — stopping scheduling');
            break;
          }

          const nextStepNum = contact.current_step + 1;

          // Look up the next step definition
          const stepDef = await env.D1.prepare(
            'SELECT frame_id, delay_hours, condition, channel FROM lcs_sequence_def WHERE sequence_id = ? AND step_number = ? AND is_active = 1'
          ).bind(contact.sequence_id, nextStepNum).first<{
            frame_id: string;
            delay_hours: number;
            condition: string | null;
            channel: string;
          }>();

          if (!stepDef) {
            // No more steps — complete the sequence
            await env.D1.prepare(`
              UPDATE lcs_contact_sequence_state
              SET status = 'completed', updated_at = datetime('now')
              WHERE id = ?
            `).bind(contact.id).run();
            completed++;
            continue;
          }

          // BAR-308 fix: Re-read last_engagement to avoid stale batch data (webhook race)
          const freshState = await env.D1.prepare(
            "SELECT last_engagement FROM lcs_contact_sequence_state WHERE contact_email = ? AND status = 'active'"
          ).bind(contact.contact_email).first<any>();
          const currentEngagement = freshState?.last_engagement ?? contact.last_engagement;

          // Check step condition against fresh last_engagement
          const conditionMet = isSequenceConditionMet(stepDef.condition, currentEngagement);

          if (conditionMet) {
            // Insert signal into lcs_signal_queue with this step's frame_id
            const sigId = `SIG-SCHED-${Date.now().toString(36)}-${crypto.randomUUID().slice(0, 8)}`;
            await env.D1.prepare(`
              INSERT INTO lcs_signal_queue (
                id, signal_set_hash, signal_category, sovereign_company_id,
                lifecycle_phase, preferred_channel, preferred_lane, agent_number,
                signal_data, source_hub, source_signal_id, status, priority, created_at
              ) VALUES (?, ?, 'SEQUENCE_STEP', ?, 'OUTREACH', ?, NULL, 'SA-001', ?, 'campaign-scheduler', ?, 'pending', 7, datetime('now'))
            `).bind(
              sigId,
              stepDef.frame_id,
              contact.sovereign_company_id,
              stepDef.channel === 'MG' ? 'email' : 'linkedin',
              JSON.stringify({
                sequence_id: contact.sequence_id,
                step_number: nextStepNum,
                contact_email: contact.contact_email,
                frame_id: stepDef.frame_id,
                trigger: 'campaign_scheduler',
              }),
              contact.id,
            ).run();

            // Advance the sequence state
            const nextDelay = await env.D1.prepare(
              'SELECT delay_hours FROM lcs_sequence_def WHERE sequence_id = ? AND step_number = ? AND is_active = 1'
            ).bind(contact.sequence_id, nextStepNum + 1).first<{ delay_hours: number }>();

            if (nextDelay) {
              const nextAfter = new Date(Date.now() + nextDelay.delay_hours * 3600_000).toISOString();
              await env.D1.prepare(`
                UPDATE lcs_contact_sequence_state
                SET current_step = ?, last_step_at = datetime('now'), next_step_after = ?, updated_at = datetime('now')
                WHERE id = ?
              `).bind(nextStepNum, nextAfter, contact.id).run();
            } else {
              // This was the last step — will complete on next cron
              await env.D1.prepare(`
                UPDATE lcs_contact_sequence_state
                SET current_step = ?, last_step_at = datetime('now'), next_step_after = NULL, updated_at = datetime('now')
                WHERE id = ?
              `).bind(nextStepNum, contact.id).run();
            }

            scheduled++;
          } else {
            // Condition not met — skip to next valid step
            let found = false;
            for (let s = nextStepNum + 1; s <= nextStepNum + 10; s++) {
              const altStep = await env.D1.prepare(
                'SELECT frame_id, delay_hours, condition, channel FROM lcs_sequence_def WHERE sequence_id = ? AND step_number = ? AND is_active = 1'
              ).bind(contact.sequence_id, s).first<{ frame_id: string; delay_hours: number; condition: string | null; channel: string }>();

              if (!altStep) break; // No more steps — complete

              if (isSequenceConditionMet(altStep.condition, currentEngagement)) {
                // Found a valid step — update state to point at it, will fire next cron
                // BAR-308 fix: keep current_step at last executed step, schedule from step s's delay
                const nextAfter = new Date(Date.now() + altStep.delay_hours * 3600_000).toISOString();
                await env.D1.prepare(`
                  UPDATE lcs_contact_sequence_state
                  SET current_step = ?, next_step_after = ?, updated_at = datetime('now')
                  WHERE id = ?
                `).bind(contact.current_step, nextAfter, contact.id).run();
                found = true;
                skipped++;
                break;
              }
            }
            if (!found) {
              // All remaining steps skipped — complete the sequence
              await env.D1.prepare(`
                UPDATE lcs_contact_sequence_state
                SET status = 'completed', updated_at = datetime('now')
                WHERE id = ?
              `).bind(contact.id).run();
              completed++;
            }
          }
        }

        if (scheduled > 0 || skipped > 0 || completed > 0) {
          console.log(`[scheduler] Scheduled: ${scheduled}, Skipped: ${skipped}, Completed: ${completed}`);
        }
      } else {
        console.log('[scheduler] No domain capacity — skipping campaign scheduling');
      }

      // ── BAR-308: No-Response Detector ───────────────────────
      // Detects MIDs that were sent but got no engagement signal after 3 or 7 days.
      // Inserts ENGAGEMENT_RESPONSE signals for the engagement rules to process.

      // 3-day no-response
      // BAR-303 OE-3: JOIN lcs_cid to get signal_set_hash + sovereign_company_id in one query
      const noResponse3d = await env.D1.prepare(`
        SELECT m.mid_id, m.recipient_email, m.communication_id, c.sovereign_company_id, c.signal_set_hash
        FROM lcs_mid_sequence_state m
        JOIN lcs_cid c ON c.communication_id = m.communication_id
        WHERE m.delivery_status = 'SENT'
          AND m.created_at < datetime('now', '-3 days')
          AND m.created_at >= datetime('now', '-4 days')
          AND NOT EXISTS (
            SELECT 1 FROM lcs_event e
            WHERE e.message_run_id = m.message_run_id
              AND e.event_type IN ('MID_OPENED', 'MID_CLICKED', 'MID_REPLIED')
          )
          AND NOT EXISTS (
            SELECT 1 FROM lcs_signal_queue sq
            WHERE sq.source_signal_id = m.mid_id
              AND sq.signal_category = 'ENGAGEMENT_RESPONSE'
              AND json_extract(sq.signal_data, '$.trigger_event') = 'no_response_3d'
          )
        LIMIT 50
      `).all<{ mid_id: string; recipient_email: string; communication_id: string; sovereign_company_id: string; signal_set_hash: string }>();

      for (const mid of noResponse3d.results ?? []) {
        const sigId = `SIG-NR3D-${Date.now().toString(36)}-${crypto.randomUUID().slice(0, 8)}`;
        await env.D1.prepare(`
          INSERT INTO lcs_signal_queue (
            id, signal_set_hash, signal_category, sovereign_company_id,
            lifecycle_phase, preferred_channel, preferred_lane, agent_number,
            signal_data, source_hub, source_signal_id, status, priority, created_at
          ) VALUES (?, ?, 'ENGAGEMENT_RESPONSE', ?, 'OUTREACH', NULL, NULL, 'SA-001', ?, 'no-response-detector', ?, 'pending', 5, datetime('now'))
        `).bind(
          sigId,
          mid.signal_set_hash,
          mid.sovereign_company_id,
          JSON.stringify({
            trigger_event: 'no_response_3d',
            source_mid_id: mid.mid_id,
            contact_email: mid.recipient_email,
          }),
          mid.mid_id,
        ).run();
      }

      // 7-day no-response
      // BAR-303 OE-3: JOIN lcs_cid to get signal_set_hash + sovereign_company_id in one query
      const noResponse7d = await env.D1.prepare(`
        SELECT m.mid_id, m.recipient_email, m.communication_id, c.sovereign_company_id, c.signal_set_hash
        FROM lcs_mid_sequence_state m
        JOIN lcs_cid c ON c.communication_id = m.communication_id
        WHERE m.delivery_status = 'SENT'
          AND m.created_at < datetime('now', '-7 days')
          AND m.created_at >= datetime('now', '-8 days')
          AND NOT EXISTS (
            SELECT 1 FROM lcs_event e
            WHERE e.message_run_id = m.message_run_id
              AND e.event_type IN ('MID_OPENED', 'MID_CLICKED', 'MID_REPLIED')
          )
          AND NOT EXISTS (
            SELECT 1 FROM lcs_signal_queue sq
            WHERE sq.source_signal_id = m.mid_id
              AND sq.signal_category = 'ENGAGEMENT_RESPONSE'
              AND json_extract(sq.signal_data, '$.trigger_event') = 'no_response_7d'
          )
        LIMIT 50
      `).all<{ mid_id: string; recipient_email: string; communication_id: string; sovereign_company_id: string; signal_set_hash: string }>();

      for (const mid of noResponse7d.results ?? []) {
        const sigId = `SIG-NR7D-${Date.now().toString(36)}-${crypto.randomUUID().slice(0, 8)}`;
        await env.D1.prepare(`
          INSERT INTO lcs_signal_queue (
            id, signal_set_hash, signal_category, sovereign_company_id,
            lifecycle_phase, preferred_channel, preferred_lane, agent_number,
            signal_data, source_hub, source_signal_id, status, priority, created_at
          ) VALUES (?, ?, 'ENGAGEMENT_RESPONSE', ?, 'OUTREACH', NULL, NULL, 'SA-001', ?, 'no-response-detector', ?, 'pending', 5, datetime('now'))
        `).bind(
          sigId,
          mid.signal_set_hash,
          mid.sovereign_company_id,
          JSON.stringify({
            trigger_event: 'no_response_7d',
            source_mid_id: mid.mid_id,
            contact_email: mid.recipient_email,
          }),
          mid.mid_id,
        ).run();
      }

      const nr3count = noResponse3d.results?.length ?? 0;
      const nr7count = noResponse7d.results?.length ?? 0;
      if (nr3count > 0 || nr7count > 0) {
        console.log(`[no-response] 3d: ${nr3count}, 7d: ${nr7count} signals inserted`);
      }

      // 4. Find pending signals in spine D1
      const pending = await env.D1.prepare(`
        SELECT id, sovereign_company_id, signal_set_hash, priority
        FROM lcs_signal_queue
        WHERE lower(status) = 'pending'
        ORDER BY priority DESC, created_at ASC
        LIMIT 50
      `).all<{
        id: string;
        sovereign_company_id: string;
        signal_set_hash: string;
        priority: number;
      }>();

      if (!pending.results || pending.results.length === 0) {
        console.log('[scheduled] No pending signals. Done.');
        return;
      }

      console.log(`[scheduled] Found ${pending.results.length} pending signals`);

      // 5. Queue a compilation job for each signal
      let queued = 0;
      for (const signal of pending.results) {
        await env.LCS_QUEUE.send({
          job_type: 'compile_cid',
          sovereign_company_id: signal.sovereign_company_id,
          signal_ids: [signal.id],
        });
        queued++;
      }

      console.log(`[scheduled] Queued ${queued} compilation jobs`);
    } catch (err) {
      console.error(`[scheduled] Producer failed: ${err instanceof Error ? err.message : err}`);
    }
  },

  // ── Queue Consumer ───────────────────────────────────────
  // Processes pipeline jobs: compile_cid → design_sid → deliver_mid

  async queue(
    batch: MessageBatch<PipelineJob>,
    env: Env,
    _ctx: ExecutionContext,
  ): Promise<void> {
    console.log(`[queue] Received batch of ${batch.messages.length} jobs`);

    for (const msg of batch.messages) {
      const job = msg.body;

      try {
        switch (job.job_type) {
          case 'compile_cid': {
            // Each signal gets its own CID compilation
            const signalIds = job.signal_ids ?? [];
            for (const sigId of signalIds) {
              console.log(`[queue] Compiling CID for signal ${sigId}`);
              const cidResult = await compileCid(env, sigId);
              if (cidResult && cidResult.status === 'COMPILED') {
                // Auto-chain: CID → SID
                await env.LCS_QUEUE.send({
                  job_type: 'design_sid',
                  sovereign_company_id: job.sovereign_company_id,
                  cid_id: cidResult.communication_id,
                });
              }
            }
            break;
          }

          case 'design_sid': {
            console.log(`[queue] Constructing SID for ${job.cid_id}`);
            const sidResult = await constructSid(env, job.cid_id!);
            if (sidResult) {
              // Auto-chain: SID → MID
              await env.LCS_QUEUE.send({
                job_type: 'deliver_mid',
                sovereign_company_id: job.sovereign_company_id,
                sid_id: sidResult.sid_id,
              });
            }
            break;
          }

          case 'deliver_mid':
            console.log(`[queue] Delivering MID for SID ${job.sid_id}`);
            await deliverMid(env, job.sid_id!);
            break;

          case 'process_webhook':
            console.log(`[queue] Processing webhook from ${job.webhook_source}`);
            await processWebhook(env, job);
            break;

          default:
            console.error(`[queue] Unknown job type: ${(job as any).job_type}`);
        }

        msg.ack();
      } catch (err) {
        console.error(`[queue] Job failed: ${err instanceof Error ? err.message : err}`);
        msg.retry();
      }
    }
  },

  // ── HTTP API ─────────────────────────────────────────────

  async fetch(
    request: Request,
    env: Env,
    _ctx: ExecutionContext,
  ): Promise<Response> {
    const url = new URL(request.url);
    const path = url.pathname;

    const corsHeaders = {
      'Access-Control-Allow-Origin': '*',
      'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
      'Access-Control-Allow-Headers': 'Content-Type, Authorization',
    };

    if (request.method === 'OPTIONS') {
      return new Response(null, { status: 204, headers: corsHeaders });
    }

    try {
      // ── Health Check ────────────────────────────────────
      if (path === '/health') {
        const signalCount = await env.D1.prepare(
          "SELECT COUNT(*) as cnt FROM lcs_signal_queue"
        ).first<{ cnt: number }>();
        const cidCount = await env.D1.prepare(
          "SELECT COUNT(*) as cnt FROM lcs_cid"
        ).first<{ cnt: number }>();
        const companyCount = await env.D1_OUTREACH.prepare(
          "SELECT COUNT(*) as cnt FROM outreach_company_target"
        ).first<{ cnt: number }>();

        // Domain rotation status
        const domains = await env.D1.prepare(
          "SELECT domain, sent_today, daily_cap, total_sent, is_paused, warmup_week FROM lcs_domain_rotation ORDER BY domain"
        ).all();
        const domainsAvailable = (domains.results ?? []).filter((d: any) => !d.is_paused && d.sent_today < d.daily_cap).length;
        const totalCapacity = (domains.results ?? []).reduce((sum: number, d: any) => sum + (d.is_paused ? 0 : d.daily_cap - d.sent_today), 0);

        return json({
          status: 'ok',
          worker: 'lcs-hub',
          version: 'v2',
          spine_db: 'svg-d1-spine',
          outreach_db: 'svg-d1-outreach-ops',
          signals: signalCount?.cnt ?? 0,
          cids: cidCount?.cnt ?? 0,
          companies: companyCount?.cnt ?? 0,
          domain_rotation: {
            domains_available: domainsAvailable,
            total_remaining_capacity: totalCapacity,
            domains: domains.results ?? [],
          },
          timestamp: new Date().toISOString(),
        }, corsHeaders);
      }

      // ── Signal Ingestion (spoke IN) ─────────────────────
      if (path === '/signal' && request.method === 'POST') {
        const body = await request.json<Record<string, unknown>>();
        const result = await ingestSignal(env.D1, body);
        const status = 'error' in result ? 400 : 201;
        return json(result, corsHeaders, status);
      }

      // ── Batch Signal Ingestion ──────────────────────────
      // â”€â”€ Website / Page Events â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
      if (path === '/page-event' && request.method === 'POST') {
        const body = await request.json<Record<string, unknown>>();
        const eventType = typeof body.event_type === 'string' ? body.event_type.trim() : '';
        if (!eventType) {
          return json({ error: 'event_type is required' }, corsHeaders, 400);
        }

        const pageSlug = new URL(request.url).searchParams.get('slug') ?? 'home';
        const communicationId = typeof body.communication_id === 'string' && body.communication_id.trim()
          ? body.communication_id.trim()
          : `WEB-${pageSlug.toUpperCase()}`;

        await logEvent(env.D1, {
          sovereign_company_id: typeof body.sovereign_company_id === 'string' && body.sovereign_company_id.trim()
            ? body.sovereign_company_id.trim()
            : 'PUBLIC',
          communication_id: communicationId,
          event_type: eventType,
          signal_set_hash: typeof body.signal_set_hash === 'string' && body.signal_set_hash.trim()
            ? body.signal_set_hash.trim()
            : 'website',
          frame_id: typeof body.frame_id === 'string' && body.frame_id.trim() ? body.frame_id.trim() : 'website',
          channel: 'WEB',
          lifecycle_phase: typeof body.lifecycle_phase === 'string' && body.lifecycle_phase.trim()
            ? body.lifecycle_phase.trim()
            : 'WEB',
          lane: 'WEB',
          agent_number: 'SA-WEB',
          step_number: typeof body.step_number === 'number' ? body.step_number : 0,
          step_name: typeof body.page_step === 'string' && body.page_step.trim() ? body.page_step.trim() : 'page_loaded',
          payload: JSON.stringify({
            ...body,
            request_url: request.url,
          }),
        });

        return json({ ok: true, communication_id: communicationId }, corsHeaders, 201);
      }

      if (path === '/signals' && request.method === 'POST') {
        const body = await request.json<Record<string, unknown>[]>();
        const result = await ingestSignalBatch(env.D1, body);
        return json(result, corsHeaders, 201);
      }

      // ── Webhook: Mailgun ────────────────────────────────
      if (path === '/webhook/mailgun' && request.method === 'POST') {
        const payload = await request.json<Record<string, unknown>>();
        // Process directly (local dev) instead of via queue
        await processWebhook(env, {
          job_type: 'process_webhook',
          sovereign_company_id: '',
          webhook_source: 'mailgun',
          webhook_payload: payload,
        });
        return json({ received: true, processed: true }, corsHeaders);
      }

      // ── Webhook: HeyReach ───────────────────────────────
      if (path === '/webhook/heyreach' && request.method === 'POST') {
        const payload = await request.json<Record<string, unknown>>();
        await processWebhook(env, {
          job_type: 'process_webhook',
          sovereign_company_id: '',
          webhook_source: 'heyreach',
          webhook_payload: payload,
        });
        return json({ received: true, processed: true }, corsHeaders);
      }

      // ── Status: Pipeline overview ───────────────────────
      if (path === '/status') {
        const stats = await getPipelineStats(env.D1);
        return json(stats, corsHeaders);
      }

      // ── Status: Company detail ──────────────────────────
      if (path.startsWith('/company/') && request.method === 'GET') {
        const companyId = path.replace('/company/', '');
        const detail = await getCompanyDetail(env.D1, companyId);
        return json(detail, corsHeaders);
      }

      // ── Trace: Bidirectional ID lookup ──────────────────
      if (path.startsWith('/trace/') && request.method === 'GET') {
        const id = path.replace('/trace/', '');
        const trace = await traceId(env.D1, id);
        return json(trace, corsHeaders);
      }

      // ── Manual Pipeline Trigger (smoke test) ─────────────
      // Bypasses queue — runs full pipeline directly
      if (path === '/run' && request.method === 'POST') {
        const body = await request.json<{ signal_queue_id?: string; sovereign_company_id?: string }>();

        let signalId = body.signal_queue_id;

        // If no signal_queue_id, find the first pending signal for this company
        if (!signalId && body.sovereign_company_id) {
          const pending = await env.D1.prepare(
            "SELECT id FROM lcs_signal_queue WHERE sovereign_company_id = ? AND lower(status) = 'pending' ORDER BY priority DESC LIMIT 1"
          ).bind(body.sovereign_company_id).first<{ id: string }>();
          signalId = pending?.id;
        }

        if (!signalId) {
          return json({ error: 'signal_queue_id or sovereign_company_id with pending signal required' }, corsHeaders, 400);
        }

        const result = await runPipeline(env, signalId);
        return json({ pipeline: 'complete', ...result }, corsHeaders);
      }

      // ── Batch Run (manual cron trigger) ────────────────
      // Processes up to N pending signals directly (no queue).
      // Use this to kick off the pipeline manually or after a case-mismatch fix.
      if (path === '/run-batch' && request.method === 'POST') {
        const body = await request.json<{ limit?: number }>().catch(() => ({} as { limit?: number }));
        const limit = Math.min(body?.limit ?? 20, 50);

        const pending = await env.D1.prepare(`
          SELECT id FROM lcs_signal_queue
          WHERE lower(status) = 'pending'
          ORDER BY priority DESC, created_at ASC
          LIMIT ?
        `).bind(limit).all<{ id: string }>();

        if (!pending.results || pending.results.length === 0) {
          return json({ processed: 0, message: 'No pending signals' }, corsHeaders);
        }

        let sent = 0, failed = 0, compiled = 0;
        for (const { id } of pending.results) {
          const result = await runPipeline(env, id);
          if (result.cid?.status === 'COMPILED') compiled++;
          if (result.mid?.status === 'SENT') sent++;
          else failed++;
        }

        return json({ processed: pending.results.length, compiled, sent, failed }, corsHeaders);
      }

      // ── SEED: Discover DOL schema in Neon ─────────────
      if (path === '/seed/dol-schema' && request.method === 'GET') {
        const schema = await discoverDolSchema(env);
        return json(schema, corsHeaders);
      }

      // ── SEED: Pull full DOL data for one EIN (summary) ──
      if (path.startsWith('/seed/dol/') && !path.includes('/full/') && request.method === 'GET') {
        const ein = path.replace('/seed/dol/', '');
        if (!ein || ein.length < 5) {
          return json({ error: 'EIN required (e.g., /seed/dol/510340880)' }, corsHeaders, 400);
        }
        const data = await seedDolForEin(env, ein);
        return json(data, corsHeaders);
      }

      // ── SEED: Full DOL dump — ALL tables, ALL schedules ──
      if (path.startsWith('/seed/dol-full/') && request.method === 'GET') {
        const ein = path.replace('/seed/dol-full/', '');
        if (!ein || ein.length < 5) {
          return json({ error: 'EIN required (e.g., /seed/dol-full/510340880)' }, corsHeaders, 400);
        }
        const data = await fullDolDump(env, ein);
        return json(data, corsHeaders);
      }

      // ── SEED: Pull DOL from Neon → D1 for one EIN ──────
      if (path.startsWith('/seed/dol-to-d1/') && request.method === 'POST') {
        const ein = path.replace('/seed/dol-to-d1/', '');
        const body = await request.json<{ outreach_id?: string }>().catch(() => ({} as { outreach_id?: string }));
        const data = await seedDolToD1(env, ein, body.outreach_id ?? null);
        return json(data, corsHeaders);
      }

      // ── SEED: Full company dump — ALL sub-hubs from D1 ──
      if (path.startsWith('/seed/company-dump/') && request.method === 'GET') {
        const companyId = path.replace('/seed/company-dump/', '');
        const data = await fullCompanyDump(env, companyId);
        return json(data, corsHeaders);
      }

      // ── SEED: Batch — ALL agent-assigned companies ─────
      // POST /seed/batch?limit=100&offset=0
      // Pulls ALL sub-hub data from Neon → D1 for agent-assigned companies
      if (path === '/seed/batch' && request.method === 'POST') {
        const url = new URL(request.url);
        const limit = parseInt(url.searchParams.get('limit') ?? '100');
        const offset = parseInt(url.searchParams.get('offset') ?? '0');
        const data = await batchSeedAllCompanies(env, { limit, offset });
        return json(data, corsHeaders);
      }

      // ── SEED FIX: Re-SEED people_people_master ─────────
      // POST /seed/fix-people — pulls missing person records from Neon
      if (path === '/seed/fix-people' && request.method === 'POST') {
        const data = await seedFixPeopleMaster(env);
        return json(data, corsHeaders);
      }

      // ── SEED FIX: Create missing CEO/CFO/HR slots ──────
      // POST /seed/fix-slots?limit=3000&offset=0 — D1 only, paginated
      if (path === '/seed/fix-slots' && request.method === 'POST') {
        const seedUrl = new URL(request.url);
        const limit = parseInt(seedUrl.searchParams.get('limit') ?? '3000');
        const offset = parseInt(seedUrl.searchParams.get('offset') ?? '0');
        const data = await seedFixMissingSlots(env, { limit, offset });
        return json(data, corsHeaders);
      }

      // ── SEED FIX: Agent assignment per company ─────────
      // POST /seed/fix-agents — queries Neon coverage, updates D1
      if (path === '/seed/fix-agents' && request.method === 'POST') {
        const data = await seedFixAgentAssignment(env);
        return json(data, corsHeaders);
      }

      // ── SEED: Full people_people_master from Neon ──────
      // POST /seed/full-people?limit=5000&offset=0
      if (path === '/seed/full-people' && request.method === 'POST') {
        const seedUrl = new URL(request.url);
        const limit = parseInt(seedUrl.searchParams.get('limit') ?? '5000');
        const offset = parseInt(seedUrl.searchParams.get('offset') ?? '0');
        const data = await seedFullPeopleMaster(env, { limit, offset });
        return json(data, corsHeaders);
      }

      // ── SEED FIX: Match existing people to empty slots ──
      // POST /seed/fix-match?limit=1000 — D1 only, matches by title pattern
      if (path === '/seed/fix-match' && request.method === 'POST') {
        const seedUrl = new URL(request.url);
        const limit = parseInt(seedUrl.searchParams.get('limit') ?? '1000');
        const data = await seedFixMatchPeopleToSlots(env, { limit });
        return json(data, corsHeaders);
      }

      // ── SEED: Clean SEED from seed_views ─────────────────
      // POST /seed/clean?table=all&limit=5000&offset=0
      // Reads from seed_views.* in Neon, pours into D1.
      // table: all, company_target, outreach, cl_identity, blog, dol, slots, people,
      //        hunter_contacts, hunter_patterns, vendor_people, vendor_ct
      if (path === '/seed/clean' && request.method === 'POST') {
        const seedUrl = new URL(request.url);
        const tbl = seedUrl.searchParams.get('table') ?? 'all';
        const limit = parseInt(seedUrl.searchParams.get('limit') ?? '5000');
        const offset = parseInt(seedUrl.searchParams.get('offset') ?? '0');
        const data = await seedClean(env, { table: tbl, limit, offset });
        return json(data, corsHeaders);
      }

      // ── SEED: Global ZIP codes → imo-d1-global ─────────
      // POST /seed/global-zips — pulls reference.us_zip_codes from Neon
      if (path === '/seed/global-zips' && request.method === 'POST') {
        const data = await seedGlobalZipCodes(env);
        return json(data, corsHeaders);
      }

      // ── GET /outreach/voice — Voice constants for Mission Control (BAR-285) ──
      // Returns all active voice profiles from lcs_voice_library.
      // Dave can see the current constants from MC without reading the database directly.
      if (path === '/outreach/voice' && request.method === 'GET') {
        const voices = await env.D1.prepare(
          'SELECT voice_id, voice_name, target_role, tone, style_rules, forbidden_phrases, opening_patterns, closing_patterns, proof_points, is_active, created_at FROM lcs_voice_library WHERE is_active = 1 ORDER BY voice_id'
        ).all<any>();

        const parsed = (voices.results ?? []).map((v: any) => ({
          voice_id: v.voice_id,
          voice_name: v.voice_name,
          target_role: v.target_role,
          tone: v.tone,
          style_rules: tryParseJson(v.style_rules, []),
          forbidden_phrases: tryParseJson(v.forbidden_phrases, []),
          opening_patterns: tryParseJson(v.opening_patterns, []),
          closing_patterns: tryParseJson(v.closing_patterns, []),
          proof_points: tryParseJson(v.proof_points, []),
          is_active: v.is_active,
          created_at: v.created_at,
        }));

        return json({ voices: parsed, count: parsed.length }, corsHeaders);
      }

      return json({ error: 'Not found' }, corsHeaders, 404);
    } catch (err) {
      const msg = err instanceof Error ? err.message : String(err);
      return json({ error: msg }, corsHeaders, 500);
    }
  },
};

// ── Webhook Processing ──────────────────────────────────────

async function processWebhook(env: Env, job: PipelineJob): Promise<void> {
  const payload = job.webhook_payload ?? {};
  const source = job.webhook_source;

  // Extract MID from webhook payload (v2 uses communication_id + message_run_id)
  let messageRunId: string | null = null;
  let communicationId: string | null = null;
  let eventType: string | null = null;

  if (source === 'mailgun') {
    const eventData = payload['event-data'] as any ?? payload;
    messageRunId = eventData?.['user-variables']?.message_run_id ?? null;
    communicationId = eventData?.['user-variables']?.communication_id ?? null;
    const mgEvent = eventData?.event ?? '';
    eventType = mgEvent === 'delivered' ? 'MID_DELIVERED'
      : mgEvent === 'opened' ? 'MID_OPENED'
      : mgEvent === 'clicked' ? 'MID_CLICKED'
      : mgEvent === 'replied' ? 'MID_REPLIED'
      : mgEvent === 'inbound' ? 'MID_REPLIED'
      : mgEvent === 'complained' ? 'MID_COMPLAINED'
      : mgEvent === 'failed' || mgEvent === 'bounced' ? 'MID_BOUNCED'
      : mgEvent === 'unsubscribed' ? 'MID_UNSUBSCRIBED'
      : null;
  } else if (source === 'heyreach') {
    messageRunId = (payload as any)?.custom_variables?.message_run_id ?? null;
    communicationId = (payload as any)?.custom_variables?.communication_id ?? null;
    eventType = (payload as any)?.event === 'accepted' ? 'MID_DELIVERED' : 'MID_BOUNCED';
  }

  if (!messageRunId || !eventType) {
    console.log(`[webhook] Could not extract message_run_id from ${source} payload`);
    return;
  }

  // Update MID record in spine
  const mid = await env.D1.prepare('SELECT * FROM lcs_mid_sequence_state WHERE mid_id = ?')
    .bind(messageRunId).first<any>();

  if (!mid) {
    console.log(`[webhook] MID ${messageRunId} not found in spine`);
    return;
  }

  const newDeliveryStatus = eventType === 'MID_DELIVERED' ? 'DELIVERED'
    : eventType === 'MID_OPENED' ? 'OPENED'
    : eventType === 'MID_CLICKED' ? 'CLICKED'
    : eventType === 'MID_REPLIED' ? 'REPLIED'
    : eventType === 'MID_BOUNCED' ? 'BOUNCED'
    : eventType === 'MID_COMPLAINED' ? 'SUPPRESSED'
    : eventType === 'MID_UNSUBSCRIBED' ? 'SUPPRESSED'
    : mid.delivery_status;

  await env.D1.prepare(
    "UPDATE lcs_mid_sequence_state SET delivery_status = ?, attempted_at = datetime('now') WHERE mid_id = ?"
  ).bind(newDeliveryStatus, messageRunId).run();

  // Suppress recipient on complaint, unsubscribe, or hard bounce — never send again
  if (eventType === 'MID_COMPLAINED' || eventType === 'MID_UNSUBSCRIBED' || eventType === 'MID_BOUNCED') {
    const recipientEmail = mid.recipient_email ?? null;
    if (recipientEmail) {
      await env.D1.prepare(
        `INSERT OR IGNORE INTO lcs_suppression (email, reason, source_mid_id, created_at)
         VALUES (?, ?, ?, datetime('now'))`
      ).bind(recipientEmail, newDeliveryStatus, messageRunId).run();
    }
  }

  // Get CID for context
  const cid = communicationId
    ? await env.D1.prepare('SELECT * FROM lcs_cid WHERE communication_id = ?').bind(communicationId).first<any>()
    : null;

  // Log event to CET
  if (cid) {
    await env.D1.prepare(`
      INSERT INTO lcs_event (
        communication_id, message_run_id, sovereign_company_id,
        entity_type, entity_id, signal_set_hash, frame_id,
        adapter_type, channel, delivery_status, lifecycle_phase,
        event_type, lane, agent_number, step_number, step_name,
        created_at
      ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))
    `).bind(
      communicationId, messageRunId, cid.sovereign_company_id,
      'company', cid.entity_id, cid.signal_set_hash, cid.frame_id,
      mid.adapter_type, mid.channel, newDeliveryStatus, cid.lifecycle_phase,
      eventType, cid.lane, cid.agent_number, mid.sequence_position, 'webhook',
    ).run();
  }

  // ── Closed Loop: insert engagement signal for actionable events ──
  // BAR-303: The Circle closes here. Engagement events re-enter the pipeline.
  // Bounced/Complained/Unsubscribed handled by suppression above — excluded here.
  const engagementTriggerMap: Record<string, string> = {
    MID_OPENED:  'opened',
    MID_CLICKED: 'clicked',
    MID_REPLIED: 'replied',
  };
  const triggerEvent = engagementTriggerMap[eventType ?? ''];
  if (triggerEvent && cid) {
    // Deterministic ID: same MID + same event = same signal ID (prevents duplicate from webhook retries)
    const engSigRaw = new TextEncoder().encode(`${messageRunId}-${triggerEvent}`);
    const engSigHash = Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256', engSigRaw)))
      .map(b => b.toString(16).padStart(2, '0')).join('').slice(0, 12);
    const engSigId = `SIG-ENG-${engSigHash}`;
    // BAR-303 C-1: Read signal_priority from rules table (fallback to 8 if no rule)
    const engRule = await env.D1.prepare(
      "SELECT signal_priority FROM lcs_engagement_rules WHERE trigger_event = ? AND is_active = 1"
    ).bind(triggerEvent).first<any>();
    const engPriority = engRule?.signal_priority ?? 8;
    await env.D1.prepare(`
      INSERT OR IGNORE INTO lcs_signal_queue (
        id, signal_set_hash, signal_category, sovereign_company_id,
        lifecycle_phase, preferred_channel, preferred_lane, agent_number,
        signal_data, source_hub, source_signal_id, status, priority, created_at
      ) VALUES (?, ?, 'ENGAGEMENT_RESPONSE', ?, ?, ?, ?, ?, ?, 'webhook', ?, 'pending', ?, datetime('now'))
    `).bind(
      engSigId,
      cid.signal_set_hash,
      cid.sovereign_company_id,
      cid.lifecycle_phase,
      mid.channel ?? 'MG',
      cid.lane ?? 'COLD',
      cid.agent_number ?? 'SA-001',
      JSON.stringify({
        trigger_event: triggerEvent,
        source_mid_id: messageRunId,
        source_communication_id: communicationId,
        contact_email: mid.recipient_email ?? null,
      }),
      messageRunId,
      engPriority,
    ).run();
    console.log(`[webhook] Circle closed: ${triggerEvent} → engagement signal ${engSigId} (priority=${engPriority}) for ${cid.sovereign_company_id}`);
  }

  // ── BAR-305: Update contact engagement score ──
  // Weighted scoring: delivered=1, opened=5, clicked=15. Hot lead threshold=25.
  if (mid.recipient_email && cid) {
    const scoreWeights: Record<string, number> = {
      MID_DELIVERED: 1,
      MID_OPENED: 5,
      MID_CLICKED: 15,
      MID_REPLIED: 25,
    };
    const weight = scoreWeights[eventType ?? ''] ?? 0;
    if (weight > 0) {
      const channel = mid.channel ?? 'MG';
      const scoreField = channel === 'HR' ? 'linkedin_score' : 'email_score';
      await env.D1.prepare(`
        INSERT INTO lcs_contact_engagement_score (contact_email, sovereign_company_id, ${scoreField}, composite_score, total_events, last_event_type, last_event_at, updated_at)
        VALUES (?, ?, ?, ?, 1, ?, datetime('now'), datetime('now'))
        ON CONFLICT(contact_email) DO UPDATE SET
          ${scoreField} = ${scoreField} + ?,
          composite_score = email_score + linkedin_score + web_score,
          total_events = total_events + 1,
          last_event_type = ?,
          last_event_at = datetime('now'),
          is_hot_lead = CASE WHEN (email_score + linkedin_score + web_score) >= 25 THEN 1 ELSE 0 END,
          updated_at = datetime('now')
      `).bind(
        mid.recipient_email, cid.sovereign_company_id,
        weight, weight, eventType,
        weight, eventType,
      ).run();
    }

    // BAR-307: UPSERT channel state — ensure every contacted person has a channel state record
    try {
      await env.D1.prepare(`
        INSERT INTO lcs_contact_channel_state (contact_email, sovereign_company_id, primary_channel, channel_state, email_status, linkedin_status)
        VALUES (?, ?, 'MG', 'email_active', 'active', 'not_started')
        ON CONFLICT(contact_email) DO UPDATE SET
          updated_at = datetime('now')
      `).bind(mid.recipient_email, cid.sovereign_company_id).run();
    } catch (_chErr) {
      // Non-blocking — channel state tracking failure doesn't stop webhook processing
    }
  }

  // If bounced → ORBT strike
  if (eventType === 'MID_BOUNCED' && cid) {
    const strikes = await env.D1.prepare(
      "SELECT COUNT(*) as cnt FROM lcs_err0 WHERE sovereign_company_id = ? AND failure_type LIKE 'DELIVERY%'"
    ).bind(cid.sovereign_company_id).first<{ cnt: number }>();

    const strikeNum = (strikes?.cnt ?? 0) + 1;
    const orbtAction = strikeNum >= 3 ? 'HUMAN_ESCALATION'
      : strikeNum >= 2 ? 'ALT_CHANNEL'
      : 'AUTO_RETRY';

    await env.D1.prepare(`
      INSERT INTO lcs_err0 (
        error_id, message_run_id, communication_id, sovereign_company_id,
        failure_type, failure_message, lifecycle_phase, adapter_type,
        orbt_strike_number, orbt_action_taken, created_at
      ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))
    `).bind(
      `ERR-${crypto.randomUUID().replace(/-/g, '').slice(0, 12)}`,
      messageRunId, communicationId, cid.sovereign_company_id,
      'DELIVERY_BOUNCE', `${source} bounce on ${messageRunId}`,
      cid.lifecycle_phase, mid.adapter_type,
      strikeNum, orbtAction,
    ).run();
  }
}

// ── Status Helpers ──────────────────────────────────────────

async function getPipelineStats(d1: D1Database): Promise<Record<string, unknown>> {
  const signals = await d1.prepare(
    "SELECT status, COUNT(*) as cnt FROM lcs_signal_queue GROUP BY status"
  ).all();
  const cids = await d1.prepare(
    "SELECT compilation_status as status, COUNT(*) as cnt FROM lcs_cid GROUP BY compilation_status"
  ).all();
  const sids = await d1.prepare(
    "SELECT construction_status as status, COUNT(*) as cnt FROM lcs_sid_output GROUP BY construction_status"
  ).all();
  const mids = await d1.prepare(
    "SELECT delivery_status, COUNT(*) as cnt FROM lcs_mid_sequence_state GROUP BY delivery_status"
  ).all();
  const errors = await d1.prepare(
    "SELECT failure_type, COUNT(*) as cnt FROM lcs_err0 GROUP BY failure_type"
  ).all();
  const events = await d1.prepare(
    "SELECT event_type, COUNT(*) as cnt FROM lcs_event GROUP BY event_type"
  ).all();

  return {
    signals: signals.results ?? [],
    cids: cids.results ?? [],
    sids: sids.results ?? [],
    mids: mids.results ?? [],
    errors: errors.results ?? [],
    events: events.results ?? [],
    timestamp: new Date().toISOString(),
  };
}

async function getCompanyDetail(
  d1: D1Database,
  companyId: string,
): Promise<Record<string, unknown>> {
  const signals = await d1.prepare(
    'SELECT * FROM lcs_signal_queue WHERE sovereign_company_id = ? ORDER BY created_at DESC LIMIT 20'
  ).bind(companyId).all();
  const cids = await d1.prepare(
    'SELECT * FROM lcs_cid WHERE sovereign_company_id = ? ORDER BY created_at DESC LIMIT 5'
  ).bind(companyId).all();
  const sids = await d1.prepare(
    'SELECT * FROM lcs_sid_output WHERE communication_id IN (SELECT communication_id FROM lcs_cid WHERE sovereign_company_id = ?) ORDER BY created_at DESC LIMIT 5'
  ).bind(companyId).all();
  const mids = await d1.prepare(
    'SELECT * FROM lcs_mid_sequence_state WHERE communication_id IN (SELECT communication_id FROM lcs_cid WHERE sovereign_company_id = ?) ORDER BY created_at DESC LIMIT 20'
  ).bind(companyId).all();
  const events = await d1.prepare(
    'SELECT * FROM lcs_event WHERE sovereign_company_id = ? ORDER BY created_at DESC LIMIT 50'
  ).bind(companyId).all();
  const errors = await d1.prepare(
    'SELECT * FROM lcs_err0 WHERE sovereign_company_id = ? ORDER BY created_at DESC LIMIT 20'
  ).bind(companyId).all();

  return {
    sovereign_company_id: companyId,
    signals: signals.results ?? [],
    cids: cids.results ?? [],
    sids: sids.results ?? [],
    mids: mids.results ?? [],
    events: events.results ?? [],
    errors: errors.results ?? [],
  };
}

async function traceId(
  d1: D1Database,
  id: string,
): Promise<Record<string, unknown>> {
  // Detect ID type by prefix
  if (id.startsWith('LCS-')) {
    // communication_id — trace the full chain
    const cid = await d1.prepare('SELECT * FROM lcs_cid WHERE communication_id = ?').bind(id).first();
    const sids = await d1.prepare('SELECT * FROM lcs_sid_output WHERE communication_id = ?').bind(id).all();
    const mids = await d1.prepare('SELECT * FROM lcs_mid_sequence_state WHERE communication_id = ?').bind(id).all();
    const events = await d1.prepare('SELECT * FROM lcs_event WHERE communication_id = ? ORDER BY created_at').bind(id).all();
    const errors = await d1.prepare('SELECT * FROM lcs_err0 WHERE communication_id = ?').bind(id).all();
    return { type: 'communication', data: cid, sids: sids.results, mids: mids.results, events: events.results, errors: errors.results };
  }
  if (id.startsWith('SID-')) {
    const sid = await d1.prepare('SELECT * FROM lcs_sid_output WHERE sid_id = ?').bind(id).first();
    const mids = await d1.prepare('SELECT * FROM lcs_mid_sequence_state WHERE communication_id = (SELECT communication_id FROM lcs_sid_output WHERE sid_id = ?)').bind(id).all();
    return { type: 'sid', data: sid, deliveries: mids.results };
  }
  if (id.startsWith('RUN-')) {
    const mid = await d1.prepare('SELECT * FROM lcs_mid_sequence_state WHERE mid_id = ?').bind(id).first();
    return { type: 'mid', data: mid };
  }
  if (id.startsWith('ERR-')) {
    const err = await d1.prepare('SELECT * FROM lcs_err0 WHERE error_id = ?').bind(id).first();
    return { type: 'error', data: err };
  }

  // Try as sovereign_company_id
  const events = await d1.prepare('SELECT * FROM lcs_event WHERE sovereign_company_id = ? ORDER BY created_at DESC LIMIT 50').bind(id).all();
  if (events.results && events.results.length > 0) {
    return { type: 'company', events: events.results };
  }

  return { error: 'Unknown ID format. Use LCS- (communication), SID-, RUN- (mid), ERR-, or sovereign_company_id.' };
}

// ── Helpers ─────────────────────────────────────────────────

function json(data: unknown, headers: Record<string, string>, status = 200): Response {
  return Response.json(data, { status, headers: { ...headers, 'Content-Type': 'application/json' } });
}

// BAR-285: Safe JSON parse with fallback — used by /outreach/voice to deserialize
// lcs_voice_library JSON columns (style_rules, forbidden_phrases, etc.).
function tryParseJson(raw: string | null | undefined, fallback: unknown): unknown {
  if (!raw) return fallback;
  try {
    return JSON.parse(raw);
  } catch {
    return fallback;
  }
}
