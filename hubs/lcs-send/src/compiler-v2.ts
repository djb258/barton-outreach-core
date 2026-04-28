// â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
// LCS Hub â€” Compiler v2 (Blueprint-Native)
// â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
// Reads from existing spine + outreach D1 schemas.
// Config-driven via registries (signal, frame, adapter).
// No hardcoded campaign types or message templates.
//
// D1 (spine): lcs_signal_queue, lcs_cid, lcs_sid_output,
//             lcs_mid_sequence_state, lcs_event, lcs_err0
// D1_OUTREACH: outreach_company_target, outreach_dol,
//              people_company_slot
// â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•

import type { Env } from './types';
import { asciiNormalize, buildSignatureFooter, validateOutboundEmailCopy } from './voice-spec';
import { EMAIL_DELIVERABILITY_CONFIG } from './deliverability';

// â”€â”€ ID Minting â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

function mintCommId(phase: string): string {
  const date = new Date().toISOString().slice(0, 10).replace(/-/g, '');
  const rand = crypto.randomUUID().replace(/-/g, '').slice(0, 12);
  return `LCS-${phase}-${date}-${rand}`;
}

function mintRunId(commId: string, channel: string, attempt: number): string {
  return `RUN-${commId}-${channel}-${String(attempt).padStart(2, '0')}`;
}

function mintErrorId(): string {
  const rand = crypto.randomUUID().replace(/-/g, '').slice(0, 12);
  return `ERR-${rand}`;
}

// â”€â”€ Stage 1: CID Compilation â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
// Reads signal from spine, company data from outreach,
// determines intelligence tier, writes lcs_cid.

export async function compileCid(
  env: Env,
  signalQueueId: string,
): Promise<{ communication_id: string; status: string } | null> {
  try {
    // 1. Read the signal from spine
    const signal = await env.D1.prepare(
      'SELECT * FROM lcs_signal_queue WHERE id = ?'
    ).bind(signalQueueId).first<any>();

    if (!signal || signal.status?.toLowerCase() !== 'pending') {
      return null;
    }

    // â”€â”€ Engagement Response Path (BAR-303: Close the Circle) â”€â”€
    // Short-circuits normal CID compilation for engagement signals.
    // Reads rules table directly. No frame registry selection.
    if (signal.signal_category === 'ENGAGEMENT_RESPONSE') {
      return await compileEngagementResponse(env, signal, signalQueueId);
    }

    // 2. Read signal definition from registry
    const signalDef = await env.D1.prepare(
      'SELECT * FROM lcs_signal_registry WHERE signal_set_hash = ? AND is_active = 1'
    ).bind(signal.signal_set_hash).first<any>();

    // 3. Read company identity from spine D1 (trunk â€” has canonical_name + outreach_id)
    const identity = await env.D1.prepare(
      'SELECT * FROM cl_company_identity WHERE company_unique_id = ?'
    ).bind(signal.sovereign_company_id).first<any>();

    if (!identity || !identity.outreach_id) {
      await logErr0(env.D1, {
        message_run_id: 'NONE',
        sovereign_company_id: signal.sovereign_company_id,
        failure_type: 'COMPANY_NOT_FOUND',
        failure_message: `Company ${signal.sovereign_company_id} not found in spine cl_company_identity or missing outreach_id`,
        lifecycle_phase: signal.lifecycle_phase,
      });
      await env.D1.prepare(
        "UPDATE lcs_signal_queue SET status = 'failed', processed_at = datetime('now') WHERE id = ?"
      ).bind(signalQueueId).run();
      return null;
    }

    // Read targeting data from outreach D1
    const company = await env.D1_OUTREACH.prepare(
      'SELECT * FROM outreach_company_target WHERE outreach_id = ?'
    ).bind(identity.outreach_id).first<any>();

    if (!company) {
      await logErr0(env.D1, {
        message_run_id: 'NONE',
        sovereign_company_id: signal.sovereign_company_id,
        failure_type: 'OUTREACH_NOT_FOUND',
        failure_message: `Outreach record not found for outreach_id ${identity.outreach_id}`,
        lifecycle_phase: signal.lifecycle_phase,
      });
      return null;
    }

    // 4. Read DOL data
    const dol = await env.D1_OUTREACH.prepare(
      'SELECT * FROM outreach_dol WHERE outreach_id = ?'
    ).bind(identity.outreach_id).first<any>();

    // 5. Read people slots
    const slots = await env.D1_OUTREACH.prepare(
      'SELECT * FROM people_company_slot WHERE outreach_id = ? AND is_filled = 1'
    ).bind(identity.outreach_id).all<any>();

    // 6. Determine intelligence tier based on data completeness
    let tier = 5; // lowest â€” generic
    if (dol && dol.filing_present) tier = Math.min(tier, 3);
    if (slots.results && slots.results.length >= 2) tier = Math.min(tier, 3);
    if (signal.signal_category === 'RENEWAL_PROXIMITY' && dol) tier = Math.min(tier, 2);

    // 8. Mint communication_id
    const communicationId = mintCommId(signal.lifecycle_phase);

    // 9. Determine compilation status
    const hasMinData = identity.outreach_id && (company.state || identity.canonical_name);
    const compilationStatus = hasMinData ? 'COMPILED' : 'FAILED';
    const compilationReason = hasMinData ? null : 'Insufficient company data';

    // 10. Find matching frame from registry based on tier
    const frame = await env.D1.prepare(
      `SELECT * FROM lcs_frame_registry
       WHERE lifecycle_phase = ? AND tier <= ? AND is_active = 1
       ORDER BY step_in_sequence ASC, tier ASC LIMIT 1`
    ).bind(signal.lifecycle_phase, tier).first<any>();

    // 11. Write CID to spine
    await env.D1.prepare(`
      INSERT INTO lcs_cid (
        communication_id, sovereign_company_id, entity_type, entity_id,
        signal_set_hash, signal_queue_id, frame_id, lifecycle_phase,
        lane, agent_number, intelligence_tier, compilation_status,
        compilation_reason, created_at
      ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))
    `).bind(
      communicationId,
      signal.sovereign_company_id,
      'company',
      identity.outreach_id,
      signal.signal_set_hash,
      signalQueueId,
      frame?.frame_id ?? 'OUT-GENERAL-V1',
      signal.lifecycle_phase,
      company.email_method ?? 'COLD',
      signal.agent_number ?? 'SA-001',
      tier,
      compilationStatus,
      compilationReason,
    ).run();

    // 12. Update signal status
    await env.D1.prepare(
      "UPDATE lcs_signal_queue SET status = 'processed', processed_at = datetime('now') WHERE id = ?"
    ).bind(signalQueueId).run();

    // 13. Log event
    await logEvent(env.D1, {
      communication_id: communicationId,
      message_run_id: 'CID',
      sovereign_company_id: signal.sovereign_company_id,
      entity_type: 'company',
      entity_id: company.outreach_id,
      signal_set_hash: signal.signal_set_hash,
      frame_id: frame?.frame_id ?? 'OUT-GENERAL-V1',
      adapter_type: 'NONE',
      channel: 'NONE',
      delivery_status: compilationStatus,
      lifecycle_phase: signal.lifecycle_phase,
      event_type: compilationStatus === 'COMPILED' ? 'CID_COMPILED' : 'CID_FAILED',
      lane: company.email_method ?? 'COLD',
      agent_number: company.agent_number ?? signal.agent_number ?? 'SA-001',
      step_number: 0,
      step_name: 'compilation',
      intelligence_tier: tier,
    });

    return { communication_id: communicationId, status: compilationStatus };
  } catch (err) {
    const msg = err instanceof Error ? err.message : String(err);
    await logErr0(env.D1, {
      message_run_id: 'NONE',
      sovereign_company_id: '',
      failure_type: 'CID_COMPILATION_ERROR',
      failure_message: msg,
      lifecycle_phase: 'OUTREACH',
    });
    return null;
  }
}

// â”€â”€ Stage 2: SID Construction â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
// Reads CID from spine, builds message using frame registry,
// pulls recipient from people slots.

