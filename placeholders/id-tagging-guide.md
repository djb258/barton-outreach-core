# ID Tagging Guide - Marketing Outreach Doctrine

## Unique ID Format
Pattern: `[database].[subhive].[microprocess].[tool].[altitude].[step]`

Example: `01.04.01.01.05.01`
- 01: Marketing database
- 04: Outreach subhive  
- 01: Lead Intake microprocess
- 01: Apollo tool
- 05: 5,000ft altitude
- 01: First step

## Process ID Format
Pattern: `[Verb] [Object]` (capitalized)

Examples:
- Acquire Companies
- Insert Companies
- Scrape Executives
- Validate Contacts
- Compose Message
- Publish Messages

## Blank Template Fields
When creating new processes, leave these blank for Tracker:
- unique_id: [____]
- process_id: [Fill with Verb + Object]

## ID Assignment Rules
1. Keep unique_id sortable (numerical sequence)
2. Process IDs must be action-oriented (Verb + Object)
3. Don't mix altitude details upward
4. Gate data at each step
5. Use consistent tool numbering across processes
