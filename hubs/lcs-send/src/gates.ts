// ═══════════════════════════════════════════════════════════════
// LCS Hub — 9-Gate Stack (The Valves)
// ═══════════════════════════════════════════════════════════════
// Gate 0: Agent assignment (100mi radius)
// Gates 1-5: Deterministic constants (geography, size, DOL)
// Gates 6-7: Signal-driven (talent flow, blog)
// Gate 8: Composite signal strength
//
// Each gate is binary: PASS or FAIL.
// All gates must PASS for a company to proceed to CID compilation.
// ═══════════════════════════════════════════════════════════════

import type { GateResult } from './types';

// Gate 0-5 data comes from Neon vault (company_target + DOL views)
export interface CompanyData {
  sovereign_company_id: string;
  company_name: string;
  state: string;
  zip: string;
  employee_count: number | null;
  assigned_agent: string | null;
  // DOL data
  has_5500_filing: boolean;
  renewal_month: number | null;
  premium_current: number | null;
  premium_prior: number | null;
  carrier_current: string | null;
  carrier_prior: string | null;
  broker_current: string | null;
  broker_prior: string | null;
  // Slots
  ceo_name: string | null;
  ceo_email: string | null;
  cfo_name: string | null;
  cfo_email: string | null;
  hr_name: string | null;
  hr_email: string | null;
}

// Signal presence for gates 6-8
export interface SignalPresence {
  has_talent_flow_signal: boolean;
  has_blog_signal: boolean;
  active_signal_count: number;
  signal_types: string[];
}

const VALID_STATES = ['PA', 'VA', 'MD', 'OH', 'WV', 'KY'];
const MIN_EMPLOYEES = 50;
const MAX_EMPLOYEES = 2000;
const RENEWAL_WINDOW_DAYS = 120;

export function runGateStack(
  company: CompanyData,
  signals: SignalPresence,
): GateResult[] {
  const results: GateResult[] = [];

  // Gate 0: Agent assignment
  results.push({
    gate: 0,
    name: 'agent_assignment',
    passed: company.assigned_agent !== null && company.assigned_agent !== '',
    reason: company.assigned_agent
      ? `Assigned to ${company.assigned_agent}`
      : 'No agent in range — not marketed to',
  });

  // Gate 1: Geography (PA/VA/MD/OH/WV/KY)
  results.push({
    gate: 1,
    name: 'geography',
    passed: VALID_STATES.includes(company.state?.toUpperCase()),
    reason: VALID_STATES.includes(company.state?.toUpperCase())
      ? `State ${company.state} is in territory`
      : `State ${company.state} is outside territory`,
  });

  // Gate 2: Size (50-2,000 employees)
  const sizeOk = company.employee_count !== null
    && company.employee_count >= MIN_EMPLOYEES
    && company.employee_count <= MAX_EMPLOYEES;
  results.push({
    gate: 2,
    name: 'size',
    passed: sizeOk,
    reason: sizeOk
      ? `${company.employee_count} employees within range`
      : `${company.employee_count ?? 'unknown'} employees outside ${MIN_EMPLOYEES}-${MAX_EMPLOYEES} range`,
  });

  // Gate 3: DOL 5500 filing exists
  results.push({
    gate: 3,
    name: 'dol_filing',
    passed: company.has_5500_filing,
    reason: company.has_5500_filing
      ? 'Form 5500 filing exists'
      : 'No Form 5500 filing found',
  });

  // Gate 4: Renewal window approaching
  const renewalApproaching = isRenewalApproaching(company.renewal_month, RENEWAL_WINDOW_DAYS);
  results.push({
    gate: 4,
    name: 'renewal_window',
    passed: renewalApproaching,
    reason: renewalApproaching
      ? `Renewal month ${company.renewal_month} within ${RENEWAL_WINDOW_DAYS}-day window`
      : `Renewal month ${company.renewal_month ?? 'unknown'} not approaching`,
  });

  // Gate 5: Premium trend — cost pressure
  const premiumUp = company.premium_current !== null
    && company.premium_prior !== null
    && company.premium_current > company.premium_prior;
  results.push({
    gate: 5,
    name: 'premium_trend',
    passed: premiumUp,
    reason: premiumUp
      ? `Premium increased: ${company.premium_prior} → ${company.premium_current}`
      : 'No premium increase detected',
  });

  // Gate 6: Talent Flow signal
  results.push({
    gate: 6,
    name: 'talent_flow',
    passed: signals.has_talent_flow_signal,
    reason: signals.has_talent_flow_signal
      ? 'Talent Flow signal active'
      : 'No Talent Flow signal',
  });

  // Gate 7: Blog signal
  results.push({
    gate: 7,
    name: 'blog_signal',
    passed: signals.has_blog_signal,
    reason: signals.has_blog_signal
      ? 'Blog signal active'
      : 'No Blog signal',
  });

  // Gate 8: Composite signal strength
  // At least gate 0 + one of gates 3-7 must pass (beyond geography+size)
  const substantiveGates = results.filter(r => r.gate >= 3 && r.passed).length;
  results.push({
    gate: 8,
    name: 'composite_signal',
    passed: substantiveGates >= 1,
    reason: `${substantiveGates} substantive gates passed (need >= 1)`,
  });

  return results;
}

/** Check if all gates passed */
export function allGatesPassed(results: GateResult[]): boolean {
  // Gates 0-3 are hard stops. Gates 4-8 are signal boosters.
  // Must pass: gate 0 (agent), gate 1 (geo), gate 2 (size), gate 3 (DOL)
  // Plus gate 8 (at least one substantive signal)
  const hardGates = [0, 1, 2, 3, 8];
  return hardGates.every(g => {
    const result = results.find(r => r.gate === g);
    return result?.passed === true;
  });
}

function isRenewalApproaching(renewalMonth: number | null, windowDays: number): boolean {
  if (renewalMonth === null) return false;
  const now = new Date();
  const currentYear = now.getFullYear();
  // Build renewal date for this year
  const renewalDate = new Date(currentYear, renewalMonth - 1, 1);
  // If renewal already passed this year, check next year
  if (renewalDate < now) {
    renewalDate.setFullYear(currentYear + 1);
  }
  const daysUntilRenewal = Math.floor(
    (renewalDate.getTime() - now.getTime()) / (1000 * 60 * 60 * 24)
  );
  return daysUntilRenewal <= windowDays && daysUntilRenewal >= 0;
}
