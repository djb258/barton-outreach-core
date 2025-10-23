<!--
─────────────────────────────────────────────
📁 CTB Classification Metadata
─────────────────────────────────────────────
CTB Branch: docs/pages
Barton ID: 06.01.07
Unique ID: CTB-F3740AF0
Blueprint Hash:
Last Updated: 2025-10-23
Enforcement: HEIR
─────────────────────────────────────────────
-->

<\!-- generated from modules/altitude-10000/page-10000.md -->
# Page 3 – 10,000 ft (Specialization)
Unique ID Prefix: 01.04.01.00.10
process_id: Detail Outreach Specialization

Branch 1 – Lead Intake & Validation (vertical flow):
Pull Company List by State from Apollo
  ↓ Assign company_unique_id
  ↓ Insert into marketing_company_intake (Neon)
Scrape Executives via Apify
  ↓ Assign contact_unique_id
  ↓ Store in staging
Validate Emails via MillionVerifier
  ↓ Drop Invalid
  ↓ Insert Validated Contacts into people (Neon)
  ↓ Link to Company

Branch 2 – Message Generation (Agent) (vertical flow):
Retrieve validated contacts from Neon
  ↓ Personalize per role
  ↓ Apply message rules
  ↓ Store in outreach_message_registry

Branch 3 – Campaign Execution & Telemetry (vertical flow):
Push messages to Instantly / HeyReach API
  ↓ Record delivery status
  ↓ Update campaign_run_log
  ↓ Send metrics to dashboard
EOF < /dev/null
