#!/usr/bin/env python3
"""
Build Complete Column Registry — Every column in every non-archive table gets:
  - column_unique_id (schema.table.column)
  - description
  - semantic_role (identifier | foreign_key | attribute | metric)
  - format (UUID | STRING | EMAIL | ENUM | BOOLEAN | INTEGER | NUMERIC | ISO-8601 | JSONB | ARRAY)

Sources (in priority order):
  1. dol.column_metadata (1,081 DOL filing columns)
  2. outreach.column_registry (48 outreach columns)
  3. enrichment.column_registry (53 enrichment columns)
  4. column_registry.yml (55 sub-hub core columns)
  5. Pattern-based inference for everything else

Output:
  docs/COLUMN_REGISTRY_COMPLETE.md — Human-readable reference
  column_registry_complete.yml — Machine-readable YAML

Usage:
    doppler run -- python scripts/build_column_registry.py
"""

import os
import re
import sys
import yaml
import psycopg2
from collections import defaultdict, OrderedDict

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")


def get_connection():
    return psycopg2.connect(
        host=os.environ["NEON_HOST"],
        dbname=os.environ["NEON_DATABASE"],
        user=os.environ["NEON_USER"],
        password=os.environ["NEON_PASSWORD"],
        sslmode="require",
    )


# ═══════════════════════════════════════════════════════════════════
# PATTERN-BASED INFERENCE
# ═══════════════════════════════════════════════════════════════════

def infer_semantic_role(col_name, col_type):
    """Infer semantic_role from column name and type."""
    name = col_name.lower()

    # Identifiers
    if name in ("id", "unique_id", "person_id", "slot_id", "blog_id",
                "error_id", "log_id", "candidate_id", "domain_id",
                "movement_id", "target_id", "registry_id", "record_id",
                "event_id", "batch_id", "run_id"):
        return "identifier"
    if name.endswith("_id") and name in (
        "sovereign_company_id", "company_unique_id", "sovereign_id",
        "outreach_id", "coverage_id", "service_agent_id",
        "person_unique_id", "company_slot_unique_id",
        "parent_company_id", "source_record_id",
    ):
        if "outreach" in name or "sovereign" in name or "company" in name or "person" in name or "slot" in name or "coverage" in name or "service_agent" in name:
            return "foreign_key"
    if name.endswith("_id") and ("fk" in name or "ref" in name):
        return "foreign_key"
    if name == "outreach_id":
        return "foreign_key"
    if name == "sovereign_id":
        return "foreign_key"
    if name in ("company_unique_id", "person_unique_id", "company_slot_unique_id"):
        return "foreign_key"
    if name.endswith("_id") and name not in ("barton_id",):
        # Most _id columns are either identifiers or FKs
        # If it's the first column, likely identifier; otherwise FK
        return "identifier"

    # Metrics
    if any(name.startswith(p) for p in ("count_", "total_", "num_", "pct_", "rate_")):
        return "metric"
    if any(name.endswith(s) for s in ("_count", "_total", "_rate", "_score", "_pct",
                                       "_amount", "_magnitude", "_confidence")):
        return "metric"
    if name in ("confidence_score", "name_match_score", "bit_score",
                "domain_name_confidence", "n_live_tup", "row_count"):
        return "metric"

    # Everything else is attribute
    return "attribute"


def infer_format(col_name, col_type):
    """Infer format from column name and SQL type."""
    name = col_name.lower()
    dtype = col_type.lower()

    if "uuid" in dtype:
        return "UUID"
    if "timestamp" in dtype:
        return "ISO-8601"
    if "boolean" in dtype:
        return "BOOLEAN"
    if "jsonb" in dtype or "json" in dtype:
        return "JSONB"
    if "array" in dtype:
        return "ARRAY"
    if "integer" in dtype or "bigint" in dtype or "smallint" in dtype:
        return "INTEGER"
    if "numeric" in dtype or "double" in dtype or "real" in dtype or "decimal" in dtype:
        return "NUMERIC"
    if "date" in dtype and "timestamp" not in dtype:
        return "DATE"

    # Text columns — infer from name
    if "email" in name and "email" != name:
        return "EMAIL"
    if name == "email":
        return "EMAIL"
    if "_url" in name or name.endswith("_url") or name == "url":
        return "URL"
    if name.endswith("_enum") or name in ("status", "state", "phase_status",
                                           "leaf_type", "slot_type", "source_type",
                                           "error_type", "funding_type", "retry_strategy",
                                           "error_stage", "verification_status",
                                           "domain_health"):
        return "ENUM"

    return "STRING"