export async function constructSid(
  env: Env,
  communicationId: string,
): Promise<{ sid_id: string } | null> {
  try {
    // 1. Read CID
    const cid = await env.D1.prepare(
      'SELECT * FROM lcs_cid WHERE communication_id = ?'
    ).bind(communicationId).first<any>();

    if (!cid || cid.compilation_status !== 'COMPILED') {
      return null;
    }

    // 2. BAR-307: Advisory channel state check
    // If the CID's channel doesn't match the contact's primary_channel, log a warning.
    // Does NOT block â€” channel state is advisory for now.
    const cidChannel = cid.preferred_channel ?? 'MG';
    try {
      const contactEmailForChannel = cid.signal_data
        ? (JSON.parse(cid.signal_data ?? '{}').contact_email ?? null)
        : null;
      if (contactEmailForChannel) {
        const channelState = await env.D1.prepare(
          'SELECT primary_channel FROM lcs_contact_channel_state WHERE contact_email = ?'
        ).bind(contactEmailForChannel).first<any>();
        if (channelState && channelState.primary_channel !== cidChannel) {
          console.warn(`[channel-advisory] CID ${communicationId} channel=${cidChannel} but contact ${contactEmailForChannel} primary_channel=${channelState.primary_channel}`);
        }
      }
    } catch (_chErr) {
      // Non-blocking â€” channel check failure doesn't stop the pipeline
    }

    // 2b. Read frame template
    const frame = await env.D1.prepare(
      'SELECT * FROM lcs_frame_registry WHERE frame_id = ? AND is_active = 1'
    ).bind(cid.frame_id).first<any>();

    if (!frame) {
      await logErr0(env.D1, {
        message_run_id: 'NONE',
        communication_id: communicationId,
        sovereign_company_id: cid.sovereign_company_id,
        failure_type: 'FRAME_NOT_FOUND',
        failure_message: `Frame ${cid.frame_id} not found or inactive`,
        lifecycle_phase: cid.lifecycle_phase,
      });
      return null;
    }

    // 2c. Read voice constants from lcs_voice_library (BAR-285)
    // Frame carries voice_id FK. Query that voice + fallback to VCE-BARTON-ALL.
    const voiceId = frame.voice_id ?? 'VCE-BARTON-ALL';
    let voiceConstants: VoiceConstants | null = null;
    try {
      const voiceRow = await env.D1.prepare(
        'SELECT * FROM lcs_voice_library WHERE voice_id = ? AND is_active = 1'
      ).bind(voiceId).first<any>();
      // Always load ALL-role base voice for forbidden phrases
      const baseVoiceRow = voiceId === 'VCE-BARTON-ALL'
        ? voiceRow
        : await env.D1.prepare(
            "SELECT * FROM lcs_voice_library WHERE voice_id = 'VCE-BARTON-ALL' AND is_active = 1"
          ).first<any>();
      if (voiceRow) {
        voiceConstants = parseVoiceRow(voiceRow, baseVoiceRow);
      }
    } catch (_voiceErr) {
      // Non-blocking â€” voice lookup failure falls back to hardcoded templates
    }

    // 3. Get recipient from people slots
    // people_company_slot.person_unique_id â†’ people_people_master.unique_id
    const targetSlot = frame.channel === 'MG' ? 'CFO' : 'CEO'; // Money path default
    const recipient = await env.D1_OUTREACH.prepare(`
      SELECT cs.slot_type, pm.first_name, pm.last_name, pm.email, pm.linkedin_url, pm.outreach_ready
      FROM people_company_slot cs
      LEFT JOIN people_people_master pm ON cs.person_unique_id = pm.unique_id
      WHERE cs.outreach_id = ? AND cs.slot_type = ? AND cs.is_filled = 1
      LIMIT 1
    `).bind(cid.entity_id, targetSlot).first<any>();

    // Fallback to any filled slot with email
    const actualRecipient = (recipient && recipient.email) ? recipient : await env.D1_OUTREACH.prepare(`
      SELECT cs.slot_type, pm.first_name, pm.last_name, pm.email, pm.linkedin_url, pm.outreach_ready
      FROM people_company_slot cs
      LEFT JOIN people_people_master pm ON cs.person_unique_id = pm.unique_id
      WHERE cs.outreach_id = ? AND cs.is_filled = 1 AND pm.email IS NOT NULL
      ORDER BY CASE cs.slot_type WHEN 'CFO' THEN 1 WHEN 'CEO' THEN 2 WHEN 'HR' THEN 3 ELSE 4 END
      LIMIT 1
    `).bind(cid.entity_id).first<any>();

    // 4. Get company name from spine identity
    const company = await env.D1.prepare(
      'SELECT canonical_name, company_name, company_domain FROM cl_company_identity WHERE outreach_id = ?'
    ).bind(cid.entity_id).first<any>();

    // 4b. Read grid data â€” company targeting + DOL for personalization
    const companyTarget = await env.D1_OUTREACH.prepare(
      'SELECT industry, employees, state, city FROM outreach_company_target WHERE outreach_id = ?'
    ).bind(cid.entity_id).first<any>();

    const dolData = await env.D1_OUTREACH.prepare(
      'SELECT filing_present, funding_type, carrier, broker_or_advisor, renewal_month FROM outreach_dol WHERE outreach_id = ?'
    ).bind(cid.entity_id).first<any>();

    // 4c. Build grid context object â€” everything we know about this company
    const grid = {
      industry: companyTarget?.industry ?? null,
      employees: companyTarget?.employees ?? null,
      state: companyTarget?.state ?? null,
      city: companyTarget?.city ?? null,
      hasDol: dolData?.filing_present === 1,
      fundingType: dolData?.funding_type ?? null,
      carrier: dolData?.carrier ?? null,
      broker: dolData?.broker_or_advisor ?? null,
      renewalMonth: dolData?.renewal_month ?? null,
      slotType: actualRecipient?.slot_type ?? null,
    };

    // 5. Build SID output
    const sidId = `SID-${communicationId}`;
    const recipientName = actualRecipient
      ? `${actualRecipient.first_name ?? ''} ${actualRecipient.last_name ?? ''}`.trim()
      : 'there';
    const recipientEmail = actualRecipient?.email ?? null;
    const companyName = company?.canonical_name ?? company?.company_name ?? 'your company';

    // 6. Query LBB for content enrichment (AI tail â€” after deterministic compilation)
    // Deterministic templates are the spine. LBB enriches when content is available.
    const signalCategory = cid.lifecycle_phase ?? 'OUTREACH';
    const talkingPoints = await getSalesTalkingPoints(env, signalCategory, companyName);
    const companyIntel = await getCompanyIntelligence(env, companyName);

    // 6b. Fetch sender signature from D1 â€” keyed by agent_number, fallback to first active row
    let senderSig: SenderSignature = DEFAULT_SIGNATURE;
    try {
      const agentNumber = cid.agent_number ?? null;
      const rawSig = agentNumber
        ? await env.D1.prepare(
            'SELECT name, title, company, website, linkedin_url, booking_link, tagline FROM lcs_email_signature WHERE agent_number = ? AND is_active = 1 LIMIT 1'
          ).bind(agentNumber).first<SenderSignature>()
        : await env.D1.prepare(
            'SELECT name, title, company, website, linkedin_url, booking_link, tagline FROM lcs_email_signature WHERE is_active = 1 LIMIT 1'
          ).first<SenderSignature>();
      if (rawSig) senderSig = rawSig;
    } catch (_sigErr) {
      // Non-blocking â€” fall back to DEFAULT_SIGNATURE if D1 lookup fails
    }

    // BAR Option-B: body + subject now sourced from D1 lcs_frame_registry.
    // If either template is missing/empty, log FRAME_TEMPLATE_MISSING and skip.
    let bodyPlain = buildMessageBody(frame, companyName, recipientName, cid, talkingPoints, companyIntel, grid, senderSig);
    let subjectLine = buildSubjectLine(frame, companyName, recipientName, senderSig);

    if (bodyPlain === null || subjectLine === null) {
      await logErr0(env.D1, {
        message_run_id: 'NONE',
        communication_id: communicationId,
        sovereign_company_id: cid.sovereign_company_id,
        failure_type: 'FRAME_TEMPLATE_MISSING',
        failure_message: `Frame ${cid.frame_id} is missing ${bodyPlain === null ? 'body_template' : ''}${bodyPlain === null && subjectLine === null ? ' and ' : ''}${subjectLine === null ? 'subject_line_template' : ''} in lcs_frame_registry`,
        lifecycle_phase: cid.lifecycle_phase,
      });
      return null;
    }

    // BAR-285 / Thread 2: Voice validation — enforce the machine voice spec
    // before the SID is written or Mailgun sees the payload.
    // voice-spec v1.2.0: `non_ascii_content:*` is a WARNING (non-blocking).
    // The compiler-v2 deliverMailgun boundary normalizes the body via
    // asciiNormalize() before Mailgun POST. Authors should still write ASCII,
    // but drift doesn't block the send.
    const voiceIssues = validateOutboundEmailCopy(subjectLine, bodyPlain, cid.frame_id);
    const blockingIssues = voiceIssues.filter((i) => !i.startsWith('non_ascii_content'));
    if (blockingIssues.length > 0) {
      await logErr0(env.D1, {
        message_run_id: 'NONE',
        communication_id: communicationId,
        sovereign_company_id: cid.sovereign_company_id,
        failure_type: 'VOICE_SPEC_VIOLATION',
        failure_message: `Voice spec check failed: ${blockingIssues.join('; ')}`,
        lifecycle_phase: cid.lifecycle_phase,
      });
      // Return null — do NOT write SID, do NOT send
      return null;
    }
    if (voiceIssues.length > 0) {
      // Warnings only — non-blocking. Log advisory and proceed.
      console.warn(`[voice-spec] ${communicationId} warnings: ${voiceIssues.join('; ')}`);
    }

    // 7. Write SID to spine
    const constructionStatus = recipientEmail ? 'CONSTRUCTED' : 'FAILED';

    await env.D1.prepare(`
      INSERT INTO lcs_sid_output (
        sid_id, communication_id, frame_id, template_id,
        subject_line, body_plain, body_html,
        sender_identity, sender_email,
        recipient_email, recipient_name,
        construction_status, construction_reason, created_at
      ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))
    `).bind(
      sidId,
      communicationId,
      cid.frame_id,
      null, // template_id â€” future BAR-48 content library
      subjectLine,
      bodyPlain,
      '', // body_html â€” future
      'Dave Barton',
      `dave@${env.MAILGUN_DOMAIN}`,
      recipientEmail,
      recipientName,
      constructionStatus,
      constructionStatus === 'FAILED' ? 'No recipient email found' : null,
    ).run();

    // 8. Log event
    await logEvent(env.D1, {
      communication_id: communicationId,
      message_run_id: sidId,
      sovereign_company_id: cid.sovereign_company_id,
      entity_type: 'company',
      entity_id: cid.entity_id,
      signal_set_hash: cid.signal_set_hash,
      frame_id: cid.frame_id,
      adapter_type: 'NONE',
      channel: frame.channel,
      delivery_status: constructionStatus,
      lifecycle_phase: cid.lifecycle_phase,
      event_type: constructionStatus === 'CONSTRUCTED' ? 'SID_CONSTRUCTED' : 'SID_FAILED',
      lane: cid.lane,
      agent_number: cid.agent_number,
      step_number: 1,
      step_name: 'construction',
      intelligence_tier: cid.intelligence_tier,
    });

    return constructionStatus === 'CONSTRUCTED' ? { sid_id: sidId } : null;
  } catch (err) {
    const msg = err instanceof Error ? err.message : String(err);
    await logErr0(env.D1, {
      message_run_id: 'NONE',
      communication_id: communicationId,
      failure_type: 'SID_CONSTRUCTION_ERROR',
      failure_message: msg,
      lifecycle_phase: 'OUTREACH',
    });
    return null;
  }
}

