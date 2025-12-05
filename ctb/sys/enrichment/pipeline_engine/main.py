"""
Pipeline Engine - Company Identity Pipeline Orchestrator
=========================================================
Multi-phase company identity enrichment pipeline (Phases 1-4).
Handles company matching, domain resolution, and email pattern discovery.

The People Pipeline (Phases 5-8) is a separate process that takes
the output from this pipeline.

Usage:
    python -m pipeline_engine.main --input people.csv --output results/
    python -m pipeline_engine.main --config config.yaml

Company Identity Pipeline Architecture:
    ┌─────────────────────────────────────────────────────────────────┐
    │              COMPANY IDENTITY PIPELINE (Phases 1-4)             │
    └─────────────────────────────────────────────────────────────────┘

    INPUT: CSV/DataFrame with people (name, company, city, state)
           ↓
    ┌──────────────────────────────────────────────────────────────┐
    │ PHASE 1: Company Matching                                     │
    │ - Domain match (GOLD = 1.0)                                  │
    │ - Exact name match (SILVER = 0.95)                           │
    │ - Fuzzy match with city guardrail (BRONZE = 0.85-0.92)      │
    │ - Collision detection (threshold = 0.03)                     │
    │ - OUTPUT: person_id + company_id linkage                     │
    └──────────────────────────────────────────────────────────────┘
           ↓
    ┌──────────────────────────────────────────────────────────────┐
    │ PHASE 1b: Unmatched Hold Export                              │
    │ - Export no_match, collision, low_confidence to HOLD CSV    │
    │ - Prevents premature enrichment                              │
    │ - OUTPUT: people_unmatched_hold.csv                          │
    └──────────────────────────────────────────────────────────────┘
           ↓
    ┌──────────────────────────────────────────────────────────────┐
    │ PHASE 2: Domain Resolution                                    │
    │ - Pull domain from company_master                            │
    │ - Use input record domain if available                       │
    │ - Validate DNS/MX records                                    │
    │ - Flag for enrichment if missing                             │
    │ - OUTPUT: company_id + domain                                │
    └──────────────────────────────────────────────────────────────┘
           ↓
    ┌──────────────────────────────────────────────────────────────┐
    │ PHASE 3: Email Pattern Waterfall                              │
    │ - Tier 0 (Free): Firecrawl, WebScraper, Google Places       │
    │ - Tier 1 (Low Cost): Hunter.io, Clearbit, Apollo            │
    │ - Tier 2 (Premium): Prospeo, Snov, Clay                     │
    │ - Suggest common patterns if all fail                        │
    │ - OUTPUT: domain + email_pattern                             │
    └──────────────────────────────────────────────────────────────┘
           ↓
    ┌──────────────────────────────────────────────────────────────┐
    │ PHASE 4: Pattern Verification                                 │
    │ - Test pattern against known emails                          │
    │ - Verify via MX records                                      │
    │ - SMTP verification (optional)                               │
    │ - Calculate confidence score                                 │
    │ - OUTPUT: verified_pattern + confidence_score                │
    └──────────────────────────────────────────────────────────────┘
           ↓
    OUTPUT: Enriched records ready for People Pipeline (Phases 5-8)
"""

import argparse
import os
import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any, Tuple
import pandas as pd
import uuid
import json

from .phases.phase1_company_matching import Phase1CompanyMatching, Phase1Stats
from .phases.phase1b_unmatched_hold_export import Phase1bUnmatchedHoldExport, Phase1bStats
from .phases.phase2_domain_resolution import Phase2DomainResolution, Phase2Stats
from .phases.phase3_email_pattern_waterfall import Phase3EmailPatternWaterfall, Phase3Stats
from .phases.phase4_pattern_verification import Phase4PatternVerification, Phase4Stats
from .phases.talentflow_phase0_company_gate import TalentFlowCompanyGate, CompanyGateResult

# People Pipeline (Phases 5-8)
from .phases.phase5_email_generation import Phase5EmailGeneration, Phase5Stats
from .phases.phase6_slot_assignment import Phase6SlotAssignment, Phase6Stats
from .phases.phase7_enrichment_queue import Phase7EnrichmentQueue, Phase7Stats
from .phases.phase8_output_writer import Phase8OutputWriter, Phase8Stats, PipelineSummary

from .utils.logging import (
    PipelineLogger,
    EventType,
    LogLevel,
    log_phase_start,
    log_phase_complete,
    log_error
)
from .utils.config import PipelineConfig, load_config

# Provider Benchmark Engine (System-Level)
from ctb.sys.enrichment.provider_benchmark import ProviderBenchmarkEngine

# Waterfall Optimization Engine (System-Level)
from ctb.sys.enrichment.waterfall_optimization import WaterfallOptimizer

# Movement Engine (4-Funnel GTM System)
from .movement_engine import MovementEngine, LifecycleState, EventType as MovementEventType


