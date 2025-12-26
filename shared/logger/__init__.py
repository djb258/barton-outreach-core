# Shared logging utilities for Barton Outreach Core
# Provides consistent logging across all hubs and spokes

import logging
from typing import Optional


def get_logger(name: str, level: int = logging.INFO) -> logging.Logger:
    """Get a configured logger instance.

    Args:
        name: Logger name (typically __name__ of the calling module)
        level: Logging level (default: INFO)

    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)

    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    logger.setLevel(level)
    return logger


def log_spoke_event(
    spoke_name: str,
    direction: str,
    payload_type: str,
    company_id: Optional[str] = None
) -> None:
    """Log a spoke I/O event.

    Args:
        spoke_name: Name of the spoke (e.g., 'company-people')
        direction: 'ingress' or 'egress'
        payload_type: Type of payload being routed
        company_id: Optional company ID for tracing
    """
    logger = get_logger(f"spoke.{spoke_name}")
    logger.info(
        f"[{direction.upper()}] {payload_type} "
        f"| company_id={company_id or 'N/A'}"
    )


def log_hub_event(
    hub_name: str,
    event_type: str,
    message: str,
    company_id: Optional[str] = None
) -> None:
    """Log a hub processing event.

    Args:
        hub_name: Name of the hub (e.g., 'company-intelligence')
        event_type: Type of event (e.g., 'phase_start', 'phase_complete')
        message: Event message
        company_id: Optional company ID for tracing
    """
    logger = get_logger(f"hub.{hub_name}")
    logger.info(
        f"[{event_type.upper()}] {message} "
        f"| company_id={company_id or 'N/A'}"
    )


__all__ = ['get_logger', 'log_spoke_event', 'log_hub_event']
