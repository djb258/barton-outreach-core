-- ─────────────────────────────────────────────────────────────
-- BAR-175: Frame Registry + Message Templates
--
-- lcs_frame_registry already exists (created prior to this migration
-- with legacy schema). This migration:
--   1. Adds missing columns: sequence_id, target_role, voice_id,
--      subject_line_template, body_template, notes
--   2. Seeds real message templates for SEQ-COLD-EMAIL-V1
--   3. Updates lcs_sequence_def to use canonical OUT-HAMMER frame IDs
--
-- Frame IDs match what compiler-v2.ts resolves in buildMessageBody():
--   OUT-HAMMER-01      = first touch, CEO/CFO version
--   OUT-HAMMER-01-HR   = first touch, HR version
--   OUT-HAMMER-01-LITE = first touch, minimal data version
--   OUT-HAMMER-02      = they opened — the 90/15 rule
--   OUT-HAMMER-03      = they did not open — the gap nobody talks about
--   OUT-HAMMER-04      = step 4 value proof point / last-one-from-me
--   FOLLOWUP-BREAK-V1  = step 5 final break-up
--   OUT-GENERAL-V1     = fallback catch-all
--
-- Template variables resolved at SID construction time:
--   {{company_name}}, {{contact_name}}, {{savings_range}},
--   {{renewal_date}}, {{booking_link}}, {{linkedin}}
-- ─────────────────────────────────────────────────────────────

-- Step 1: Add missing columns to existing lcs_frame_registry
ALTER TABLE lcs_frame_registry ADD COLUMN sequence_id         TEXT DEFAULT 'SEQ-COLD-EMAIL-V1';
ALTER TABLE lcs_frame_registry ADD COLUMN target_role         TEXT DEFAULT 'ALL';
ALTER TABLE lcs_frame_registry ADD COLUMN voice_id            TEXT DEFAULT 'VCE-BARTON-ALL';
ALTER TABLE lcs_frame_registry ADD COLUMN subject_line_template TEXT;
ALTER TABLE lcs_frame_registry ADD COLUMN body_template       TEXT;
ALTER TABLE lcs_frame_registry ADD COLUMN notes               TEXT;

-- Step 2: Seed OUT-HAMMER-01 (CEO/CFO first touch — education-first, define the category)
INSERT OR IGNORE INTO lcs_frame_registry (
  frame_id, frame_name, lifecycle_phase, frame_type, tier, channel,
  step_in_sequence, is_active,
  sequence_id, target_role, voice_id,
  subject_line_template, body_template, notes
) VALUES (
  'OUT-HAMMER-01',
  'Hammer 01 — Insurance Informatics Intro',
  'OUTREACH',
  'cold_email',
  5,
  'MG',
  1,
  1,
  'SEQ-COLD-EMAIL-V1',
  'CFO',
  'VCE-BARTON-CFO',
  '{{company_name}} — quick question',
  '{{contact_name}},

Dave Barton. I do something called insurance informatics — insurance + IT. Using data and AI to manage health insurance cost in real time, not just shop carriers once a year.

I keep looking for someone else doing this. I cannot find one. Other people have pieces, but nobody has put the whole thing together.

You shop for everything else. Why aren''t you shopping for something that''s going to cost you $100,000 or more? The answer used to be that nobody had the systems to do it. Now I do.

I take zero commission. You pay me a flat fee. I have no incentive to push any carrier. We are aligned.

My job isn''t to sell you anything. It''s to show you how this stuff works. If you want to do it, great. If you don''t, great. I''m not going to waste your time and you''re not going to waste mine.

This might not be the right time. But if saving time and money on your health plan is ever a priority, I want to be on your radar.

15 minutes: {{booking_link}}

Or follow along — I break this down on LinkedIn: {{linkedin}}

Dave Barton
SVG Agency
Insurance Informatics',
  'Education-first. Define the category. CEO/CFO default. No fluff, no apology. Two doors: booking link or LinkedIn. Under 200 words.'
);

-- OUT-HAMMER-01-HR (HR first touch — pain-first, not category definition)
INSERT OR IGNORE INTO lcs_frame_registry (
  frame_id, frame_name, lifecycle_phase, frame_type, tier, channel,
  step_in_sequence, is_active,
  sequence_id, target_role, voice_id,
  subject_line_template, body_template, notes
) VALUES (
  'OUT-HAMMER-01-HR',
  'Hammer 01 HR — Administrative Burden Intro',
  'OUTREACH',
  'cold_email',
  5,
  'MG',
  1,
  1,
  'SEQ-COLD-EMAIL-V1',
  'HR',
  'VCE-BARTON-HR',
  '{{company_name}} — quick question',
  '{{contact_name}},

Dave Barton. When one of your employees gets a $200K hospital bill, who checks if that hospital has a legal obligation to offer financial assistance?

Right now, at most companies, nobody does. That call lands with HR.

I built a system called insurance informatics. It routes those situations automatically — high-dollar claims, specialty drug programs, financial assistance eligibility — so your team is not chasing them manually.

5,500 DOL government filings tell me what your employees are dealing with. Not surveys. Actual plan data.

I take zero commission. Flat fee. No carrier incentive.

If reducing the administrative load on your team is ever worth 15 minutes: {{booking_link}}

Or follow along: {{linkedin}}

Dave Barton
SVG Agency
Insurance Informatics',
  'HR lead = name the pain first. Administrative burden angle. 5500 DOL proof anchor. Short — under 200 words. No ROI language.'
);