@dataclass
class PipelineRunStats:
    """Aggregate statistics for a complete pipeline run."""
    run_id: str
    started_at: datetime
    completed_at: Optional[datetime] = None
    duration_seconds: float = 0.0

    # Input/Output counts
    input_records: int = 0
    matched_records: int = 0
    unmatched_records: int = 0
    domains_resolved: int = 0
    patterns_discovered: int = 0
    patterns_verified: int = 0

    # Phase statistics
    phase1_stats: Optional[Phase1Stats] = None
    phase1b_stats: Optional[Phase1bStats] = None
    phase2_stats: Optional[Phase2Stats] = None
    phase3_stats: Optional[Phase3Stats] = None
    phase4_stats: Optional[Phase4Stats] = None

    # Error tracking
    errors: int = 0
    warnings: int = 0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            'run_id': self.run_id,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'duration_seconds': self.duration_seconds,
            'input_records': self.input_records,
            'matched_records': self.matched_records,
            'unmatched_records': self.unmatched_records,
            'domains_resolved': self.domains_resolved,
            'patterns_discovered': self.patterns_discovered,
            'patterns_verified': self.patterns_verified,
            'errors': self.errors,
            'warnings': self.warnings
        }


@dataclass
class PipelineRun:
    """Tracks a single pipeline execution."""
    run_id: str
    started_at: datetime
    completed_at: Optional[datetime] = None
    status: str = 'running'  # 'running', 'completed', 'failed'
    input_file: Optional[str] = None
    output_directory: str = './output'
    stats: Optional[PipelineRunStats] = None
    error_message: Optional[str] = None


