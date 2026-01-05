# Talent Flow Doctrine — Executive Movement Detection Spoke
## Barton Doctrine Framework | SVG-PLE Marketing Core

**Document ID**: `04.01.02.04.20000.001`
**Version**: 2.0.0
**Last Updated**: 2025-11-10
**Spoke Type**: Talent Flow (Executive Movement Detection)
**Role**: Data Ingestion Spoke → BIT Axle Integration
**Status**: Active | Production Ready

---

## 🏔️ VISION — 30,000 ft Altitude

### Strategic Purpose

The **Talent Flow Spoke** serves as a critical data ingestion pipeline within the SVG-PLE (Shenandoah Valley Group Perpetual Lead Engine) architecture. This spoke detects, validates, and tracks executive-level personnel movements across target accounts, converting human capital changes into quantified buying intent signals that drive sales prioritization and outreach automation.

### Position in SVG-PLE Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│                    SVG-PLE Architecture                           │
│              Hub-Spoke-Axle Marketing Engine                      │
└──────────────────────────────────────────────────────────────────┘

HUB (Core Intelligence)
└─▶ Marketing DB (Neon PostgreSQL)
    ├── company_master (04.04.01.01.#####.###)
    ├── people_master (04.04.02.04.#####.###)
    └── company_slot (04.04.02.04.#####.###)

SPOKES (Data Ingestion) ← YOU ARE HERE
├─▶ Talent Flow Spoke (04.01.02.04.20000.###)
│   └── Executive movements, hiring signals, departures
│   └── Triggers: BIT events for role changes
│
├─▶ Renewal Spoke (04.01.02.04.30000.###)
│   └── Contract expiration windows
│
└─▶ Compliance Spoke (04.01.02.04.40000.###)
    └── DOL violations, regulatory events

AXLE (BIT — Buyer Intent Tool)
└─▶ Converts spoke data → BIT events → Intent scores
    ├── Rule engine (configurable weights)
    ├── Event aggregation (multiple signals)
    └── Score calculation (0-100 scale)

WHEEL (Lead Cycles)
└─▶ Outreach automation based on BIT scores
    ├── High intent (80-100): Immediate outreach
    ├── Medium intent (50-79): Nurture campaign
    └── Low intent (0-49): Monitor only
```

For full details on strategic positioning, ROI calculation, and business value, see:
- **Migration File**: `infra/migrations/2025-11-10-talent-flow.sql`
- **Related Doctrine**: `doctrine/ple/BIT-Doctrine.md`
- **Verification**: `infra/VERIFICATION_QUERIES.sql` (Section 11)

---

## 📂 CATEGORY — 20,000 ft Altitude

### Data Model & Schema Design

#### Primary Entity: `svg_marketing.talent_flow_movements`

**Barton ID Format**: `04.01.02.04.20000.###`

**Key Fields**:
- `movement_id` — Primary key (Barton ID)
- `company_unique_id` — FK to marketing.company_master
- `person_unique_id` — FK to marketing.people_master
- `movement_type` — hire, departure, promotion, role_change, backfill
- `position_level` — C-suite, VP, Director, Senior Manager
- `confidence_score` — 0.00-1.00 detection confidence
- `bit_event_created` — Trigger status flag
- `bit_event_id` — Reference to bit.events

#### Movement Type Taxonomy

| Movement Type | Weight | BIT Rule |
|---------------|--------|----------|
| hire (C-suite) | 25 | executive_movement |
| departure (C-suite) | 20 | executive_departure |
| hire (VP) | 15 | vp_hire |
| promotion | 10 | internal_promotion |
| role_change | 15 | executive_role_change |
| backfill | 18 | executive_backfill |

#### Spoke-to-Axle Integration

**Trigger**: `trg_talent_flow_to_bit`
**Function**: `fn_insert_bit_event()`

**Logic Flow**:
1. Movement inserted/updated → Trigger fires
2. Check idempotency (`bit_event_created = false`)
3. Validate confidence (≥0.80) OR verification (`verified`)
4. Map movement_type + position_level → BIT rule
5. Insert event into `bit.events`
6. Update movement with `bit_event_id` and `processed_at`

---

## ⚙️ EXECUTION — 10,000 ft Altitude

### Quick Start

```bash
# 1. Run migration
psql $DATABASE_URL -f infra/migrations/2025-11-10-talent-flow.sql

# 2. Verify installation
psql $DATABASE_URL -f infra/VERIFICATION_QUERIES.sql

# 3. Test movement insertion
psql $DATABASE_URL -c "
INSERT INTO svg_marketing.talent_flow_movements (
    company_unique_id, movement_type, position_title, position_level,
    movement_date, detection_source, confidence_score, verification_status
)
VALUES (
    '04.04.01.01.00001.001', 'hire', 'Chief Financial Officer', 'C-suite',
    CURRENT_DATE, 'linkedin_enrichment', 0.95, 'verified'
);
"

# 4. Verify BIT event created
psql $DATABASE_URL -c "
SELECT tfm.movement_id, e.event_id, r.rule_name, r.weight
FROM svg_marketing.talent_flow_movements tfm
JOIN bit.events e ON tfm.bit_event_id = e.event_id
JOIN bit.rule_reference r ON e.rule_id = r.rule_id
WHERE tfm.company_unique_id = '04.04.01.01.00001.001';
"
```

### Analytics View

**vw_talent_flow_summary** — Dashboard-ready metrics

```sql
SELECT * FROM svg_marketing.vw_talent_flow_summary
WHERE total_movements > 0
ORDER BY most_recent_movement_date DESC
LIMIT 20;
```

**Key Metrics**:
- Total movements by type (hire, departure, promotion)
- BIT event creation rate %
- Churn risk level (high_churn_risk, moderate_churn_risk, stable)
- Detection source breakdown
- Average confidence score

---

## 🔧 OPS — 5,000 ft Altitude

### Daily Monitoring

**Morning Checklist** (9:00 AM)
```sql
-- 1. Review overnight movements
SELECT COUNT(*) FROM svg_marketing.talent_flow_movements
WHERE detected_at >= CURRENT_DATE;

-- 2. Check BIT creation rate
SELECT
    COUNT(*) AS total,
    COUNT(*) FILTER (WHERE bit_event_created) AS bit_events,
    ROUND(100.0 * COUNT(*) FILTER (WHERE bit_event_created) / COUNT(*), 1) AS rate_pct
FROM svg_marketing.talent_flow_movements
WHERE detected_at >= CURRENT_DATE;
-- Expected: rate_pct >= 70%

-- 3. High-priority alerts
SELECT * FROM svg_marketing.vw_talent_flow_summary
WHERE churn_risk_level = 'high_churn_risk'
ORDER BY most_recent_movement_date DESC;
```

### Error Handling

**Issue: BIT Event Not Created**

```sql
-- Diagnosis
SELECT movement_id, confidence_score, verification_status
FROM svg_marketing.talent_flow_movements
WHERE bit_event_created = false
LIMIT 10;

-- Resolution 1: Verify movement
UPDATE svg_marketing.talent_flow_movements
SET verification_status = 'verified'
WHERE movement_id = '04.01.02.04.20000.###';

-- Resolution 2: Increase confidence
UPDATE svg_marketing.talent_flow_movements
SET confidence_score = 0.90
WHERE movement_id = '04.01.02.04.20000.###';
```

### Performance Optimization

**Index Usage Analysis**
```sql
SELECT indexname, idx_scan, idx_tup_read
FROM pg_stat_user_indexes
WHERE schemaname = 'svg_marketing'
  AND tablename = 'talent_flow_movements'
ORDER BY idx_scan DESC;
```

### Cross-References

**Related BIT Rules**:
- See `infra/migrations/2025-11-10-talent-flow.sql` lines 385-455

**Related BIT Events**:
- Query: `SELECT * FROM bit.events WHERE detection_source = 'talent_flow_spoke';`

**Related Dashboards**:
- Grafana: Recent Executive Movements panel
- Lovable.dev: Talent Flow Summary widget

---

## 📚 Appendix

### Barton Audit Log

```sql
SELECT * FROM shq.audit_log
WHERE audit_id = '04.01.02.04.20000.001';
```

### Version History

| Version | Date | Changes |
|---------|------|---------|
| 2.0.0 | 2025-11-10 | Complete rewrite for svg_marketing schema migration |
| 1.0.0 | 2025-11-07 | Initial version (legacy people.contact schema) |

### Related Files

- `infra/migrations/2025-11-10-talent-flow.sql` — Schema migration
- `infra/VERIFICATION_QUERIES.sql` (Section 11) — Verification queries
- `doctrine/ple/BIT-Doctrine.md` — BIT Axle documentation

---

**End of Talent Flow Doctrine**
