"""
Gates Module - Barton Toolbox Hub

Pipeline gates that control flow between phases.

Available Gates:
- SlotCompletionGate: 3/3 slot completion check (CEO, CFO, HR)

Usage:
    from backend.gates import SlotCompletionGate

    gate = SlotCompletionGate()
    result = gate.check_company(company_id)

    if result.passed:
        proceed_to_outreach()
    else:
        enrich_missing_slots(result.missing_slots)
"""

from .slot_completion_gate import (
    SlotCompletionGate,
    GateStatus,
    GateResult,
    SlotStatus,
    check_slot_completion,
    get_companies_needing_enrichment,
    REQUIRED_SLOTS,
    SLOT_MESSAGING_TEMPLATES
)

__all__ = [
    'SlotCompletionGate',
    'GateStatus',
    'GateResult',
    'SlotStatus',
    'check_slot_completion',
    'get_companies_needing_enrichment',
    'REQUIRED_SLOTS',
    'SLOT_MESSAGING_TEMPLATES'
]