-- OUT-HAMMER-01-LITE (shorter fallback for lower-tier data)
INSERT OR IGNORE INTO lcs_frame_registry (
  frame_id, frame_name, lifecycle_phase, frame_type, tier, channel,
  step_in_sequence, is_active,
  sequence_id, target_role, voice_id,
  subject_line_template, body_template, notes
) VALUES (
  'OUT-HAMMER-01-LITE',
  'Hammer 01 Lite — Minimal First Touch',
  'OUTREACH',
  'cold_email',
  5,
  'MG',
  1,
  1,
  'SEQ-COLD-EMAIL-V1',
  'ALL',
  'VCE-BARTON-ALL',
  '{{company_name}} — quick question',
  '{{contact_name}},

Dave Barton. I do insurance informatics — using data and AI to manage health insurance cost, not just shop carriers once a year. I keep looking for someone else doing this. I cannot find one.

If saving time and money on your health plan is ever a priority, I want to be on your radar.

{{booking_link}}

{{linkedin}}

Dave Barton
SVG Agency
Insurance Informatics',
  'Lite version for lower-tier or minimal grid data. Same voice, fewer proof points. Two lines and two doors. Fallback when specific grid data is absent.'
);

-- OUT-HAMMER-02 (they opened — follow up with deeper value, the 90/15 rule)
INSERT OR IGNORE INTO lcs_frame_registry (
  frame_id, frame_name, lifecycle_phase, frame_type, tier, channel,
  step_in_sequence, is_active,
  sequence_id, target_role, voice_id,
  subject_line_template, body_template, notes
) VALUES (
  'OUT-HAMMER-02',
  'Hammer 02 — The 90/15 Rule',
  'OUTREACH',
  'followup_email',
  5,
  'MG',
  2,
  1,
  'SEQ-COLD-EMAIL-V1',
  'ALL',
  'VCE-BARTON-ALL',
  '{{company_name}} — something most employers don''t know',
  '{{contact_name}},

Following up on my last note. Here is something most employers have never been told:

90% of your employees only cause 15% of your claims cost. Routine stuff. The other 10% — cancer, surgeries, high-dollar drugs — that''s 85% of what you spend. Every dollar is won or lost right there.

The 90% basically run the way they''re supposed to. Money in, money out, no big deal. The 10% is where people need help. And right now, nobody''s helping.

This could always have been managed. But until recently, the data systems to actually do it did not exist. Now they do.

That 10% is costing you money every day nobody''s managing it. And your HR team is spending time chasing problems a system should handle.

Want to see what it looks like: {{booking_link}}

Or follow along here: {{linkedin}}

Dave Barton
SVG Agency
Insurance Informatics',
  'Triggered when contact opened Step 1. Teach the 90/15 rule. One concept. Do not sell — teach. CTA = see what it looks like. Works for CEO/CFO/HR — name the cost AND the HR burden.'
);

-- OUT-HAMMER-03 (they did not open — gap nobody talks about)
INSERT OR IGNORE INTO lcs_frame_registry (
  frame_id, frame_name, lifecycle_phase, frame_type, tier, channel,
  step_in_sequence, is_active,
  sequence_id, target_role, voice_id,
  subject_line_template, body_template, notes
) VALUES (
  'OUT-HAMMER-03',
  'Hammer 03 — The Gap Nobody Talks About',
  'OUTREACH',
  'followup_email',
  5,
  'MG',
  3,
  1,
  'SEQ-COLD-EMAIL-V1',
  'ALL',
  'VCE-BARTON-ALL',
  '{{company_name}} — the gap nobody talks about',
  '{{contact_name}},

Your broker shops carriers, negotiates rates, handles your renewal. That is their job and most of them do it fine.

Here is what nobody does: manage the claims in between. When one of your employees gets a $200K hospital bill, who is checking if that hospital has a legal obligation to offer financial assistance? Who is routing the $15K/month drug to a manufacturer program that gets it for free?

Nobody. That gap costs you money — and it costs your HR team time tracking down issues that should be routed automatically.

You shop for everything else your company spends six figures on. This should be no different.

15 minutes if you want to see it: {{booking_link}}

Or follow along here: {{linkedin}}

Dave Barton
SVG Agency
Insurance Informatics',
  'Triggered when contact did NOT open Step 1. Different angle from HAMMER-01. Broker vs gap framing. HR pain + CEO cost in one email. Under 150 words.'
);

