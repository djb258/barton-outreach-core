// ═══════════════════════════════════════════════════════════════
// LCS Hub — Bounce Monitor (BAR-417)
// ═══════════════════════════════════════════════════════════════
// Single source of truth for rolling-24h bounce rate.
// Used by /fire-batch auto-halt and /bounce-check endpoint.
//
// Conservative: if it can't read the table, it returns 0 (don't
// false-halt). Actual domain pausing happens in scheduled() via
// the existing lcs_domain_rotation logic.
// ═══════════════════════════════════════════════════════════════

import type { Env } from './types';

export interface BounceStats {
  rolling_24h_bounce_rate: number;
  bounced: number;
  delivered: number;
  sent: number;
  total_attempted: number;
  per_domain: DomainBounceStats[];
  is_healthy: boolean;
  threshold: number;
}

export interface DomainBounceStats {
  domain: string;
  sent_today: number;
  bounce_count_24h: number;
  bounce_rate: number;
  is_paused: number;
  daily_cap: number;
}

/** Rolling 24h bounce rate threshold — above this, halt the fire-batch. */
export const BOUNCE_HALT_THRESHOLD = 0.02; // 2%

/**
 * Compute rolling 24h bounce rate from lcs_mid_sequence_state.
 * Reads rows where attempted_at (or created_at) is within the last 24h.
 * bounce_rate = BOUNCED / (BOUNCED + DELIVERED + SENT)
 */
export async function getRolling24hBounceRate(env: Env): Promise<BounceStats> {
  try {
    const rows = await env.D1.prepare(`
      SELECT delivery_status, COUNT(*) as cnt
      FROM lcs_mid_sequence_state
      WHERE (
        attempted_at >= datetime('now', '-24 hours')
        OR (attempted_at IS NULL AND created_at >= datetime('now', '-24 hours'))
      )
      GROUP BY delivery_status
    `).all<{ delivery_status: string; cnt: number }>();

    let bounced = 0;
    let delivered = 0;
    let sent = 0;

    for (const row of rows.results ?? []) {
      const s = (row.delivery_status ?? '').toUpperCase();
      if (s === 'BOUNCED' || s === 'SUPPRESSED') bounced += row.cnt;
      else if (s === 'DELIVERED' || s === 'OPENED' || s === 'CLICKED' || s === 'REPLIED') delivered += row.cnt;
      else if (s === 'SENT') sent += row.cnt;
    }

    const total = bounced + delivered + sent;
    const bounceRate = total > 0 ? bounced / total : 0;

    // Per-domain breakdown from lcs_domain_rotation
    const domainRows = await env.D1.prepare(`
      SELECT domain, sent_today, bounce_count_24h, is_paused, daily_cap
      FROM lcs_domain_rotation
      ORDER BY domain
    `).all<DomainBounceStats>();

    const perDomain = (domainRows.results ?? []).map((d) => ({
      ...d,
      bounce_rate: d.sent_today > 0 ? d.bounce_count_24h / d.sent_today : 0,
    }));

    return {
      rolling_24h_bounce_rate: bounceRate,
      bounced,
      delivered,
      sent,
      total_attempted: total,
      per_domain: perDomain,
      is_healthy: bounceRate <= BOUNCE_HALT_THRESHOLD,
      threshold: BOUNCE_HALT_THRESHOLD,
    };
  } catch (err) {
    // Conservative: unknown state = treat as healthy (don't false-halt)
    console.error('[bounce-monitor] Failed to read bounce stats:', err instanceof Error ? err.message : err);
    return {
      rolling_24h_bounce_rate: 0,
      bounced: 0,
      delivered: 0,
      sent: 0,
      total_attempted: 0,
      per_domain: [],
      is_healthy: true,
      threshold: BOUNCE_HALT_THRESHOLD,
    };
  }
}

/**
 * Auto-pause any domain whose per-domain bounce rate exceeds the threshold.
 * Returns list of domains that were paused.
 * Called optionally from /bounce-check and from scheduled() (TODO below).
 *
 * TODO: wire into scheduled() — add a branch at the top of scheduled()
 * that calls autoPauseBadDomains(env) before the existing domain warmup logic.
 * That's a separate gated step in the cron ladder; not tonight.
 */
export async function autoPauseBadDomains(env: Env): Promise<string[]> {
  const stats = await getRolling24hBounceRate(env);
  const paused: string[] = [];

  for (const d of stats.per_domain) {
    if (!d.is_paused && d.sent_today > 0 && d.bounce_rate > BOUNCE_HALT_THRESHOLD) {
      await env.D1.prepare(
        "UPDATE lcs_domain_rotation SET is_paused = 1, pause_reason = 'bounce_threshold_exceeded_bar417', updated_at = datetime('now') WHERE domain = ?"
      ).bind(d.domain).run();
      paused.push(d.domain);
      console.log(`[bounce-monitor] AUTO-PAUSED domain ${d.domain} — bounce rate ${(d.bounce_rate * 100).toFixed(1)}%`);
    }
  }

  return paused;
}
