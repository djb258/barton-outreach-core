# ID Tagging Guide

## Barton Doctrine: Marketing > Outreach

**Database:** 01 (Marketing)  
**Subhive:** 04 (Marketing Subhive)  
**Microprocess:** 01 (Outreach)

---

## Unique ID Requirements

### 5,000 Foot Altitude (Execution Level)

All execution-level documents must include:

#### unique_id: [____]
- Format: [To be defined by implementation team]
- Purpose: Unique identifier for tracking and reference
- Location: Header section of execution documents
- Required: Yes (execution level only)

#### process_id: [Verb + Object]
- Format: Action verb + Target object
- Purpose: Describes the core action of the process
- Examples: 
  - "Engage + Prospects"
  - "Generate + Leads" 
  - "Build + Relationships"
- Location: Header section of execution documents
- Required: Yes (execution level only)

### Implementation Notes

1. **Altitude Purity**: Only execution-level (5k) documents require ID tagging
2. **Consistency**: Use consistent formatting across all execution documents
3. **Tracking**: IDs should integrate with process tracking systems
4. **Updates**: Update IDs when processes are modified or split

### Template Format

```markdown
**unique_id:** [____]  
**process_id:** [Verb + Object]
```

---

**Note:** This tagging system supports process tracking and integration with operational systems. Higher altitude documents (30k, 20k, 10k) do not require ID tagging.