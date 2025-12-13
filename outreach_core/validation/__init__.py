"""
Validation Module - Barton Outreach Core
=========================================

Standalone validation modules for company and people records.
Implements Barton Outreach Doctrine validation rules.
"""

from .company_validator import validate_company, validate_companies
from .people_validator import validate_person, validate_people

__all__ = [
    'validate_company',
    'validate_companies',
    'validate_person',
    'validate_people',
]