-- OUT-HAMMER-04 (step 4 — value proof point, premium vs cost gap, Patton close)
INSERT OR IGNORE INTO lcs_frame_registry (
  frame_id, frame_name, lifecycle_phase, frame_type, tier, channel,
  step_in_sequence, is_active,
  sequence_id, target_role, voice_id,
  subject_line_template, body_template, notes
) VALUES (
  'OUT-HAMMER-04',
  'Hammer 04 — Premium vs Cost Gap',
  'OUTREACH',
  'followup_email',
  5,
  'MG',
  4,
  1,
  'SEQ-COLD-EMAIL-V1',
  'ALL',
  'VCE-BARTON-CFO',
  '{{company_name}} — last one from me',
  '{{contact_name}},

Last note. One thing I''d leave you with:

Your premium is what you budget. Your cost is what you actually spend. The gap between those two is either your money or the insurance company''s money.

Most employers do not know that gap exists. The tools to manage it did not exist until recently. Now they do.

At the end of the day, this is about time and money. I built a system that manages both. If that is ever worth a conversation, I''m here.

{{booking_link}}

{{linkedin}}

Dave Barton
SVG Agency
Insurance Informatics',
  'Step 4. Premium vs cost — the gap framing. Short. Direct. Patton close — leave it with them. CTA is one link, no explanation. Works for CEO/CFO primary, acceptable for HR.'
);

-- FOLLOWUP-BREAK-V1 (final step — break-up email, direct ask for meeting)
INSERT OR IGNORE INTO lcs_frame_registry (
  frame_id, frame_name, lifecycle_phase, frame_type, tier, channel,
  step_in_sequence, is_active,
  sequence_id, target_role, voice_id,
  subject_line_template, body_template, notes
) VALUES (
  'FOLLOWUP-BREAK-V1',
  'Break-Up — Closing the Loop',
  'OUTREACH',
  'break_email',
  5,
  'MG',
  5,
  1,
  'SEQ-COLD-EMAIL-V1',
  'ALL',
  'VCE-BARTON-ALL',
  '{{company_name}} — closing the loop',
  '{{contact_name}},

Last one. I will not keep following up after this.

I have sent a few notes about insurance informatics — using data to manage health plan cost between renewals, not just at renewal. If that has ever been a priority or is becoming one, here is how to reach me:

{{booking_link}}

If not, no problem. I will close the loop on my end.

Dave Barton
SVG Agency
Insurance Informatics',
  'Final step. Break-up format. Direct ask. No teaching, no proof points — just the door and the out. Respects their time. Leaves it clean.'
);

-- OUT-GENERAL-V1 (catch-all fallback referenced by compiler when no frame matches)
INSERT OR IGNORE INTO lcs_frame_registry (
  frame_id, frame_name, lifecycle_phase, frame_type, tier, channel,
  step_in_sequence, is_active,
  sequence_id, target_role, voice_id,
  subject_line_template, body_template, notes
) VALUES (
  'OUT-GENERAL-V1',
  'General Fallback',
  'OUTREACH',
  'cold_email',
  5,
  'MG',
  1,
  1,
  'SEQ-COLD-EMAIL-V1',
  'ALL',
  'VCE-BARTON-ALL',
  '{{company_name}} — Dave Barton, Insurance Informatics',
  '{{contact_name}},

Dave Barton. I do insurance informatics — using data and AI to manage health insurance cost, not just shop carriers once a year. I keep looking for someone else doing this. I cannot find one.

If saving time and money on your health plan is ever a priority, I want to be on your radar.

{{booking_link}}

{{linkedin}}

Dave Barton
SVG Agency
Insurance Informatics',
  'Catch-all fallback when no frame matches by frame_id. Compiler references frame?.frame_id ?? ''OUT-GENERAL-V1''. Same voice, minimal content.'
);

-- Step 3: Update lcs_sequence_def to use canonical OUT-HAMMER frame IDs.
-- Migration 007 seeded placeholder IDs (COLD-INTRO-V1 etc).
-- These must match the frame_ids the compiler resolves via buildMessageBody().
UPDATE lcs_sequence_def SET frame_id = 'OUT-HAMMER-01'     WHERE sequence_id = 'SEQ-COLD-EMAIL-V1' AND step_number = 1;
UPDATE lcs_sequence_def SET frame_id = 'OUT-HAMMER-02'     WHERE sequence_id = 'SEQ-COLD-EMAIL-V1' AND step_number = 2;
UPDATE lcs_sequence_def SET frame_id = 'OUT-HAMMER-03'     WHERE sequence_id = 'SEQ-COLD-EMAIL-V1' AND step_number = 3;
UPDATE lcs_sequence_def SET frame_id = 'OUT-HAMMER-04'     WHERE sequence_id = 'SEQ-COLD-EMAIL-V1' AND step_number = 4;
UPDATE lcs_sequence_def SET frame_id = 'FOLLOWUP-BREAK-V1' WHERE sequence_id = 'SEQ-COLD-EMAIL-V1' AND step_number = 5;

-- Step 4: Fix pre-existing rows with NULL step_in_sequence.
-- These are legacy newsletter/pond frames. NULL sorts before 1 in SQLite ASC,
-- so they would have won LIMIT 1 in the CID frame lookup (returning a newsletter
-- frame for a cold outreach signal). Set to 99 so they sort last.
UPDATE lcs_frame_registry SET step_in_sequence = 99 WHERE step_in_sequence IS NULL;
