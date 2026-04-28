# SVG Agency — How Data Replaced Cold Calling

## The Problem With Traditional Insurance Outreach

Most insurance agencies rely on cold calling, referrals, and buying leads. The close rates are terrible, the data is stale, and agents spend 80% of their time chasing people who don't need what they're selling. It's a volume game with no intelligence behind it.

Dave Barton took a different approach: what if you could know exactly which companies need insurance services before you ever pick up the phone?

## The DOL Filing Pipeline

Every company with an employee benefit plan is required to file Form 5500 with the Department of Labor. These filings are public record. They contain the company name, EIN, number of participants, plan assets, insurance carriers, brokers of record, and service providers.

SVG built a pipeline that ingests and processes these filings — over 171,000 records and growing. The system:

1. **Downloads** annual DOL filing data (Form 5500 and 5500-SF)
2. **Parses** the filings to extract company details, plan characteristics, and broker information
3. **Matches** filings to companies using EIN and name matching algorithms
4. **Enriches** company records with additional data — decision maker names, email addresses, phone numbers, LinkedIn profiles
5. **Scores** companies based on plan size, broker tenure, filing patterns, and market signals
6. **Routes** qualified prospects into the outreach pipeline

The result: instead of cold calling from a phone book, SVG reaches out to companies where the data says there's an opportunity — a plan with no broker, a broker who hasn't filed in years, a company growing past compliance thresholds.

## The 10-3-1 Pipeline

SVG's sales process follows a 10-3-1 conversion model:

- **10 Outreach Meetings** — The goal is to get 10 qualified conversations per cycle. These come from the enriched DOL data, not random cold calls. Every prospect has been pre-screened: we know their plan size, their current broker situation, and their compliance status.

- **3 Proposals** — Of the 10 meetings, 3 result in formal proposals. These are companies where the fit is confirmed — they need what SVG offers, the timing is right, and the decision maker is engaged.

- **1 Close** — Of the 3 proposals, 1 becomes a client. This isn't a failure rate — it's a qualification funnel. The 7 who didn't close this cycle stay in the pipeline for next year's renewal season.

## The Data Infrastructure

### 32,000+ Companies
Every company that has filed a Form 5500 in SVG's target market is tracked. Company records include EIN, name, address, industry, plan type, assets, participants, and filing history.

### 109,000+ Contacts
Decision makers at those companies — HR directors, CFOs, benefits managers, business owners. Contacts are enriched with email addresses (verified), phone numbers, LinkedIn profiles, and role assignments.

### 14 Email Domains
SVG operates 14 sending domains for outreach campaigns, managed through Mailgun. Domain rotation, deliverability monitoring, and reputation management are automated.

### Campaign Management
Multi-channel outreach: email sequences, LinkedIn connections (via HeyReach), and direct outreach. Each campaign is tracked from send to response to meeting to proposal to close.

## What Makes This Different

1. **Public data, private intelligence.** The DOL filings are public. What SVG does with them — the enrichment, the scoring, the matching — is the competitive advantage.

2. **Compliance as a sales tool.** Many companies don't know they have filing obligations, or their current broker isn't handling compliance properly. SVG identifies these gaps from the data before the first conversation.

3. **Automated enrichment.** Finding the right person at a company used to take hours of manual research. The pipeline does it automatically — matching names to roles, verifying emails, pulling LinkedIn profiles.

4. **Year-round pipeline.** Insurance renewals happen on a predictable cycle. The system tracks renewal dates and triggers outreach at the right time — not too early, not too late.

## The Technology Stack

- **Data Processing:** Python scripts for DOL filing import, parsing, and matching
- **Database:** Neon PostgreSQL (vault) + Cloudflare D1 (operational)
- **Email:** Mailgun (14 domains, deliverability monitoring)
- **LinkedIn:** HeyReach (automated connection and messaging)
- **Enrichment:** Hunter.io, Prospeo (email finding and verification)
- **Orchestration:** Cloudflare Workers (barton-outreach-core)
- **Knowledge:** Library Barton Brain (LBB) for institutional knowledge

## The Numbers Tell the Story

Traditional insurance agency: 2-3% response rate on cold outreach, 50+ dials per meeting booked.

SVG with data-driven outreach: higher response rates because every touchpoint is relevant — the prospect has an actual need that shows up in their filing data. The conversation starts with "I noticed your company's Form 5500 shows..." instead of "Hi, do you need insurance?"