def infer_description(schema, table, col_name, col_type):
    """Generate a description from column name, table context, and type."""
    name = col_name.lower()
    tbl = table.lower()

    # ── Universal patterns ──

    # Timestamps
    if name == "created_at":
        return "When this record was created"
    if name == "updated_at":
        return "When this record was last updated"
    if name == "archived_at":
        return "When this record was archived"
    if name == "resolved_at":
        return "When this error/issue was resolved"
    if name == "filled_at":
        return "When this slot was filled with a person"
    if name == "checked_at":
        return "When this record was last checked/verified"
    if name == "verified_at":
        return "When verification was completed"
    if name == "deleted_at":
        return "When this record was soft-deleted"
    if name == "expired_at" or name == "expires_at":
        return "When this record expires"
    if name == "last_extracted_at":
        return "When data was last extracted/scraped"
    if name == "detected_at":
        return "When this event/signal was detected"
    if name == "requested_at":
        return "When this request was made"
    if name.endswith("_at") and "timestamp" in col_type.lower():
        return f"Timestamp for {name.replace('_at', '').replace('_', ' ')} event"

    # Common FKs
    if name == "outreach_id":
        return "FK to outreach.outreach spine table (universal join key)"
    if name == "sovereign_id" or name == "sovereign_company_id":
        return "FK to cl.company_identity (sovereign company identifier)"
    if name == "company_unique_id":
        return "FK to cl.company_identity or Barton company ID"
    if name == "person_unique_id":
        return "FK to people.people_master.unique_id (Barton person ID)"
    if name == "company_slot_unique_id":
        return "FK to people.company_slot.slot_id"
    if name == "coverage_id":
        return "FK to coverage.service_agent_coverage"
    if name == "service_agent_id":
        return "FK to coverage.service_agent"
    if name == "error_id":
        return "Primary key for this error record"
    if name == "slot_id":
        return "Primary key for this company slot record"
    if name == "blog_id":
        return "Primary key for this blog record"
    if name == "log_id":
        return "Primary key for this log entry"
    if name == "candidate_id":
        return "Primary key for this candidate record"
    if name == "domain_id":
        return "Primary key for this domain record"
    if name == "movement_id":
        return "Primary key for this movement event"
    if name == "target_id":
        return "Primary key for this target record"

    # Common identifiers
    if name == "unique_id":
        return "Primary identifier for this record (Barton ID format)"
    if name == "ein":
        return "Employer Identification Number (9-digit, no dashes)"
    if name == "domain":
        return "Company website domain (lowercase, no protocol)"
    if name == "barton_id":
        return "Barton hierarchical identifier"

    # Common attributes
    if name == "company_name":
        return "Company legal or common name"
    if name == "first_name":
        return "Person first name"
    if name == "last_name":
        return "Person last name"
    if name == "email":
        return "Email address"
    if name == "phone" or name == "phone_number" or name == "work_phone_e164":
        return "Phone number (E.164 format preferred)"
    if name == "title" or name == "job_title":
        return "Job title or position"
    if name == "linkedin_url":
        return "LinkedIn profile URL"
    if name == "linkedin_company_url":
        return "LinkedIn company page URL"
    if name == "website_url":
        return "Company website URL"
    if name == "source_system":
        return "System that originated this record"
    if name == "source":
        return "Data source identifier"
    if name == "status":
        return "Current status of this record"
    if name == "state" or name == "state_id" or name == "state_code":
        return "US state code (2-letter)"
    if name == "city":
        return "City name"
    if name == "zip" or name == "zip_code" or name == "postal_code":
        return "ZIP/postal code (5-digit)"
    if name == "country":
        return "Country name or code"
    if name == "address" or name.endswith("_address"):
        return f"{'Mailing a' if name == 'address' else 'A'}ddress"

    # Slot-specific
    if name == "slot_type":
        return "Executive role type (CEO, CFO, HR, CTO, CMO, COO)"
    if name == "is_filled":
        return "Whether this slot has an assigned person"
    if name == "slot_phone":
        return "Phone number stored on the slot"
    if name == "slot_phone_source":
        return "Source of the slot phone number"
    if name == "slot_phone_updated_at":
        return "When slot phone was last updated"

    # Blog-specific
    if name == "about_url":
        return "Company About Us page URL"
    if name == "news_url":
        return "Company news/press page URL"
    if name == "source_url":
        return "URL of the content source"
    if name == "context_summary":
        return "Summary of blog/content context"
    if name == "extraction_method":
        return "Method used to extract content (sitemap, crawl, etc.)"

    # DOL-specific
    if name == "filing_present":
        return "Whether a Form 5500 filing exists for this EIN"
    if name == "funding_type":
        return "Benefit funding classification (pension_only, fully_insured, self_funded)"
    if name == "renewal_month":
        return "Plan year begin month (1-12)"
    if name == "outreach_start_month":
        return "5 months before renewal month (1-12)"
    if name == "carrier":
        return "Insurance carrier name from Schedule A"
    if name == "broker_or_advisor":
        return "Broker/advisor name from Schedule C code 28"

    # Error table patterns
    if name == "error_type":
        return "Discriminator column classifying the error type"
    if name == "error_message":
        return "Human-readable error description"
    if name == "error_stage":
        return "Pipeline stage where error occurred"
    if name == "retry_strategy":
        return "How to handle retry (manual_fix, auto_retry, discard)"
    if name == "retry_count":
        return "Number of retry attempts so far"
    if name == "retry_ceiling":
        return "Maximum number of retries allowed"
    if name == "retry_after":
        return "Earliest time to retry"

    # Verification
    if name == "email_verified":
        return "Whether email was verified via Million Verifier"
    if name == "outreach_ready":
        return "Whether email is safe to send outreach (TRUE = VALID verified)"
    if name == "verification_status":
        return "Current verification status"
    if name == "verification_error":
        return "Error message from verification attempt"

    # Score/metric patterns
    if name == "confidence_score" or name == "confidence":
        return "Confidence score (0-100)"
    if name == "bit_score":
        return "BIT/CLS authorization score"
    if name.endswith("_score"):
        label = name.replace("_score", "").replace("_", " ")
        return f"{label.title()} score"
    if name.endswith("_count"):
        label = name.replace("_count", "").replace("_", " ")
        return f"Count of {label}"

    # Boolean patterns
    if name.startswith("is_") or name.startswith("has_"):
        label = name.replace("is_", "").replace("has_", "").replace("_", " ")
        return f"Whether this record {label}"
    if name.startswith("mx_"):
        return f"MX record {'status' if name == 'mx_present' else name.replace('mx_', '')}"

    # URL patterns
    if name.endswith("_url"):
        label = name.replace("_url", "").replace("_", " ")
        return f"{label.title()} URL"

    # Archive patterns
    if name == "archive_reason":
        return "Reason this record was archived"
    if name == "final_outcome":
        return "Final outcome after processing"
    if name == "final_reason":
        return "Reason for final outcome"

    # Audit patterns
    if name == "correlation_id":
        return "UUID linking related operations across tables"
    if name.endswith("_run_id"):
        label = name.replace("_run_id", "").replace("_", " ")
        return f"Run identifier for {label} batch"
    if name == "event_type":
        return "Type of audit/system event"
    if name == "event_source":
        return "System or process that generated this event"
    if name == "details":
        return "Event details (JSON)"
    if name == "notes":
        return "Human-readable notes"

    # Coverage
    if name == "anchor_zip":
        return "Center ZIP code for this market radius"
    if name == "radius_miles":
        return "Radius in miles from anchor ZIP"

    # Agent
    if name == "agent_number":
        return "Service agent identifier (SA-NNN format)"
    if name == "agent_name":
        return "Service agent display name"

    # Catch-all: generate from column name
    label = name.replace("_", " ")
    return f"{label.title()}"


