"""
Phase 8: Output Writer
======================
Final phase - writes pipeline results to CSV files and optionally to Neon.
Generates summary reports and final output.

Output Files (to /output/ folder):
- people_final.csv: All people with emails and slot assignments
- slot_assignments.csv: Slot assignments by company
- enrichment_queue.csv: Items needing additional enrichment
- pipeline_summary.txt: Human-readable run summary

Database Writes (optional, if NEON_WRITE_ENABLED=true):
- marketing.people_master: Person records
- marketing.company_slot: Slot assignments
- marketing.data_enrichment_log: Enrichment queue

All output anchored to company_id (Company-First doctrine).
"""

import os
import time
import uuid
import logging
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime
import pandas as pd

# Doctrine enforcement imports
from ops.enforcement.correlation_id import validate_correlation_id, CorrelationIDError

# Neon database writer (optional)
from .neon_writer import (
    NeonDatabaseWriter,
    NeonConfig,
    NeonWriterStats,
    WriteResult as NeonWriteResult,
    write_to_neon,
    check_neon_connection,
)


logger = logging.getLogger(__name__)


@dataclass
class WriteResult:
    """Result of a write operation."""
    file_name: str
    records_written: int
    file_path: str
    file_size_bytes: int = 0
    errors: List[str] = field(default_factory=list)
    duration_seconds: float = 0.0


@dataclass
class PipelineSummary:
    """Summary of People Pipeline run."""
    run_id: str
    started_at: datetime
    completed_at: Optional[datetime] = None
    duration_seconds: float = 0.0

    # Input stats
    input_people: int = 0
    input_patterns: int = 0

    # Phase 5 stats
    emails_generated: int = 0
    verified_emails: int = 0
    derived_emails: int = 0
    low_confidence_emails: int = 0
    missing_pattern_people: int = 0

    # Phase 6 stats
    slots_assigned: int = 0
    chro_filled: int = 0
    hr_manager_filled: int = 0
    benefits_lead_filled: int = 0
    payroll_admin_filled: int = 0
    hr_support_filled: int = 0
    unslotted_people: int = 0
    slot_conflicts: int = 0

    # Phase 7 stats
    queue_total: int = 0
    queue_high_priority: int = 0
    queue_medium_priority: int = 0
    queue_low_priority: int = 0

    # Output stats
    files_written: int = 0
    total_records_written: int = 0


@dataclass
class Phase8Stats:
    """Statistics for Phase 8 execution."""
    # CSV output
    files_written: int = 0
    total_records: int = 0
    people_final_count: int = 0
    slot_assignments_count: int = 0
    enrichment_queue_count: int = 0
    # Database output (Neon)
    neon_write_enabled: bool = False
    neon_write_success: bool = False
    neon_people_written: int = 0
    neon_slots_written: int = 0
    neon_queue_written: int = 0
    neon_errors: List[str] = field(default_factory=list)
    # General
    errors: List[str] = field(default_factory=list)
    duration_seconds: float = 0.0
    correlation_id: str = ""  # Propagated unchanged