// â”€â”€ Stage 3: MID Delivery â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
// Reads SID, checks gates (suppression, capacity, freshness),
// routes to adapter, writes delivery state.

export async function deliverMid(
  env: Env,
  sidId: string,
): Promise<{ mid_id: string; status: string } | null> {
  try {
    // 1. Read SID
    const sid = await env.D1.prepare(
      'SELECT * FROM lcs_sid_output WHERE sid_id = ?'
    ).bind(sidId).first<any>();

    if (!sid || sid.construction_status !== 'CONSTRUCTED') {
      return null;
    }

    // 2. Read CID for context
    const cid = await env.D1.prepare(
      'SELECT * FROM lcs_cid WHERE communication_id = ?'
    ).bind(sid.communication_id).first<any>();

    if (!cid) return null;

    // 3. Read adapter from registry
    const frame = await env.D1.prepare(
      'SELECT * FROM lcs_frame_registry WHERE frame_id = ?'
    ).bind(cid.frame_id).first<any>();

    const channel = frame?.channel ?? 'MG';
    const adapter = await env.D1.prepare(
      'SELECT * FROM lcs_adapter_registry WHERE adapter_type = ? AND is_active = 1'
    ).bind(channel).first<any>();

    if (!adapter) {
      await logErr0(env.D1, {
        message_run_id: sidId,
        communication_id: sid.communication_id,
        sovereign_company_id: cid.sovereign_company_id,
        failure_type: 'ADAPTER_NOT_FOUND',
        failure_message: `No active adapter for channel ${channel}`,
        lifecycle_phase: cid.lifecycle_phase,
        adapter_type: channel,
      });
      return null;
    }

    // 4. Check daily cap
    if (adapter.daily_cap && adapter.sent_today >= adapter.daily_cap) {
      // Throttled â€” schedule for tomorrow
      const midId = mintRunId(sid.communication_id, channel, 1);
      await writeMidState(env.D1, {
        mid_id: midId,
        message_run_id: midId,
        communication_id: sid.communication_id,
        adapter_type: channel,
        channel: channel,
        sequence_position: frame?.step_in_sequence ?? 1,
        attempt_number: 1,
        gate_verdict: 'THROTTLED',
        gate_reason: `Daily cap reached (${adapter.sent_today}/${adapter.daily_cap})`,
        delivery_status: 'SCHEDULED',
      });
      return { mid_id: midId, status: 'THROTTLED' };
    }

    // 5. Deliver
    const midId = mintRunId(sid.communication_id, channel, 1);
    let deliveryResult: { success: boolean; provider_id: string | null; error: string | null };

    if (channel === 'MG') {
      deliveryResult = await deliverMailgun(env, sid, cid, midId);
    } else if (channel === 'HR') {
      deliveryResult = await deliverHeyReach(env, sid, cid, midId);
    } else {
      deliveryResult = { success: false, provider_id: null, error: `Unknown channel: ${channel}` };
    }

    // 6. Write MID state (include recipient_email so webhook can suppress on bounce/complaint)
    await writeMidState(env.D1, {
      mid_id: midId,
      message_run_id: midId,
      communication_id: sid.communication_id,
      adapter_type: channel,
      channel: channel,
      sequence_position: frame?.step_in_sequence ?? 1,
      attempt_number: 1,
      gate_verdict: 'PASS',
      delivery_status: deliveryResult.success ? 'SENT' : 'FAILED',
      recipient_email: sid.recipient_email ?? null,
    });

    // 7. Update adapter sent count
    await env.D1.prepare(
      "UPDATE lcs_adapter_registry SET sent_today = sent_today + 1, updated_at = datetime('now') WHERE adapter_type = ?"
    ).bind(channel).run();

    // 8. Log event
    await logEvent(env.D1, {
      communication_id: sid.communication_id,
      message_run_id: midId,
      sovereign_company_id: cid.sovereign_company_id,
      entity_type: 'company',
      entity_id: cid.entity_id,
      signal_set_hash: cid.signal_set_hash,
      frame_id: cid.frame_id,
      adapter_type: channel,
      channel: channel,
      delivery_status: deliveryResult.success ? 'SENT' : 'FAILED',
      lifecycle_phase: cid.lifecycle_phase,
      event_type: deliveryResult.success ? 'MID_SENT' : 'MID_FAILED',
      lane: cid.lane,
      agent_number: cid.agent_number,
      step_number: frame?.step_in_sequence ?? 1,
      step_name: 'delivery',
      intelligence_tier: cid.intelligence_tier,
      adapter_response: deliveryResult.provider_id,
    });

    // 9. If failed, log to err0 with ORBT strike
    if (!deliveryResult.success) {
      // Count existing strikes for this company
      const strikes = await env.D1.prepare(
        "SELECT COUNT(*) as cnt FROM lcs_err0 WHERE sovereign_company_id = ? AND failure_type LIKE 'DELIVERY%'"
      ).bind(cid.sovereign_company_id).first<{ cnt: number }>();

      const strikeNum = (strikes?.cnt ?? 0) + 1;
      const orbtAction = strikeNum >= 3 ? 'HUMAN_ESCALATION'
        : strikeNum >= 2 ? 'ALT_CHANNEL'
        : 'AUTO_RETRY';

      await logErr0(env.D1, {
        message_run_id: midId,
        communication_id: sid.communication_id,
        sovereign_company_id: cid.sovereign_company_id,
        failure_type: 'DELIVERY_FAILED',
        failure_message: deliveryResult.error ?? 'Unknown delivery error',
        lifecycle_phase: cid.lifecycle_phase,
        adapter_type: channel,
        orbt_strike_number: strikeNum,
        orbt_action_taken: orbtAction,
      });
    }

    return { mid_id: midId, status: deliveryResult.success ? 'SENT' : 'FAILED' };
  } catch (err) {
    const msg = err instanceof Error ? err.message : String(err);
    await logErr0(env.D1, {
      message_run_id: sidId,
      failure_type: 'MID_DELIVERY_ERROR',
      failure_message: msg,
      lifecycle_phase: 'OUTREACH',
    });
    return null;
  }
}

// â”€â”€ Full Pipeline Run â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
// Convenience: runs all 3 stages for a single signal.

