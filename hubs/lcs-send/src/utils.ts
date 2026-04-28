// ═══════════════════════════════════════════════════════════════
// LCS Hub — Utilities
// ═══════════════════════════════════════════════════════════════

/** Generate a ULID-like ID with prefix */
export function mintId(prefix: string): string {
  const date = new Date().toISOString().slice(0, 10).replace(/-/g, '');
  const rand = crypto.randomUUID().replace(/-/g, '').slice(0, 12);
  return `${prefix}-${date}-${rand}`;
}

/** Log an event to lcs_event (append-only) */
export async function logEvent(
  d1: D1Database,
  params: {
    sovereign_company_id: string;
    communication_id?: string;
    message_run_id?: string;
    event_type: string;
    signal_set_hash?: string;
    frame_id?: string;
    channel?: string;
    delivery_status?: string;
    lifecycle_phase?: string;
    lane?: string;
    agent_number?: string;
    step_number?: number;
    step_name?: string;
    intelligence_tier?: number;
    payload?: string;
  },
): Promise<void> {
  await d1.prepare(`
    INSERT INTO lcs_event (
      communication_id, message_run_id, sovereign_company_id,
      entity_type, entity_id, signal_set_hash, frame_id,
      adapter_type, channel, delivery_status, lifecycle_phase,
      event_type, lane, agent_number, step_number, step_name,
      payload, created_at
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
  `).bind(
    params.communication_id ?? 'NONE',
    params.message_run_id ?? 'NONE',
    params.sovereign_company_id,
    'company', null,
    params.signal_set_hash ?? null,
    params.frame_id ?? null,
    'NONE', params.channel ?? 'NONE',
    params.delivery_status ?? 'NONE',
    params.lifecycle_phase ?? 'OUTREACH',
    params.event_type,
    params.lane ?? 'COLD',
    params.agent_number ?? 'SA-001',
    params.step_number ?? 0,
    params.step_name ?? 'signal',
    params.payload ?? null,
    `${new Date().toISOString()}.${Math.random().toString(36).slice(2, 6)}`,
  ).run();
}

/** Log an error to lcs_err0 (the drain) */
export async function logError(
  d1: D1Database,
  params: {
    sovereign_company_id?: string;
    communication_id?: string;
    message_run_id?: string;
    stage: string;
    error_type: string;
    error_message: string;
  },
): Promise<void> {
  await d1.prepare(`
    INSERT INTO lcs_err0 (error_id, message_run_id, communication_id, sovereign_company_id, failure_type, failure_message, lifecycle_phase, created_at)
    VALUES (?, ?, ?, ?, ?, ?, ?, datetime('now'))
  `).bind(
    mintId('ERR'),
    params.message_run_id ?? 'NONE',
    params.communication_id ?? null,
    params.sovereign_company_id ?? null,
    params.error_type,
    `[${params.stage}] ${params.error_message}`,
    'OUTREACH',
  ).run();
}

/** Check suppression list */
export async function isSuppressed(
  d1: D1Database,
  entityType: string,
  entityValue: string,
): Promise<boolean> {
  const row = await d1.prepare(
    'SELECT 1 FROM lcs_suppression WHERE entity_type = ? AND entity_value = ?'
  ).bind(entityType, entityValue).first();
  return row !== null;
}

/** Add to suppression list */
export async function suppress(
  d1: D1Database,
  params: {
    sovereign_company_id?: string;
    entity_type: string;
    entity_value: string;
    reason: string;
  },
): Promise<void> {
  await d1.prepare(`
    INSERT OR IGNORE INTO lcs_suppression (suppression_id, sovereign_company_id, entity_type, entity_value, reason)
    VALUES (?, ?, ?, ?, ?)
  `).bind(
    mintId('SUP'),
    params.sovereign_company_id ?? null,
    params.entity_type,
    params.entity_value,
    params.reason,
  ).run();
}