class Phase8OutputWriter:
    """
    Phase 8: Write pipeline results to CSV files and optionally to Neon.

    Output targets:
    - CSV (always): people_final.csv, slot_assignments.csv, enrichment_queue.csv, pipeline_summary.txt
    - Neon (optional): marketing.people_master, marketing.company_slot, marketing.data_enrichment_log

    Neon writes enabled via:
    - NEON_WRITE_ENABLED=true environment variable, OR
    - neon_write_enabled=True in config

    Movement Engine Integration:
    - Triggers APPOINTMENT event if meeting metadata exists in output
    - Reports EventType.MOVEMENT_APPOINTMENT for meeting-booked records

    REQUIRES: company_id anchor (Company-First doctrine)
    """

    # Default output directory
    DEFAULT_OUTPUT_DIR = "output"

    # Output file names
    OUTPUT_FILES = {
        'people_final': 'people_final.csv',
        'slot_assignments': 'slot_assignments.csv',
        'enrichment_queue': 'enrichment_queue.csv',
        'summary': 'pipeline_summary.txt'
    }

    def __init__(self, config: Dict[str, Any] = None, movement_engine=None):
        """
        Initialize Phase 8.

        Args:
            config: Configuration dictionary with:
                - output_dir: Output directory path (default: ./output)
                - run_id: Optional run ID (auto-generated if not provided)
                - include_timestamp: Add timestamp to file names (default: True)
                - neon_write_enabled: Enable Neon database writes (default: False)
                - neon_config: Optional NeonConfig overrides
            movement_engine: Optional MovementEngine instance for event reporting
        """
        self.config = config or {}
        self.output_dir = self.config.get('output_dir', self.DEFAULT_OUTPUT_DIR)
        self.run_id = self.config.get('run_id', self._generate_run_id())
        self.include_timestamp = self.config.get('include_timestamp', True)
        self.movement_engine = movement_engine

        # Neon database write configuration
        # Check env var first, then config
        env_enabled = os.getenv("NEON_WRITE_ENABLED", "").lower() == "true"
        self.neon_write_enabled = self.config.get('neon_write_enabled', env_enabled)
        self.neon_config = self.config.get('neon_config', {})

        # Ensure output directory exists
        os.makedirs(self.output_dir, exist_ok=True)

    def run(
        self,
        people_with_emails_df: pd.DataFrame,
        slotted_people_df: pd.DataFrame,
        unslotted_people_df: pd.DataFrame,
        slot_summary_df: pd.DataFrame,
        enrichment_queue_df: pd.DataFrame,
        correlation_id: str,
        phase_stats: Dict[str, Any] = None
    ) -> Tuple[PipelineSummary, Phase8Stats]:
        """
        Run output writer phase.

        DOCTRINE: correlation_id is MANDATORY. FAIL HARD if missing.

        Args:
            people_with_emails_df: People with generated emails (from Phase 5)
            slotted_people_df: People with slot assignments (from Phase 6)
            unslotted_people_df: People without slots (from Phase 6)
            slot_summary_df: Slot summary by company (from Phase 6)
            enrichment_queue_df: Enrichment queue (from Phase 7)
            correlation_id: MANDATORY - End-to-end trace ID (UUID v4)
            phase_stats: Dictionary of stats from previous phases

        Returns:
            Tuple of (PipelineSummary, Phase8Stats)

        Raises:
            CorrelationIDError: If correlation_id is missing or invalid (FAIL HARD)
        """
        # DOCTRINE ENFORCEMENT: Validate correlation_id (FAIL HARD)
        process_id = "people.lifecycle.output.phase8"
        correlation_id = validate_correlation_id(correlation_id, process_id, "Phase 8")

        start_time = time.time()
        stats = Phase8Stats(correlation_id=correlation_id)
        phase_stats = phase_stats or {}

        # Create pipeline summary
        summary = PipelineSummary(
            run_id=self.run_id,
            started_at=phase_stats.get('started_at', datetime.now())
        )

        # Populate summary from phase stats
        self._populate_summary(summary, phase_stats)

        # 1. Write people_final.csv (merged people with emails and slots)
        people_final_df = self._prepare_people_final(
            people_with_emails_df, slotted_people_df, unslotted_people_df
        )
        result1 = self._write_csv(people_final_df, 'people_final')
        if result1.errors:
            stats.errors.extend(result1.errors)
        else:
            stats.files_written += 1
            stats.people_final_count = result1.records_written

        # Check for meeting metadata and report APPOINTMENT events
        # Phase 8 triggers APPOINTMENT event if meeting metadata exists
        if self.movement_engine and people_final_df is not None and len(people_final_df) > 0:
            self._report_appointment_events(people_final_df)

        # 2. Write slot_assignments.csv
        result2 = self._write_csv(slot_summary_df, 'slot_assignments')
        if result2.errors:
            stats.errors.extend(result2.errors)
        else:
            stats.files_written += 1
            stats.slot_assignments_count = result2.records_written

        # 3. Write enrichment_queue.csv
        result3 = self._write_csv(enrichment_queue_df, 'enrichment_queue')
        if result3.errors:
            stats.errors.extend(result3.errors)
        else:
            stats.files_written += 1
            stats.enrichment_queue_count = result3.records_written

        # 4. Optionally write to Neon database
        stats.neon_write_enabled = self.neon_write_enabled
        if self.neon_write_enabled:
            neon_stats, neon_results = self._write_to_neon(
                people_final_df,
                slotted_people_df,
                enrichment_queue_df,
                correlation_id
            )
            stats.neon_write_success = neon_stats.failed_writes == 0
            stats.neon_people_written = neon_stats.people_inserted
            stats.neon_slots_written = neon_stats.slots_assigned
            stats.neon_queue_written = neon_stats.enrichment_logged
            for neon_result in neon_results:
                if neon_result.errors:
                    stats.neon_errors.extend(neon_result.errors)
            logger.info(
                f"Neon database write complete: "
                f"{stats.neon_people_written} people, "
                f"{stats.neon_slots_written} slots, "
                f"{stats.neon_queue_written} queue items"
            )

        # 5. Write pipeline_summary.txt
        summary.completed_at = datetime.now()
        summary.duration_seconds = time.time() - phase_stats.get('pipeline_start_time', start_time)
        summary.files_written = stats.files_written
        summary.total_records_written = (
            stats.people_final_count +
            stats.slot_assignments_count +
            stats.enrichment_queue_count
        )

        summary_path = self._write_summary(summary)
        if summary_path:
            stats.files_written += 1

        stats.total_records = summary.total_records_written
        stats.duration_seconds = time.time() - start_time

        return summary, stats

    def _prepare_people_final(
        self,
        people_with_emails_df: pd.DataFrame,
        slotted_people_df: pd.DataFrame,
        unslotted_people_df: pd.DataFrame
    ) -> pd.DataFrame:
        """
        Prepare final people output by merging email and slot data.

        Args:
            people_with_emails_df: People with emails from Phase 5
            slotted_people_df: Slotted people from Phase 6
            unslotted_people_df: Unslotted people from Phase 6

        Returns:
            Merged DataFrame for output
        """
        # Start with people who have emails
        if people_with_emails_df is None or len(people_with_emails_df) == 0:
            return pd.DataFrame()

        # Create output columns
        output_columns = [
            'person_id', 'company_id', 'first_name', 'last_name',
            'job_title', 'generated_email', 'email_confidence',
            'slot_type', 'slot_reason', 'seniority_score',
            'pattern_used', 'email_domain'
        ]

        records = []

        # Process people with emails
        for idx, row in people_with_emails_df.iterrows():
            person_id = str(row.get('person_id', idx))

            record = {
                'person_id': person_id,
                'company_id': row.get('company_id', '') or row.get('matched_company_id', ''),
                'first_name': row.get('first_name', ''),
                'last_name': row.get('last_name', ''),
                'job_title': row.get('job_title', '') or row.get('title', ''),
                'generated_email': row.get('generated_email', ''),
                'email_confidence': row.get('email_confidence', ''),
                'pattern_used': row.get('pattern_used', ''),
                'email_domain': row.get('email_domain', ''),
                'slot_type': '',
                'slot_reason': '',
                'seniority_score': 0
            }

            # Check if person is in slotted
            if slotted_people_df is not None and len(slotted_people_df) > 0:
                slotted_match = slotted_people_df[
                    slotted_people_df['person_id'].astype(str) == person_id
                ]
                if len(slotted_match) > 0:
                    slot_row = slotted_match.iloc[0]
                    record['slot_type'] = slot_row.get('slot_type', '')
                    record['slot_reason'] = slot_row.get('slot_reason', '')
                    record['seniority_score'] = slot_row.get('seniority_score', 0)

            records.append(record)

        # Add unslotted people (might not have emails)
        if unslotted_people_df is not None and len(unslotted_people_df) > 0:
            existing_ids = {r['person_id'] for r in records}

            for idx, row in unslotted_people_df.iterrows():
                person_id = str(row.get('person_id', idx))

                if person_id not in existing_ids:
                    record = {
                        'person_id': person_id,
                        'company_id': row.get('company_id', '') or row.get('matched_company_id', ''),
                        'first_name': row.get('first_name', ''),
                        'last_name': row.get('last_name', ''),
                        'job_title': row.get('job_title', '') or row.get('title', ''),
                        'generated_email': row.get('generated_email', ''),
                        'email_confidence': row.get('email_confidence', ''),
                        'pattern_used': row.get('pattern_used', ''),
                        'email_domain': row.get('email_domain', ''),
                        'slot_type': row.get('slot_type', 'UNSLOTTED'),
                        'slot_reason': row.get('slot_reason', ''),
                        'seniority_score': row.get('seniority_score', 0)
                    }
                    records.append(record)

        return pd.DataFrame(records)

    def _write_csv(self, df: pd.DataFrame, file_type: str) -> WriteResult:
        """
        Write DataFrame to CSV file.

        Args:
            df: DataFrame to write
            file_type: Type of output file (people_final, slot_assignments, etc.)

        Returns:
            WriteResult with statistics
        """
        start_time = time.time()
        file_name = self.OUTPUT_FILES.get(file_type, f'{file_type}.csv')

        # Add timestamp if configured
        if self.include_timestamp:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            base, ext = os.path.splitext(file_name)
            file_name = f"{base}_{timestamp}{ext}"

        file_path = os.path.join(self.output_dir, file_name)

        result = WriteResult(
            file_name=file_name,
            records_written=0,
            file_path=file_path
        )

        try:
            if df is None or len(df) == 0:
                # Write empty file with headers
                pd.DataFrame().to_csv(file_path, index=False)
                result.records_written = 0
            else:
                df.to_csv(file_path, index=False)
                result.records_written = len(df)

            # Get file size
            if os.path.exists(file_path):
                result.file_size_bytes = os.path.getsize(file_path)

        except Exception as e:
            result.errors.append(f"Error writing {file_type}: {str(e)}")

        result.duration_seconds = time.time() - start_time
        return result

    def _write_to_neon(
        self,
        people_df: pd.DataFrame,
        slotted_df: pd.DataFrame,
        enrichment_queue_df: pd.DataFrame,
        correlation_id: str
    ) -> Tuple[NeonWriterStats, List[NeonWriteResult]]:
        """
        Write pipeline output to Neon PostgreSQL database.

        Args:
            people_df: People final output
            slotted_df: Slot assignments
            enrichment_queue_df: Enrichment queue
            correlation_id: Pipeline trace ID

        Returns:
            Tuple of (NeonWriterStats, List of WriteResults)
        """
        try:
            # Check connection first
            if not check_neon_connection():
                logger.warning("Neon database not available, skipping database writes")
                return NeonWriterStats(correlation_id=correlation_id), []

            # Write to Neon
            return write_to_neon(
                people_df=people_df,
                slotted_df=slotted_df,
                enrichment_queue_df=enrichment_queue_df,
                correlation_id=correlation_id,
                config=self.neon_config
            )
        except Exception as e:
            logger.error(f"Neon database write failed: {e}")
            stats = NeonWriterStats(correlation_id=correlation_id)
            stats.failed_writes = 3
            result = NeonWriteResult(
                success=False,
                table_name="*",
                errors=[str(e)]
            )
            return stats, [result]

    def _write_summary(self, summary: PipelineSummary) -> str:
        """
        Write human-readable summary report.

        Args:
            summary: Pipeline run summary

        Returns:
            Path to summary file
        """
        file_name = self.OUTPUT_FILES['summary']

        if self.include_timestamp:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            base, ext = os.path.splitext(file_name)
            file_name = f"{base}_{timestamp}{ext}"

        file_path = os.path.join(self.output_dir, file_name)

        try:
            report = self._generate_summary_report(summary)
            with open(file_path, 'w') as f:
                f.write(report)
            return file_path
        except Exception as e:
            return ""

    def _generate_summary_report(self, summary: PipelineSummary) -> str:
        """
        Generate human-readable summary report.

        Args:
            summary: Pipeline run summary

        Returns:
            Formatted summary string
        """
        lines = [
            "=" * 70,
            "PEOPLE PIPELINE - RUN SUMMARY",
            "=" * 70,
            "",
            f"Run ID: {summary.run_id}",
            f"Started: {summary.started_at.strftime('%Y-%m-%d %H:%M:%S') if summary.started_at else 'N/A'}",
            f"Completed: {summary.completed_at.strftime('%Y-%m-%d %H:%M:%S') if summary.completed_at else 'N/A'}",
            f"Duration: {summary.duration_seconds:.2f} seconds",
            "",
            "-" * 70,
            "INPUT",
            "-" * 70,
            f"  People: {summary.input_people:,}",
            f"  Patterns: {summary.input_patterns:,}",
            "",
            "-" * 70,
            "PHASE 5 - EMAIL GENERATION",
            "-" * 70,
            f"  Emails Generated: {summary.emails_generated:,}",
            f"    - Verified: {summary.verified_emails:,}",
            f"    - Derived: {summary.derived_emails:,}",
            f"    - Low Confidence: {summary.low_confidence_emails:,}",
            f"  Missing Pattern: {summary.missing_pattern_people:,}",
            "",
            "-" * 70,
            "PHASE 6 - SLOT ASSIGNMENT",
            "-" * 70,
            f"  Slots Assigned: {summary.slots_assigned:,}",
            f"    - CHRO: {summary.chro_filled:,}",
            f"    - HR Manager: {summary.hr_manager_filled:,}",
            f"    - Benefits Lead: {summary.benefits_lead_filled:,}",
            f"    - Payroll Admin: {summary.payroll_admin_filled:,}",
            f"    - HR Support: {summary.hr_support_filled:,}",
            f"  Unslotted: {summary.unslotted_people:,}",
            f"  Conflicts Resolved: {summary.slot_conflicts:,}",
            "",
            "-" * 70,
            "PHASE 7 - ENRICHMENT QUEUE",
            "-" * 70,
            f"  Total Queued: {summary.queue_total:,}",
            f"    - HIGH Priority: {summary.queue_high_priority:,}",
            f"    - MEDIUM Priority: {summary.queue_medium_priority:,}",
            f"    - LOW Priority: {summary.queue_low_priority:,}",
            "",
            "-" * 70,
            "OUTPUT",
            "-" * 70,
            f"  Files Written: {summary.files_written:,}",
            f"  Total Records: {summary.total_records_written:,}",
            "",
            "=" * 70,
            "END OF REPORT",
            "=" * 70,
        ]

        return "\n".join(lines)

    def _populate_summary(self, summary: PipelineSummary, phase_stats: Dict[str, Any]):
        """
        Populate summary from phase statistics.

        Args:
            summary: Summary to populate
            phase_stats: Dictionary of stats from phases
        """
        # Phase 5 stats
        phase5 = phase_stats.get('phase5', {})
        summary.input_people = phase5.get('total_input', 0)
        summary.emails_generated = phase5.get('emails_generated', 0)
        summary.verified_emails = phase5.get('verified_emails', 0)
        summary.derived_emails = phase5.get('derived_emails', 0)
        summary.low_confidence_emails = phase5.get('low_confidence_emails', 0)
        summary.missing_pattern_people = phase5.get('missing_pattern', 0)

        # Phase 6 stats
        phase6 = phase_stats.get('phase6', {})
        summary.slots_assigned = phase6.get('slots_assigned', 0)
        summary.chro_filled = phase6.get('chro_count', 0)
        summary.hr_manager_filled = phase6.get('hr_manager_count', 0)
        summary.benefits_lead_filled = phase6.get('benefits_lead_count', 0)
        summary.payroll_admin_filled = phase6.get('payroll_admin_count', 0)
        summary.hr_support_filled = phase6.get('hr_support_count', 0)
        summary.unslotted_people = phase6.get('unslotted_count', 0)
        summary.slot_conflicts = phase6.get('conflicts_resolved', 0)

        # Phase 7 stats
        phase7 = phase_stats.get('phase7', {})
        summary.queue_total = phase7.get('total_queued', 0)
        summary.queue_high_priority = phase7.get('high_priority', 0)
        summary.queue_medium_priority = phase7.get('medium_priority', 0)
        summary.queue_low_priority = phase7.get('low_priority', 0)

        # Input patterns
        summary.input_patterns = phase_stats.get('input_patterns', 0)

    def _generate_run_id(self) -> str:
        """Generate unique run ID."""
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        unique = uuid.uuid4().hex[:6].upper()
        return f"PPL-{timestamp}-{unique}"

    def validate_output(self, output_dir: str = None) -> Dict[str, Any]:
        """
        Validate output files exist and contain data.

        Args:
            output_dir: Directory to check (default: configured output_dir)

        Returns:
            Validation results
        """
        output_dir = output_dir or self.output_dir

        results = {
            'valid': True,
            'files_checked': 0,
            'files_found': 0,
            'total_records': 0,
            'issues': []
        }

        for file_type, file_name in self.OUTPUT_FILES.items():
            results['files_checked'] += 1

            # Find the file (with possible timestamp suffix)
            matching_files = [
                f for f in os.listdir(output_dir)
                if f.startswith(file_name.split('.')[0])
            ]

            if matching_files:
                results['files_found'] += 1

                # Get most recent file
                latest_file = sorted(matching_files)[-1]
                file_path = os.path.join(output_dir, latest_file)

                if file_type != 'summary':
                    try:
                        df = pd.read_csv(file_path)
                        results['total_records'] += len(df)
                    except Exception as e:
                        results['issues'].append(f"Error reading {latest_file}: {str(e)}")
            else:
                results['issues'].append(f"Missing file: {file_name}")

        if results['issues']:
            results['valid'] = False

        return results

    def _report_appointment_events(
        self,
        people_final_df: pd.DataFrame
    ) -> None:
        """
        Report APPOINTMENT events for people with meeting metadata.

        Phase 8 triggers APPOINTMENT event if meeting metadata exists.
        This signals to the Movement Engine that the person has a meeting
        scheduled and should be marked as APPOINTMENT state.

        Args:
            people_final_df: Final people DataFrame with all enrichments
        """
        if not self.movement_engine:
            return

        # Meeting-related columns to check
        meeting_columns = [
            'has_meeting', 'meeting_scheduled', 'meeting_booked',
            'appointment', 'calendar_meeting', 'meeting_date',
            'meeting_time', 'meeting_url'
        ]

        try:
            # Check which meeting columns exist in the DataFrame
            existing_meeting_cols = [
                col for col in meeting_columns
                if col in people_final_df.columns
            ]

            if not existing_meeting_cols:
                return

            for idx, row in people_final_df.iterrows():
                person_id = str(row.get('person_id', ''))
                company_id = str(row.get('company_id', ''))

                if not person_id or not company_id:
                    continue

                # Check if any meeting column has a truthy value
                has_meeting = False
                meeting_metadata = {}

                for col in existing_meeting_cols:
                    value = row.get(col)
                    if value is not None and self._is_truthy(value):
                        has_meeting = True
                        meeting_metadata[col] = str(value)

                if has_meeting:
                    # Report APPOINTMENT event
                    self.movement_engine.detect_event(
                        company_id=company_id,
                        person_id=person_id,
                        event_type='appointment',
                        metadata={
                            'phase': 8,
                            'meeting_metadata': meeting_metadata,
                            'event_category': 'MOVEMENT_APPOINTMENT'
                        }
                    )
        except Exception:
            # Don't fail output writing due to movement event errors
            pass

    def _is_truthy(self, value) -> bool:
        """Check if value is truthy (handles strings, bools, ints)."""
        if value is None:
            return False
        if isinstance(value, bool):
            return value
        if isinstance(value, (int, float)):
            return value > 0
        if isinstance(value, str):
            return value.lower() in ('true', 'yes', '1', 'y') or bool(value.strip())
        return bool(value)