export async function runPipeline(
  env: Env,
  signalQueueId: string,
): Promise<{ cid: any; sid: any; mid: any }> {
  const cidResult = await compileCid(env, signalQueueId);
  if (!cidResult || cidResult.status !== 'COMPILED') {
    return { cid: cidResult, sid: null, mid: null };
  }

  const sidResult = await constructSid(env, cidResult.communication_id);
  if (!sidResult) {
    return { cid: cidResult, sid: null, mid: null };
  }

  const midResult = await deliverMid(env, sidResult.sid_id);

  // â”€â”€ BAR-304: Sequence State Tracking â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
  // After successful MID delivery, advance the contact's sequence state.
  // Reads sequence_def for delay_hours to calculate next_step_after.
  if (midResult && midResult.status === 'SENT') {
    try {
      // Resolve contact email + company from the SID
      const sid = await env.D1.prepare(
        'SELECT recipient_email, communication_id FROM lcs_sid_output WHERE sid_id = ?'
      ).bind(sidResult.sid_id).first<any>();
      const cid = await env.D1.prepare(
        'SELECT sovereign_company_id, frame_id FROM lcs_cid WHERE communication_id = ?'
      ).bind(cidResult.communication_id).first<any>();

      if (sid?.recipient_email && cid?.sovereign_company_id) {
        await advanceSequenceState(
          env.D1,
          cid.sovereign_company_id,
          sid.recipient_email,
          'SEQ-COLD-EMAIL-V1',
        );
      }
    } catch (seqErr) {
      // Sequence tracking is non-blocking â€” delivery already succeeded
      console.error('[sequence] state tracking failed:', seqErr instanceof Error ? seqErr.message : String(seqErr));
    }
  }

  return { cid: cidResult, sid: sidResult, mid: midResult };
}

// â”€â”€ Domain Rotation â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

async function pickSendingDomain(d1: D1Database): Promise<{ domain: string; fromEmail: string } | null> {
  // Pick the next available domain: not paused, under daily cap, healthy bounce rate,
  // and bias toward the warmest safe domains first.
  const domain = await d1.prepare(`
    SELECT domain FROM lcs_domain_rotation
    WHERE is_paused = 0
      AND sent_today < daily_cap
      AND (bounce_count_24h * 100) < (daily_cap * ?)
    ORDER BY warmup_week ASC, bounce_count_24h ASC, last_sent_at ASC NULLS FIRST, sent_today ASC
    LIMIT 1
  `).bind(EMAIL_DELIVERABILITY_CONFIG.warmup.bounce_rate_threshold_percent).first<{ domain: string }>();

  if (!domain) return null; // All domains at capacity or paused

  // Build from email: dave@{domain}
  const fromEmail = `dave@${domain.domain}`;
  return { domain: domain.domain, fromEmail };
}

async function recordDomainSend(d1: D1Database, domain: string, bounced: boolean): Promise<void> {
  await d1.prepare(`
    UPDATE lcs_domain_rotation
    SET sent_today = sent_today + 1,
        total_sent = total_sent + 1,
        bounce_count_24h = bounce_count_24h + CASE WHEN ? THEN 1 ELSE 0 END,
        last_sent_at = datetime('now'),
        updated_at = datetime('now')
    WHERE domain = ?
  `).bind(bounced ? 1 : 0, domain).run();
}

// â”€â”€ Delivery Adapters â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

async function deliverMailgun(
  env: Env, sid: any, cid: any, midId: string,
): Promise<{ success: boolean; provider_id: string | null; error: string | null }> {
  if (!sid.recipient_email) {
    return { success: false, provider_id: null, error: 'No recipient email' };
  }

  // Check suppression list â€” never send to complained/bounced/unsubscribed
  const suppressed = await env.D1.prepare(
    'SELECT email FROM lcs_suppression WHERE email = ?'
  ).bind(sid.recipient_email).first();
  if (suppressed) {
    return { success: false, provider_id: null, error: `Suppressed: ${sid.recipient_email}` };
  }

  // Pick sending domain from rotation
  const sendingDomain = await pickSendingDomain(env.D1);
  if (!sendingDomain) {
    return { success: false, provider_id: null, error: 'All sending domains at daily capacity or paused' };
  }

  try {
    // CAN-SPAM footer injection (BAR-176 addendum) — compiler is single source of truth.
    // Idempotency guard: only inject if footer not already present.
    const CAN_SPAM_MARKER = '1177 Briar Valley';
    const CAN_SPAM_FOOTER_PLAIN = '\n\n\n— — — — — — — — — — — — — — — — — — — — — — — —\nSVG Agency · 1177 Briar Valley Road · Bedford, PA 15522\nTo stop receiving these emails, reply with STOP.\n';
    const CAN_SPAM_FOOTER_HTML = '<br><br>\n<hr style="border:none;border-top:1px solid #ccc;margin:20px 0;">\n<p style="font-size:11px;color:#666;font-family:sans-serif;">\n  SVG Agency · 1177 Briar Valley Road · Bedford, PA 15522<br>\n  To stop receiving these emails, reply with STOP.\n</p>';

    let bodyPlain: string = sid.body_plain ?? '';
    if (!bodyPlain.includes(CAN_SPAM_MARKER)) {
      bodyPlain = bodyPlain + CAN_SPAM_FOOTER_PLAIN;
    }

    let bodyHtml: string | null = sid.body_html ?? null;
    if (bodyHtml && !bodyHtml.includes(CAN_SPAM_MARKER)) {
      const closingBodyIdx = bodyHtml.toLowerCase().lastIndexOf('</body>');
      if (closingBodyIdx !== -1) {
        bodyHtml = bodyHtml.slice(0, closingBodyIdx) + CAN_SPAM_FOOTER_HTML + bodyHtml.slice(closingBodyIdx);
      } else {
        bodyHtml = bodyHtml + CAN_SPAM_FOOTER_HTML;
      }
    }

    // ── ASCII normalization (voice-spec v1.2.0) ────────────────────────────
    // Single chokepoint for outbound email. Runs AFTER CAN-SPAM footer
    // injection so footer constants (em-dashes, middle dots) get normalized
    // too — single source of truth for ASCII-safe rendering in every email
    // client (mojibake-proof). Applies to subject, plain body, and HTML.
    bodyPlain = asciiNormalize(bodyPlain);
    if (bodyHtml) bodyHtml = asciiNormalize(bodyHtml);
    const subjectLineAscii = asciiNormalize(sid.subject_line ?? '');

    const form = new FormData();
    form.append('from', `${sid.sender_identity} <${sendingDomain.fromEmail}>`);
    form.append('h:Reply-To', EMAIL_DELIVERABILITY_CONFIG.reply_to);
    form.append('to', sid.recipient_email);
    form.append('subject', subjectLineAscii);
    form.append('text', bodyPlain);
    if (bodyHtml) form.append('html', bodyHtml);
    form.append('o:tag', cid.lane ?? 'COLD');
    form.append('o:tag', cid.frame_id);
    form.append('o:tag', sendingDomain.domain); // Track which domain sent it
    form.append('v:communication_id', sid.communication_id);
    form.append('v:message_run_id', midId);
    form.append('v:sovereign_company_id', cid.sovereign_company_id);
    form.append('v:sending_domain', sendingDomain.domain);

    const resp = await fetch(
      `https://api.mailgun.net/v3/${sendingDomain.domain}/messages`,
      {
        method: 'POST',
        headers: { Authorization: `Basic ${btoa(`api:${env.MAILGUN_API_KEY}`)}` },
        body: form,
      },
    );

    if (!resp.ok) {
      const body = await resp.text();
      await recordDomainSend(env.D1, sendingDomain.domain, true);
      return { success: false, provider_id: null, error: `Mailgun ${resp.status} via ${sendingDomain.domain}: ${body}` };
    }

    const data = await resp.json<{ id?: string }>();
    await recordDomainSend(env.D1, sendingDomain.domain, false);
    return { success: true, provider_id: data.id ?? null, error: null };
  } catch (err) {
    await recordDomainSend(env.D1, sendingDomain.domain, true);
    return { success: false, provider_id: null, error: err instanceof Error ? err.message : String(err) };
  }
}

