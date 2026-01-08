"""
Blog Sub-Hub — Output Layer
═══════════════════════════════════════════════════════════════════════════

Signal emission and AIR logging.

Modules:
    - emit_bit_signal: BIT signal emission and logging
"""

from .emit_bit_signal import (
    emit_bit_signal,
    log_queued_article,
    log_dropped_article,
    EmissionResult,
    EmittedSignal,
    TerminalState,
)

__all__ = [
    'emit_bit_signal',
    'log_queued_article',
    'log_dropped_article',
    'EmissionResult',
    'EmittedSignal',
    'TerminalState',
]
