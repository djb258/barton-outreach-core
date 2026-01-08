"""
People Intelligence Hub - Email Generation
===========================================
Email GENERATION (People-owned).

- bulk_verifier.py: Verify emails in bulk

NOTE: Email PATTERN discovery belongs to Company Intelligence Hub.
      People generates actual emails using Company's pattern.
"""

from .bulk_verifier import BulkVerifier

__all__ = [
    'BulkVerifier',
]