async function deliverHeyReach(
  env: Env, sid: any, cid: any, midId: string,
): Promise<{ success: boolean; provider_id: string | null; error: string | null }> {
  // Check suppression list â€” never send to complained/bounced/unsubscribed
  if (sid.recipient_email) {
    const suppressed = await env.D1.prepare(
      'SELECT email FROM lcs_suppression WHERE email = ?'
    ).bind(sid.recipient_email).first();
    if (suppressed) {
      return { success: false, provider_id: null, error: `Suppressed: ${sid.recipient_email}` };
    }
  }

  // HeyReach needs LinkedIn URL from the people master (via slot join)
  const slot = await env.D1_OUTREACH.prepare(`
    SELECT pm.linkedin_url FROM people_company_slot cs
    JOIN people_people_master pm ON cs.person_unique_id = pm.unique_id
    WHERE cs.outreach_id = ? AND cs.is_filled = 1 AND pm.linkedin_url IS NOT NULL LIMIT 1
  `).bind(cid.entity_id).first<any>();

  if (!slot?.linkedin_url) {
    return { success: false, provider_id: null, error: 'No LinkedIn URL for recipient' };
  }

  try {
    const resp = await fetch('https://api.heyreach.io/api/public/v2/leads/add', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-API-KEY': env.HEYREACH_API_KEY,
      },
      body: JSON.stringify({
        linkedin_url: slot.linkedin_url,
        custom_variables: {
          communication_id: sid.communication_id,
          message_run_id: midId,
          message: sid.body_plain,
        },
      }),
    });

    if (!resp.ok) {
      const body = await resp.text();
      return { success: false, provider_id: null, error: `HeyReach ${resp.status}: ${body}` };
    }

    const data = await resp.json<{ id?: string }>();
    return { success: true, provider_id: data.id ?? null, error: null };
  } catch (err) {
    return { success: false, provider_id: null, error: err instanceof Error ? err.message : String(err) };
  }
}

// â”€â”€ LBB Query (Library Barton Brain) â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
// Single knowledge store. Tail arbitration only â€” deterministic
// templates are the spine. LBB enriches when content is available.

interface LbbRecord {
  record_id: string;
  title: string;
  content: string;
  subject_id: string;
  tags: string;
}

async function queryLbb(
  env: Env,
  query: string,
  subjectId: string,
  limit = 3,
): Promise<LbbRecord[]> {
  try {
    const resp = await fetch(`${env.LBB_URL}/query`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${env.LBB_API_KEY}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ query, subject_id: subjectId, limit }),
    });
    if (!resp.ok) return [];
    const data = await resp.json<{ results?: LbbRecord[]; records?: LbbRecord[] }>();
    return data.results ?? data.records ?? [];
  } catch {
    return []; // LBB down = fall back to hardcoded templates. No pipeline break.
  }
}

// Pull Dave's talking points from svg-sales for message enrichment
async function getSalesTalkingPoints(
  env: Env,
  signalCategory: string,
  companyContext: string,
): Promise<string | null> {
  // Map signal categories to search queries that hit Dave's slide library
  const queryMap: Record<string, string> = {
    'RENEWAL_PROXIMITY': 'self-insured benefits cost management renewal',
    'BROKER_CHANGE': 'broker comparison value proposition informatics',
    'DOL_PREMIUM_PRESSURE': 'claims cost 10 percent population management',
    'EXEC_CHANGE': 'new CFO CEO benefits data dashboard introduction',
    'OUTREACH': 'insurance informatics value proposition 10 percent 85 percent',
  };
  const searchQuery = queryMap[signalCategory] ?? 'insurance informatics value proposition benefits';

  const records = await queryLbb(env, searchQuery, 'svg-sales', 2);
  if (records.length === 0) return null;

  // Extract the most relevant talking point content
  const points = records
    .map(r => r.content)
    .filter(c => c && c.length > 20)
    .join('\n\n');

  return points || null;
}

// Pull company-specific intelligence from svg-outreach
async function getCompanyIntelligence(
  env: Env,
  companyName: string,
): Promise<string | null> {
  const records = await queryLbb(env, companyName, 'svg-outreach', 2);
  if (records.length === 0) return null;

  const intel = records
    .map(r => `${r.title}: ${r.content}`)
    .filter(c => c.length > 20)
    .join('\n');

  return intel || null;
}

// â”€â”€ Voice Constants (BAR-285) â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
// Loaded from lcs_voice_library per-frame before buildMessageBody.
// Passed through to buildMessageBody for future LLM tail personalization.
// Forbidden phrases are validated AFTER message build â€” any hit = block.

interface VoiceConstants {
  voiceId: string;
  targetRole: string;
  tone: string;
  styleRules: string[];
  forbiddenPhrases: string[];
  openingPatterns: string[];
  closingPatterns: string[];
  proofPoints: string[];
}

function parseJsonArray(raw: string | null | undefined): string[] {
  if (!raw) return [];
  try {
    const parsed = JSON.parse(raw);
    return Array.isArray(parsed) ? parsed.map(String) : [];
  } catch {
    return [];
  }
}

// Merges role-specific voice with ALL-role base voice.
// forbidden_phrases = union of both (ALL rules always apply).
function parseVoiceRow(row: any, baseRow: any): VoiceConstants {
  const roleForbidden = parseJsonArray(row.forbidden_phrases);
  const baseForbidden = baseRow && baseRow.voice_id !== row.voice_id
    ? parseJsonArray(baseRow.forbidden_phrases)
    : [];
  const merged = Array.from(new Set([...baseForbidden, ...roleForbidden]));

  return {
    voiceId: row.voice_id,
    targetRole: row.target_role,
    tone: row.tone ?? '',
    styleRules: parseJsonArray(row.style_rules),
    forbiddenPhrases: merged,
    openingPatterns: parseJsonArray(row.opening_patterns),
    closingPatterns: parseJsonArray(row.closing_patterns),
    proofPoints: parseJsonArray(row.proof_points),
  };
}

// â”€â”€ Message Building â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

