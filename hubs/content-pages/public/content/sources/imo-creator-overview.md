# IMO Creator — The Machine Behind Three Businesses

## What Is IMO Creator?

IMO Creator is a custom-built operational platform that runs three distinct businesses from a single command center. Built by Dave Barton, it's not a SaaS product or an off-the-shelf tool — it's a purpose-built infrastructure that manages insurance, real estate, and personal operations through one unified system.

The name "IMO" stands for Input-Middle-Output — the universal pattern that every process follows. Something comes in, something happens to it, something comes out. Dave applied this pattern at every level of his businesses, from individual tasks to entire divisions.

## The Three Businesses

### SVG Agency — Insurance
Shenandoah Valley Group (SVG) is a full-service insurance agency. The platform manages over 32,000 companies, 109,000 contacts, and 171,000 Department of Labor filings. The operation runs a 10-3-1 pipeline: 10 outreach meetings generate 3 proposals that close 1 client.

What makes SVG different is the data infrastructure behind it. Instead of cold calling, Dave built an informatics pipeline that uses public DOL data (Form 5500 filings) to identify companies that need insurance services. The system enriches company data, identifies decision makers, and routes qualified prospects into a structured sales process.

The sales process itself follows four meetings: fact finding, insurance education, cost presentation, and ongoing service. Each step has its own preparation materials, data models, and follow-up automation.

### Real Estate
The real estate operation covers property investment, self-storage facilities, and deal screening. The same analytical framework that identifies undervalued insurance prospects is applied to identify undervalued properties and storage markets.

### Personal Operations
Personal financial management — accounts, budgeting, goals, and tax planning — all run through the same infrastructure.

## The Architecture

### Mission Control
Everything flows through Mission Control — a single web dashboard that shows system health, active tasks, email, calendar, and project status across all three businesses. It's the cockpit view.

### The Garage
IMO Creator is organized like an aviation maintenance hangar. Workers (Cloudflare Workers) are the "aircraft" — each one does a specific job. They come into the hangar for maintenance, get certified, and go back to work. Every worker has an identity (HEIR — like a VIN number) and a state machine (ORBT — Operate, Repair, Build, Troubleshoot/Train).

### Workers and Services
The platform runs on Cloudflare's edge network — Workers for compute, D1 databases for structured data, Pages for web interfaces, Stream for video hosting, and R2 for file storage. Currently there are 18+ workers handling everything from email campaigns to document processing to AI-powered research.

### The Dispatch System
A universal inbox where any device — phone, desktop, or automated trigger — can submit work packets. Tasks get prioritized (urgent/high/normal/low) and claimed by whatever system is available to execute them. It doesn't matter which device or which session picks up the work — the structure is the same everywhere.

### Knowledge Management
The Library Barton Brain (LBB) is the single knowledge store. It uses a Dewey Decimal-style classification system with six main categories: system architecture, outreach intelligence, sales knowledge, client service, research, and cross-cutting processes. Every session's learnings get ingested back into LBB, so the system gets smarter over time.

### Content Factory
NotebookLM serves as the content factory — taking source documents and generating podcasts, videos, slide decks, reports, infographics, quizzes, and flashcards. These artifacts feed into branded web pages deployed on Cloudflare Pages, creating client-facing educational content.

## What Makes This Different

1. **One person, three businesses.** The infrastructure scales across domains because the thinking framework is universal. The processes are the constants — the business domain is the variable.

2. **Data-driven, not gut-driven.** Every decision flows through structured data pipelines. The DOL filing pipeline alone processes 171,000+ records to identify insurance prospects.

3. **Built, not bought.** This isn't stitched together from 47 SaaS products. It's custom infrastructure designed for how Dave actually works.

4. **Documentation is the product.** Every process is documented. Every worker has an identity. Every error is tracked. The system maintains its own maintenance log — like an aircraft logbook.

5. **AI-augmented, not AI-dependent.** AI tools (Claude, NotebookLM, Codex) handle the variable work — research, content generation, code review. The deterministic infrastructure handles everything that shouldn't require judgment.

## The Numbers

| Metric | Value |
|--------|-------|
| Companies tracked | 32,000+ |
| Contacts | 109,000+ |
| DOL filings | 171,000+ |
| Active workers | 18+ |
| D1 databases | 12 |
| Neon vault databases | 7 |
| Email domains | 14 |
| NotebookLM notebooks | 13 |

## Who Is Dave Barton?

Dave is a builder. He runs SVG Agency (insurance), invests in real estate, and manages personal operations — all through infrastructure he designed and built himself. His background spans decades of insurance industry experience, combined with a self-taught engineering approach to business operations.

His philosophy: if you're doing something more than three times, it should be a system. If the system breaks three times, you don't patch it — you redesign it. Documentation isn't overhead — it's the product. The code is disposable. The thinking framework behind it is what matters.
