"""
Talent Flow Input Layer
=======================

Fetches person records from People Intelligence hub for movement detection.

Doctrine:
    - Spoke is I/O only - no logic, no state
    - Reads from company_people spoke output
    - Requires company_unique_id (CLGate enforced)
"""

from dataclasses import dataclass
from typing import List, Optional
from datetime import datetime
import uuid


@dataclass
class PersonRecord:
    """Person record for movement tracking."""
    company_unique_id: uuid.UUID
    person_id: uuid.UUID
    name: str
    linkedin_url: Optional[str]
    current_company: Optional[str]
    current_title: Optional[str]
    last_seen_at: datetime
    previous_company: Optional[str] = None
    previous_title: Optional[str] = None
    

class PersonRecordFetcher:
    """
    Fetches person records from People Intelligence for movement detection.
    
    Doctrine Compliance:
        - I/O only - no business logic
        - Requires company_unique_id (CLGate enforced upstream)
        - Returns raw data for middle layer processing
    """
    
    def __init__(self, db_connection):
        """
        Initialize the fetcher.
        
        Args:
            db_connection: Neon database connection
        """
        self.db = db_connection
    
    def fetch_by_company(self, company_unique_id: uuid.UUID) -> List[PersonRecord]:
        """
        Fetch all person records for a company.
        
        Args:
            company_unique_id: The CL-provided company identifier
            
        Returns:
            List of PersonRecord objects
        """
        # This would query the people-intelligence output
        # For now, return empty list as scaffold
        return []
    
    def fetch_with_history(self, company_unique_id: uuid.UUID) -> List[PersonRecord]:
        """
        Fetch person records with job history for movement detection.
        
        Args:
            company_unique_id: The CL-provided company identifier
            
        Returns:
            List of PersonRecord objects with previous position data
        """
        # This would query people-intelligence with historical data
        # For now, return empty list as scaffold
        return []


__all__ = ['PersonRecord', 'PersonRecordFetcher']