function titleCase(s: string): string {
  return s.toLowerCase().replace(/\b\w/g, c => c.toUpperCase())
    .replace(/\bLlc\b/gi, 'LLC').replace(/\bInc\.\b/gi, 'Inc.').replace(/\bInc\b/gi, 'Inc.')
    .replace(/\bLlp\b/gi, 'LLP').replace(/\bInc\.\./g, 'Inc.').replace(/'S\b/g, "'s");
}

// BAR Option-B refactor: subject line content is sourced from D1
// (lcs_frame_registry.subject_line_template). The compiler no longer
// hardcodes per-frame strings. Returns null if the template is absent
// or empty so the caller can log + skip SID construction.
function buildSubjectLine(
  frame: any,
  companyName: string,
  recipientName: string,
  senderSig: SenderSignature,
): string | null {
  const template: string | null = frame?.subject_line_template ?? null;
  if (!template || typeof template !== 'string' || template.trim() === '') {
    return null;
  }
  const cn = companyName === companyName.toUpperCase() ? titleCase(companyName) : companyName;
  return interpolateMergeTags(template, cn, recipientName, senderSig);
}

// â”€â”€ Grid-Driven Fact Builder â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
// Only outputs facts we actually have. No data = no mention.

interface GridData {
  industry: string | null;
  employees: number | null;
  state: string | null;
  city: string | null;
  hasDol: boolean;
  fundingType: string | null;
  carrier: string | null;
  broker: string | null;
  renewalMonth: number | null;
  slotType: string | null;
}

const MONTH_NAMES = ['January','February','March','April','May','June','July','August','September','October','November','December'];

function buildCompanyFact(companyName: string, grid: GridData): string {
  const cn = companyName === companyName.toUpperCase() ? titleCase(companyName) : companyName;
  const parts: string[] = [];

  // Size context â€” if we have employee count
  if (grid.employees && grid.employees > 0) {
    if (grid.employees <= 25) parts.push(`a ${grid.employees}-person operation`);
    else if (grid.employees <= 100) parts.push(`a ${grid.employees}-employee company`);
    else if (grid.employees <= 500) parts.push(`${grid.employees} employees`);
    else parts.push(`${grid.employees}+ employees`);
  }

  // Location
  if (grid.city && grid.state) parts.push(`${grid.city}, ${grid.state}`);
  else if (grid.state) parts.push(grid.state);

  // Industry
  if (grid.industry) parts.push(grid.industry.toLowerCase());

  if (parts.length === 0) return '';
  return `${cn} â€” ${parts.join(', ')}`;
}

function buildDolFact(grid: GridData): string | null {
  if (!grid.hasDol) return null;
  const facts: string[] = [];

  if (grid.renewalMonth) {
    const monthName = MONTH_NAMES[(grid.renewalMonth - 1) % 12];
    facts.push(`your plan year ends in ${monthName}`);
  }
  if (grid.carrier) facts.push(`current carrier is ${grid.carrier}`);
  if (grid.broker) facts.push(`your broker of record is ${grid.broker}`);
  if (grid.fundingType === 'self-funded') facts.push(`you're self-funded`);

  return facts.length > 0 ? facts.join('. ') : 'your DOL filing is on file';
}

interface SenderSignature {
  name: string;
  title: string;
  company: string;
  website: string | null;
  linkedin_url: string | null;
  booking_link: string | null;
  tagline: string | null;
}

// Default signature â€” used only when D1 lookup fails (fallback, never primary)
const DEFAULT_SIGNATURE: SenderSignature = {
  name: 'Dave Barton',
  title: 'Founder & Insurance Informatics Pioneer',
  company: 'Insurance Informatics',
  website: 'insuranceinformatics.com',
  linkedin_url: 'linkedin.com/in/dbarton',
  booking_link: 'https://calendar.app.google/VT41mpEgTWDexFET8',
  tagline: 'The only insurance informatics firm in the country.',
};

function formatSignature(sig: SenderSignature): string {
  const lines = [sig.name, sig.title, sig.company];
  if (sig.website) lines.push(sig.website);
  if (sig.tagline) lines.push(sig.tagline);
  return buildSignatureFooter(lines);
}

// BAR Option-B refactor: body content is sourced from D1
// (lcs_frame_registry.body_template). The compiler reads the template,
// interpolates {merge_tags}, and appends the signature block.
// Code no longer owns copy. Template changes = D1 UPDATE, no deploy.
// Returns null if the template is missing/empty — caller logs + skips SID.
function interpolateMergeTags(
  template: string,
  cn: string,
  recipientName: string,
  senderSig: SenderSignature,
): string {
  // Derive first name: first whitespace-delimited token if a space exists,
  // otherwise the full recipientName. Fallback to 'there' if empty.
  let firstName: string;
  if (recipientName && recipientName.trim() !== '' && recipientName !== 'there') {
    firstName = recipientName.includes(' ')
      ? recipientName.split(' ')[0]
      : recipientName;
  } else {
    firstName = 'there';
  }

  const agentName = senderSig.name ?? 'Dave Barton';
  // senderSig does not carry an email field today — hardcode the canonical
  // sender address. When the signature table adds an email column, swap this.
  const agentEmail = 'dave@svg.agency';
  const agentPhone = (senderSig as any).phone ?? '(304) 821-2400';
  const bookingLink = senderSig.booking_link ?? DEFAULT_SIGNATURE.booking_link!;

  return template
    .replace(/\{first_name\}/g, firstName)
    .replace(/\{company_name\}/g, cn)
    .replace(/\{agent_name\}/g, agentName)
    .replace(/\{agent_email\}/g, agentEmail)
    .replace(/\{agent_phone\}/g, agentPhone)
    .replace(/\{booking_link\}/g, bookingLink);
}

function buildMessageBody(
  frame: any,
  companyName: string,
  recipientName: string,
  _cid: any,
  _talkingPoints: string | null = null,
  _companyIntel: string | null = null,
  _grid: GridData = { industry: null, employees: null, state: null, city: null, hasDol: false, fundingType: null, carrier: null, broker: null, renewalMonth: null, slotType: null },
  senderSig: SenderSignature = DEFAULT_SIGNATURE,
): string | null {
  const template: string | null = frame?.body_template ?? null;
  if (!template || typeof template !== 'string' || template.trim() === '') {
    return null;
  }

  const cn = companyName === companyName.toUpperCase() ? titleCase(companyName) : companyName;
  const interpolated = interpolateMergeTags(template, cn, recipientName, senderSig);
  const sig = formatSignature(senderSig);

  // Signature is the compiler's responsibility, not the template's.
  // Append with a double-newline separator so layout stays consistent
  // regardless of whether the template writer remembered trailing space.
  return `${interpolated}\n\n${sig}`;
}
// ── BAR-304: Sequence Engine ────────────────────────────────────────────────
// Tracks contact progress through multi-step sequences.
// lcs_sequence_def: defines steps (frame_id, delay_hours, condition)
// lcs_contact_sequence_state: tracks per-contact progress

async function advanceSequenceState(
  d1: D1Database,
  sovereignCompanyId: string,
  contactEmail: string,
  sequenceId: string,
): Promise<void> {
  // Step 2's delay tells us when step 2 should fire (the wait after step 1)
  const nextStep = await getSequenceStep(d1, sequenceId, 2);
  const firstDelayHours = nextStep?.delay_hours ?? 48;
  const firstNextStepAfter = new Date(Date.now() + firstDelayHours * 3600_000).toISOString();

  // Race-safe UPSERT: INSERT at step 1, or advance current_step if already exists.
  // Requires UNIQUE index on (contact_email, sequence_id) â€” see migration 011.
  const id = `SEQ-${crypto.randomUUID().replace(/-/g, '').slice(0, 16)}`;

  await d1.prepare(`
    INSERT INTO lcs_contact_sequence_state (
      id, sovereign_company_id, contact_email, sequence_id,
      current_step, status, last_step_at, next_step_after,
      created_at, updated_at
    ) VALUES (?, ?, ?, ?, 1, 'active', datetime('now'), ?, datetime('now'), datetime('now'))
    ON CONFLICT(contact_email, sequence_id) DO UPDATE SET
      current_step = current_step + 1,
      last_step_at = datetime('now'),
      next_step_after = excluded.next_step_after,
      updated_at = datetime('now')
  `).bind(id, sovereignCompanyId, contactEmail, sequenceId, firstNextStepAfter).run();

  // After upsert, check if the (possibly advanced) step actually exists
  const state = await d1.prepare(
    'SELECT current_step FROM lcs_contact_sequence_state WHERE contact_email = ? AND sequence_id = ?'
  ).bind(contactEmail, sequenceId).first<any>();

  if (!state) return; // Shouldn't happen after upsert, but guard

  const currentStep = state.current_step ?? 1;

  if (currentStep > 1) {
    // Was an UPDATE (advance) â€” verify the step exists
    const stepDef = await getSequenceStep(d1, sequenceId, currentStep);
    if (!stepDef) {
      // Sequence complete â€” no more steps defined
      await d1.prepare(`
        UPDATE lcs_contact_sequence_state
        SET status = 'completed', current_step = ?, last_step_at = datetime('now'),
            next_step_after = NULL, updated_at = datetime('now')
        WHERE contact_email = ? AND sequence_id = ?
      `).bind(currentStep - 1, contactEmail, sequenceId).run();
      return;
    }

    // Recalculate next_step_after using the actual step's delay_hours
    const delayHours = stepDef.delay_hours ?? 48;
    const nextStepAfter = new Date(Date.now() + delayHours * 3600_000).toISOString();

    await d1.prepare(`
      UPDATE lcs_contact_sequence_state
      SET next_step_after = ?, updated_at = datetime('now')
      WHERE contact_email = ? AND sequence_id = ?
    `).bind(nextStepAfter, contactEmail, sequenceId).run();
  }
}

async function getSequenceStep(
  d1: D1Database,
  sequenceId: string,
  stepNumber: number,
): Promise<{ frame_id: string; delay_hours: number; condition: string | null; channel: string } | null> {
  return await d1.prepare(
    'SELECT frame_id, delay_hours, condition, channel FROM lcs_sequence_def WHERE sequence_id = ? AND step_number = ? AND is_active = 1'
  ).bind(sequenceId, stepNumber).first<any>() ?? null;
}

// Checks if the current sequence step's condition is met based on engagement history.
// Returns true if the step SHOULD be executed, false if it should be skipped.
export function isSequenceConditionMet(
  condition: string | null,
  lastEngagement: string | null,
): boolean {
  if (!condition) return true; // No condition = always execute

  const positiveEngagements = ['opened', 'clicked'];
  const hasPositive = lastEngagement ? positiveEngagements.includes(lastEngagement) : false;

  if (condition === 'opened' || condition === 'clicked') {
    // Step requires positive engagement â€” skip if none
    return hasPositive;
  }
  if (condition === 'not_opened') {
    // Step requires NO positive engagement â€” skip if they engaged
    return !hasPositive;
  }

  // Unknown condition â€” execute by default (don't silently skip)
  return true;
}

// Finds the next valid step in a sequence, skipping steps whose conditions aren't met.
// Returns the step definition or null if sequence is exhausted.
async function findNextValidStep(
  d1: D1Database,
  sequenceId: string,
  startStep: number,
  lastEngagement: string | null,
  maxSteps = 10,
): Promise<{ step_number: number; frame_id: string; delay_hours: number; condition: string | null; channel: string } | null> {
  for (let step = startStep; step < startStep + maxSteps; step++) {
    const stepDef = await getSequenceStep(d1, sequenceId, step);
    if (!stepDef) return null; // No more steps in sequence

    if (isSequenceConditionMet(stepDef.condition, lastEngagement)) {
      return { step_number: step, ...stepDef };
    }
    // Condition not met â€” skip this step, try next
  }
  return null; // All remaining steps skipped
}

// Updates last_engagement on a contact's sequence state (called from engagement response path)
async function updateSequenceEngagement(
  d1: D1Database,
  sovereignCompanyId: string,
  contactEmail: string,
  triggerEvent: string,
): Promise<void> {
  await d1.prepare(`
    UPDATE lcs_contact_sequence_state
    SET last_engagement = ?, updated_at = datetime('now')
    WHERE sovereign_company_id = ? AND contact_email = ?
    AND status = 'active'
  `).bind(triggerEvent, sovereignCompanyId, contactEmail).run();
}

// â”€â”€ D1 Helpers â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

// â”€â”€ Engagement Response Compiler (BAR-303) â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
// Reads lcs_engagement_rules for the trigger_event.
// send_followup â†’ mints CID with rule's frame_id, then normal SIDâ†’MID pipeline.
// stop/escalate â†’ marks signal processed, logs event, done.

async function compileEngagementResponse(
  env: Env,
  signal: any,
  signalQueueId: string,
): Promise<{ communication_id: string; status: string } | null> {
  try {
    const signalData = JSON.parse(signal.signal_data ?? '{}');
    const triggerEvent: string = signalData.trigger_event ?? '';

    if (!triggerEvent) {
      await env.D1.prepare(
        "UPDATE lcs_signal_queue SET status = 'failed', processed_at = datetime('now') WHERE id = ?"
      ).bind(signalQueueId).run();
      return null;
    }

    // 1. Check suppression FIRST â€” before anything else (Codex audit fix #2)
    // A bounce webhook and an open webhook can race. If the bounce hasn't written
    // the suppression record yet, this check passes. Belt-and-suspenders: delivery
    // stage also checks suppression, so even if this passes, the MID won't send.
    const contactEmail = signalData.contact_email ?? null;
    if (contactEmail) {
      const suppressed = await env.D1.prepare(
        "SELECT 1 FROM lcs_suppression WHERE email = ? LIMIT 1"
      ).bind(contactEmail).first();
      if (suppressed) {
        await env.D1.prepare(
          "UPDATE lcs_signal_queue SET status = 'suppressed', processed_at = datetime('now') WHERE id = ?"
        ).bind(signalQueueId).run();
        return null;
      }
    }

    // 2. BAR-304: Update sequence engagement state BEFORE rule lookup
    // This records that the contact engaged, so condition checks downstream are current.
    if (contactEmail && signal.sovereign_company_id) {
      try {
        await updateSequenceEngagement(env.D1, signal.sovereign_company_id, contactEmail, triggerEvent);
      } catch (seqErr) {
        // Non-blocking â€” engagement tracking failure doesn't stop the pipeline
        console.error('[sequence] engagement update failed:', seqErr instanceof Error ? seqErr.message : String(seqErr));
      }
    }

    // 3. Look up rule
    const rule = await env.D1.prepare(
      "SELECT * FROM lcs_engagement_rules WHERE trigger_event = ? AND is_active = 1"
    ).bind(triggerEvent).first<any>();

    if (!rule) {
      await env.D1.prepare(
        "UPDATE lcs_signal_queue SET status = 'processed', processed_at = datetime('now') WHERE id = ?"
      ).bind(signalQueueId).run();
      return null;
    }

    // 4. Non-send actions (stop, escalate_channel, wait)
    if (rule.action === 'escalate_channel') {
      // BAR-307: Cross-channel orchestration â€” switch from email to LinkedIn
      const channelState = contactEmail
        ? await env.D1.prepare(
            'SELECT * FROM lcs_contact_channel_state WHERE contact_email = ?'
          ).bind(contactEmail).first<any>()
        : null;

      if (channelState && channelState.email_status === 'active') {
        // Switch: email exhausted â†’ LinkedIn active
        await env.D1.prepare(`
          UPDATE lcs_contact_channel_state SET
            email_status = 'exhausted',
            linkedin_status = 'active',
            primary_channel = 'HR',
            channel_state = 'linkedin_active',
            switch_reason = 'email_no_response_7d',
            last_channel_switch_at = datetime('now'),
            updated_at = datetime('now')
          WHERE contact_email = ?
        `).bind(contactEmail).run();

        // Insert a new signal pointing to HR (LinkedIn/HeyReach) channel
        const switchSigId = `SIG-CHSW-${crypto.randomUUID().replace(/-/g, '').slice(0, 12)}`;
        await env.D1.prepare(`
          INSERT INTO lcs_signal_queue (
            id, signal_set_hash, signal_category,
            sovereign_company_id, lifecycle_phase, preferred_channel,
            lane, agent_number, signal_data, source_signal_id,
            status, priority, created_at
          ) VALUES (?, ?, 'OUTREACH', ?, ?, 'HR', ?, ?, ?, ?, 'pending', 8, datetime('now'))
        `).bind(
          switchSigId,
          signal.signal_set_hash,
          signal.sovereign_company_id,
          signal.lifecycle_phase,
          signal.lane ?? 'COLD',
          signal.agent_number ?? 'SA-001',
          JSON.stringify({
            trigger_event: 'channel_switch',
            source_signal_id: signalQueueId,
            contact_email: contactEmail,
            switch_reason: 'email_no_response_7d',
          }),
          signalQueueId,
        ).run();

        console.log(`[channel] ${contactEmail} switched MGâ†’HR (email_no_response_7d) for ${signal.sovereign_company_id}`);
      } else if (!channelState && contactEmail) {
        // No channel state record yet â€” create one already set to HR
        await env.D1.prepare(`
          INSERT OR IGNORE INTO lcs_contact_channel_state (contact_email, sovereign_company_id, primary_channel, channel_state, email_status, linkedin_status, switch_reason, last_channel_switch_at)
          VALUES (?, ?, 'HR', 'linkedin_active', 'exhausted', 'active', 'email_no_response_7d', datetime('now'))
        `).bind(contactEmail, signal.sovereign_company_id).run();
        console.log(`[channel] ${contactEmail} created as HR (no prior state) for ${signal.sovereign_company_id}`);
      } else {
        console.log(`[channel] ${contactEmail} already switched or no email â€” skipping escalate for ${signal.sovereign_company_id}`);
      }

      await env.D1.prepare(
        "UPDATE lcs_signal_queue SET status = 'processed', processed_at = datetime('now') WHERE id = ?"
      ).bind(signalQueueId).run();
      return null;
    }

    if (rule.action !== 'send_followup') {
      await env.D1.prepare(
        "UPDATE lcs_signal_queue SET status = 'processed', processed_at = datetime('now') WHERE id = ?"
      ).bind(signalQueueId).run();
      console.log(`[engagement] ${triggerEvent} â†’ ${rule.action} for ${signal.sovereign_company_id}`);
      return null;
    }

    // 5. send_followup â€” need a frame
    if (!rule.followup_frame_id) {
      await logErr0(env.D1, {
        message_run_id: signalData.source_mid_id ?? 'NONE',
        sovereign_company_id: signal.sovereign_company_id,
        failure_type: 'ENGAGEMENT_NO_FRAME',
        failure_message: `Rule ${rule.rule_id} has action=send_followup but no followup_frame_id`,
        lifecycle_phase: signal.lifecycle_phase,
      });
      await env.D1.prepare(
        "UPDATE lcs_signal_queue SET status = 'failed', processed_at = datetime('now') WHERE id = ?"
      ).bind(signalQueueId).run();
      return null;
    }

    // 5b. BAR-304: Check sequence condition before minting CID
    // If contact is in a sequence, check if the current step's condition is met.
    // If not, skip to the next valid step or complete the sequence.
    if (contactEmail && signal.sovereign_company_id) {
      try {
        const seqState = await env.D1.prepare(
          "SELECT * FROM lcs_contact_sequence_state WHERE sovereign_company_id = ? AND contact_email = ? AND status = 'active'"
        ).bind(signal.sovereign_company_id, contactEmail).first<any>();

        if (seqState) {
          const nextStepNum = (seqState.current_step ?? 1) + 1;
          const currentStepDef = await getSequenceStep(env.D1, seqState.sequence_id, nextStepNum);

          if (currentStepDef && !isSequenceConditionMet(currentStepDef.condition, triggerEvent)) {
            // Condition not met â€” find next valid step
            const validStep = await findNextValidStep(
              env.D1, seqState.sequence_id, nextStepNum + 1, triggerEvent,
            );

            if (!validStep) {
              // No valid steps remain â€” complete the sequence, skip this send
              await env.D1.prepare(`
                UPDATE lcs_contact_sequence_state
                SET status = 'completed', updated_at = datetime('now')
                WHERE sovereign_company_id = ? AND contact_email = ? AND sequence_id = ?
              `).bind(signal.sovereign_company_id, contactEmail, seqState.sequence_id).run();
              await env.D1.prepare(
                "UPDATE lcs_signal_queue SET status = 'processed', processed_at = datetime('now') WHERE id = ?"
              ).bind(signalQueueId).run();
              console.log(`[sequence] all remaining steps skipped for ${contactEmail} â€” condition not met`);
              return null;
            }

            // Valid step found â€” persist the skip so sequence doesn't loop at the old step
            await env.D1.prepare(
              "UPDATE lcs_contact_sequence_state SET current_step = ?, next_step_after = datetime('now', '+' || ? || ' hours'), updated_at = datetime('now') WHERE contact_email = ? AND sequence_id = ? AND status = 'active'"
            ).bind(validStep.step_number, validStep.delay_hours ?? 0, contactEmail, seqState.sequence_id).run();

            // Override the rule's frame_id with the valid step's frame_id
            rule.followup_frame_id = validStep.frame_id;

            console.log(`[sequence] step ${nextStepNum} skipped (condition=${currentStepDef.condition}, engagement=${triggerEvent}), advancing to step ${validStep.step_number}`);
          }
        }
      } catch (seqErr) {
        // Non-blocking â€” condition check failure doesn't stop the pipeline
        console.error('[sequence] condition check failed:', seqErr instanceof Error ? seqErr.message : String(seqErr));
      }
    }

    // 6. Resolve company identity (same pattern as compileCid)
    const identity = await env.D1.prepare(
      'SELECT * FROM cl_company_identity WHERE company_unique_id = ?'
    ).bind(signal.sovereign_company_id).first<any>();

    if (!identity || !identity.outreach_id) {
      await logErr0(env.D1, {
        message_run_id: signalData.source_mid_id ?? 'NONE',
        sovereign_company_id: signal.sovereign_company_id,
        failure_type: 'ENGAGEMENT_COMPANY_NOT_FOUND',
        failure_message: `Company ${signal.sovereign_company_id} not found for engagement follow-up`,
        lifecycle_phase: signal.lifecycle_phase,
      });
      await env.D1.prepare(
        "UPDATE lcs_signal_queue SET status = 'failed', processed_at = datetime('now') WHERE id = ?"
      ).bind(signalQueueId).run();
      return null;
    }

    // 7. Setpoint â€” max follow-up count per contact (BAR-303 OE-1)
    const followupCount = await env.D1.prepare(
      "SELECT COUNT(*) as cnt FROM lcs_cid WHERE sovereign_company_id = ? AND compilation_reason = 'engagement_followup'"
    ).bind(signal.sovereign_company_id).first<{cnt: number}>();
    const MAX_ENGAGEMENT_FOLLOWUPS = 5; // setpoint â€” human tunes this
    if ((followupCount?.cnt ?? 0) >= MAX_ENGAGEMENT_FOLLOWUPS) {
      await env.D1.prepare(
        "UPDATE lcs_signal_queue SET status = 'processed', processed_at = datetime('now') WHERE id = ?"
      ).bind(signalQueueId).run();
      console.log('[engagement] setpoint reached â€” max follow-ups for', signal.sovereign_company_id);
      return null;
    }

    // 8. Mint CID with the rule's frame_id
    const communicationId = mintCommId(signal.lifecycle_phase ?? 'OUTREACH');

    // BAR-303: Inherit intelligence_tier from original CID (DOL context carries forward)
    const originalCid = signalData.source_communication_id
      ? await env.D1.prepare('SELECT intelligence_tier FROM lcs_cid WHERE communication_id = ?')
        .bind(signalData.source_communication_id).first<any>()
      : null;
    const tier = originalCid?.intelligence_tier ?? 5;

    await env.D1.prepare(`
      INSERT INTO lcs_cid (
        communication_id, sovereign_company_id, entity_type, entity_id,
        signal_set_hash, signal_queue_id, frame_id, lifecycle_phase,
        lane, agent_number, intelligence_tier, compilation_status,
        compilation_reason, created_at
      ) VALUES (?, ?, 'company', ?, ?, ?, ?, ?, ?, ?, ?, 'COMPILED', 'engagement_followup', datetime('now'))
    `).bind(
      communicationId,
      signal.sovereign_company_id,
      identity.outreach_id,  // entity_id = outreach_id for slot lookups
      signal.signal_set_hash,
      signalQueueId,
      rule.followup_frame_id,
      signal.lifecycle_phase ?? 'OUTREACH',
      signal.preferred_lane ?? 'WARM',  // engagement = warm, not cold
      signal.agent_number ?? 'SA-001',
      tier,
    ).run();

    await env.D1.prepare(
      "UPDATE lcs_signal_queue SET status = 'processed', processed_at = datetime('now') WHERE id = ?"
    ).bind(signalQueueId).run();

    console.log(`[engagement] ${triggerEvent} â†’ send_followup (${rule.followup_frame_id}) â†’ ${communicationId} for ${signal.sovereign_company_id}`);

    return { communication_id: communicationId, status: 'COMPILED' };
  } catch (err) {
    const msg = err instanceof Error ? err.message : String(err);
    try { await logErr0(env.D1, {
      message_run_id: 'NONE',
      sovereign_company_id: signal.sovereign_company_id ?? '',
      failure_type: 'ENGAGEMENT_COMPILATION_ERROR',
      failure_message: msg,
      lifecycle_phase: signal.lifecycle_phase ?? 'OUTREACH',
    }); } catch {}
    try {
      await env.D1.prepare(
        "UPDATE lcs_signal_queue SET status = 'failed', processed_at = datetime('now') WHERE id = ?"
      ).bind(signalQueueId).run();
    } catch {}
    return null;
  }
}


async function logEvent(d1: D1Database, params: {
  communication_id: string;
  message_run_id: string;
  sovereign_company_id: string;
  entity_type: string;
  entity_id: string;
  signal_set_hash: string;
  frame_id: string;
  adapter_type: string;
  channel: string;
  delivery_status: string;
  lifecycle_phase: string;
  event_type: string;
  lane: string;
  agent_number: string;
  step_number: number;
  step_name: string;
  intelligence_tier?: number;
  sender_identity?: string;
  adapter_response?: string | null;
}): Promise<void> {
  await d1.prepare(`
    INSERT INTO lcs_event (
      communication_id, message_run_id, sovereign_company_id,
      entity_type, entity_id, signal_set_hash, frame_id,
      adapter_type, channel, delivery_status, lifecycle_phase,
      event_type, lane, agent_number, step_number, step_name,
      payload, adapter_response, intelligence_tier, sender_identity,
      created_at
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
  `).bind(
    params.communication_id, params.message_run_id, params.sovereign_company_id,
    params.entity_type, params.entity_id, params.signal_set_hash, params.frame_id,
    params.adapter_type, params.channel, params.delivery_status, params.lifecycle_phase,
    params.event_type, params.lane, params.agent_number, params.step_number, params.step_name,
    null, params.adapter_response ?? null, params.intelligence_tier ?? null, params.sender_identity ?? null,
    `${new Date().toISOString()}.${Math.random().toString(36).slice(2, 6)}`, // unique timestamp to avoid PK collision
  ).run();
}

async function logErr0(d1: D1Database, params: {
  message_run_id: string;
  communication_id?: string;
  sovereign_company_id?: string;
  failure_type: string;
  failure_message: string;
  lifecycle_phase?: string;
  adapter_type?: string;
  orbt_strike_number?: number;
  orbt_action_taken?: string;
}): Promise<void> {
  await d1.prepare(`
    INSERT INTO lcs_err0 (
      error_id, message_run_id, communication_id, sovereign_company_id,
      failure_type, failure_message, lifecycle_phase, adapter_type,
      orbt_strike_number, orbt_action_taken, created_at
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))
  `).bind(
    mintErrorId(),
    params.message_run_id,
    params.communication_id ?? null,
    params.sovereign_company_id ?? null,
    params.failure_type,
    params.failure_message,
    params.lifecycle_phase ?? null,
    params.adapter_type ?? null,
    params.orbt_strike_number ?? null,
    params.orbt_action_taken ?? null,
  ).run();
}

async function writeMidState(d1: D1Database, params: {
  mid_id: string;
  message_run_id: string;
  communication_id: string;
  adapter_type: string;
  channel: string;
  sequence_position: number;
  attempt_number: number;
  gate_verdict: string;
  gate_reason?: string;
  delivery_status: string;
  recipient_email?: string;
}): Promise<void> {
  await d1.prepare(`
    INSERT INTO lcs_mid_sequence_state (
      mid_id, message_run_id, communication_id, adapter_type, channel,
      sequence_position, attempt_number, gate_verdict, gate_reason,
      throttle_status, delivery_status, recipient_email, created_at
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))
  `).bind(
    params.mid_id, params.message_run_id, params.communication_id,
    params.adapter_type, params.channel, params.sequence_position,
    params.attempt_number, params.gate_verdict, params.gate_reason ?? null,
    null, params.delivery_status, params.recipient_email ?? null,
  ).run();
}
// v2.2 â€” BAR-304: sequence engine wired into compiler (state tracking, engagement update, condition check)