def sql_type_to_format(sql_type):
    """Map SQL type string to format label."""
    t = sql_type.lower()
    if "uuid" in t:
        return "UUID"
    if "timestamp" in t:
        return "ISO-8601"
    if "boolean" in t:
        return "BOOLEAN"
    if "jsonb" in t:
        return "JSONB"
    if "json" in t:
        return "JSON"
    if "array" in t:
        return "ARRAY"
    if "integer" in t or "bigint" in t or "smallint" in t or "serial" in t:
        return "INTEGER"
    if "numeric" in t or "double" in t or "real" in t or "decimal" in t:
        return "NUMERIC"
    if "date" in t and "timestamp" not in t:
        return "DATE"
    if "text" in t or "character" in t or "varchar" in t:
        return "STRING"
    if "user-defined" in t:
        return "ENUM"
    return "STRING"


# ===================================================================
# TABLE -> HUB/SUB-HUB OWNERSHIP
# ===================================================================
# From REGISTRY.yaml + hub manifests + CLAUDE.md hub registry.
# Format: "schema.table" -> ("hub_id", "hub_name")

TABLE_HUB_MAP = {
    # -- CL (PARENT) --
    "cl.company_identity":             ("CL",      "CL Authority Registry"),
    "cl.company_identity_archive":     ("CL",      "CL Authority Registry"),
    "cl.company_identity_excluded":    ("CL",      "CL Authority Registry"),
    "cl.company_identity_bridge":      ("CL",      "CL Authority Registry"),
    "cl.company_domains":              ("CL",      "CL Authority Registry"),
    "cl.company_domains_archive":      ("CL",      "CL Authority Registry"),
    "cl.company_domains_excluded":     ("CL",      "CL Authority Registry"),
    "cl.company_names":                ("CL",      "CL Authority Registry"),
    "cl.company_names_archive":        ("CL",      "CL Authority Registry"),
    "cl.company_names_excluded":       ("CL",      "CL Authority Registry"),
    "cl.domain_hierarchy":             ("CL",      "CL Authority Registry"),
    "cl.domain_hierarchy_archive":     ("CL",      "CL Authority Registry"),
    "cl.identity_confidence":          ("CL",      "CL Authority Registry"),
    "cl.identity_confidence_archive":  ("CL",      "CL Authority Registry"),
    "cl.identity_confidence_excluded": ("CL",      "CL Authority Registry"),
    "cl.company_candidate":            ("CL",      "CL Authority Registry"),
    "cl.cl_err_existence":             ("CL",      "CL Authority Registry"),
    "cl.cl_errors_archive":            ("CL",      "CL Authority Registry"),
    "cl.movement_code_registry":       ("CL",      "CL Authority Registry"),
    "cl.sovereign_mint_backup_20260218": ("CL",    "CL Authority Registry"),
    # -- Outreach Spine (04.04) --
    "outreach.outreach":               ("04.04",   "Outreach Spine"),
    "outreach.outreach_archive":       ("04.04",   "Outreach Spine"),
    "outreach.outreach_errors":        ("04.04",   "Outreach Spine"),
    "outreach.outreach_excluded":      ("04.04",   "Outreach Spine"),
    "outreach.outreach_legacy_quarantine": ("04.04","Outreach Spine"),
    "outreach.outreach_orphan_archive":("04.04",   "Outreach Spine"),
    "outreach.hub_registry":           ("04.04",   "Outreach Spine"),
    "outreach.column_registry":        ("04.04",   "Outreach Spine"),
    "outreach.manual_overrides":       ("04.04",   "Outreach Spine"),
    "outreach.override_audit_log":     ("04.04",   "Outreach Spine"),
    "outreach.pipeline_audit_log":     ("04.04",   "Outreach Spine"),
    "outreach.ctb_audit_log":          ("04.04",   "Outreach Spine"),
    "outreach.ctb_queue":              ("04.04",   "Outreach Spine"),
    "outreach.entity_resolution_queue":("04.04",   "Outreach Spine"),
    "outreach.mv_credit_usage":        ("04.04",   "Outreach Spine"),
    "outreach.engagement_events":      ("04.04",   "Outreach Spine"),
    # -- Company Target (04.04.01) --
    "outreach.company_target":         ("04.04.01","Company Target"),
    "outreach.company_target_archive": ("04.04.01","Company Target"),
    "outreach.company_target_errors":  ("04.04.01","Company Target"),
    "outreach.company_target_errors_archive": ("04.04.01","Company Target"),
    "outreach.company_target_orphaned_archive": ("04.04.01","Company Target"),
    "outreach.company_target_dead_ends":("04.04.01","Company Target"),
    "outreach.company_hub_status":     ("04.04.01","Company Target"),
    "outreach.url_discovery_failures": ("04.04.01","Company Target"),
    "outreach.url_discovery_failures_archive": ("04.04.01","Company Target"),
    # -- People Intelligence (04.04.02) --
    "people.company_slot":             ("04.04.02","People Intelligence"),
    "people.company_slot_archive":     ("04.04.02","People Intelligence"),
    "people.people_master":            ("04.04.02","People Intelligence"),
    "people.people_master_archive":    ("04.04.02","People Intelligence"),
    "people.people_errors":            ("04.04.02","People Intelligence"),
    "people.people_errors_archive":    ("04.04.02","People Intelligence"),
    "people.people_invalid":           ("04.04.02","People Intelligence"),
    "people.people_sidecar":           ("04.04.02","People Intelligence"),
    "people.person_scores":            ("04.04.02","People Intelligence"),
    "people.pressure_signals":         ("04.04.02","People Intelligence"),
    "people.slot_ingress_control":     ("04.04.02","People Intelligence"),
    "people.title_slot_mapping":       ("04.04.02","People Intelligence"),
    "people.slot_assignment_history":  ("04.04.02","People Intelligence"),
    "people.company_resolution_log":   ("04.04.02","People Intelligence"),
    "people.people_promotion_audit":   ("04.04.02","People Intelligence"),
    "people.people_resolution_history":("04.04.02","People Intelligence"),
    "people.people_resolution_queue":  ("04.04.02","People Intelligence"),
    "people.paid_enrichment_queue":    ("04.04.02","People Intelligence"),
    "people.person_movement_history":  ("04.04.02","People Intelligence"),
    "people.slot_orphan_snapshot_r0_002": ("04.04.02","People Intelligence"),
    "people.slot_quarantine_r0_002":   ("04.04.02","People Intelligence"),
    "outreach.people":                 ("04.04.02","People Intelligence"),
    "outreach.people_archive":         ("04.04.02","People Intelligence"),
    "outreach.people_errors":          ("04.04.02","People Intelligence"),
    # -- DOL Filings (04.04.03) --
    "outreach.dol":                    ("04.04.03","DOL Filings"),
    "outreach.dol_archive":            ("04.04.03","DOL Filings"),
    "outreach.dol_errors":             ("04.04.03","DOL Filings"),
    "outreach.dol_errors_archive":     ("04.04.03","DOL Filings"),
    "outreach.dol_audit_log":          ("04.04.03","DOL Filings"),
    "outreach.dol_url_enrichment":     ("04.04.03","DOL Filings"),
    # -- BIT/CLS Authorization (04.04.04) --
    "outreach.bit_scores":             ("04.04.04","BIT/CLS Authorization"),
    "outreach.bit_scores_archive":     ("04.04.04","BIT/CLS Authorization"),
    "outreach.bit_errors":             ("04.04.04","BIT/CLS Authorization"),
    "outreach.bit_signals":            ("04.04.04","BIT/CLS Authorization"),
    "outreach.bit_input_history":      ("04.04.04","BIT/CLS Authorization"),
    "outreach.campaigns":              ("04.04.04","Outreach Execution (deprecated)"),
    "outreach.sequences":              ("04.04.04","Outreach Execution (deprecated)"),
    "outreach.send_log":               ("04.04.04","Outreach Execution (deprecated)"),
    # -- Blog Content (04.04.05) --
    "outreach.blog":                   ("04.04.05","Blog Content"),
    "outreach.blog_archive":           ("04.04.05","Blog Content"),
    "outreach.blog_errors":            ("04.04.05","Blog Content"),
    "outreach.blog_ingress_control":   ("04.04.05","Blog Content"),
    "outreach.blog_source_history":    ("04.04.05","Blog Content"),
    "outreach.sitemap_discovery":      ("04.04.05","Blog Content"),
    "outreach.source_urls":            ("04.04.05","Blog Content"),
    # -- Coverage (04.04.06) --
    "coverage.service_agent":          ("04.04.06","Coverage"),
    "coverage.service_agent_coverage": ("04.04.06","Coverage"),
    # -- Isolated Lanes --
    "sales.appointments_already_had":  ("LANE-A",  "Appointment Reactivation"),
    "outreach.appointments":           ("LANE-A",  "Appointment Reactivation"),
    "partners.fractional_cfo_master":  ("LANE-B",  "Fractional CFO Partners"),
    "partners.partner_appointments":   ("LANE-B",  "Fractional CFO Partners"),
}