def write_pipeline_output(
    people_with_emails_df: pd.DataFrame,
    slotted_people_df: pd.DataFrame,
    unslotted_people_df: pd.DataFrame,
    slot_summary_df: pd.DataFrame,
    enrichment_queue_df: pd.DataFrame,
    correlation_id: str,
    phase_stats: Dict[str, Any] = None,
    config: Dict[str, Any] = None
) -> Tuple[PipelineSummary, Phase8Stats]:
    """
    Convenience function to write pipeline output.

    Args:
        people_with_emails_df: People with emails from Phase 5
        slotted_people_df: Slotted people from Phase 6
        unslotted_people_df: Unslotted people from Phase 6
        slot_summary_df: Slot summary from Phase 6
        enrichment_queue_df: Enrichment queue from Phase 7
        correlation_id: MANDATORY - Pipeline trace ID (UUID v4)
        phase_stats: Dictionary of stats from previous phases
        config: Optional configuration (neon_write_enabled=True enables DB writes)

    Returns:
        Tuple of (PipelineSummary, Phase8Stats)
    """
    phase8 = Phase8OutputWriter(config=config)
    return phase8.run(
        people_with_emails_df,
        slotted_people_df,
        unslotted_people_df,
        slot_summary_df,
        enrichment_queue_df,
        correlation_id=correlation_id,
        phase_stats=phase_stats
    )
