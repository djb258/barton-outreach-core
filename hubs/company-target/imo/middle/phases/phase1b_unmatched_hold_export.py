"""
Phase 1b: Unmatched Hold Export
===============================
Exports unmatched/ambiguous people to a HOLD CSV for later processing.

People who cannot be matched to a company during Phase 1 are staged here
rather than being enriched immediately. Once company enrichment completes
and domains are resolved, the pipeline is re-run with improved matching.

HOLD Reasons:
- no_match: No company match found
- low_confidence: Match score below threshold
- collision: Multiple ambiguous matches
- missing_data: Insufficient data for matching

DOCTRINE ENFORCEMENT:
- correlation_id is MANDATORY (FAIL HARD if missing)
"""

import time
from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List, Tuple
from datetime import datetime
from pathlib import Path
from enum import Enum
import pandas as pd
import json

# Doctrine enforcement imports
from ops.enforcement.correlation_id import validate_correlation_id, CorrelationIDError

from ..logging_config import (
    PipelineLogger,
    EventType,
    LogLevel,
    log_phase_start,
    log_phase_complete
)


class HoldReason(Enum):
    """Reasons for placing a record in HOLD."""
    NO_MATCH = "no_match"           # No company match found
    LOW_CONFIDENCE = "low_confidence"  # Match score below threshold
    COLLISION = "collision"          # Multiple ambiguous matches
    MISSING_DATA = "missing_data"    # Insufficient data for matching


class HoldTTLLevel(Enum):
    """
    Hold Queue TTL Escalation Levels.

    DOCTRINE: Records escalate through levels based on time in HOLD.
    - INITIAL (7 days): First attempt at re-matching
    - ESCALATED_1 (21 days): Second attempt with relaxed matching
    - ESCALATED_2 (28 days): Manual review flag
    - FINAL (30 days): Archive or purge decision required

    No probabilistic logic. No ML. Deterministic time-based escalation.
    """
    INITIAL = "initial"           # 0-7 days in HOLD
    ESCALATED_1 = "escalated_1"   # 7-21 days in HOLD
    ESCALATED_2 = "escalated_2"   # 21-28 days in HOLD
    FINAL = "final"               # 28+ days in HOLD (30 day purge)


# TTL thresholds in days
HOLD_TTL_DAYS = {
    HoldTTLLevel.INITIAL: 7,      # First 7 days
    HoldTTLLevel.ESCALATED_1: 21, # After 21 days
    HoldTTLLevel.ESCALATED_2: 28, # After 28 days
    HoldTTLLevel.FINAL: 30,       # After 30 days (archive/purge)
}


@dataclass
class HoldExportResult:
    """Result of HOLD export operation."""
    export_path: str
    records_exported: int
    export_timestamp: datetime
    hold_reasons: Dict[str, int]  # Reason -> count
    collision_details_path: Optional[str] = None
    duration_seconds: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Phase1bStats:
    """Statistics for Phase 1b execution."""
    total_input: int = 0
    no_match_count: int = 0
    low_confidence_count: int = 0
    collision_count: int = 0
    missing_data_count: int = 0
    exported_count: int = 0
    duration_seconds: float = 0.0
    correlation_id: str = ""  # Propagated unchanged