class CompanyIdentityPipeline:
    """
    Company Identity Pipeline Orchestrator (Phases 1-4).

    This pipeline handles:
    - Company matching (exact, fuzzy, domain-based)
    - Domain resolution and validation
    - Email pattern discovery via tiered waterfall
    - Pattern verification

    Output is passed to the People Pipeline (Phases 5-8) for email
    generation, slot assignment, and database writes.
    """

    def __init__(self, config: Dict[str, Any] = None, logger: PipelineLogger = None):
        """
        Initialize Company Identity Pipeline.

        Args:
            config: Pipeline configuration dictionary
            logger: Optional PipelineLogger instance
        """
        self.config = config or {}
        self.run_id = str(uuid.uuid4())[:8]
        self.logger = logger or PipelineLogger(run_id=self.run_id, config=self.config)

        # Output directory
        self.output_dir = Path(self.config.get('output_directory', './output'))
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Initialize Provider Benchmark Engine (System-Level Singleton)
        self.provider_benchmark = ProviderBenchmarkEngine.get_instance()

        # Initialize Waterfall Optimization Engine (System-Level)
        self.waterfall_optimizer = WaterfallOptimizer()

        # Initialize Movement Engine (4-Funnel GTM System)
        # Hooks only - no database writes yet
        self.movement_engine = MovementEngine()

        # Initialize phases with shared logger
        self.phase1 = Phase1CompanyMatching(config=self.config, logger=self.logger)
        self.phase1b = Phase1bUnmatchedHoldExport(config=self.config, logger=self.logger)
        self.phase2 = Phase2DomainResolution(config=self.config, logger=self.logger)
        self.phase3 = Phase3EmailPatternWaterfall(config=self.config, logger=self.logger)
        self.phase4 = Phase4PatternVerification(config=self.config, logger=self.logger)

        # Run tracking
        self.current_run: Optional[PipelineRun] = None

    def run(self, people_df: pd.DataFrame,
            company_df: pd.DataFrame = None,
            save_intermediates: bool = True) -> Tuple[pd.DataFrame, PipelineRunStats]:
        """
        Run the complete Company Identity Pipeline (Phases 1-4).

        Args:
            people_df: Input DataFrame with people records
                Required columns: first_name, last_name, company_name
                Optional columns: company_domain, city, state, email, title
            company_df: Company master DataFrame (loads from config if not provided)
                Required columns: company_unique_id, company_name
                Optional columns: website_url, domain, address_city, address_state
            save_intermediates: Whether to save intermediate outputs

        Returns:
            Tuple of (final_df, PipelineRunStats)
        """
        start_time = time.time()
        self.current_run = PipelineRun(
            run_id=self.run_id,
            started_at=datetime.now(),
            output_directory=str(self.output_dir)
        )

        stats = PipelineRunStats(
            run_id=self.run_id,
            started_at=datetime.now(),
            input_records=len(people_df)
        )

        self.logger.info(
            f"Starting Company Identity Pipeline run {self.run_id}",
            metadata={'input_records': len(people_df)}
        )

        try:
            # ==========================================
            # PHASE 1: Company Matching
            # ==========================================
            self.logger.info("=" * 60)
            self.logger.info("PHASE 1: Company Matching")
            self.logger.info("=" * 60)

            if company_df is None:
                company_df = self._load_company_master()

            phase1_result, phase1_stats = self.phase1.run(people_df, company_df)
            stats.phase1_stats = phase1_stats

            # Split into matched and unmatched
            matched_df = phase1_result[
                (phase1_result['match_type'].notna()) &
                (phase1_result['match_type'] != 'none') &
                (phase1_result['is_collision'] != True)
            ].copy()

            unmatched_df = phase1_result[
                (phase1_result['match_type'].isna()) |
                (phase1_result['match_type'] == 'none') |
                (phase1_result['is_collision'] == True)
            ].copy()

            stats.matched_records = len(matched_df)
            stats.unmatched_records = len(unmatched_df)

            self.logger.info(
                f"Phase 1 complete: {stats.matched_records} matched, "
                f"{stats.unmatched_records} unmatched/collision"
            )

            if save_intermediates:
                phase1_result.to_csv(
                    self.output_dir / f'phase1_results_{self.run_id}.csv', index=False
                )

            # ==========================================
            # PHASE 1b: Unmatched Hold Export
            # ==========================================
            if len(unmatched_df) > 0:
                self.logger.info("=" * 60)
                self.logger.info("PHASE 1b: Unmatched Hold Export")
                self.logger.info("=" * 60)

                hold_path = str(self.output_dir / f'people_unmatched_hold_{self.run_id}.csv')
                hold_result, phase1b_stats = self.phase1b.run(unmatched_df, hold_path, self.run_id)
                stats.phase1b_stats = phase1b_stats

                self.logger.info(f"Phase 1b complete: {hold_result.records_exported} exported to HOLD")

            # ==========================================
            # PHASE 2: Domain Resolution
            # ==========================================
            self.logger.info("=" * 60)
            self.logger.info("PHASE 2: Domain Resolution")
            self.logger.info("=" * 60)

            if len(matched_df) == 0:
                self.logger.warning("No matched records for Phase 2")
                phase2_result = matched_df.copy()
                phase2_stats = Phase2Stats()
            else:
                phase2_result, phase2_stats = self.phase2.run(matched_df, company_df)

            stats.phase2_stats = phase2_stats
            stats.domains_resolved = phase2_stats.valid_domains

            self.logger.info(
                f"Phase 2 complete: {stats.domains_resolved} domains resolved, "
                f"{phase2_stats.missing_domains} missing"
            )

            if save_intermediates:
                phase2_result.to_csv(
                    self.output_dir / f'phase2_results_{self.run_id}.csv', index=False
                )

            # ==========================================
            # PHASE 3: Email Pattern Waterfall
            # ==========================================
            self.logger.info("=" * 60)
            self.logger.info("PHASE 3: Email Pattern Waterfall")
            self.logger.info("=" * 60)

            # Filter to records with valid domains
            has_domain_df = phase2_result[
                (phase2_result['resolved_domain'].notna()) &
                (phase2_result['domain_status'].isin(['valid', 'valid_no_mx']))
            ].copy() if 'resolved_domain' in phase2_result.columns else phase2_result

            if len(has_domain_df) == 0:
                self.logger.warning("No records with valid domains for Phase 3")
                phase3_result = phase2_result.copy()
                phase3_stats = Phase3Stats()
            else:
                phase3_result, phase3_stats = self.phase3.run(has_domain_df)

            stats.phase3_stats = phase3_stats
            stats.patterns_discovered = phase3_stats.patterns_found

            self.logger.info(
                f"Phase 3 complete: {stats.patterns_discovered} patterns discovered, "
                f"{phase3_stats.patterns_suggested} suggested"
            )

            if save_intermediates:
                phase3_result.to_csv(
                    self.output_dir / f'phase3_results_{self.run_id}.csv', index=False
                )

            # ==========================================
            # PHASE 4: Pattern Verification
            # ==========================================
            self.logger.info("=" * 60)
            self.logger.info("PHASE 4: Pattern Verification")
            self.logger.info("=" * 60)

            if len(phase3_result) == 0 or 'email_pattern' not in phase3_result.columns:
                self.logger.warning("No patterns to verify in Phase 4")
                phase4_result = phase3_result.copy()
                phase4_stats = Phase4Stats()
            else:
                phase4_result, phase4_stats = self.phase4.run(phase3_result)

            stats.phase4_stats = phase4_stats
            stats.patterns_verified = phase4_stats.patterns_verified

            self.logger.info(
                f"Phase 4 complete: {stats.patterns_verified} verified, "
                f"{phase4_stats.patterns_likely_valid} likely valid, "
                f"{phase4_stats.fallbacks_required} need fallback"
            )

            # ==========================================
            # FINALIZE
            # ==========================================
            stats.completed_at = datetime.now()
            stats.duration_seconds = time.time() - start_time

            # Save final output
            final_output_path = self.output_dir / f'company_identity_output_{self.run_id}.csv'
            phase4_result.to_csv(final_output_path, index=False)

            # Save run statistics
            stats_path = self.output_dir / f'pipeline_stats_{self.run_id}.json'
            with open(stats_path, 'w') as f:
                json.dump(stats.to_dict(), f, indent=2)

            # Save audit log
            self.logger.save_audit_log(
                str(self.output_dir / f'audit_log_{self.run_id}.json')
            )

            self.current_run.status = 'completed'
            self.current_run.completed_at = datetime.now()

            self.logger.info("=" * 60)
            self.logger.info(f"PIPELINE COMPLETE in {stats.duration_seconds:.2f}s")
            self.logger.info(f"  Input: {stats.input_records}")
            self.logger.info(f"  Matched: {stats.matched_records}")
            self.logger.info(f"  Domains: {stats.domains_resolved}")
            self.logger.info(f"  Patterns: {stats.patterns_discovered}")
            self.logger.info(f"  Verified: {stats.patterns_verified}")
            self.logger.info(f"  Output: {final_output_path}")
            self.logger.info("=" * 60)

            return phase4_result, stats

        except Exception as e:
            self.current_run.status = 'failed'
            self.current_run.error_message = str(e)
            stats.errors += 1

            log_error(self.logger, e, context={'phase': 'orchestration'})

            # Save partial audit log on error
            self.logger.save_audit_log(
                str(self.output_dir / f'audit_log_{self.run_id}_error.json')
            )

            raise

    def run_phase(self, phase_num: int, input_df: pd.DataFrame,
                  company_df: pd.DataFrame = None) -> pd.DataFrame:
        """
        Run a specific phase only.

        Args:
            phase_num: Phase number (1, 2, 3, or 4)
            input_df: Input DataFrame for phase
            company_df: Company master (required for Phase 1 and 2)

        Returns:
            DataFrame with phase output
        """
        if phase_num == 1:
            if company_df is None:
                company_df = self._load_company_master()
            result, _ = self.phase1.run(input_df, company_df)
            return result
        elif phase_num == 2:
            result, _ = self.phase2.run(input_df, company_df)
            return result
        elif phase_num == 3:
            result, _ = self.phase3.run(input_df)
            return result
        elif phase_num == 4:
            result, _ = self.phase4.run(input_df)
            return result
        else:
            raise ValueError(f"Invalid phase number: {phase_num}. Must be 1-4.")

    def _load_company_master(self) -> pd.DataFrame:
        """
        Load company_master from database or file.

        Returns:
            DataFrame with company records
        """
        # Check for file path in config
        company_file = self.config.get('company_master_file')
        if company_file and Path(company_file).exists():
            self.logger.info(f"Loading company_master from {company_file}")
            return pd.read_csv(company_file)

        # Check for database config
        db_config = self.config.get('database', {})
        if db_config:
            self.logger.info("Loading company_master from database")
            return self._load_from_database(db_config)

        raise ValueError(
            "No company_master source configured. "
            "Set company_master_file or database config."
        )

    def _load_from_database(self, db_config: Dict[str, Any]) -> pd.DataFrame:
        """Load company_master from database."""
        try:
            import psycopg2
            from psycopg2.extras import RealDictCursor

            conn = psycopg2.connect(
                host=db_config.get('host'),
                port=db_config.get('port', 5432),
                database=db_config.get('database'),
                user=db_config.get('user'),
                password=db_config.get('password'),
                sslmode=db_config.get('sslmode', 'require')
            )

            query = """
                SELECT
                    company_unique_id,
                    company_name,
                    website_url,
                    address_city,
                    address_state
                FROM company.company_master
            """

            df = pd.read_sql(query, conn)
            conn.close()

            self.logger.info(f"Loaded {len(df)} companies from database")
            return df

        except Exception as e:
            self.logger.error(f"Failed to load from database: {e}", error=e)
            raise

    def load_input_file(self, file_path: str) -> pd.DataFrame:
        """
        Load input data from file.

        Supports: CSV, Excel, JSON

        Args:
            file_path: Path to input file

        Returns:
            DataFrame with input records
        """
        path = Path(file_path)

        if not path.exists():
            raise FileNotFoundError(f"Input file not found: {file_path}")

        if path.suffix.lower() == '.csv':
            return pd.read_csv(file_path)
        elif path.suffix.lower() in ['.xlsx', '.xls']:
            return pd.read_excel(file_path)
        elif path.suffix.lower() == '.json':
            return pd.read_json(file_path)
        else:
            raise ValueError(f"Unsupported file format: {path.suffix}")

    def get_run_status(self) -> Dict[str, Any]:
        """
        Get current pipeline status.

        Returns:
            Dict with run status, progress, and metrics
        """
        if not self.current_run:
            return {'status': 'not_started'}

        return {
            'run_id': self.current_run.run_id,
            'status': self.current_run.status,
            'started_at': self.current_run.started_at.isoformat(),
            'completed_at': self.current_run.completed_at.isoformat() if self.current_run.completed_at else None,
            'output_directory': self.current_run.output_directory,
            'error': self.current_run.error_message
        }

    # ==========================================
    # WATERFALL OPTIMIZATION
    # ==========================================

    def optimize_waterfall(self):
        """
        Generate optimized waterfall tier ordering.

        Reads Provider Benchmark Engine (PBE) scorecards and produces
        an OptimizationPlan with recommended tier ordering.

        Returns:
            OptimizationPlan with:
                - ordered_providers: Dict of tier -> provider list
                - promoted: List of promoted providers
                - demoted: List of demoted providers
                - removed: List of removed providers
                - rationale: Explanation of changes
        """
        return self.waterfall_optimizer.generate_optimized_order()

    def get_waterfall_profiles(self) -> Dict[str, Any]:
        """
        Get all waterfall profiles for different pipelines.

        Returns optimized waterfall orderings for:
        - global: Baseline waterfall order
        - company_pipeline: Company Pipeline specific order
        - people_pipeline: People Pipeline order (prioritizes quality)
        - talent_flow_pipeline: Talent Flow order (prioritizes speed)

        NOTE: This method does NOT apply profiles automatically.
        Profiles are returned for inspection/manual application only.

        Returns:
            Dict with keys:
                - global: Global waterfall order
                - company_pipeline: Company Pipeline order
                - people_pipeline: People Pipeline order
                - talent_flow_pipeline: Talent Flow order
        """
        plan = self.optimize_waterfall()
        return {
            "global": plan.global_order,
            "company_pipeline": plan.company_pipeline_order,
            "people_pipeline": plan.people_pipeline_order,
            "talent_flow_pipeline": plan.talent_flow_pipeline_order
        }

    # ==========================================
    # TALENT FLOW ORCHESTRATORS
    # ==========================================

    def run_company_identity_pipeline(self, people_df: pd.DataFrame,
                                       company_df: pd.DataFrame = None) -> Tuple[pd.DataFrame, PipelineRunStats]:
        """
        Wrapper around Company Identity Pipeline (Phases 1-4).

        This is an alias for run() method, provided for clarity when used
        in conjunction with Talent Flow processing.

        Args:
            people_df: Input DataFrame with people records
            company_df: Optional company master DataFrame

        Returns:
            Tuple of (result_df, PipelineRunStats)
        """
        # TODO: implement - currently delegates to run()
        pass

    def run_talent_flow_pipeline(self, movement_event: Dict[str, Any]) -> Optional[CompanyGateResult]:
        """
        Entry point for Talent Flow.

        Handles employer change events by ensuring the new company
        exists and is enriched before processing the person update.

        Steps (shell only):
        1. Extract new company name from movement_event
        2. Invoke TalentFlowCompanyGate to ensure company exists/enriched
        3. Pass enriched company into People Pipeline (Phases 5-8)

        Args:
            movement_event: Dict containing movement details:
                - person_id: ID of person who changed employers
                - new_company_name: Name of new employer
                - previous_company_id: Optional ID of previous employer
                - movement_type: Type of change (job_change, promotion, etc.)
                - detected_at: When the change was detected
                - source: Source of the movement signal

        Returns:
            CompanyGateResult or None
        """
        # TODO: implement
        # Step 1: Extract new company name
        # Step 2: Load company master
        # Step 3: Run TalentFlowCompanyGate
        # Step 4: If company missing, trigger Company Identity Pipeline
        # Step 5: Pass to People Pipeline (Phases 5-8)
        pass

    def process_talent_flow_batch(self, movement_events: list) -> list:
        """
        Process multiple talent flow events in batch.

        Args:
            movement_events: List of movement event dicts

        Returns:
            List of CompanyGateResult objects
        """
        # TODO: implement batch processing
        pass

    # ==========================================
    # MOVEMENT ENGINE HOOKS (4-Funnel GTM System)
    # ==========================================
    # These hooks are called from appropriate pipeline locations
    # to detect events for the Movement Engine. No database writes.

    def hook_movement_reply(self, company_id: str, person_id: str,
                            reply_text: str = None, metadata: Dict[str, Any] = None) -> None:
        """
        Hook: Detect reply event for Movement Engine.

        Called when an email reply is received.
        Logs event and queues for Movement Engine processing.

        Args:
            company_id: Company unique ID
            person_id: Person unique ID
            reply_text: Optional reply text for sentiment analysis
            metadata: Optional additional metadata
        """
        try:
            event = self.movement_engine.detect_event(
                company_id=company_id,
                person_id=person_id,
                event_type='email_reply',
                metadata={'reply_text': reply_text, **(metadata or {})}
            )
            self.logger.log_movement_reply(
                company_id=company_id,
                person_id=person_id,
                reply_text=reply_text,
                sentiment=event.metadata.get('sentiment') if event else None
            )
        except Exception as e:
            self.logger.warning(f"Movement hook error (reply): {e}")

    def hook_movement_warm_engagement(self, company_id: str, person_id: str,
                                       opens: int = 0, clicks: int = 0,
                                       bit_score: int = None,
                                       metadata: Dict[str, Any] = None) -> None:
        """
        Hook: Detect warm engagement event for Movement Engine.

        Called when engagement thresholds are crossed (opens >= 3, clicks >= 2,
        or BIT score crosses threshold).

        Args:
            company_id: Company unique ID
            person_id: Person unique ID
            opens: Number of email opens
            clicks: Number of link clicks
            bit_score: Optional BIT score
            metadata: Optional additional metadata
        """
        try:
            # Determine event type based on engagement
            if opens >= 3:
                event_type = 'email_opens'
            elif clicks >= 2:
                event_type = 'link_clicks'
            elif bit_score and bit_score >= 25:
                event_type = 'bit_threshold'
            else:
                event_type = 'warm_engagement'

            event = self.movement_engine.detect_event(
                company_id=company_id,
                person_id=person_id,
                event_type=event_type,
                metadata={'opens': opens, 'clicks': clicks, 'bit_score': bit_score, **(metadata or {})}
            )
            self.logger.log_movement_warm_engagement(
                company_id=company_id,
                person_id=person_id,
                opens=opens,
                clicks=clicks,
                bit_score=bit_score
            )
        except Exception as e:
            self.logger.warning(f"Movement hook error (warm_engagement): {e}")

    def hook_movement_talentflow(self, company_id: str, person_id: str,
                                  signal_type: str, new_company: str = None,
                                  metadata: Dict[str, Any] = None) -> None:
        """
        Hook: Detect TalentFlow event for Movement Engine.

        Called when TalentFlow detects job movement (employer change,
        promotion, title change).

        Args:
            company_id: Company unique ID
            person_id: Person unique ID
            signal_type: Type of TalentFlow signal (job_change, promotion, etc.)
            new_company: Optional new company name
            metadata: Optional additional metadata
        """
        try:
            event = self.movement_engine.detect_event(
                company_id=company_id,
                person_id=person_id,
                event_type='talentflow_signal',
                metadata={'signal_type': signal_type, 'new_company': new_company, **(metadata or {})}
            )
            self.logger.log_movement_talentflow(
                company_id=company_id,
                person_id=person_id,
                signal_type=signal_type,
                new_company=new_company
            )
        except Exception as e:
            self.logger.warning(f"Movement hook error (talentflow): {e}")

    def hook_movement_appointment(self, company_id: str, person_id: str,
                                   appointment_type: str = None,
                                   metadata: Dict[str, Any] = None) -> None:
        """
        Hook: Detect appointment booked event for Movement Engine.

        Called when a meeting is scheduled with a contact.

        Args:
            company_id: Company unique ID
            person_id: Person unique ID
            appointment_type: Optional type of appointment
            metadata: Optional additional metadata
        """
        try:
            event = self.movement_engine.detect_event(
                company_id=company_id,
                person_id=person_id,
                event_type='appointment_booked',
                metadata={'appointment_type': appointment_type, **(metadata or {})}
            )
            self.logger.log_movement_appointment(
                company_id=company_id,
                person_id=person_id,
                appointment_type=appointment_type
            )
        except Exception as e:
            self.logger.warning(f"Movement hook error (appointment): {e}")

    # ==========================================
    # PEOPLE PIPELINE (PHASES 5-8)
    # ==========================================

    def run_people_pipeline(
        self,
        matched_people_df: pd.DataFrame,
        pattern_df: pd.DataFrame,
        output_dir: str = None
    ) -> Tuple[PipelineSummary, Dict[str, Any]]:
        """
        Run the People Pipeline (Phases 5-8).

        Takes output from Company Identity Pipeline (Phases 1-4) and:
        - Phase 5: Generates emails using verified patterns
        - Phase 6: Assigns people to company HR slots
        - Phase 7: Builds enrichment queue for items needing follow-up
        - Phase 8: Writes final output to CSV files

        REQUIRES: company_id anchor (Company-First doctrine)

        Args:
            matched_people_df: DataFrame with matched people from Company Pipeline
                Required columns: person_id, company_id, first_name, last_name
                Optional columns: job_title, title
            pattern_df: DataFrame with verified patterns from Phase 4
                Required columns: company_id, email_pattern, resolved_domain
                Optional columns: pattern_confidence, verification_status
            output_dir: Output directory (default: configured output_dir)

        Returns:
            Tuple of (PipelineSummary, phase_stats_dict)
        """
        start_time = time.time()
        output_dir = output_dir or str(self.output_dir)

        self.logger.info("=" * 60)
        self.logger.info("STARTING PEOPLE PIPELINE (Phases 5-8)")
        self.logger.info("=" * 60)

        # Track all phase stats
        phase_stats = {
            'started_at': datetime.now(),
            'pipeline_start_time': start_time,
            'input_patterns': len(pattern_df) if pattern_df is not None else 0
        }

        try:
            # ==========================================
            # PHASE 5: Email Generation
            # ==========================================
            self.logger.info("-" * 60)
            self.logger.info("PHASE 5: Email Generation")
            self.logger.info("-" * 60)

            phase5 = Phase5EmailGeneration(config=self.config)
            people_with_emails_df, people_missing_pattern_df, phase5_stats = phase5.run(
                matched_people_df, pattern_df
            )

            phase_stats['phase5'] = {
                'total_input': phase5_stats.total_input,
                'emails_generated': phase5_stats.emails_generated,
                'verified_emails': phase5_stats.verified_emails,
                'derived_emails': phase5_stats.derived_emails,
                'low_confidence_emails': phase5_stats.low_confidence_emails,
                'waterfall_emails': phase5_stats.waterfall_emails,
                'waterfall_patterns_discovered': phase5_stats.waterfall_patterns_discovered,
                'waterfall_api_calls': phase5_stats.waterfall_api_calls,
                'missing_pattern': phase5_stats.missing_pattern,
                'missing_name': phase5_stats.missing_name,
                'duration_seconds': phase5_stats.duration_seconds
            }

            waterfall_info = ""
            if phase5_stats.waterfall_patterns_discovered > 0:
                waterfall_info = f" ({phase5_stats.waterfall_patterns_discovered} patterns via waterfall)"

            self.logger.info(
                f"Phase 5 complete: {phase5_stats.emails_generated} emails generated, "
                f"{phase5_stats.missing_pattern} missing pattern{waterfall_info}"
            )

            # ==========================================
            # PHASE 6: Slot Assignment
            # ==========================================
            self.logger.info("-" * 60)
            self.logger.info("PHASE 6: Slot Assignment")
            self.logger.info("-" * 60)

            phase6 = Phase6SlotAssignment(config=self.config)
            slotted_df, unslotted_df, slot_summary_df, phase6_stats = phase6.run(
                people_with_emails_df
            )

            phase_stats['phase6'] = {
                'total_input': phase6_stats.total_input,
                'slots_assigned': phase6_stats.slots_assigned,
                'chro_count': phase6_stats.chro_count,
                'hr_manager_count': phase6_stats.hr_manager_count,
                'benefits_lead_count': phase6_stats.benefits_lead_count,
                'payroll_admin_count': phase6_stats.payroll_admin_count,
                'hr_support_count': phase6_stats.hr_support_count,
                'unslotted_count': phase6_stats.unslotted_count,
                'conflicts_resolved': phase6_stats.conflicts_resolved,
                'duration_seconds': phase6_stats.duration_seconds
            }

            self.logger.info(
                f"Phase 6 complete: {phase6_stats.slots_assigned} slots assigned, "
                f"{phase6_stats.unslotted_count} unslotted"
            )

            # ==========================================
            # PHASE 7: Enrichment Queue
            # ==========================================
            self.logger.info("-" * 60)
            self.logger.info("PHASE 7: Enrichment Queue")
            self.logger.info("-" * 60)

            phase7 = Phase7EnrichmentQueue(config=self.config)
            enrichment_queue_df, resolved_patterns_df, phase7_stats = phase7.run(
                people_missing_pattern_df,
                unslotted_df,
                slot_summary_df
            )

            phase_stats['phase7'] = {
                'total_queued': phase7_stats.total_queued,
                'high_priority': phase7_stats.high_priority,
                'medium_priority': phase7_stats.medium_priority,
                'low_priority': phase7_stats.low_priority,
                'company_items': phase7_stats.company_items,
                'person_items': phase7_stats.person_items,
                'pattern_missing': phase7_stats.pattern_missing,
                'slot_missing': phase7_stats.slot_missing,
                'waterfall_processed': phase7_stats.waterfall_processed,
                'waterfall_resolved': phase7_stats.waterfall_resolved,
                'waterfall_exhausted': phase7_stats.waterfall_exhausted,
                'waterfall_api_calls': phase7_stats.waterfall_api_calls,
                'duration_seconds': phase7_stats.duration_seconds
            }

            waterfall_info = ""
            if phase7_stats.waterfall_processed > 0:
                waterfall_info = f" (Waterfall: {phase7_stats.waterfall_resolved}/{phase7_stats.waterfall_processed} resolved)"

            self.logger.info(
                f"Phase 7 complete: {phase7_stats.total_queued} items queued "
                f"(HIGH: {phase7_stats.high_priority}, MEDIUM: {phase7_stats.medium_priority}, "
                f"LOW: {phase7_stats.low_priority}){waterfall_info}"
            )

            # ==========================================
            # PHASE 8: Output Writer
            # ==========================================
            self.logger.info("-" * 60)
            self.logger.info("PHASE 8: Output Writer")
            self.logger.info("-" * 60)

            phase8_config = {**self.config, 'output_dir': output_dir}
            phase8 = Phase8OutputWriter(config=phase8_config)
            summary, phase8_stats = phase8.run(
                people_with_emails_df,
                slotted_df,
                unslotted_df,
                slot_summary_df,
                enrichment_queue_df,
                phase_stats
            )

            phase_stats['phase8'] = {
                'files_written': phase8_stats.files_written,
                'total_records': phase8_stats.total_records,
                'people_final_count': phase8_stats.people_final_count,
                'slot_assignments_count': phase8_stats.slot_assignments_count,
                'enrichment_queue_count': phase8_stats.enrichment_queue_count,
                'errors': phase8_stats.errors,
                'duration_seconds': phase8_stats.duration_seconds
            }

            self.logger.info(
                f"Phase 8 complete: {phase8_stats.files_written} files written, "
                f"{phase8_stats.total_records} total records"
            )

            # ==========================================
            # FINALIZE
            # ==========================================
            total_duration = time.time() - start_time

            self.logger.info("=" * 60)
            self.logger.info(f"PEOPLE PIPELINE COMPLETE in {total_duration:.2f}s")
            self.logger.info(f"  Input: {phase5_stats.total_input} people, {len(pattern_df) if pattern_df is not None else 0} patterns")
            self.logger.info(f"  Emails Generated: {phase5_stats.emails_generated}")
            self.logger.info(f"  Slots Assigned: {phase6_stats.slots_assigned}")
            self.logger.info(f"  Queued for Enrichment: {phase7_stats.total_queued}")
            self.logger.info(f"  Files Written: {phase8_stats.files_written}")
            self.logger.info(f"  Output Directory: {output_dir}")
            self.logger.info("=" * 60)

            return summary, phase_stats

        except Exception as e:
            log_error(self.logger, e, context={'phase': 'people_pipeline'})
            raise


