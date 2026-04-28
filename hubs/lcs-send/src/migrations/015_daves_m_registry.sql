-- Dave's M Registry — every constant Dave owns, AI-ready
-- Follows MAP_KEY.md universal constant record format
-- This table IS the inventory. The engine queries it for gap analysis.
-- Migration: 015
-- Created: 2026-04-16

CREATE TABLE IF NOT EXISTS lcs_m_registry (
  id                TEXT PRIMARY KEY,        -- unique ID: M-{category}-{seq} e.g. M-INFRA-001
  name              TEXT NOT NULL,           -- human-readable name
  abbreviation      TEXT DEFAULT NULL,       -- shorthand (CID, SID, MID, EIN, etc.)
  description       TEXT NOT NULL,           -- plain-language: what this IS and what it does. AI reads this.
  category          TEXT NOT NULL,           -- targeting, infrastructure, data, value_prop, identity, process, voice, timing, trigger, intelligence
  primitive         TEXT NOT NULL,           -- Thing, Flow, or Change
  ctb_placement     TEXT NOT NULL DEFAULT 'Leaf',  -- Trunk, Branch, or Leaf
  imo_topology      TEXT DEFAULT NULL,       -- Input, Middle, or Output
  format            TEXT DEFAULT NULL,       -- what it structurally contains (data type, schema, etc.)
  current_value     TEXT DEFAULT NULL,       -- the actual value if applicable (e.g., "8" for states, "14" for domains)
  source            TEXT DEFAULT NULL,       -- where this lives (D1 table, worker, config, human knowledge)
  source_detail     TEXT DEFAULT NULL,       -- specific table.column or file path
  status            TEXT NOT NULL DEFAULT 'active',  -- active, deprecated, planned
  locked            INTEGER NOT NULL DEFAULT 1,      -- 1 = constant (Dave declared), 0 = variable (can change)
  last_verified     TEXT DEFAULT NULL,       -- when was this last confirmed accurate
  created_at        TEXT NOT NULL DEFAULT (datetime('now')),
  updated_at        TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_m_category ON lcs_m_registry(category);
CREATE INDEX IF NOT EXISTS idx_m_primitive ON lcs_m_registry(primitive);
CREATE INDEX IF NOT EXISTS idx_m_status ON lcs_m_registry(status);

-- ============================================================
-- SEED: ALL OF DAVE'S CONSTANTS
-- 35 records across 9 categories
-- ============================================================

-- -------------------------------------------------------
-- TARGETING (5 constants)
-- -------------------------------------------------------

INSERT OR IGNORE INTO lcs_m_registry (id, name, abbreviation, description, category, primitive, ctb_placement, imo_topology, format, current_value, source, source_detail, status, locked, last_verified) VALUES
(
  'M-TGT-001',
  '8 States Targeting',
  NULL,
  'SVG Agency operates in exactly 8 US states. This is a geographic boundary — the company list, contacts, and outreach are scoped to companies headquartered or operating in these 8 states only. Not a preference — a hard business constraint that determines the total addressable market.',
  'targeting',
  'Thing',
  'Trunk',
  'Input',
  'enum(8 states)',
  '8 states',
  'human-declared constraint',
  'business operating territory',
  'active',
  1,
  '2026-04-16'
);

INSERT OR IGNORE INTO lcs_m_registry (id, name, abbreviation, description, category, primitive, ctb_placement, imo_topology, format, current_value, source, source_detail, status, locked, last_verified) VALUES
(
  'M-TGT-002',
  '50-5000 Employee Band',
  NULL,
  'Target companies have between 50 and 5,000 employees. Below 50, benefits plans are too small to generate meaningful savings. Above 5,000, they typically have in-house benefits teams and self-insured plans that do not match SVG model. This employee count range defines which companies from the 5500 DOL filings are in scope.',
  'targeting',
  'Thing',
  'Trunk',
  'Input',
  'integer range [50, 5000]',
  '50-5000',
  'human-declared constraint',
  'ICP employee band',
  'active',
  1,
  '2026-04-16'
);

INSERT OR IGNORE INTO lcs_m_registry (id, name, abbreviation, description, category, primitive, ctb_placement, imo_topology, format, current_value, source, source_detail, status, locked, last_verified) VALUES
(
  'M-TGT-003',
  '32K Companies in D1',
  NULL,
  '32,702 companies stored in Cloudflare D1 database (svg-d1-spine). Each company record comes from DOL Form 5500 filings — government-mandated annual benefit plan disclosures. Every company that files a 5500 with 50-5000 employees in the 8 target states is in this list. The list is static (refreshed annually when DOL publishes new filings) and serves as the total addressable market.',
  'targeting',
  'Thing',
  'Trunk',
  'Input',
  'integer count',
  '32702',
  'D1: svg-d1-outreach-ops',
  'outreach_company_target',
  'active',
  1,
  '2026-04-16'
);

INSERT OR IGNORE INTO lcs_m_registry (id, name, abbreviation, description, category, primitive, ctb_placement, imo_topology, format, current_value, source, source_detail, status, locked, last_verified) VALUES
(
  'M-TGT-004',
  '57K Contacts in D1',
  NULL,
  '57,000+ individual contacts (CEOs, CFOs, HR directors) associated with the 32K companies. Contacts are discovered via Process 201 (email discovery) and Process 202 (LinkedIn discovery). Stored in D1 with email addresses, LinkedIn URLs, and job titles. Each contact is linked to a company via EIN.',
  'targeting',
  'Thing',
  'Trunk',
  'Input',
  'integer count',
  '58890',
  'D1: svg-d1-outreach-ops',
  'people_people_master',
  'active',
  1,
  '2026-04-16'
);

INSERT OR IGNORE INTO lcs_m_registry (id, name, abbreviation, description, category, primitive, ctb_placement, imo_topology, format, current_value, source, source_detail, status, locked, last_verified) VALUES
(
  'M-TGT-005',
  'CEO CFO HR Target Roles',
  NULL,
  'The three decision-maker roles targeted in outreach. CEO and CFO are reached with numbers-based messaging (ROI, cost savings, data). HR directors are reached with relief-based messaging (less burden, easier administration, fewer silos). These three roles are the ONLY roles that can authorize a broker-of-record change for employee benefits. No one else in the organization has that authority.',
  'targeting',
  'Thing',
  'Trunk',
  'Input',
  'enum(CEO, CFO, HR)',
  '3 roles',
  'human-declared constraint',
  'decision-maker roles for benefits BOR change',
  'active',
  1,
  '2026-04-16'
);

-- -------------------------------------------------------
-- INFRASTRUCTURE (14 constants)
-- -------------------------------------------------------

INSERT OR IGNORE INTO lcs_m_registry (id, name, abbreviation, description, category, primitive, ctb_placement, imo_topology, format, current_value, source, source_detail, status, locked, last_verified) VALUES
(
  'M-INFRA-001',
  '14 Mailgun Sending Domains',
  NULL,
  '14 verified email sending domains configured in Mailgun, currently in warmup (week 1, 20 emails/domain/day = 280 total daily capacity). Each domain has proper DNS (SPF, DKIM, DMARC). Multiple domains provide sender rotation to protect deliverability — if one domain gets flagged, the others continue operating. These are the physical sending infrastructure for email outreach.',
  'infrastructure',
  'Thing',
  'Trunk',
  'Middle',
  'array(14 FQDNs)',
  '14',
  'D1: svg-d1-spine',
  'lcs_domain_rotation',
  'active',
  1,
  '2026-04-16'
);

INSERT OR IGNORE INTO lcs_m_registry (id, name, abbreviation, description, category, primitive, ctb_placement, imo_topology, format, current_value, source, source_detail, status, locked, last_verified) VALUES
(
  'M-INFRA-002',
  'SVG Agency Website',
  NULL,
  'The primary SVG Agency website at svg.agency with 73 published pages. Serves as the digital credibility anchor — when a prospect receives an email or LinkedIn message, this is where they go to verify legitimacy. Contains service descriptions, methodology explanation, case studies, and contact forms. Acts as the inbound capture mechanism for outbound outreach.',
  'infrastructure',
  'Thing',
  'Branch',
  'Output',
  'URL + integer page count',
  '73 pages',
  'human-declared constraint',
  'svg.agency website',
  'active',
  1,
  '2026-04-16'
);

INSERT OR IGNORE INTO lcs_m_registry (id, name, abbreviation, description, category, primitive, ctb_placement, imo_topology, format, current_value, source, source_detail, status, locked, last_verified) VALUES
(
  'M-INFRA-003',
  'Dave Barton LinkedIn Profile',
  NULL,
  'Dave Barton personal LinkedIn profile — the human identity behind all LinkedIn outreach. LinkedIn outreach comes from this profile, not a company page. Personal profiles get 5-10x higher engagement than company pages for B2B cold outreach. The profile establishes Dave as the insurance informatics pioneer and is the sender identity for all LinkedIn connection requests and messages.',
  'infrastructure',
  'Thing',
  'Branch',
  'Input',
  'LinkedIn profile URL',
  NULL,
  'HeyReach',
  'LinkedIn sender identity',
  'active',
  1,
  '2026-04-16'
);

INSERT OR IGNORE INTO lcs_m_registry (id, name, abbreviation, description, category, primitive, ctb_placement, imo_topology, format, current_value, source, source_detail, status, locked, last_verified) VALUES
(
  'M-INFRA-004',
  'Million Verifier Email Gate',
  NULL,
  'Million Verifier is the email verification service that gates all outbound email. Every discovered email address must pass verification before entering the send pipeline. Unverified or invalid emails are blocked from sending. This protects the 14 Mailgun domains from bounce-rate damage — sending to invalid addresses destroys domain reputation and deliverability. The gate is binary: verified = proceed to send queue, unverified = blocked.',
  'infrastructure',
  'Thing',
  'Branch',
  'Middle',
  'binary gate (verified | blocked)',
  NULL,
  'Million Verifier API',
  'email quality gate before lcs_signal_queue',
  'active',
  1,
  '2026-04-16'
);

INSERT OR IGNORE INTO lcs_m_registry (id, name, abbreviation, description, category, primitive, ctb_placement, imo_topology, format, current_value, source, source_detail, status, locked, last_verified) VALUES
(
  'M-INFRA-005',
  'LCS Pipeline Campaign Compiler',
  'CID/SID/MID',
  'The LCS (Lead Campaign System) compiler built in compiler-v2.ts. Assembles three components into a sendable campaign unit: CID (Company ID) = the company footprint record compiled from 5500 DOL filing data, including employee count, plan types, carrier names, premium amounts, renewal date, all Schedule A data. SID (Sender ID) = which of the 14 Mailgun domains to send from plus which sender persona/signature to use. MID (Message ID) = which message template to use, matched to the target role (CEO gets numbers, HR gets relief). CID+SID+MID = one complete, personalized, ready-to-send outreach unit.',
  'infrastructure',
  'Thing',
  'Trunk',
  'Middle',
  'pipeline(CID, SID, MID)',
  NULL,
  'CF Worker: lcs-hub',
  'workers/lcs-hub/src/compiler-v2.ts',
  'active',
  1,
  '2026-04-16'
);

INSERT OR IGNORE INTO lcs_m_registry (id, name, abbreviation, description, category, primitive, ctb_placement, imo_topology, format, current_value, source, source_detail, status, locked, last_verified) VALUES
(
  'M-INFRA-006',
  'Process 201 Email Discovery',
  'P201',
  'Process 201 discovers email addresses for contacts at the 32K target companies. Takes a company name + domain as input, discovers individual email addresses for CEO, CFO, and HR contacts using multiple data sources (Apollo, Hunter, LinkedIn scraping, pattern matching). Output is verified email addresses linked to company records via EIN. Feeds into the Million Verifier gate before entering the send pipeline.',
  'infrastructure',
  'Flow',
  'Branch',
  'Input',
  'process(company_name, domain) -> email[]',
  NULL,
  'factory/processes',
  'factory/processes/201-email-discovery',
  'active',
  1,
  '2026-04-16'
);

INSERT OR IGNORE INTO lcs_m_registry (id, name, abbreviation, description, category, primitive, ctb_placement, imo_topology, format, current_value, source, source_detail, status, locked, last_verified) VALUES
(
  'M-INFRA-007',
  'Process 202 LinkedIn Discovery',
  'P202',
  'Process 202 discovers LinkedIn profile URLs for contacts at the 32K target companies. Takes company name + target role as input, finds the actual LinkedIn profiles for CEO, CFO, and HR contacts. Output is LinkedIn URLs linked to company records via EIN. These profiles become targets for LinkedIn connection requests and direct messaging from Dave profile.',
  'infrastructure',
  'Flow',
  'Branch',
  'Input',
  'process(company_name, role) -> linkedin_url[]',
  NULL,
  'factory/processes',
  'factory/processes/202-linkedin-discovery',
  'active',
  1,
  '2026-04-16'
);

INSERT OR IGNORE INTO lcs_m_registry (id, name, abbreviation, description, category, primitive, ctb_placement, imo_topology, format, current_value, source, source_detail, status, locked, last_verified) VALUES
(
  'M-INFRA-008',
  'Engagement Feedback Loop',
  NULL,
  'The closed-loop system that receives engagement events from Mailgun and HeyReach webhooks (delivered, opened, clicked, bounced, unsubscribed) and feeds them back into the signal queue as ENGAGEMENT_RESPONSE signals. These signals trigger the rules engine which decides the next action: send a follow-up, escalate to LinkedIn, wait, or stop. Without this loop, the system sends blind and cannot adapt. Built in BAR-303.',
  'infrastructure',
  'Flow',
  'Trunk',
  'Middle',
  'webhook -> signal_queue -> rules_engine -> next_action',
  NULL,
  'D1: svg-d1-spine',
  'lcs_engagement_rules + compileEngagementResponse in lcs-hub',
  'active',
  1,
  '2026-04-16'
);

INSERT OR IGNORE INTO lcs_m_registry (id, name, abbreviation, description, category, primitive, ctb_placement, imo_topology, format, current_value, source, source_detail, status, locked, last_verified) VALUES
(
  'M-INFRA-009',
  'Multi-Touch Sequence Engine',
  NULL,
  'The multi-step outreach sequence system that defines a campaign as a series of timed messages (e.g., email day 0, follow-up day 2, escalation day 5). Tracks each contact progress through the sequence — which step they are on, when the next step should fire, whether conditions are met (e.g., only send step 3 if step 2 was not opened). Built in BAR-304. Enables structured drip campaigns instead of single-shot blasts.',
  'infrastructure',
  'Flow',
  'Branch',
  'Middle',
  'sequence_def(steps) + contact_sequence_state(progress)',
  NULL,
  'D1: svg-d1-spine',
  'lcs_sequence_def + lcs_contact_sequence_state',
  'active',
  1,
  '2026-04-16'
);

INSERT OR IGNORE INTO lcs_m_registry (id, name, abbreviation, description, category, primitive, ctb_placement, imo_topology, format, current_value, source, source_detail, status, locked, last_verified) VALUES
(
  'M-INFRA-010',
  'Engagement Scoring System',
  NULL,
  'Weighted scoring system that assigns a numeric engagement score to each contact based on their interactions. Scoring weights: delivered=1, opened=5, clicked=15. A composite score above 25 marks a contact as a hot lead requiring immediate attention. The score persists and accumulates across all outreach interactions — a contact that opens 3 emails scores 15 before any click. Built in BAR-305.',
  'infrastructure',
  'Thing',
  'Branch',
  'Output',
  'integer score (0+), hot_lead_threshold=25',
  NULL,
  'D1: svg-d1-spine',
  'lcs_contact_engagement_score',
  'active',
  1,
  '2026-04-16'
);

INSERT OR IGNORE INTO lcs_m_registry (id, name, abbreviation, description, category, primitive, ctb_placement, imo_topology, format, current_value, source, source_detail, status, locked, last_verified) VALUES
(
  'M-INFRA-011',
  'Cross-Channel Orchestration',
  NULL,
  'System that tracks and manages which channel (email or LinkedIn) is active for each contact, and handles the escalation when email is exhausted. After 7 days of no email response, the system automatically switches the contact to LinkedIn outreach. Each contact has a tracked channel state: which is primary, which is exhausted, and when the switch happened. Built in BAR-307.',
  'infrastructure',
  'Flow',
  'Branch',
  'Middle',
  'enum(email_active, linkedin_active, exhausted) per contact',
  NULL,
  'D1: svg-d1-spine',
  'lcs_contact_channel_state',
  'active',
  1,
  '2026-04-16'
);

INSERT OR IGNORE INTO lcs_m_registry (id, name, abbreviation, description, category, primitive, ctb_placement, imo_topology, format, current_value, source, source_detail, status, locked, last_verified) VALUES
(
  'M-INFRA-012',
  'Campaign Scheduler and No-Response Detector',
  NULL,
  'Two cron-triggered systems built in BAR-308. The campaign scheduler fires periodically and checks lcs_contact_sequence_state for contacts whose next_step_after timestamp has passed — these get a new signal inserted to send the next sequence step. The no-response detector checks lcs_mid_sequence_state for MIDs that were sent but received no engagement after 3 or 7 days, then inserts no_response signals that trigger the rules engine. Together they drive the automatic progression of every outreach campaign.',
  'infrastructure',
  'Flow',
  'Branch',
  'Middle',
  'cron(schedule) -> signal_queue inserts',
  NULL,
  'CF Worker: lcs-hub',
  'cron triggers in wrangler.toml + lcs-hub scheduler handlers',
  'active',
  1,
  '2026-04-16'
);

INSERT OR IGNORE INTO lcs_m_registry (id, name, abbreviation, description, category, primitive, ctb_placement, imo_topology, format, current_value, source, source_detail, status, locked, last_verified) VALUES
(
  'M-INFRA-013',
  'Calendar Booking Link',
  NULL,
  'Google Calendar appointment booking link that Dave sends to hot leads and meeting-ready prospects. This is the conversion point for outreach — all outreach activity is designed to produce a click on this link. Without a booking mechanism, there is no way to convert engagement into meetings. The link must appear in the right messages at the right stage of the sequence.',
  'infrastructure',
  'Thing',
  'Leaf',
  'Output',
  'URL (Google Calendar appointment scheduler)',
  NULL,
  'Google Calendar',
  'appointment scheduling URL',
  'active',
  1,
  '2026-04-16'
);

INSERT OR IGNORE INTO lcs_m_registry (id, name, abbreviation, description, category, primitive, ctb_placement, imo_topology, format, current_value, source, source_detail, status, locked, last_verified) VALUES
(
  'M-INFRA-014',
  'Reply Inbox',
  NULL,
  'Dedicated email inbox that receives replies from email outreach campaigns. When a prospect replies to a campaign email, the reply lands here. Without a monitored reply inbox, inbound responses are lost and opportunities are missed. This is the human hand-off point — when a reply comes in, Dave sees it and takes over from the automated system.',
  'infrastructure',
  'Thing',
  'Leaf',
  'Output',
  'email inbox',
  NULL,
  'human-declared constraint',
  'dedicated inbox for email replies from outreach',
  'active',
  1,
  '2026-04-16'
);

-- -------------------------------------------------------
-- DATA (4 constants)
-- -------------------------------------------------------

INSERT OR IGNORE INTO lcs_m_registry (id, name, abbreviation, description, category, primitive, ctb_placement, imo_topology, format, current_value, source, source_detail, status, locked, last_verified) VALUES
(
  'M-DATA-001',
  '14K DOL 5500 Filings',
  '5500',
  '14,000+ Department of Labor Form 5500 annual filings stored in the system. Every company with an ERISA-qualified benefits plan must file a 5500 annually with the DOL — it is federal law. The filing contains: number of participants, total plan assets, total contributions, carrier names (Schedule A), broker names (Schedule A), plan types, and the plan year end date (renewal date). This is public data — anyone can access it. Dave is the only one systematically mining it for outreach intelligence. Each 5500 is a complete financial X-ray of a company benefits program.',
  'data',
  'Thing',
  'Trunk',
  'Input',
  'structured DOL filing records',
  '14000+',
  'D1: svg-d1-outreach-ops',
  'dol_form_5500',
  'active',
  1,
  '2026-04-16'
);

INSERT OR IGNORE INTO lcs_m_registry (id, name, abbreviation, description, category, primitive, ctb_placement, imo_topology, format, current_value, source, source_detail, status, locked, last_verified) VALUES
(
  'M-DATA-002',
  '9.5K Schedule A Broker Carrier Data',
  'Schedule A',
  '9,500+ Schedule A attachments from the 5500 filings. Schedule A is the section that lists every insurance carrier and every broker/agent receiving commissions from the plan. This is the competitive intelligence goldmine — it tells Dave exactly who the current broker is, which carriers are on the plan, and how much commission is being paid. Year-over-year comparison of Schedule A data reveals broker-of-record changes (a company switched brokers) which is a trigger signal for outreach timing.',
  'data',
  'Thing',
  'Branch',
  'Input',
  'structured Schedule A attachment records',
  '9500+',
  'D1: svg-d1-outreach-ops',
  'dol_schedule_a',
  'active',
  1,
  '2026-04-16'
);

INSERT OR IGNORE INTO lcs_m_registry (id, name, abbreviation, description, category, primitive, ctb_placement, imo_topology, format, current_value, source, source_detail, status, locked, last_verified) VALUES
(
  'M-DATA-003',
  'EIN as Join Key',
  'EIN',
  'EIN (Employer Identification Number) is the federal tax ID assigned to every business entity. It serves as the universal join key across ALL data sources in the system: 5500 filings use EIN, company records use EIN, contact records link to companies via EIN, enrichment data links via EIN. If a company record has an EIN match to a 5500 filing, that is P=1 (full data available — plan, carrier, broker, renewal date, everything). If no EIN match, P=0 (company name but no 5500 intelligence).',
  'data',
  'Thing',
  'Trunk',
  'Middle',
  'string(EIN format: XX-XXXXXXX)',
  NULL,
  'D1: multiple tables',
  'universal join key across dol_form_5500, outreach_company_target, people_people_master',
  'active',
  1,
  '2026-04-16'
);

INSERT OR IGNORE INTO lcs_m_registry (id, name, abbreviation, description, category, primitive, ctb_placement, imo_topology, format, current_value, source, source_detail, status, locked, last_verified) VALUES
(
  'M-DATA-004',
  'Slot Workbench 98K Enrichment Records',
  NULL,
  '98,000+ enrichment records in the slot workbench — a D1 database table that tracks the enrichment status of every company-contact pair. Each slot is a combination of company + contact + data source, tracking what data has been collected (email found? LinkedIn found? 5500 matched? Schedule A parsed?). The workbench is the operational dashboard for the enrichment pipeline — it shows exactly which companies are fully enriched (ready for outreach) vs which have gaps.',
  'data',
  'Thing',
  'Branch',
  'Middle',
  'enrichment tracking records',
  '98106',
  'D1: svg-d1-outreach-ops',
  'people_company_slot',
  'active',
  1,
  '2026-04-16'
);

-- -------------------------------------------------------
-- VALUE PROP (4 constants)
-- -------------------------------------------------------

INSERT OR IGNORE INTO lcs_m_registry (id, name, abbreviation, description, category, primitive, ctb_placement, imo_topology, format, current_value, source, source_detail, status, locked, last_verified) VALUES
(
  'M-VAL-001',
  'Insurance Informatics Methodology',
  NULL,
  'Dave Barton proprietary methodology that applies data science and systems engineering to insurance benefits administration. He is the only person in the US doing this — verified by industry research. This is the core value proposition differentiator. Not "we save you money on insurance" (commodity claim), but "we engineered a system that uses your own DOL filing data to mathematically identify waste in your benefits program." No competitor can make this claim.',
  'value_prop',
  'Thing',
  'Trunk',
  'Output',
  'unique market position (no competing claims)',
  'only firm in the country',
  'human-declared constraint',
  'unique market position verified by industry research',
  'active',
  1,
  '2026-04-16'
);

INSERT OR IGNORE INTO lcs_m_registry (id, name, abbreviation, description, category, primitive, ctb_placement, imo_topology, format, current_value, source, source_detail, status, locked, last_verified) VALUES
(
  'M-VAL-002',
  '20-55% Cost Savings Range',
  NULL,
  'Documented savings range achieved for clients through insurance informatics analysis. 20% is the floor (conservative, nearly always achievable). 55% is the ceiling (maximum documented case). This range is the primary hook for CEO/CFO messaging — it is quantifiable, provable from 5500 data, and significantly above the 3-7% that traditional brokers typically deliver through renewal negotiation alone.',
  'value_prop',
  'Thing',
  'Branch',
  'Output',
  'percentage range [20%, 55%]',
  '20-55%',
  'human-declared constraint',
  'proven savings range from client outcomes',
  'active',
  1,
  '2026-04-16'
);

INSERT OR IGNORE INTO lcs_m_registry (id, name, abbreviation, description, category, primitive, ctb_placement, imo_topology, format, current_value, source, source_detail, status, locked, last_verified) VALUES
(
  'M-VAL-003',
  'Full System Automation',
  NULL,
  'The entire SVG Agency operational stack is automated end-to-end: data ingestion (5500 filings), enrichment (company and contact discovery), analysis (benefits plan evaluation), outreach (email campaigns via LCS compiler), and tracking (engagement monitoring). No manual data entry, no spreadsheet handoffs, no human-in-the-loop for routine operations. The automation IS the product — it is what enables one person to service a pipeline that would normally require a team of 10+.',
  'value_prop',
  'Thing',
  'Branch',
  'Output',
  'boolean (fully automated end-to-end)',
  'fully automated',
  'human-declared constraint',
  'operational architecture value proposition',
  'active',
  1,
  '2026-04-16'
);

INSERT OR IGNORE INTO lcs_m_registry (id, name, abbreviation, description, category, primitive, ctb_placement, imo_topology, format, current_value, source, source_detail, status, locked, last_verified) VALUES
(
  'M-VAL-004',
  'No Software Silos — All Systems Integrated',
  NULL,
  'Every system in the SVG stack talks to every other system through APIs and shared databases. CRM data connects to 5500 data connects to email data connects to enrichment data. Zero manual transfers between systems. This is a direct contrast to the insurance industry norm where agents use 5-10 disconnected software tools and manually copy-paste between them. The integration enables the informatics methodology — you cannot do data-driven analysis if your data is trapped in silos.',
  'value_prop',
  'Thing',
  'Branch',
  'Output',
  'boolean (no silo architecture)',
  'zero silos',
  'human-declared constraint',
  'system integration architecture value proposition',
  'active',
  1,
  '2026-04-16'
);

-- -------------------------------------------------------
-- VOICE / IDENTITY (3 constants)
-- -------------------------------------------------------

INSERT OR IGNORE INTO lcs_m_registry (id, name, abbreviation, description, category, primitive, ctb_placement, imo_topology, format, current_value, source, source_detail, status, locked, last_verified) VALUES
(
  'M-ID-001',
  'Barton Voice — Direct No BS',
  NULL,
  'Dave Barton communication style — direct, no corporate fluff, mechanical engineer precision with words. Not salesy, not consultative, not warm-and-fuzzy. Says what the data shows and what it means. This voice is a constant across ALL outreach — email templates, LinkedIn messages, website copy, meeting presentations. It is the brand identity. Any outreach that does not sound like Dave talking is wrong.',
  'voice',
  'Thing',
  'Trunk',
  'Output',
  'tone specification (direct, data-driven, no filler)',
  'direct no BS',
  'law/VOICE-LIBRARY.md',
  'law/VOICE-LIBRARY.md',
  'active',
  1,
  '2026-04-16'
);

INSERT OR IGNORE INTO lcs_m_registry (id, name, abbreviation, description, category, primitive, ctb_placement, imo_topology, format, current_value, source, source_detail, status, locked, last_verified) VALUES
(
  'M-ID-002',
  'CEO CFO Frame — Numbers ROI Data',
  NULL,
  'When messaging CEOs and CFOs, the frame is exclusively quantitative: cost savings percentages, ROI calculations, premium benchmarks against industry averages, Schedule A commission analysis, per-employee cost comparisons. CEOs and CFOs make decisions based on financial impact. Every email and LinkedIn message to these roles leads with a number, backs it with 5500 data, and closes with a specific dollar or percentage claim. No emotional appeals, no "let me help you" language.',
  'voice',
  'Thing',
  'Branch',
  'Output',
  'messaging frame (quantitative, data-backed)',
  'numbers ROI data',
  'human-declared constraint',
  'C-suite messaging frame',
  'active',
  1,
  '2026-04-16'
);

INSERT OR IGNORE INTO lcs_m_registry (id, name, abbreviation, description, category, primitive, ctb_placement, imo_topology, format, current_value, source, source_detail, status, locked, last_verified) VALUES
(
  'M-ID-003',
  'HR Frame — Relief Easier Less Burden',
  NULL,
  'When messaging HR directors, the frame is operational relief: fewer vendors to manage, less manual data entry, no more juggling disconnected software systems, automated compliance reporting, employees stop complaining about benefits confusion. HR directors do not control the budget (CEO/CFO do), but they control the process and strongly influence the decision. They are overwhelmed and understaffed. The message is "this makes your job easier" not "this saves money."',
  'voice',
  'Thing',
  'Branch',
  'Output',
  'messaging frame (operational relief, ease of use)',
  'relief easier less burden',
  'human-declared constraint',
  'HR messaging frame',
  'active',
  1,
  '2026-04-16'
);

-- -------------------------------------------------------
-- TIMING (4 constants)
-- -------------------------------------------------------

INSERT OR IGNORE INTO lcs_m_registry (id, name, abbreviation, description, category, primitive, ctb_placement, imo_topology, format, current_value, source, source_detail, status, locked, last_verified) VALUES
(
  'M-TIME-001',
  'Renewal Date as Anchor Constant',
  NULL,
  'The plan year end date from the 5500 filing — this IS the renewal date for the company benefits plan. This is the single most important timing constant in the outreach system. Companies only change brokers at renewal time. The renewal date determines WHEN to reach out to each company — too early and they are not thinking about it, too late and they have already made their decision. Every company in the 32K list has a known renewal date from their 5500 filing.',
  'timing',
  'Thing',
  'Trunk',
  'Input',
  'date (plan_year_end from 5500)',
  NULL,
  'D1: svg-d1-outreach-ops',
  'dol_form_5500.plan_year_end',
  'active',
  1,
  '2026-04-16'
);

INSERT OR IGNORE INTO lcs_m_registry (id, name, abbreviation, description, category, primitive, ctb_placement, imo_topology, format, current_value, source, source_detail, status, locked, last_verified) VALUES
(
  'M-TIME-002',
  '5 Months Prior — Start Outreach',
  NULL,
  'Outreach to a company begins exactly 5 months before their benefits renewal date. This is based on the insurance buying cycle — companies start evaluating alternatives 4-6 months before renewal. Starting at 5 months puts Dave in the conversation early enough to influence the decision but not so early that it is irrelevant. For December renewals (5,702 companies — the biggest wave), outreach starts in July.',
  'timing',
  'Thing',
  'Branch',
  'Input',
  'integer months before renewal_date = 5',
  '5 months',
  'human-declared constraint',
  'outreach timing start anchor',
  'active',
  1,
  '2026-04-16'
);

INSERT OR IGNORE INTO lcs_m_registry (id, name, abbreviation, description, category, primitive, ctb_placement, imo_topology, format, current_value, source, source_detail, status, locked, last_verified) VALUES
(
  'M-TIME-003',
  '2 Months Prior — Hard Stop',
  NULL,
  'All outreach to a company stops exactly 2 months before their renewal date. By this point, the company has either engaged (meeting set, proposal in play) or has made their decision. Continuing to email or message after 2 months prior is wasted effort and risks annoying a prospect who might be open next year. The hard stop preserves the relationship for the next renewal cycle.',
  'timing',
  'Thing',
  'Branch',
  'Input',
  'integer months before renewal_date = 2',
  '2 months',
  'human-declared constraint',
  'outreach timing cutoff anchor',
  'active',
  1,
  '2026-04-16'
);

INSERT OR IGNORE INTO lcs_m_registry (id, name, abbreviation, description, category, primitive, ctb_placement, imo_topology, format, current_value, source, source_detail, status, locked, last_verified) VALUES
(
  'M-TIME-004',
  'December Renewals — 5702 Companies Biggest Wave',
  NULL,
  '5,702 companies in the target list have December 31 plan year end dates — the single largest renewal cohort. Calendar-year plans are the most common in employer benefits. This means July is the start of the biggest outreach wave (5 months prior), and October is the hard stop (2 months prior). The December wave represents approximately 17% of the total 32K company list and is the first major campaign to execute.',
  'timing',
  'Thing',
  'Branch',
  'Input',
  'integer count of December-renewal companies',
  '5702',
  'D1: svg-d1-outreach-ops',
  'dol_form_5500 WHERE plan_year_end ends in -12-31',
  'active',
  1,
  '2026-04-16'
);

-- -------------------------------------------------------
-- TRIGGERS (2 constants)
-- -------------------------------------------------------

INSERT OR IGNORE INTO lcs_m_registry (id, name, abbreviation, description, category, primitive, ctb_placement, imo_topology, format, current_value, source, source_detail, status, locked, last_verified) VALUES
(
  'M-TRIG-001',
  'Talent Flow — Hire Promote Terminate',
  NULL,
  'Three talent flow events that serve as outreach trigger signals: HIRE (new executive joins — new decision-maker who may want to evaluate benefits), PROMOTE (existing employee promoted to CEO/CFO/HR — new authority to make changes), TERMINATE (executive leaves — replacement will review all vendor relationships). These events are detectable through LinkedIn monitoring and public announcements. Each event opens a window of opportunity because new decision-makers are more likely to evaluate alternatives than incumbents.',
  'trigger',
  'Change',
  'Branch',
  'Input',
  'enum(HIRE, PROMOTE, TERMINATE)',
  '3 event types',
  'human-declared constraint',
  'talent flow trigger events detected via LinkedIn monitoring',
  'active',
  1,
  '2026-04-16'
);

INSERT OR IGNORE INTO lcs_m_registry (id, name, abbreviation, description, category, primitive, ctb_placement, imo_topology, format, current_value, source, source_detail, status, locked, last_verified) VALUES
(
  'M-TRIG-002',
  'Broker of Record Changes YoY',
  NULL,
  'Year-over-year comparison of Schedule A data from consecutive 5500 filings reveals when a company changed their insurance broker. If Broker A was on the 2023 filing and Broker B is on the 2024 filing, that company switched brokers. This is a high-value signal for two reasons: (1) companies that recently switched are unlikely to switch again soon (cool-off), and (2) companies that have not switched in years may be ripe for change. The YoY diff is a computed constant from the 5500 data.',
  'trigger',
  'Change',
  'Branch',
  'Input',
  'boolean diff(schedule_a_year_n, schedule_a_year_n-1)',
  NULL,
  'D1: svg-d1-outreach-ops',
  'dol_schedule_a year-over-year broker comparison',
  'active',
  1,
  '2026-04-16'
);

-- -------------------------------------------------------
-- PIPELINE / PROCESS (1 constant)
-- -------------------------------------------------------

INSERT OR IGNORE INTO lcs_m_registry (id, name, abbreviation, description, category, primitive, ctb_placement, imo_topology, format, current_value, source, source_detail, status, locked, last_verified) VALUES
(
  'M-PIPE-001',
  '10-3-1 Pipeline Model',
  '10-3-1',
  'The sales pipeline conversion model: for every 10 meetings set, 3 will advance to a formal proposal, and 1 will close as a new client. P=1 for the outreach system means generating 10 qualified meetings per outreach cycle. This is the top-of-funnel target that Dave has declared as the success metric. Everything upstream — email campaigns, LinkedIn sequences, content, deliverability — exists to produce these 10 meetings. If the system generates 10 meetings per cycle, the math works: 1 new client per cycle at the savings range Dave delivers.',
  'process',
  'Flow',
  'Trunk',
  'Output',
  'ratio: meetings:proposals:closes = 10:3:1',
  '10-3-1',
  'human-declared constraint',
  'pipeline conversion model and P=1 target for outreach system',
  'active',
  1,
  '2026-04-16'
);
