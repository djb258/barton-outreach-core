<!--
─────────────────────────────────────────────
📁 CTB Classification Metadata
─────────────────────────────────────────────
CTB Branch: docs/pages
Barton ID: 06.01.07
Unique ID: CTB-E8D00525
Blueprint Hash:
Last Updated: 2025-10-23
Enforcement: None
─────────────────────────────────────────────
-->

<\!-- generated from modules/altitude-20000/page-20000.md -->
# Page 2 – 20,000 ft (Categories)
Unique ID Prefix: 01.04.01.00.20
process_id: Organize Outreach Categories

Horizontal Diagram:
[ Lead Intake & Validation ] ── [ Message Generation (Agent) ] ── [ Campaign Execution & Telemetry ]

Branch 1 – Lead Intake & Validation (10k key sub-steps only):
- Acquire Companies by State from Apollo
- Insert Companies into Neon (Company Table)
- Scrape Executives (CEO/CFO/HR) for Each Company
- Validate Contacts (Email/Phone)
- Insert Validated Contacts into Neon (People Table)
- Link People to Company

Branch 2 – Message Generation (Agent) (10k key sub-steps only):
- Compose Outreach Message per Person (Role-Aware)
- Fallback to Generic Template if Personalization Fails
- Record Message Variant, Role, and Version Tag
- Store Message Payload for Deployment

Branch 3 – Campaign Execution & Telemetry (10k key sub-steps only):
- Publish Messages to Instantly / HeyReach via API
- Track Sends, Opens, Replies, Bounces
- Update Lead / Campaign Status in Neon
- Surface Live Metrics on Command Center Dashboard
EOF < /dev/null
