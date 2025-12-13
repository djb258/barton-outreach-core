"""
Backblaze B2 Storage Integration for Validation Failures

This module provides integration with Backblaze B2 object storage for storing
validation failures. Replaces Google Sheets with a simpler, more scalable solution.

Key Features:
- Direct upload to B2 object storage
- No OAuth/authentication complexity
- Batch upload support
- Automatic file organization by date and type
- JSON and CSV export formats

Status: Production Ready
Date: 2025-11-18
"""

from .b2_client import B2Client
from .push_to_b2 import push_to_b2, push_company_failures, push_person_failures
from .push_to_b2_batched import push_to_b2_batched, push_company_failures_batched, push_person_failures_batched

__all__ = [
    'B2Client',
    'push_to_b2',
    'push_company_failures',
    'push_person_failures',
    'push_to_b2_batched',
    'push_company_failures_batched',
    'push_person_failures_batched'
]