# Schema-level defaults for tables not explicitly mapped
SCHEMA_HUB_DEFAULTS = {
    "cl":           ("CL",         "CL Authority Registry"),
    "dol":          ("04.04.03",   "DOL Filings"),
    "bit":          ("04.04.04",   "BIT/CLS Authorization"),
    "blog":         ("04.04.05",   "Blog Content"),
    "people":       ("04.04.02",   "People Intelligence"),
    "coverage":     ("04.04.06",   "Coverage"),
    "enrichment":   ("SYS",        "Enrichment (system)"),
    "intake":       ("SYS",        "Intake & Staging (system)"),
    "outreach_ctx": ("SYS",        "Outreach Context (system)"),
    "ref":          ("SYS",        "Reference Data (system)"),
    "reference":    ("SYS",        "Reference Data (system)"),
    "shq":          ("SYS",        "System Health (system)"),
    "catalog":      ("SYS",        "Catalog (system)"),
    "company":      ("DEPRECATED", "company schema (deprecated)"),
    "marketing":    ("DEPRECATED", "marketing schema (deprecated)"),
    "talent_flow":  ("DEPRECATED", "talent_flow schema (deprecated)"),
    "clnt":         ("FUTURE",     "Client Hub (future)"),
    "lcs":          ("FUTURE",     "Lifecycle Signals (future)"),
    "partners":     ("LANE-B",     "Fractional CFO Partners"),
    "sales":        ("LANE-A",     "Appointment Reactivation"),
    "archive":      ("ARCHIVE",    "Archive"),
}