# Convenience function for simple usage
def run_company_identity_pipeline(
    people_df: pd.DataFrame,
    company_df: pd.DataFrame = None,
    config: Dict[str, Any] = None
) -> Tuple[pd.DataFrame, PipelineRunStats]:
    """
    Run the Company Identity Pipeline.

    Args:
        people_df: Input DataFrame with people records
        company_df: Optional company master DataFrame
        config: Optional configuration

    Returns:
        Tuple of (result_df, PipelineRunStats)
    """
    pipeline = CompanyIdentityPipeline(config=config)
    return pipeline.run(people_df, company_df)


def run_people_pipeline(
    matched_people_df: pd.DataFrame,
    pattern_df: pd.DataFrame,
    output_dir: str = './output',
    config: Dict[str, Any] = None
) -> Tuple[PipelineSummary, Dict[str, Any]]:
    """
    Run the People Pipeline (Phases 5-8).

    Convenience function for running People Pipeline standalone.

    Args:
        matched_people_df: DataFrame with matched people from Company Pipeline
            Required columns: person_id, company_id, first_name, last_name
            Optional columns: job_title, title
        pattern_df: DataFrame with verified patterns from Phase 4
            Required columns: company_id, email_pattern, resolved_domain
        output_dir: Output directory for CSV files
        config: Optional configuration

    Returns:
        Tuple of (PipelineSummary, phase_stats_dict)
    """
    config = config or {}
    config['output_directory'] = output_dir

    pipeline = CompanyIdentityPipeline(config=config)
    return pipeline.run_people_pipeline(matched_people_df, pattern_df, output_dir)


