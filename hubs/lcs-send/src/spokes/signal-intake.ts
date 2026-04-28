// ═══════════════════════════════════════════════════════════════
// Spoke IN: Signal Intake
// ═══════════════════════════════════════════════════════════════
// Receives signals from dumb workers in standard format.
// Validates schema. Writes to signal_queue. That's it.
// Hub doesn't care which worker produced the signal.
// ═══════════════════════════════════════════════════════════════

import type { Signal } from '../types';
import { mintId, logEvent, logError } from '../utils';

/** Validate incoming signal has required fields */
function validateSignal(body: Record<string, unknown>): Record<string, unknown> | null {
  if (!body.sovereign_company_id || typeof body.sovereign_company_id !== 'string') return null;
  if (!body.signal_set_hash || typeof body.signal_set_hash !== 'string') return null;

  return {
    id: mintId('SIG'),
    sovereign_company_id: body.sovereign_company_id as string,
    signal_set_hash: body.signal_set_hash as string,
    signal_category: (body.signal_category as string) ?? 'OUTREACH',
    lifecycle_phase: (body.lifecycle_phase as string) ?? 'OUTREACH',
    preferred_channel: (body.preferred_channel as string) ?? null,
    preferred_lane: (body.preferred_lane as string) ?? null,
    agent_number: (body.agent_number as string) ?? 'SA-001',
    signal_data: body.signal_data ? JSON.stringify(body.signal_data) : '{}',
    source_hub: (body.source_hub as string) ?? 'manual',
    source_signal_id: (body.source_signal_id as string) ?? null,
    priority: typeof body.priority === 'number' ? body.priority : 5,
  };
}

/** Ingest a signal into lcs_signal_queue */
export async function ingestSignal(
  d1: D1Database,
  body: Record<string, unknown>,
): Promise<{ signal_id: string } | { error: string }> {
  const signal = validateSignal(body);
  if (!signal) {
    return { error: 'Invalid signal: requires sovereign_company_id, signal_set_hash' };
  }

  try {
    await d1.prepare(`
      INSERT INTO lcs_signal_queue (
        id, signal_set_hash, signal_category, sovereign_company_id,
        lifecycle_phase, preferred_channel, preferred_lane, agent_number,
        signal_data, source_hub, source_signal_id, status, priority, created_at
      ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'pending', ?, datetime('now'))
    `).bind(
      signal.id,
      signal.signal_set_hash,
      signal.signal_category,
      signal.sovereign_company_id,
      signal.lifecycle_phase,
      signal.preferred_channel,
      signal.preferred_lane,
      signal.agent_number,
      signal.signal_data,
      signal.source_hub,
      signal.source_signal_id,
      signal.priority,
    ).run();

    return { signal_id: signal.id as string };
  } catch (err) {
    const msg = err instanceof Error ? err.message : String(err);
    try {
      await logError(d1, {
        sovereign_company_id: signal.sovereign_company_id as string,
        stage: 'signal',
        error_type: 'ingest_failure',
        error_message: msg,
      });
    } catch { /* don't fail on error logging */ }
    return { error: msg };
  }
}

/** Batch ingest multiple signals */
export async function ingestSignalBatch(
  d1: D1Database,
  signals: Record<string, unknown>[],
): Promise<{ ingested: number; errors: number }> {
  let ingested = 0;
  let errors = 0;

  for (const body of signals) {
    const result = await ingestSignal(d1, body);
    if ('signal_id' in result) {
      ingested++;
    } else {
      errors++;
    }
  }

  return { ingested, errors };
}