class Phase1bUnmatchedHoldExport:
    """
    Phase 1b: Export unmatched people to HOLD CSV.

    Purpose:
    - Prevents premature enrichment of unmatched records
    - Avoids corruption of emails, domains, slots, and Neon records
    - Enables re-processing once company enrichment improves matching

    HOLD reasons:
    - no_match: No company match found
    - low_confidence: Match score below threshold
    - collision: Multiple ambiguous matches
    - missing_data: Insufficient data for matching
    """

    # Columns required for HOLD export
    REQUIRED_COLUMNS = ['person_id']

    # Columns expected from Phase 1 results
    PHASE1_RESULT_COLUMNS = [
        'match_type', 'match_score', 'confidence',
        'is_collision', 'collision_reason'
    ]

    # Metadata columns to add
    HOLD_METADATA_COLUMNS = [
        'hold_reason', 'hold_timestamp', 'hold_source',
        'retry_count', 'hold_run_id'
    ]

    def __init__(self, config: Dict[str, Any] = None, logger: PipelineLogger = None):
        """
        Initialize Phase 1b.

        Args:
            config: Configuration dictionary with:
                - confidence_threshold: Minimum match score (default: 0.85)
                - output_directory: Where to save HOLD files
                - export_collision_details: Whether to export collision candidates
            logger: Pipeline logger instance
        """
        self.config = config or {}
        self.logger = logger or PipelineLogger()

        # Configuration
        self.confidence_threshold = self.config.get('confidence_threshold', 0.85)
        self.output_directory = Path(self.config.get('output_directory', './output'))
        self.export_collision_details = self.config.get('export_collision_details', True)

        # Ensure output directory exists
        self.output_directory.mkdir(parents=True, exist_ok=True)

    def run(self, phase1_results_df: pd.DataFrame,
            correlation_id: str,
            output_path: str = None,
            run_id: str = None) -> Tuple[HoldExportResult, Phase1bStats]:
        """
        Export unmatched/ambiguous people into a HOLD CSV.

        DOCTRINE: correlation_id is MANDATORY. FAIL HARD if missing.

        Args:
            phase1_results_df: DataFrame from Phase 1 with match results
                Expected columns: person_id, match_type, match_score, is_collision, etc.
            correlation_id: MANDATORY - End-to-end trace ID (UUID v4)
            output_path: Destination CSV file path (optional)
            run_id: Pipeline run identifier for tracking

        Returns:
            Tuple of (HoldExportResult, Phase1bStats)

        Raises:
            CorrelationIDError: If correlation_id is missing or invalid (FAIL HARD)
        """
        # DOCTRINE ENFORCEMENT: Validate correlation_id (FAIL HARD)
        process_id = "company.identity.matching.phase1b"
        correlation_id = validate_correlation_id(correlation_id, process_id, "Phase 1b")

        start_time = time.time()
        stats = Phase1bStats(total_input=len(phase1_results_df), correlation_id=correlation_id)

        log_phase_start(self.logger, 1, "Unmatched Hold Export", len(phase1_results_df))

        # Generate default output path if not provided
        if output_path is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_path = str(self.output_directory / f"people_unmatched_hold_{timestamp}.csv")

        run_id = run_id or self.logger.run_id

        # Validate input DataFrame
        validation_errors = self.validate_for_export(phase1_results_df)
        if validation_errors:
            self.logger.error(
                f"Validation failed: {validation_errors}",
                metadata={'errors': validation_errors}
            )
            # Don't fail - proceed with what we have

        # Filter to unmatched/hold records
        hold_df = self._filter_hold_records(phase1_results_df)

        if hold_df.empty:
            self.logger.info("No unmatched records to export to HOLD")
            result = HoldExportResult(
                export_path=output_path,
                records_exported=0,
                export_timestamp=datetime.now(),
                hold_reasons={},
                duration_seconds=time.time() - start_time
            )
            return result, stats

        # Categorize each record's hold reason
        hold_df = hold_df.copy()
        hold_df['hold_reason'] = hold_df.apply(self.categorize_hold_reason, axis=1)

        # Add metadata columns
        hold_df = self.add_hold_metadata(hold_df, run_id)

        # Update stats
        reason_counts = hold_df['hold_reason'].value_counts().to_dict()
        stats.no_match_count = reason_counts.get(HoldReason.NO_MATCH.value, 0)
        stats.low_confidence_count = reason_counts.get(HoldReason.LOW_CONFIDENCE.value, 0)
        stats.collision_count = reason_counts.get(HoldReason.COLLISION.value, 0)
        stats.missing_data_count = reason_counts.get(HoldReason.MISSING_DATA.value, 0)
        stats.exported_count = len(hold_df)

        # Log each hold reason
        for reason, count in reason_counts.items():
            self.logger.log_event(
                EventType.QUEUE_ADD,
                f"HOLD: {count} records - {reason}",
                metadata={'hold_reason': reason, 'count': count}
            )

        # Export main HOLD CSV
        self._export_hold_csv(hold_df, output_path)

        # Export collision details if configured
        collision_details_path = None
        if self.export_collision_details:
            collision_df = hold_df[hold_df['hold_reason'] == HoldReason.COLLISION.value]
            if not collision_df.empty:
                collision_details_path = output_path.replace('.csv', '_collision_details.json')
                self._export_collision_details(collision_df, collision_details_path)

        stats.duration_seconds = time.time() - start_time

        log_phase_complete(
            self.logger, 1, "Unmatched Hold Export",
            output_count=stats.exported_count,
            duration_seconds=stats.duration_seconds,
            stats={
                'no_match': stats.no_match_count,
                'low_confidence': stats.low_confidence_count,
                'collision': stats.collision_count,
                'missing_data': stats.missing_data_count
            }
        )

        result = HoldExportResult(
            export_path=output_path,
            records_exported=stats.exported_count,
            export_timestamp=datetime.now(),
            hold_reasons=reason_counts,
            collision_details_path=collision_details_path,
            duration_seconds=stats.duration_seconds,
            metadata={
                'run_id': run_id,
                'confidence_threshold': self.confidence_threshold
            }
        )

        return result, stats

    def _filter_hold_records(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Filter DataFrame to records that should be placed in HOLD.

        A record goes to HOLD if:
        - match_type is 'none' or missing
        - match_score < confidence_threshold
        - is_collision is True
        - Missing critical data (person_id, company_name both empty)

        Args:
            df: Phase 1 results DataFrame

        Returns:
            Filtered DataFrame of HOLD records
        """
        if df.empty:
            return df

        hold_mask = pd.Series([False] * len(df), index=df.index)

        # No match found
        if 'match_type' in df.columns:
            no_match = (df['match_type'].isna()) | (df['match_type'] == 'none')
            hold_mask = hold_mask | no_match

        # Low confidence match
        if 'match_score' in df.columns:
            low_confidence = (
                df['match_score'].notna() &
                (df['match_score'] > 0) &
                (df['match_score'] < self.confidence_threshold)
            )
            hold_mask = hold_mask | low_confidence

        # Collision (ambiguous match)
        if 'is_collision' in df.columns:
            collision = df['is_collision'] == True
            hold_mask = hold_mask | collision

        # Missing critical data
        missing_data = self._check_missing_critical_data(df)
        hold_mask = hold_mask | missing_data

        return df[hold_mask]

    def _check_missing_critical_data(self, df: pd.DataFrame) -> pd.Series:
        """
        Check for records with missing critical data.

        Args:
            df: DataFrame to check

        Returns:
            Boolean Series where True indicates missing critical data
        """
        missing = pd.Series([False] * len(df), index=df.index)

        # Check for empty person identifiers
        if 'person_id' in df.columns:
            missing = missing | df['person_id'].isna() | (df['person_id'] == '')

        # Check for both company_name and input_company_name being empty
        company_cols = ['company_name', 'input_company_name']
        company_col = None
        for col in company_cols:
            if col in df.columns:
                company_col = col
                break

        if company_col:
            missing = missing | df[company_col].isna() | (df[company_col] == '')

        return missing

    def categorize_hold_reason(self, row: pd.Series) -> str:
        """
        Determine the HOLD reason for a record.

        Priority order:
        1. missing_data - if critical fields are empty
        2. collision - if ambiguous match
        3. low_confidence - if match score below threshold
        4. no_match - if no match found

        Args:
            row: DataFrame row with match results

        Returns:
            Hold reason string (HoldReason enum value)
        """
        # Check for missing critical data
        person_id = row.get('person_id', '')
        company_name = row.get('company_name', row.get('input_company_name', ''))

        if pd.isna(person_id) or str(person_id).strip() == '':
            return HoldReason.MISSING_DATA.value

        if pd.isna(company_name) or str(company_name).strip() == '':
            return HoldReason.MISSING_DATA.value

        # Check for collision
        is_collision = row.get('is_collision', False)
        if is_collision == True or str(is_collision).lower() == 'true':
            return HoldReason.COLLISION.value

        # Check for low confidence
        match_score = row.get('match_score', 0)
        if pd.notna(match_score) and 0 < float(match_score) < self.confidence_threshold:
            return HoldReason.LOW_CONFIDENCE.value

        # Default: no match
        return HoldReason.NO_MATCH.value

    def add_hold_metadata(self, df: pd.DataFrame, run_id: str = None) -> pd.DataFrame:
        """
        Add metadata columns for HOLD tracking.

        Metadata includes:
        - hold_timestamp: When placed in HOLD
        - hold_source: Pipeline phase that created the HOLD
        - retry_count: Number of retry attempts (starts at 0)
        - hold_run_id: Pipeline run that created this HOLD

        Args:
            df: DataFrame to enhance
            run_id: Pipeline run identifier

        Returns:
            DataFrame with metadata columns
        """
        df = df.copy()

        # Timestamp
        df['hold_timestamp'] = datetime.now().isoformat()

        # Source phase
        df['hold_source'] = 'phase1b_unmatched_hold_export'

        # Retry count (starts at 0)
        if 'retry_count' not in df.columns:
            df['retry_count'] = 0
        else:
            # Increment existing retry count
            df['retry_count'] = df['retry_count'].fillna(0).astype(int) + 1

        # Run ID
        df['hold_run_id'] = run_id or 'unknown'

        # Add original input columns if available for re-processing
        original_cols = [
            'first_name', 'last_name', 'title', 'company_name', 'input_company_name',
            'company_domain', 'city', 'state', 'email', 'linkedin_url'
        ]
        for col in original_cols:
            if col not in df.columns:
                # Try to find alternative column names
                alt_col = f"input_{col}" if col not in df.columns else col
                if alt_col in df.columns:
                    df[col] = df[alt_col]

        return df

    def validate_for_export(self, df: pd.DataFrame) -> List[str]:
        """
        Validate DataFrame before export.

        Args:
            df: DataFrame to validate

        Returns:
            List of validation errors (empty if valid)
        """
        errors = []

        if df.empty:
            errors.append("DataFrame is empty")
            return errors

        # Check for required columns
        for col in self.REQUIRED_COLUMNS:
            if col not in df.columns:
                errors.append(f"Missing required column: {col}")

        # Check for at least some Phase 1 result columns
        has_phase1_cols = any(col in df.columns for col in self.PHASE1_RESULT_COLUMNS)
        if not has_phase1_cols:
            errors.append(
                f"Missing Phase 1 result columns. Expected at least one of: {self.PHASE1_RESULT_COLUMNS}"
            )

        # Check for duplicate person_ids
        if 'person_id' in df.columns:
            duplicates = df['person_id'].duplicated().sum()
            if duplicates > 0:
                errors.append(f"Found {duplicates} duplicate person_ids")

        return errors

    def _export_hold_csv(self, df: pd.DataFrame, output_path: str) -> None:
        """
        Export HOLD records to CSV.

        Args:
            df: DataFrame to export
            output_path: Destination file path
        """
        # Select columns for export (preserve order)
        export_columns = []

        # Primary identifiers first
        primary_cols = ['person_id', 'first_name', 'last_name', 'email']
        for col in primary_cols:
            if col in df.columns:
                export_columns.append(col)

        # Company info
        company_cols = ['company_name', 'input_company_name', 'company_domain', 'title']
        for col in company_cols:
            if col in df.columns and col not in export_columns:
                export_columns.append(col)

        # Location
        location_cols = ['city', 'state', 'address_city', 'address_state']
        for col in location_cols:
            if col in df.columns and col not in export_columns:
                export_columns.append(col)

        # Match results
        match_cols = [
            'match_type', 'match_tier', 'match_score', 'confidence',
            'matched_company_id', 'matched_company_name',
            'is_collision', 'collision_reason', 'city_match', 'state_match'
        ]
        for col in match_cols:
            if col in df.columns and col not in export_columns:
                export_columns.append(col)

        # HOLD metadata
        hold_cols = ['hold_reason', 'hold_timestamp', 'hold_source', 'retry_count', 'hold_run_id']
        for col in hold_cols:
            if col in df.columns and col not in export_columns:
                export_columns.append(col)

        # Any remaining columns
        for col in df.columns:
            if col not in export_columns:
                export_columns.append(col)

        # Export
        df[export_columns].to_csv(output_path, index=False)

        self.logger.info(
            f"Exported {len(df)} HOLD records to {output_path}",
            metadata={'path': output_path, 'columns': export_columns}
        )

    def _export_collision_details(self, collision_df: pd.DataFrame,
                                  output_path: str) -> None:
        """
        Export collision candidate details to JSON.

        Args:
            collision_df: DataFrame with collision records
            output_path: Destination JSON file path
        """
        collision_details = []

        for idx, row in collision_df.iterrows():
            detail = {
                'person_id': row.get('person_id', ''),
                'input_company_name': row.get('input_company_name', row.get('company_name', '')),
                'collision_reason': row.get('collision_reason', ''),
                'hold_timestamp': row.get('hold_timestamp', ''),
                'candidates': []
            }

            # Try to extract collision candidates from the row
            # These might be stored as JSON string or list
            candidates = row.get('collision_candidates', [])
            if isinstance(candidates, str):
                try:
                    candidates = json.loads(candidates)
                except json.JSONDecodeError:
                    candidates = []

            if isinstance(candidates, list):
                detail['candidates'] = candidates

            collision_details.append(detail)

        with open(output_path, 'w') as f:
            json.dump(collision_details, f, indent=2, default=str)

        self.logger.info(
            f"Exported {len(collision_details)} collision details to {output_path}",
            metadata={'path': output_path}
        )

    def get_hold_statistics(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Get statistics about HOLD records.

        Args:
            df: HOLD DataFrame

        Returns:
            Dict with counts by reason, source, retry status, etc.
        """
        if df.empty:
            return {
                'total': 0,
                'by_reason': {},
                'by_source': {},
                'retry_distribution': {},
                'ttl_distribution': {},
                'has_company_name': 0,
                'has_domain': 0,
                'has_email': 0
            }

        stats = {
            'total': len(df),
            'by_reason': {},
            'by_source': {},
            'retry_distribution': {},
            'ttl_distribution': {},
            'has_company_name': 0,
            'has_domain': 0,
            'has_email': 0
        }

        # Count by reason
        if 'hold_reason' in df.columns:
            stats['by_reason'] = df['hold_reason'].value_counts().to_dict()

        # Count by source
        if 'hold_source' in df.columns:
            stats['by_source'] = df['hold_source'].value_counts().to_dict()

        # Retry count distribution
        if 'retry_count' in df.columns:
            stats['retry_distribution'] = df['retry_count'].value_counts().to_dict()

        # TTL level distribution
        if 'ttl_level' in df.columns:
            stats['ttl_distribution'] = df['ttl_level'].value_counts().to_dict()

        # Data completeness
        company_cols = ['company_name', 'input_company_name']
        for col in company_cols:
            if col in df.columns:
                stats['has_company_name'] = df[col].notna().sum()
                break

        if 'company_domain' in df.columns:
            stats['has_domain'] = df['company_domain'].notna().sum()

        if 'email' in df.columns:
            stats['has_email'] = df['email'].notna().sum()

        return stats

    # =========================================================================
    # TTL ESCALATION METHODS
    # =========================================================================

    def calculate_ttl_level(self, hold_timestamp: datetime) -> HoldTTLLevel:
        """
        Calculate TTL escalation level based on time in HOLD.

        DOCTRINE: Deterministic time-based escalation (7/21/28/30 days).

        Args:
            hold_timestamp: When record was placed in HOLD

        Returns:
            HoldTTLLevel based on days in HOLD
        """
        now = datetime.now()
        days_in_hold = (now - hold_timestamp).days

        if days_in_hold >= HOLD_TTL_DAYS[HoldTTLLevel.FINAL]:
            return HoldTTLLevel.FINAL
        elif days_in_hold >= HOLD_TTL_DAYS[HoldTTLLevel.ESCALATED_2]:
            return HoldTTLLevel.ESCALATED_2
        elif days_in_hold >= HOLD_TTL_DAYS[HoldTTLLevel.ESCALATED_1]:
            return HoldTTLLevel.ESCALATED_1
        else:
            return HoldTTLLevel.INITIAL

    def apply_ttl_escalation(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Apply TTL escalation levels to HOLD records.

        Adds/updates 'ttl_level' column based on hold_timestamp.

        Args:
            df: HOLD DataFrame with hold_timestamp column

        Returns:
            DataFrame with ttl_level column
        """
        if df.empty:
            return df

        df = df.copy()

        if 'hold_timestamp' not in df.columns:
            self.logger.warning("No hold_timestamp column - cannot calculate TTL levels")
            df['ttl_level'] = HoldTTLLevel.INITIAL.value
            return df

        def get_level(row):
            try:
                ts = row['hold_timestamp']
                if isinstance(ts, str):
                    ts = datetime.fromisoformat(ts.replace('Z', '+00:00'))
                return self.calculate_ttl_level(ts).value
            except Exception:
                return HoldTTLLevel.INITIAL.value

        df['ttl_level'] = df.apply(get_level, axis=1)
        df['days_in_hold'] = df['hold_timestamp'].apply(
            lambda x: (datetime.now() - datetime.fromisoformat(str(x).replace('Z', '+00:00'))).days
            if pd.notna(x) else 0
        )

        return df

    def get_records_by_ttl_level(
        self,
        df: pd.DataFrame,
        level: HoldTTLLevel
    ) -> pd.DataFrame:
        """
        Filter HOLD records by TTL level.

        Args:
            df: HOLD DataFrame (must have ttl_level column)
            level: HoldTTLLevel to filter by

        Returns:
            Filtered DataFrame
        """
        if 'ttl_level' not in df.columns:
            df = self.apply_ttl_escalation(df)

        return df[df['ttl_level'] == level.value]

    def get_records_for_archive(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Get records that have reached FINAL TTL level (30+ days).

        These records should be archived or purged per doctrine.

        Args:
            df: HOLD DataFrame

        Returns:
            DataFrame of records ready for archive
        """
        return self.get_records_by_ttl_level(df, HoldTTLLevel.FINAL)

    def get_records_for_manual_review(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Get records at ESCALATED_2 level (28+ days).

        These records require manual review before final decision.

        Args:
            df: HOLD DataFrame

        Returns:
            DataFrame of records needing manual review
        """
        return self.get_records_by_ttl_level(df, HoldTTLLevel.ESCALATED_2)

    def get_ttl_summary(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Get summary of records by TTL level.

        Args:
            df: HOLD DataFrame

        Returns:
            Dict with counts by TTL level and action recommendations
        """
        if 'ttl_level' not in df.columns:
            df = self.apply_ttl_escalation(df)

        summary = {
            'total': len(df),
            'by_level': {},
            'actions_required': []
        }

        for level in HoldTTLLevel:
            count = len(df[df['ttl_level'] == level.value])
            summary['by_level'][level.value] = count

            if level == HoldTTLLevel.FINAL and count > 0:
                summary['actions_required'].append({
                    'action': 'archive_or_purge',
                    'count': count,
                    'description': f"{count} records at 30+ days - archive or purge required"
                })
            elif level == HoldTTLLevel.ESCALATED_2 and count > 0:
                summary['actions_required'].append({
                    'action': 'manual_review',
                    'count': count,
                    'description': f"{count} records at 28+ days - manual review required"
                })
            elif level == HoldTTLLevel.ESCALATED_1 and count > 0:
                summary['actions_required'].append({
                    'action': 'retry_with_relaxed_matching',
                    'count': count,
                    'description': f"{count} records at 21+ days - retry with relaxed matching"
                })

        return summary

    def load_hold_file(self, file_path: str) -> pd.DataFrame:
        """
        Load a HOLD CSV file for re-processing.

        Args:
            file_path: Path to HOLD CSV file

        Returns:
            DataFrame with HOLD records
        """
        df = pd.read_csv(file_path)

        self.logger.info(
            f"Loaded {len(df)} HOLD records from {file_path}",
            metadata={'path': file_path}
        )

        return df

    def merge_hold_files(self, file_paths: List[str],
                         output_path: str = None) -> pd.DataFrame:
        """
        Merge multiple HOLD files into one.

        Handles deduplication by person_id, keeping the record with
        the highest retry_count.

        Args:
            file_paths: List of HOLD CSV file paths
            output_path: Optional output path for merged file

        Returns:
            Merged DataFrame
        """
        dfs = []
        for path in file_paths:
            if Path(path).exists():
                dfs.append(pd.read_csv(path))

        if not dfs:
            return pd.DataFrame()

        merged = pd.concat(dfs, ignore_index=True)

        # Deduplicate by person_id, keeping highest retry_count
        if 'person_id' in merged.columns and 'retry_count' in merged.columns:
            merged = merged.sort_values('retry_count', ascending=False)
            merged = merged.drop_duplicates(subset=['person_id'], keep='first')

        if output_path:
            merged.to_csv(output_path, index=False)
            self.logger.info(
                f"Merged {len(file_paths)} HOLD files into {output_path}",
                metadata={'path': output_path, 'records': len(merged)}
            )

        return merged


def export_unmatched_to_hold(phase1_results_df: pd.DataFrame,
                             output_path: str = None,
                             config: Dict[str, Any] = None) -> HoldExportResult:
    """
    Convenience function to export unmatched records to HOLD.

    Args:
        phase1_results_df: DataFrame from Phase 1 with match results
        output_path: Destination CSV file path
        config: Optional configuration

    Returns:
        HoldExportResult
    """
    phase1b = Phase1bUnmatchedHoldExport(config=config)
    result, stats = phase1b.run(phase1_results_df, output_path)
    return result


def get_hold_summary(hold_file_path: str) -> Dict[str, Any]:
    """
    Get summary statistics from a HOLD file.

    Args:
        hold_file_path: Path to HOLD CSV file

    Returns:
        Dict with summary statistics
    """
    phase1b = Phase1bUnmatchedHoldExport()
    df = phase1b.load_hold_file(hold_file_path)
    return phase1b.get_hold_statistics(df)