def main():
    """Command-line entry point."""
    parser = argparse.ArgumentParser(
        description="Company Identity Pipeline (Phases 1-4)"
    )
    parser.add_argument(
        "--input", "-i",
        required=True,
        help="Path to input CSV/Excel file with people records"
    )
    parser.add_argument(
        "--companies", "-c",
        help="Path to company master CSV (optional, uses database if not provided)"
    )
    parser.add_argument(
        "--output", "-o",
        default="./output",
        help="Output directory for results (default: ./output)"
    )
    parser.add_argument(
        "--config",
        help="Path to configuration YAML file"
    )
    parser.add_argument(
        "--phase",
        type=int,
        choices=[1, 2, 3, 4],
        help="Run only specific phase (1-4)"
    )
    parser.add_argument(
        "--no-intermediates",
        action="store_true",
        help="Don't save intermediate outputs"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate input without processing"
    )

    args = parser.parse_args()

    # Load configuration
    config = {}
    if args.config:
        config = load_config(args.config).__dict__
    config['output_directory'] = args.output

    # Initialize pipeline
    pipeline = CompanyIdentityPipeline(config=config)

    # Load input data
    print(f"Loading input from {args.input}...")
    people_df = pipeline.load_input_file(args.input)
    print(f"Loaded {len(people_df)} records")

    # Load company master
    company_df = None
    if args.companies:
        print(f"Loading companies from {args.companies}...")
        company_df = pd.read_csv(args.companies)
        print(f"Loaded {len(company_df)} companies")

    # Dry run - just validate
    if args.dry_run:
        print("\n=== DRY RUN - Validation Only ===")
        print(f"Input columns: {list(people_df.columns)}")
        print(f"Records: {len(people_df)}")
        required = ['first_name', 'last_name', 'company_name']
        missing = [c for c in required if c not in people_df.columns]
        if missing:
            print(f"WARNING: Missing required columns: {missing}")
        else:
            print("All required columns present")
        return

    # Run specific phase or full pipeline
    if args.phase:
        print(f"\n=== Running Phase {args.phase} Only ===")
        result_df = pipeline.run_phase(args.phase, people_df, company_df)
        output_path = Path(args.output) / f'phase{args.phase}_results.csv'
        result_df.to_csv(output_path, index=False)
        print(f"Output saved to {output_path}")
    else:
        print("\n=== Running Full Company Identity Pipeline ===")
        result_df, stats = pipeline.run(
            people_df,
            company_df,
            save_intermediates=not args.no_intermediates
        )
        print(f"\nPipeline completed in {stats.duration_seconds:.2f}s")
        print(f"Results saved to {args.output}")


if __name__ == "__main__":
    main()
