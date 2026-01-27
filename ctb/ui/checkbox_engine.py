"""
Checkbox Engine - Marketing Status API
======================================

DOCTRINE: This is the ONLY interface UI should use for marketing status.
          All reads go through vw_marketing_eligibility_with_overrides.
          All writes go through kill switch functions.

The checkbox engine provides:
1. Read-only status for any company (tier, completion, override status)
2. Bulk status queries for lists
3. Override management (disable, enable, cap tier)
4. Status change webhooks (future)

NO DIRECT VIEW ACCESS FROM UI - all queries through this engine.

============================================================================
⚠️  DO NOT WRITE - READ-ONLY MODULE
============================================================================
This module is READ-ONLY for sovereign tables:
- outreach.company_hub_status
- outreach.manual_overrides
- outreach.hub_registry

All mutations must go through:
- IMO middle layers (hub_status.py)
- SQL functions (set_marketing_override, remove_marketing_override)

Violation of this doctrine will trigger MutationGuardViolation.
============================================================================
"""

from dataclasses import dataclass, asdict
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from enum import IntEnum
import uuid
import logging

logger = logging.getLogger(__name__)


# ============================================================================
# MARKETING TIERS
# ============================================================================

class MarketingTier(IntEnum):
    """Marketing tier levels."""
    INELIGIBLE = -1  # Blocked or incomplete
    COLD = 0         # Company Target PASS only
    PERSONA = 1      # People Intelligence PASS
    TRIGGER = 2      # Talent Flow PASS  
    AGGRESSIVE = 3   # All hubs PASS + BIT >= 50


TIER_NAMES = {
    MarketingTier.INELIGIBLE: "INELIGIBLE",
    MarketingTier.COLD: "Cold Outreach",
    MarketingTier.PERSONA: "Persona-Aware",
    MarketingTier.TRIGGER: "Trigger-Based",
    MarketingTier.AGGRESSIVE: "Aggressive",
}


# ============================================================================
# DATA CLASSES
# ============================================================================

@dataclass
class CompanyStatus:
    """Complete marketing status for a company."""
    company_unique_id: uuid.UUID
    
    # Tier info
    effective_tier: int
    computed_tier: int
    tier_name: str
    tier_explanation: str
    next_tier_requirement: str
    
    # Completion status
    overall_status: str  # COMPLETE, BLOCKED, IN_PROGRESS
    
    # Hub statuses
    company_target_status: str
    dol_status: str
    people_status: str
    talent_flow_status: str
    
    # BIT gate
    bit_score: int
    bit_gate_status: str
    
    # Override info
    has_active_override: bool
    override_types: List[str]
    override_reasons: List[str]
    tier_cap: Optional[int]
    
    # Missing requirements (for incomplete companies)
    missing_requirements: Optional[List[Dict[str, Any]]]
    
    # Timestamp
    retrieved_at: datetime
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        result = asdict(self)
        result['company_unique_id'] = str(self.company_unique_id)
        result['retrieved_at'] = self.retrieved_at.isoformat()
        return result
    
    @property
    def is_marketable(self) -> bool:
        """Check if company can receive any marketing."""
        return self.effective_tier >= 0
    
    @property
    def is_complete(self) -> bool:
        """Check if all required hubs have passed."""
        return self.overall_status == 'COMPLETE'


@dataclass
class OverrideRequest:
    """Request to create an override."""
    company_unique_id: uuid.UUID
    override_type: str  # marketing_disabled, tier_cap, cooldown, legal_hold, customer_requested
    reason: str
    expires_at: Optional[datetime] = None
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class OverrideResult:
    """Result of an override operation."""
    success: bool
    override_id: Optional[uuid.UUID]
    message: str


# ============================================================================
# CHECKBOX ENGINE
# ============================================================================

