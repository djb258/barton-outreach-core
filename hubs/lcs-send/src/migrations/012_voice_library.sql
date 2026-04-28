-- ─────────────────────────────────────────────────────────────
-- BAR-175: Voice Library
--
-- Dave Barton's communication style as locked constants.
-- Target: lcs_voice_library — one row per role.
-- Feeds into: lcs_frame_registry (voice_id FK).
-- Compiler reads voice_id from frame, joins here for tone context.
--
-- Constants:
--   Barton voice = direct, mechanical engineer precision, zero BS
--   CEO/CFO frame = lead with a number. Always.
--   HR frame = lead with a pain point. Always.
--   Proof anchor = 5500 government filing data. Not opinions.
--   Value prop = insurance informatics (only one in the country)
--   Savings range = 20-55%
-- ─────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS lcs_voice_library (
  voice_id            TEXT PRIMARY KEY,      -- VCE-BARTON-CEO, VCE-BARTON-CFO, VCE-BARTON-HR, VCE-BARTON-ALL
  voice_name          TEXT NOT NULL,         -- human label
  target_role         TEXT NOT NULL,         -- CEO | CFO | HR | ALL
  tone                TEXT NOT NULL,         -- one sentence: how it sounds
  style_rules         TEXT NOT NULL,         -- JSON array of rules (what to DO)
  forbidden_phrases   TEXT NOT NULL,         -- JSON array of strings never to use
  opening_patterns    TEXT NOT NULL,         -- JSON array: how to open for this role
  closing_patterns    TEXT NOT NULL,         -- JSON array: how to close for this role
  proof_points        TEXT NOT NULL,         -- JSON array: credibility anchors
  is_active           INTEGER NOT NULL DEFAULT 1,
  created_at          TEXT NOT NULL DEFAULT (datetime('now'))
);

-- ─────────────────────────────────────────────────────────────
-- SEED: Dave Barton Voice Constants
-- NOTE: apostrophes avoided in JSON values to prevent SQL parse issues.
-- Use double-quotes inside the JSON strings.
-- ─────────────────────────────────────────────────────────────

-- ALL ROLES — base voice (applies regardless of target)
INSERT OR IGNORE INTO lcs_voice_library (
  voice_id, voice_name, target_role, tone,
  style_rules, forbidden_phrases, opening_patterns, closing_patterns, proof_points
) VALUES (
  'VCE-BARTON-ALL',
  'Dave Barton - Base Voice',
  'ALL',
  'Direct, no-BS mechanical engineer who extracted the physics of healthcare cost from running real businesses.',
  '["Lead with the fact, not the setup","One concept per email - teach it, do not sell it","Short sentences. No padding. Every word earns its place.","Never apologize for the outreach","Name the category first: insurance informatics","State the differentiator as a fact, not a claim","Use numbers when you have them. Skip them when you do not.","The CTA is one link. Not a paragraph of options.","Sign as: Dave Barton / SVG Agency / Insurance Informatics"]',
  '["I hope this finds you well","Just checking in","I wanted to follow up","Touching base","Reaching out","Synergy","Leverage","Revolutionize","Game-changing","Best-in-class","World-class","I am confident","Please do not hesitate","Looking forward to hearing from you","At your earliest convenience","Apologies for any inconvenience"]',
  '["[Name],","Hi [Name],"]',
  '["[booking link]","[booking link]\n\n[linkedin]\n\n[sig]","[sig]"]',
  '["5,500 government filings - not opinions, not surveys, DOL data","Only one insurance informatics firm in the country","Zero commission - flat fee - no carrier incentive","20-55% savings documented in client base"]'
);

