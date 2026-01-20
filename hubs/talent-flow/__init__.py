"""
Talent Flow Hub - Movement Detection
====================================

Tracks executive movements between companies to detect buying intent signals.

Architecture:
    ╔═══════════════════════════════════════════════════════════╗
    ║                    TALENT FLOW HUB                        ║
    ║                      (04.04.06)                           ║
    ╠═══════════════════════════════════════════════════════════╣
    ║  INPUT  │ Person records from People Intelligence          ║
    ║         │ LinkedIn profile data, job histories            ║
    ╠═════════╪═════════════════════════════════════════════════╣
    ║  MIDDLE │ Movement detection engine                       ║
    ║         │ - Compare current vs historical positions       ║
    ║         │ - Detect title changes                          ║
    ║         │ - Track company transitions                     ║
    ║         │ - Score movement significance                   ║
    ╠═════════╪═════════════════════════════════════════════════╣
    ║  OUTPUT │ Movement events → BIT Engine                    ║
    ║         │ Vacancy signals → Outreach Execution            ║
    ╚═════════╧═════════════════════════════════════════════════╝

Doctrine:
    - CL-Child: Consumes company_unique_id from Company Lifecycle
    - NEVER mints identity
    - Required hub: gates sovereign completion
    - Waterfall order: 4 (after People Intelligence)

Movement Types:
    - JOINED: Executive joined target company
    - LEFT: Executive left target company
    - TITLE_CHANGE: Executive changed titles (promotion/lateral)

Signal Values:
    - Executive joined: +10 BIT
    - Executive left: -5 BIT
    - Title change: +3 BIT
"""

from .imo import MovementDetector, MovementEvent

__all__ = ['MovementDetector', 'MovementEvent']
