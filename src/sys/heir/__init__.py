# HEIR+ORBT Identity and Process Tracking
#
# DOCTRINE: Every operation MUST have:
# 1. unique_id (HEIR) - For identity tracing
# 2. process_id (ORBT) - For process lifecycle
#
# Usage:
#     from src.sys.heir import track_operation, generate_unique_id, generate_process_id
#
#     # Full tracking
#     with track_operation("my_pipeline") as ctx:
#         do_work(unique_id=ctx.unique_id, process_id=ctx.process_id)
#
#     # Just unique_id
#     unique_id = generate_unique_id()
#
#     # Just process_id
#     process_id = generate_process_id()

# HEIR Identity
from .heir_identity import (
    HeirIdentity,
    HeirId,
    HeirMode,
    HeirFormat,
    HeirContext,
    get_heir,
    generate_unique_id,
    get_current_unique_id,
    require_unique_id,
    with_heir_id,
)

# ORBT Process
from .orbt_process import (
    OrbtProcess,
    ProcessId,
    OrbtLayer,
    ProcessStatus,
    get_orbt,
    generate_process_id,
    get_current_process_id,
    require_process_id,
    log_operation,
    end_current_process,
    with_process,
)

# Unified Tracking
from .tracking import (
    Tracker,
    TrackingContext,
    get_tracker,
    get_tracking_context,
    require_tracking_context,
    track_operation,
    tracked,
)

__all__ = [
    # HEIR Identity
    "HeirIdentity",
    "HeirId",
    "HeirMode",
    "HeirFormat",
    "HeirContext",
    "get_heir",
    "generate_unique_id",
    "get_current_unique_id",
    "require_unique_id",
    "with_heir_id",
    # ORBT Process
    "OrbtProcess",
    "ProcessId",
    "OrbtLayer",
    "ProcessStatus",
    "get_orbt",
    "generate_process_id",
    "get_current_process_id",
    "require_process_id",
    "log_operation",
    "end_current_process",
    "with_process",
    # Unified Tracking
    "Tracker",
    "TrackingContext",
    "get_tracker",
    "get_tracking_context",
    "require_tracking_context",
    "track_operation",
    "tracked",
]
