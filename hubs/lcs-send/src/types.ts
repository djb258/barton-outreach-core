// ═══════════════════════════════════════════════════════════════
// LCS Hub — Type Definitions
// ═══════════════════════════════════════════════════════════════
// Standard interfaces for the hub-spoke architecture.
// Spokes IN must emit Signal. Spokes OUT accept MessagePackage.
// Hub processes everything in between.
// ═══════════════════════════════════════════════════════════════

// ── Environment ─────────────────────────────────────────────

export interface Env {
  D1: D1Database;           // Spine — LCS tables (event, err0, signal_queue, cid, sid, mid, suppression)
  D1_OUTREACH: D1Database;  // Outreach — company_target, DOL, people, blog
  D1_GLOBAL: D1Database;    // Global — IMO-Creator shared reference tables (ZIP codes, geo)
  HD_NEON: Hyperdrive;      // Neon vault — SEED ONLY (never during pipeline ops)
  LCS_QUEUE: Queue<PipelineJob>;
  // Neon vault
  NEON_URL: string;
  // LBB (Library Barton Brain — unified knowledge store, replaces svg-brain + imo-brain)
  LBB_URL: string;
  LBB_API_KEY: string;
  // Composio (all integrations)
  COMPOSIO_API_KEY: string;
  COMPOSIO_BASE_URL: string;
  // Mailgun
  MAILGUN_API_KEY: string;
  MAILGUN_DOMAIN: string;
  // HeyReach
  HEYREACH_API_KEY: string;
}

// ── Spoke IN: Standard Signal Format ────────────────────────
// Every dumb worker emits signals in this format.
// Hub doesn't care which worker produced it.

export type WorkerSource = 'DOL' | 'PEOPLE' | 'BLOG' | 'TALENT_FLOW';

export interface Signal {
  signal_id: string;
  sovereign_company_id: string;
  worker: WorkerSource;
  signal_type: string;
  magnitude: number | null;
  expires_at: string | null;
  raw_payload: Record<string, unknown>;
}

// ── CID: Compiled Intelligence Dossier ──────────────────────

export interface CidLayers {
  financial: Record<string, unknown> | null;
  personnel: Record<string, unknown> | null;
  behavioral: Record<string, unknown> | null;
  movement: Record<string, unknown> | null;
  engagement: Record<string, unknown> | null;
}

export interface GateResult {
  gate: number;
  name: string;
  passed: boolean;
  reason: string;
}

export interface CompiledCid {
  cid_id: string;
  sovereign_company_id: string;
  assigned_agent: string | null;
  signal_ids: string[];
  layers: CidLayers;
  gate_results: GateResult[];
  status: 'compiled' | 'promoted' | 'failed' | 'blocked';
}

// ── SID: Campaign ───────────────────────────────────────────

export type CampaignType = 'monthly_touch' | 'renewal' | 'exec_change' | 'activity' | 'priority';
export type AudiencePath = 'cfo_ceo_money' | 'hr_workload';
export type TargetSlot = 'CEO' | 'CFO' | 'HR';

export interface SidMessage {
  sequence_num: number;
  channel: 'MG' | 'HR';
  subject: string;
  body_plain: string;
  body_html: string;
  condition: string | null;  // "if msg 1 opened but not clicked" etc.
}

export interface DesignedSid {
  sid_id: string;
  cid_id: string;
  sovereign_company_id: string;
  campaign_type: CampaignType;
  audience_path: AudiencePath;
  target_slot: TargetSlot;
  target_name: string | null;
  target_email: string | null;
  target_linkedin: string | null;
  messages: SidMessage[];
  content_sources: string[];
  monte_carlo_ref: Record<string, unknown> | null;
}

// ── MID: Delivery Record ────────────────────────────────────

export type DeliveryStatus = 'queued' | 'sent' | 'delivered' | 'opened' | 'clicked' | 'bounced' | 'failed';
export type PathType = 'WARM' | 'COLD';
export type Channel = 'MG' | 'HR';

export interface MessagePackage {
  mid_id: string;
  sid_id: string;
  cid_id: string;
  sovereign_company_id: string;
  sequence_num: number;
  channel: Channel;
  path_type: PathType;
  recipient_email: string | null;
  recipient_linkedin: string | null;
  subject: string;
  body_plain: string;
  body_html: string;
}

// ── Pipeline Job (Queue) ────────────────────────────────────

export type JobType = 'compile_cid' | 'design_sid' | 'deliver_mid' | 'process_webhook';

export interface PipelineJob {
  job_type: JobType;
  sovereign_company_id: string;
  // For compile_cid
  signal_ids?: string[];
  // For design_sid
  cid_id?: string;
  // For deliver_mid
  sid_id?: string;
  mid_id?: string;
  // For process_webhook
  webhook_source?: 'mailgun' | 'heyreach';
  webhook_payload?: Record<string, unknown>;
}

// ── Event Types ─────────────────────────────────────────────

export type EventType =
  | 'signal_received'
  | 'cid_compiled'
  | 'cid_failed'
  | 'sid_designed'
  | 'mid_queued'
  | 'mid_sent'
  | 'mid_delivered'
  | 'mid_bounced'
  | 'mid_opened'
  | 'mid_clicked'
  | 'mid_replied'
  | 'campaign_stopped'
  | 'campaign_completed'
  | 'suppressed'
  | 'strike_3';