def get_table_hub(schema, table):
    """Get (hub_id, hub_name) for a table."""
    key = f"{schema}.{table}"
    if key in TABLE_HUB_MAP:
        return TABLE_HUB_MAP[key]
    if schema in SCHEMA_HUB_DEFAULTS:
        return SCHEMA_HUB_DEFAULTS[schema]
    return ("UNMAPPED", "Unmapped")


def main():
    conn = get_connection()
    cur = conn.cursor()

    # ── 1. Pull existing descriptions from DB registries ──
    existing = {}  # schema.table.column -> {description, format, ...}

    # dol.column_metadata
    cur.execute("""
        SELECT table_name, column_name, column_id, description, category,
               data_type, format_pattern, is_pii
        FROM dol.column_metadata
    """)
    for tbl, col, uid, desc, cat, dtype, fmt, pii in cur.fetchall():
        key = f"dol.{tbl}.{col}"
        existing[key] = {
            "column_unique_id": uid or key,
            "description": desc or "",
            "semantic_role": "identifier" if cat == "identifier" else
                            "metric" if cat in ("amount", "count", "monetary") else
                            "attribute",
            "format": fmt or sql_type_to_format(dtype or ""),
            "source": "dol.column_metadata",
        }

    # outreach.column_registry
    cur.execute("""
        SELECT schema_name, table_name, column_name, column_unique_id,
               column_description, column_format, fk_reference
        FROM outreach.column_registry
    """)
    for schema, tbl, col, uid, desc, fmt, fk_ref in cur.fetchall():
        key = f"{schema}.{tbl}.{col}"
        existing[key] = {
            "column_unique_id": uid or key,
            "description": desc or "",
            "semantic_role": "foreign_key" if fk_ref else
                            "identifier" if col.endswith("_id") and not fk_ref else
                            "attribute",
            "format": fmt or "",
            "source": "outreach.column_registry",
        }

    # enrichment.column_registry
    cur.execute("""
        SELECT table_name, column_name, column_id, description,
               data_type, format_pattern
        FROM enrichment.column_registry
    """)
    for tbl, col, uid, desc, dtype, fmt in cur.fetchall():
        key = f"enrichment.{tbl}.{col}"
        existing[key] = {
            "column_unique_id": uid or key,
            "description": desc or "",
            "semantic_role": infer_semantic_role(col, dtype or ""),
            "format": fmt or sql_type_to_format(dtype or ""),
            "source": "enrichment.column_registry",
        }

    # column_registry.yml
    with open("column_registry.yml", "r", encoding="utf-8") as f:
        registry = yaml.safe_load(f)

    spine = registry.get("spine_table", {})
    spine_key = f"{spine['schema']}.{spine['name']}"
    for col in spine.get("columns", []):
        key = f"{spine_key}.{col['name']}"
        if key not in existing:
            existing[key] = {
                "column_unique_id": key,
                "description": col.get("description", ""),
                "semantic_role": col.get("semantic_role", ""),
                "format": col.get("format", ""),
                "source": "column_registry.yml",
            }

    for subhub in registry.get("subhubs", []):
        for tbl_def in subhub.get("tables", []):
            tbl_key = f"{tbl_def['schema']}.{tbl_def['name']}"
            for col in tbl_def.get("columns", []):
                key = f"{tbl_key}.{col['name']}"
                if key not in existing:
                    existing[key] = {
                        "column_unique_id": key,
                        "description": col.get("description", ""),
                        "semantic_role": col.get("semantic_role", ""),
                        "format": col.get("format", ""),
                        "source": "column_registry.yml",
                    }

    # ── 2. Pull all tables + columns from information_schema ──
    cur.execute("""
        SELECT t.table_schema, t.table_name,
               COALESCE(c.leaf_type, 'UNREGISTERED') AS leaf_type,
               COALESCE(c.is_frozen, FALSE) AS is_frozen,
               COALESCE(s.n_live_tup, 0) AS rows
        FROM information_schema.tables t
        LEFT JOIN ctb.table_registry c ON c.table_schema = t.table_schema AND c.table_name = t.table_name
        LEFT JOIN pg_stat_user_tables s ON s.schemaname = t.table_schema AND s.relname = t.table_name
        WHERE t.table_schema NOT IN ('pg_catalog','information_schema','pg_toast','public','ctb','archive')
          AND t.table_schema NOT LIKE 'pg_temp%%'
          AND t.table_schema NOT LIKE 'pg_toast_temp%%'
          AND t.table_type = 'BASE TABLE'
        ORDER BY t.table_schema, t.table_name
    """)
    tables = []
    for schema, tbl, leaf, frozen, rows in cur.fetchall():
        tables.append({
            "schema": schema, "table": tbl, "leaf": leaf,
            "frozen": frozen, "rows": int(rows),
        })

    cur.execute("""
        SELECT table_schema, table_name, column_name, data_type,
               is_nullable, column_default, character_maximum_length,
               ordinal_position
        FROM information_schema.columns
        WHERE table_schema NOT IN ('pg_catalog','information_schema','pg_toast','public','ctb','archive')
          AND table_schema NOT LIKE 'pg_temp%%'
          AND table_schema NOT LIKE 'pg_toast_temp%%'
        ORDER BY table_schema, table_name, ordinal_position
    """)
    all_columns = defaultdict(list)
    for schema, tbl, col, dtype, nullable, default, maxlen, pos in cur.fetchall():
        key = f"{schema}.{tbl}"
        dtype_str = dtype
        if maxlen:
            dtype_str = f"{dtype}({maxlen})"
        all_columns[key].append({
            "name": col, "type": dtype_str, "sql_type": dtype,
            "nullable": nullable == "YES",
            "default": str(default)[:60] if default else None,
        })

    conn.close()

    # ── 3. Build complete registry ──
    total_cols = 0
    from_existing = 0
    from_inferred = 0

    by_schema = defaultdict(list)
    for t in tables:
        by_schema[t["schema"]].append(t)

    # Build YAML structure
    yaml_data = []
    # Build markdown
    md_lines = []

    def w(s=""):
        md_lines.append(s)

    w("# COMPLETE COLUMN REGISTRY")
    w()
    w("> **Source**: Neon PostgreSQL + dol.column_metadata + outreach.column_registry + enrichment.column_registry + column_registry.yml + pattern inference")
    w(f"> **Generated**: 2026-02-20")
    w("> **Scope**: All non-archive tables (archive tables mirror source table schemas)")
    w("> **Regenerate**: `doppler run -- python scripts/build_column_registry.py`")
    w()
    w("**Every column has**: `column_unique_id` | `description` | `semantic_role` | `format`")
    w()

    # Group tables by hub, not by schema
    HUB_ORDER = [
        ("CL",         "CL Authority Registry (PARENT)"),
        ("04.04",      "Outreach Spine"),
        ("04.04.01",   "Company Target"),
        ("04.04.02",   "People Intelligence"),
        ("04.04.03",   "DOL Filings"),
        ("04.04.04",   "BIT/CLS Authorization"),
        ("04.04.05",   "Blog Content"),
        ("04.04.06",   "Coverage"),
        ("LANE-A",     "Appointment Reactivation (isolated lane)"),
        ("LANE-B",     "Fractional CFO Partners (isolated lane)"),
        ("SYS",        "System / Reference / Enrichment"),
        ("DEPRECATED", "DEPRECATED (legacy, do not use)"),
        ("FUTURE",     "Future Hubs (scaffolded, not active)"),
        ("UNMAPPED",   "Unmapped Tables"),
    ]

    # Assign every table to a hub
    by_hub = defaultdict(list)
    for t in tables:
        hub_id, hub_name = get_table_hub(t["schema"], t["table"])
        by_hub[hub_id].append(t)

    stats_from_db = 0
    stats_from_yml = 0
    stats_inferred = 0

    for hub_id, hub_label in HUB_ORDER:
        hub_tables = by_hub.get(hub_id, [])
        if not hub_tables:
            continue

        hub_tables = sorted(hub_tables, key=lambda x: (x["schema"], x["table"]))
        hub_rows = sum(t["rows"] for t in hub_tables)

        w("---")
        w()
        w(f"## `{hub_id}` {hub_label}")
        w()
        w(f"**Tables**: {len(hub_tables)} | **Total rows**: {hub_rows:,}")
        w()

        for t in hub_tables:
            tbl_key = f"{t['schema']}.{t['table']}"
            cols = all_columns.get(tbl_key, [])
            if not cols:
                continue

            frozen_tag = " FROZEN" if t["frozen"] else ""
            hub_id, hub_name = get_table_hub(t["schema"], t["table"])
            w(f"### `{tbl_key}` -- {t['leaf']}{frozen_tag} -- {t['rows']:,} rows")
            w()
            w(f"**Hub**: `{hub_id}` {hub_name}")
            w()
            w("| # | Column | Unique ID | Type | Null | Description | Role | Format | Source |")
            w("|---|--------|-----------|------|------|-------------|------|--------|--------|")

            tbl_yaml = {
                "schema": t["schema"],
                "table": t["table"],
                "leaf_type": t["leaf"],
                "frozen": t["frozen"],
                "rows": t["rows"],
                "hub_id": hub_id,
                "hub_name": hub_name,
                "columns": [],
            }

            for i, c in enumerate(cols, 1):
                col_key = f"{tbl_key}.{c['name']}"
                total_cols += 1

                if col_key in existing and existing[col_key].get("description"):
                    meta = existing[col_key]
                    desc = meta["description"]
                    role = meta.get("semantic_role") or infer_semantic_role(c["name"], c["type"])
                    fmt = meta.get("format") or infer_format(c["name"], c["type"])
                    uid = meta.get("column_unique_id", col_key)
                    src = meta.get("source", "db_registry")
                    if "dol" in src:
                        stats_from_db += 1
                    elif "outreach" in src:
                        stats_from_db += 1
                    elif "enrichment" in src:
                        stats_from_db += 1
                    else:
                        stats_from_yml += 1
                    from_existing += 1
                else:
                    desc = infer_description(t["schema"], t["table"], c["name"], c["type"])
                    role = infer_semantic_role(c["name"], c["type"])
                    fmt = infer_format(c["name"], c["type"])
                    uid = col_key
                    src = "inferred"
                    stats_inferred += 1
                    from_inferred += 1

                null_str = "Y" if c["nullable"] else "N"
                # Escape pipes in description
                desc_safe = desc.replace("|", "/")

                w(f"| {i} | `{c['name']}` | `{uid}` | {c['type']} | {null_str} | {desc_safe} | {role} | {fmt} | {src} |")

                tbl_yaml["columns"].append({
                    "name": c["name"],
                    "column_unique_id": uid,
                    "type": c["type"],
                    "nullable": c["nullable"],
                    "description": desc,
                    "semantic_role": role,
                    "format": fmt,
                    "source": src,
                })

            yaml_data.append(tbl_yaml)
            w()

    # Summary
    w("---")
    w()
    w("## Statistics")
    w()
    w(f"| Metric | Count |")
    w(f"|--------|-------|")
    w(f"| Total columns documented | {total_cols:,} |")
    w(f"| From DB registries (dol/outreach/enrichment) | {stats_from_db:,} |")
    w(f"| From column_registry.yml | {stats_from_yml:,} |")
    w(f"| Pattern-inferred | {stats_inferred:,} |")
    w()

    # Write markdown
    md_path = "docs/COLUMN_REGISTRY_COMPLETE.md"
    with open(md_path, "w", encoding="utf-8") as f:
        f.write("\n".join(md_lines))

    # Write YAML
    yml_path = "column_registry_complete.yml"
    with open(yml_path, "w", encoding="utf-8") as f:
        f.write("# COMPLETE COLUMN REGISTRY\n")
        f.write("# Generated: 2026-02-20\n")
        f.write("# Every non-archive column with unique_id, description, role, format\n")
        f.write(f"# Total columns: {total_cols}\n")
        f.write(f"# From DB registries: {stats_from_db}\n")
        f.write(f"# From column_registry.yml: {stats_from_yml}\n")
        f.write(f"# Pattern-inferred: {stats_inferred}\n\n")
        yaml.dump({"tables": yaml_data}, f, default_flow_style=False,
                   allow_unicode=True, sort_keys=False, width=200)

    print(f"\nWritten:")
    print(f"  {md_path}  (human-readable)")
    print(f"  {yml_path}  (machine-readable)")
    print(f"\n  Total columns: {total_cols:,}")
    print(f"  From DB registries: {stats_from_db:,}")
    print(f"  From column_registry.yml: {stats_from_yml:,}")
    print(f"  Pattern-inferred: {stats_inferred:,}")
    print(f"  Coverage: 100%")


if __name__ == "__main__":
    main()