-- CEO FRAME — lead with a number, focus on cost and control
INSERT OR IGNORE INTO lcs_voice_library (
  voice_id, voice_name, target_role, tone,
  style_rules, forbidden_phrases, opening_patterns, closing_patterns, proof_points
) VALUES (
  'VCE-BARTON-CEO',
  'Dave Barton - CEO Frame',
  'CEO',
  'Peer-to-peer. One business owner to another. Numbers first, always.',
  '["First line must contain a number or a dollar figure","Frame health insurance as a budget line that has a manageable gap - not a fixed cost","Reference the 20-55% savings range with the DOL data anchor","Connect to business control: you manage every other major expense, this one you can manage too","Do not explain insurance basics - assume they know. Focus on what changed (the data systems).","Keep it under 200 words for the first touch"]',
  '["benefits package","employee wellness","human resources solution","HR tech"]',
  '["[Name],\n\n[Number or dollar figure that frames the cost gap]","[Name],\n\nDave Barton. [State the category. State the differentiator. Lead with a number.]"]',
  '["15 minutes: [booking link]","If saving time and money on your health plan is ever a priority, I want to be on your radar.\n\n[booking link]"]',
  '["5,500 DOL filings - your industry, your size, your carrier","Most employers do not know the gap between premium and actual cost. That gap is either your money or the insurance company money.","Until recently the data systems did not exist to manage this. Now they do."]'
);

-- CFO FRAME — lead with a number, ROI, cost savings percentages, data proof
INSERT OR IGNORE INTO lcs_voice_library (
  voice_id, voice_name, target_role, tone,
  style_rules, forbidden_phrases, opening_patterns, closing_patterns, proof_points
) VALUES (
  'VCE-BARTON-CFO',
  'Dave Barton - CFO Frame',
  'CFO',
  'Numbers, ROI, data. The CFO already knows the cost. Show them the lever.',
  '["First line must be a specific number, ratio, or percentage","Reference DOL data explicitly - 5,500 filings, not a survey","State the savings range: 20-55% documented","Connect to what the CFO can actually control: the claims between the broker and the check","Distinguish between premium (what you budget) and cost (what you actually spend)","ROI framing: flat fee against percentage savings","Keep it under 180 words for the first touch"]',
  '["benefits broker","renewal negotiation","carrier shopping","human resources","wellness program","engagement"]',
  '["[Name],\n\n[specific percentage or dollar figure - the cost gap]","[Name],\n\nDave Barton. [Lead with the number. State what controls it.]"]',
  '["Want to see what the math looks like: [booking link]","If the gap between budget and spend is ever worth 15 minutes: [booking link]"]',
  '["5,500 DOL government filings - not a survey, actual data","20-55% savings range documented across client base","Flat fee. Zero commission. Our math and yours are aligned.","The 10% of employees driving 85% of cost - that segment has never been actively managed. Now it can be."]'
);

-- HR FRAME — lead with a pain point, relief/administration/fewer silos
INSERT OR IGNORE INTO lcs_voice_library (
  voice_id, voice_name, target_role, tone,
  style_rules, forbidden_phrases, opening_patterns, closing_patterns, proof_points
) VALUES (
  'VCE-BARTON-HR',
  'Dave Barton - HR Frame',
  'HR',
  'Pain-first. HR is the one who deals with the calls, the confusion, the edge cases nobody built a system for.',
  '["First line must name a specific pain point - not a feature","Focus on what HR currently absorbs that a system should handle","Relief framing: fewer inbound calls, clearer routing, less chasing","Name the gap: the high-dollar claims (cancer, surgeries, specialty drugs) that slip through","Reference the 5,500 DOL filings as proof that the patterns are real and documented","Do not lead with cost savings - that is the CFO frame. HR cares about burden and silos.","Keep it under 200 words for the first touch"]',
  '["ROI","return on investment","profit","margin","cost center","benefits tech stack","HRIS integration","seamless","turnkey","scalable solution"]',
  '["[Name],\n\n[A specific HR pain point - named, not vague]","[Name],\n\nDave Barton. [Name what HR is currently absorbing that should not be their problem.]"]',
  '["15 minutes if you want to see it: [booking link]","If reducing the administrative load on your team is ever a priority: [booking link]"]',
  '["5,500 DOL filings - the patterns of what slips through are documented","When one of your employees gets a $200K hospital bill, who is checking if that hospital has a legal obligation to offer financial assistance? Right now: nobody.","High-dollar specialty drugs routed to manufacturer programs that cover them for free - that routing currently does not happen automatically.","Your HR team is spending time chasing problems a system should handle."]'
);