class CheckboxEngine:
    """
    Marketing status engine for UI consumption.
    
    DOCTRINE COMPLIANCE:
        - Read-only queries through vw_marketing_eligibility_with_overrides
        - Writes ONLY through official kill switch functions
        - No direct table access
        - No logic duplication from views
    """
    
    def __init__(self, db_connection):
        """
        Initialize the checkbox engine.
        
        Args:
            db_connection: Neon database connection
        """
        self.db = db_connection
        self._cache = {}  # Simple in-memory cache
        self._cache_ttl = 60  # seconds
    
    # ========================================================================
    # STATUS QUERIES (READ-ONLY)
    # ========================================================================
    
    def get_status(self, company_unique_id: uuid.UUID) -> Optional[CompanyStatus]:
        """
        Get marketing status for a single company.
        
        Args:
            company_unique_id: The company to query
            
        Returns:
            CompanyStatus if found, None otherwise
        """
        # Check cache
        cache_key = str(company_unique_id)
        if cache_key in self._cache:
            cached, timestamp = self._cache[cache_key]
            if (datetime.utcnow() - timestamp).seconds < self._cache_ttl:
                return cached
        
        # Query the authoritative view
        query = """
            SELECT *
            FROM outreach.vw_marketing_eligibility_with_overrides
            WHERE company_unique_id = %s
        """
        
        cursor = self.db.cursor()
        cursor.execute(query, (company_unique_id,))
        row = cursor.fetchone()
        cursor.close()
        
        if not row:
            return None
        
        status = self._row_to_status(row)
        
        # Cache result
        self._cache[cache_key] = (status, datetime.utcnow())
        
        return status
    
    def get_statuses_bulk(
        self, 
        company_ids: List[uuid.UUID],
        tier_filter: Optional[int] = None
    ) -> List[CompanyStatus]:
        """
        Get marketing status for multiple companies.
        
        Args:
            company_ids: List of company IDs to query
            tier_filter: Optional filter for minimum tier
            
        Returns:
            List of CompanyStatus objects
        """
        if not company_ids:
            return []
        
        # Build query
        placeholders = ','.join(['%s'] * len(company_ids))
        query = f"""
            SELECT *
            FROM outreach.vw_marketing_eligibility_with_overrides
            WHERE company_unique_id IN ({placeholders})
        """
        
        if tier_filter is not None:
            query += f" AND effective_tier >= {int(tier_filter)}"
        
        cursor = self.db.cursor()
        cursor.execute(query, tuple(company_ids))
        rows = cursor.fetchall()
        cursor.close()
        
        return [self._row_to_status(row) for row in rows]
    
    def get_marketable_companies(
        self,
        min_tier: int = 0,
        limit: int = 100,
        offset: int = 0
    ) -> List[CompanyStatus]:
        """
        Get all marketable companies above a minimum tier.
        
        Args:
            min_tier: Minimum tier (default 0 = Cold)
            limit: Max results to return
            offset: Pagination offset
            
        Returns:
            List of CompanyStatus objects
        """
        query = """
            SELECT *
            FROM outreach.vw_marketing_eligibility_with_overrides
            WHERE effective_tier >= %s
            ORDER BY effective_tier DESC, bit_score DESC
            LIMIT %s OFFSET %s
        """
        
        cursor = self.db.cursor()
        cursor.execute(query, (min_tier, limit, offset))
        rows = cursor.fetchall()
        cursor.close()
        
        return [self._row_to_status(row) for row in rows]
    
    # ========================================================================
    # OVERRIDE MANAGEMENT (WRITES)
    # ========================================================================
    
    def disable_marketing(
        self,
        company_unique_id: uuid.UUID,
        reason: str,
        expires_in_days: Optional[int] = None
    ) -> OverrideResult:
        """
        Disable all marketing for a company.
        
        Args:
            company_unique_id: Company to disable
            reason: Reason for disabling
            expires_in_days: Optional TTL in days
            
        Returns:
            OverrideResult with success status
        """
        expires_at = None
        if expires_in_days:
            expires_at = datetime.utcnow() + timedelta(days=expires_in_days)
        
        try:
            cursor = self.db.cursor()
            cursor.execute(
                "SELECT outreach.fn_disable_marketing(%s, %s, %s)",
                (company_unique_id, reason, expires_at)
            )
            override_id = cursor.fetchone()[0]
            self.db.commit()
            cursor.close()
            
            # Invalidate cache
            self._invalidate_cache(company_unique_id)
            
            return OverrideResult(
                success=True,
                override_id=override_id,
                message=f"Marketing disabled for company {company_unique_id}"
            )
        except Exception as e:
            logger.error(f"Failed to disable marketing: {e}")
            return OverrideResult(
                success=False,
                override_id=None,
                message=str(e)
            )
    
    def enable_marketing(
        self,
        company_unique_id: uuid.UUID,
        reason: str = "Manually re-enabled"
    ) -> OverrideResult:
        """
        Re-enable marketing for a company.
        
        Args:
            company_unique_id: Company to enable
            reason: Reason for enabling
            
        Returns:
            OverrideResult with success status
        """
        try:
            cursor = self.db.cursor()
            cursor.execute(
                "SELECT outreach.fn_enable_marketing(%s, %s)",
                (company_unique_id, reason)
            )
            count = cursor.fetchone()[0]
            self.db.commit()
            cursor.close()
            
            # Invalidate cache
            self._invalidate_cache(company_unique_id)
            
            return OverrideResult(
                success=True,
                override_id=None,
                message=f"Deactivated {count} overrides for company {company_unique_id}"
            )
        except Exception as e:
            logger.error(f"Failed to enable marketing: {e}")
            return OverrideResult(
                success=False,
                override_id=None,
                message=str(e)
            )
    
    def set_tier_cap(
        self,
        company_unique_id: uuid.UUID,
        max_tier: int,
        reason: str,
        expires_in_days: Optional[int] = None
    ) -> OverrideResult:
        """
        Cap a company's marketing tier.
        
        Args:
            company_unique_id: Company to cap
            max_tier: Maximum tier (0-3)
            reason: Reason for capping
            expires_in_days: Optional TTL in days
            
        Returns:
            OverrideResult with success status
        """
        if max_tier < 0 or max_tier > 3:
            return OverrideResult(
                success=False,
                override_id=None,
                message=f"Invalid tier cap: {max_tier}. Must be 0-3."
            )
        
        expires_at = None
        if expires_in_days:
            expires_at = datetime.utcnow() + timedelta(days=expires_in_days)
        
        try:
            cursor = self.db.cursor()
            cursor.execute(
                "SELECT outreach.fn_set_tier_cap(%s, %s, %s, %s)",
                (company_unique_id, max_tier, reason, expires_at)
            )
            override_id = cursor.fetchone()[0]
            self.db.commit()
            cursor.close()
            
            # Invalidate cache
            self._invalidate_cache(company_unique_id)
            
            return OverrideResult(
                success=True,
                override_id=override_id,
                message=f"Tier cap set to {max_tier} for company {company_unique_id}"
            )
        except Exception as e:
            logger.error(f"Failed to set tier cap: {e}")
            return OverrideResult(
                success=False,
                override_id=None,
                message=str(e)
            )
    
    # ========================================================================
    # INTERNAL HELPERS
    # ========================================================================
    
    def _row_to_status(self, row: Dict[str, Any]) -> CompanyStatus:
        """Convert a database row to CompanyStatus."""
        return CompanyStatus(
            company_unique_id=row['company_unique_id'],
            effective_tier=row['effective_tier'],
            computed_tier=row['computed_tier'],
            tier_name=TIER_NAMES.get(row['effective_tier'], "Unknown"),
            tier_explanation=row['effective_tier_explanation'],
            next_tier_requirement=row['next_tier_requirement'],
            overall_status=row['overall_status'],
            company_target_status=row['company_target_status'],
            dol_status=row['dol_status'],
            people_status=row['people_status'],
            talent_flow_status=row['talent_flow_status'],
            bit_score=row['bit_score'],
            bit_gate_status=row['bit_gate_status'],
            has_active_override=row['has_active_override'],
            override_types=row['override_types'] or [],
            override_reasons=row['override_reasons'] or [],
            tier_cap=row['tier_cap'],
            missing_requirements=row['missing_requirements'],
            retrieved_at=datetime.utcnow()
        )
    
    def _invalidate_cache(self, company_unique_id: uuid.UUID) -> None:
        """Invalidate cache for a company."""
        cache_key = str(company_unique_id)
        if cache_key in self._cache:
            del self._cache[cache_key]


__all__ = [
    'MarketingTier',
    'TIER_NAMES',
    'CompanyStatus',
    'OverrideRequest',
    'OverrideResult',
    'CheckboxEngine',
]
