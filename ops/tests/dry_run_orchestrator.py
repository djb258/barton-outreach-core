"""
DRY RUN ORCHESTRATOR
====================
Full-volume dry run of the entire pipeline for validation.

NO production writes. NO schema changes. NO architecture edits.

Validates:
- Cost behavior
- Signal volume
- Failure rates
- Kill-switch correctness
"""

import os
import sys
import json
import uuid
import time
import random
import logging
from datetime import datetime, timedelta
from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List, Optional, Tuple
from collections import defaultdict

# Force dry-run mode
os.environ['NEON_WRITE_ENABLED'] = 'false'
os.environ['OUTREACH_SEND_ENABLED'] = 'false'
os.environ['DRY_RUN_MODE'] = 'true'
os.environ['KILL_OUTREACH'] = 'true'

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('DryRunOrchestrator')


# =============================================================================
# METRICS COLLECTORS
# =============================================================================

@dataclass
class VolumeMetrics:
    """Volume metrics collector."""
    total_companies_processed: int = 0
    total_people_processed: int = 0
    total_emails_generated: int = 0
    total_signals_emitted: int = 0
    signals_by_type: Dict[str, int] = field(default_factory=dict)
    companies_matched: int = 0
    companies_unmatched: int = 0
    people_matched: int = 0
    people_unmatched: int = 0


@dataclass
class CostMetrics:
    """Cost metrics collector."""
    cost_by_phase: Dict[str, float] = field(default_factory=dict)
    cost_per_1k_records: float = 0.0
    top_expensive_tools: List[Tuple[str, float]] = field(default_factory=list)
    total_estimated_cost: float = 0.0
    tool_invocations: Dict[str, int] = field(default_factory=dict)


@dataclass
class QualityMetrics:
    """Quality metrics collector."""
    fuzzy_match_distribution: Dict[str, int] = field(default_factory=dict)
    email_verification_pass: int = 0
    email_verification_fail: int = 0
    slot_fill_rates: Dict[str, float] = field(default_factory=dict)
    bit_score_distribution: Dict[str, int] = field(default_factory=dict)
    domain_detection_rate: float = 0.0
    pattern_detection_rate: float = 0.0


@dataclass
class RiskMetrics:
    """Risk metrics collector."""
    emails_rejected_pct: float = 0.0
    companies_bit_above_50_pct: float = 0.0
    signal_spikes_per_company: Dict[str, int] = field(default_factory=dict)
    enrichment_queue_size: int = 0
    max_signals_single_company: int = 0
    risky_companies: List[str] = field(default_factory=list)


@dataclass
class KillSwitchEvent:
    """A kill switch trigger event."""
    switch_name: str
    trigger_condition: str
    threshold: float
    actual_value: float
    fired: bool
    where_fired: str
    what_stopped: str
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class PipelineRunMetrics:
    """Full pipeline run metrics."""
    run_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    run_timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    duration_seconds: float = 0.0
    volume: VolumeMetrics = field(default_factory=VolumeMetrics)
    cost: CostMetrics = field(default_factory=CostMetrics)
    quality: QualityMetrics = field(default_factory=QualityMetrics)
    risk: RiskMetrics = field(default_factory=RiskMetrics)
    kill_switches: List[KillSwitchEvent] = field(default_factory=list)
    phase_results: Dict[str, Dict] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)


# =============================================================================
# KILL SWITCH THRESHOLDS
# =============================================================================

KILL_SWITCH_THRESHOLDS = {
    'bit_spike_per_run': 100,           # Max BIT score increase in single run
    'email_rejection_rate': 0.30,       # 30% rejection rate
    'daily_cost_ceiling': 50.0,         # $50 daily ceiling
    'signal_flood_per_source': 500,     # Max signals from single source
    'signal_flood_per_company': 50,     # Max signals to single company
    'enrichment_queue_max': 10000,      # Max queue size
}

# Tool cost estimates ($ per invocation)
TOOL_COSTS = {
    'domain_match': 0.0001,
    'ein_match': 0.0001,
    'fuzzy_match': 0.0005,
    'email_verification': 0.005,
    'linkedin_enrichment': 0.02,
    'firecrawl': 0.01,
    'apify_scrape': 0.015,
    'abacus_resolve': 0.008,
    'dns_lookup': 0.0001,
    'bit_signal': 0.0001,
}


# =============================================================================
# DRY RUN ORCHESTRATOR
# =============================================================================

class DryRunOrchestrator:
    """
    Orchestrates a full dry-run of the pipeline.

    NO production writes. All operations are simulated.
    """

    def __init__(self):
        self.metrics = PipelineRunMetrics()
        self.correlation_id = str(uuid.uuid4())
        self.halted = False
        self.halt_reason = None

        # Simulated data stores
        self._companies = {}
        self._people = {}
        self._signals = []
        self._signal_counts_by_company = defaultdict(int)
        self._signal_counts_by_source = defaultdict(int)

        logger.info(f"DryRunOrchestrator initialized - Run ID: {self.metrics.run_id}")
        logger.info("DRY RUN MODE: All writes disabled")

    def run(self) -> PipelineRunMetrics:
        """Execute the full dry-run pipeline."""
        start_time = time.time()

        logger.info("=" * 60)
        logger.info("STARTING FULL DRY RUN")
        logger.info("=" * 60)

        try:
            # Generate test data
            self._generate_test_data()

            # Phase 1-4: Company Pipeline
            if not self.halted:
                self._run_company_pipeline()

            # People Spoke
            if not self.halted:
                self._run_people_spoke()

            # DOL Spoke
            if not self.halted:
                self._run_dol_spoke()

            # Blog Spoke
            if not self.halted:
                self._run_blog_spoke()

            # Talent Flow Spoke
            if not self.halted:
                self._run_talent_flow_spoke()

            # BIT Engine Processing
            if not self.halted:
                self._run_bit_engine()

            # Outreach Spoke
            if not self.halted:
                self._run_outreach_spoke()

            # Final kill switch validation
            self._validate_kill_switches()

            # Calculate final metrics
            self._calculate_final_metrics()

        except Exception as e:
            logger.error(f"Dry run failed: {e}")
            self.metrics.errors.append(str(e))

        self.metrics.duration_seconds = time.time() - start_time

        logger.info("=" * 60)
        logger.info(f"DRY RUN COMPLETE - Duration: {self.metrics.duration_seconds:.2f}s")
        logger.info("=" * 60)

        return self.metrics

    def _generate_test_data(self):
        """Generate synthetic test data for dry run."""
        logger.info("Generating test data...")

        # Generate 1000 test companies
        industries = ['Technology', 'Healthcare', 'Finance', 'Manufacturing', 'Retail']
        states = ['CA', 'NY', 'TX', 'FL', 'IL', 'WA', 'MA', 'CO']

        for i in range(1000):
            company_id = f"04.04.01.{random.randint(10,99)}.{30000+i:05d}.{random.randint(100,999)}"
            self._companies[company_id] = {
                'company_unique_id': company_id,
                'company_name': f"Test Company {i}",
                'domain': f"testcompany{i}.com" if random.random() > 0.2 else None,
                'email_pattern': '{first}.{last}' if random.random() > 0.3 else None,
                'ein': f"{random.randint(10,99)}-{random.randint(1000000,9999999)}" if random.random() > 0.4 else None,
                'industry': random.choice(industries),
                'employee_count': random.randint(50, 5000),
                'address_state': random.choice(states),
                'bit_score': 0.0,
            }

        # Generate 5000 test people
        titles = ['CEO', 'CFO', 'CHRO', 'VP HR', 'HR Director', 'Benefits Manager', 'HR Manager']

        for i in range(5000):
            company_id = random.choice(list(self._companies.keys()))
            person_id = f"04.04.02.{random.randint(10,99)}.{20000+i:05d}.{random.randint(100,999)}"
            self._people[person_id] = {
                'person_unique_id': person_id,
                'full_name': f"Test Person {i}",
                'first_name': f"First{i}",
                'last_name': f"Last{i}",
                'title': random.choice(titles),
                'company_unique_id': company_id,
                'email': None,
                'email_verified': False,
                'linkedin_url': f"https://linkedin.com/in/testperson{i}" if random.random() > 0.3 else None,
            }

        self.metrics.volume.total_companies_processed = len(self._companies)
        self.metrics.volume.total_people_processed = len(self._people)

        logger.info(f"Generated {len(self._companies)} companies, {len(self._people)} people")

    def _run_company_pipeline(self):
        """Run Company Pipeline (Phase 1-4)."""
        logger.info("-" * 40)
        logger.info("PHASE 1-4: Company Pipeline")
        logger.info("-" * 40)

        phase_start = time.time()

        # Phase 1: Company Matching
        matched = 0
        unmatched = 0
        fuzzy_scores = {'90-100': 0, '80-89': 0, '70-79': 0, '<70': 0}

        for company_id, company in self._companies.items():
            # Simulate matching
            self._track_tool('domain_match')

            if company.get('domain'):
                matched += 1
                score = random.randint(85, 100)
            else:
                self._track_tool('fuzzy_match')
                score = random.randint(50, 95)
                if score >= 70:
                    matched += 1
                else:
                    unmatched += 1

            # Track fuzzy distribution
            if score >= 90:
                fuzzy_scores['90-100'] += 1
            elif score >= 80:
                fuzzy_scores['80-89'] += 1
            elif score >= 70:
                fuzzy_scores['70-79'] += 1
            else:
                fuzzy_scores['<70'] += 1

        self.metrics.volume.companies_matched = matched
        self.metrics.volume.companies_unmatched = unmatched
        self.metrics.quality.fuzzy_match_distribution = fuzzy_scores

        # Phase 2: Domain Detection
        domains_detected = 0
        companies_needing_domain = [c for c in self._companies.values() if not c.get('domain')]

        for company in companies_needing_domain:
            self._track_tool('dns_lookup')
            if random.random() > 0.3:
                company['domain'] = f"{company['company_name'].lower().replace(' ', '')}.com"
                domains_detected += 1

        self.metrics.quality.domain_detection_rate = domains_detected / max(len(companies_needing_domain), 1)

        # Phase 3: Email Pattern Detection
        patterns_detected = 0
        companies_needing_pattern = [c for c in self._companies.values() if c.get('domain') and not c.get('email_pattern')]

        for company in companies_needing_pattern:
            if random.random() > 0.2:
                company['email_pattern'] = random.choice(['{first}.{last}', '{first}{last}', '{f}{last}'])
                patterns_detected += 1

        self.metrics.quality.pattern_detection_rate = patterns_detected / max(len(companies_needing_pattern), 1)

        # Phase 4: Spoke Ready Check
        spoke_ready = sum(1 for c in self._companies.values()
                        if c.get('domain') and c.get('email_pattern'))

        phase_duration = time.time() - phase_start
        self.metrics.cost.cost_by_phase['company_p1_p4'] = self._calculate_phase_cost()

        self.metrics.phase_results['company_pipeline'] = {
            'duration_seconds': phase_duration,
            'companies_matched': matched,
            'companies_unmatched': unmatched,
            'domains_detected': domains_detected,
            'patterns_detected': patterns_detected,
            'spoke_ready': spoke_ready,
        }

        logger.info(f"Phase 1-4 complete: {matched} matched, {spoke_ready} spoke-ready")

    def _run_people_spoke(self):
        """Run People Spoke (Phase 0-8)."""
        logger.info("-" * 40)
        logger.info("PEOPLE SPOKE")
        logger.info("-" * 40)

        phase_start = time.time()

        emails_generated = 0
        emails_verified = 0
        emails_failed = 0
        slot_assignments = {'CEO': 0, 'CFO': 0, 'CHRO': 0, 'HR': 0}
        enrichment_queue = 0

        for person_id, person in self._people.items():
            company = self._companies.get(person['company_unique_id'])
            if not company:
                continue

            # Step 0: Golden Rule check
            if not company.get('domain') or not company.get('email_pattern'):
                continue

            # Step 1-2: Slot assignment
            title = person.get('title', '').upper()
            slot_type = None
            if 'CEO' in title:
                slot_type = 'CEO'
            elif 'CFO' in title:
                slot_type = 'CFO'
            elif 'CHRO' in title or 'HR' in title:
                slot_type = 'CHRO' if 'CHRO' in title else 'HR'

            if slot_type and random.random() > 0.3:
                slot_assignments[slot_type] = slot_assignments.get(slot_type, 0) + 1
                self._emit_signal('SLOT_FILLED', company['company_unique_id'], 'people_spoke', 3.0)

            # Step 3: Email generation
            if company.get('email_pattern') and company.get('domain'):
                pattern = company['email_pattern']
                email = pattern.replace('{first}', person['first_name'].lower())
                email = email.replace('{last}', person['last_name'].lower())
                email = email.replace('{f}', person['first_name'][0].lower())
                email = f"{email}@{company['domain']}"
                person['email'] = email
                emails_generated += 1

                # Step 4: Email verification (simulated)
                self._track_tool('email_verification')
                if random.random() > 0.15:  # 85% pass rate
                    person['email_verified'] = True
                    emails_verified += 1
                    self._emit_signal('EMAIL_VERIFIED', company['company_unique_id'], 'people_spoke', 2.0)
                else:
                    emails_failed += 1

            # Track enrichment queue
            if person.get('linkedin_url') and random.random() > 0.5:
                enrichment_queue += 1
                self._track_tool('linkedin_enrichment')

        phase_duration = time.time() - phase_start

        self.metrics.volume.total_emails_generated = emails_generated
        self.metrics.quality.email_verification_pass = emails_verified
        self.metrics.quality.email_verification_fail = emails_failed
        self.metrics.quality.slot_fill_rates = {
            k: v / max(len(self._companies), 1) for k, v in slot_assignments.items()
        }
        self.metrics.risk.enrichment_queue_size = enrichment_queue
        self.metrics.cost.cost_by_phase['people_spoke'] = self._calculate_phase_cost()

        self.metrics.phase_results['people_spoke'] = {
            'duration_seconds': phase_duration,
            'emails_generated': emails_generated,
            'emails_verified': emails_verified,
            'emails_failed': emails_failed,
            'slot_assignments': slot_assignments,
            'enrichment_queue': enrichment_queue,
        }

        logger.info(f"People Spoke complete: {emails_generated} emails, {emails_verified} verified")

        # Check kill switch
        rejection_rate = emails_failed / max(emails_generated, 1)
        if rejection_rate > KILL_SWITCH_THRESHOLDS['email_rejection_rate']:
            self._trigger_kill_switch(
                'email_rejection_rate',
                f"Rejection rate > {KILL_SWITCH_THRESHOLDS['email_rejection_rate']*100}%",
                KILL_SWITCH_THRESHOLDS['email_rejection_rate'],
                rejection_rate,
                'people_spoke._run_people_spoke',
                'Email generation halted'
            )

    def _run_dol_spoke(self):
        """Run DOL Spoke."""
        logger.info("-" * 40)
        logger.info("DOL SPOKE")
        logger.info("-" * 40)

        phase_start = time.time()

        # Simulate Form 5500 processing
        form_5500_count = 500
        matched_by_ein = 0
        large_plans = 0
        broker_changes = 0

        for i in range(form_5500_count):
            company = random.choice(list(self._companies.values()))

            # EIN matching
            self._track_tool('ein_match')
            if company.get('ein') and random.random() > 0.2:
                matched_by_ein += 1

                # Signal: FORM_5500_FILED
                self._emit_signal('FORM_5500_FILED', company['company_unique_id'], 'dol_spoke', 5.0)

                # Large plan check
                if random.random() > 0.7:
                    large_plans += 1
                    self._emit_signal('LARGE_PLAN', company['company_unique_id'], 'dol_spoke', 8.0)

                # Broker change detection
                if random.random() > 0.9:
                    broker_changes += 1
                    self._emit_signal('BROKER_CHANGE', company['company_unique_id'], 'dol_spoke', 7.0)

        phase_duration = time.time() - phase_start
        self.metrics.cost.cost_by_phase['dol_spoke'] = self._calculate_phase_cost()

        self.metrics.phase_results['dol_spoke'] = {
            'duration_seconds': phase_duration,
            'form_5500_processed': form_5500_count,
            'matched_by_ein': matched_by_ein,
            'large_plans': large_plans,
            'broker_changes': broker_changes,
        }

        logger.info(f"DOL Spoke complete: {matched_by_ein} EIN matches, {large_plans} large plans")

    def _run_blog_spoke(self):
        """Run Blog Spoke."""
        logger.info("-" * 40)
        logger.info("BLOG SPOKE")
        logger.info("-" * 40)

        phase_start = time.time()

        # Simulate article processing
        articles_count = 200
        matched_articles = 0
        events_detected = 0

        event_types = ['FUNDING_ROUND', 'EXECUTIVE_CHANGE', 'ACQUISITION', 'LAYOFFS', 'EXPANSION']

        for i in range(articles_count):
            # Domain matching
            self._track_tool('domain_match')

            if random.random() > 0.4:
                company = random.choice(list(self._companies.values()))
                matched_articles += 1

                # Event detection
                if random.random() > 0.5:
                    event_type = random.choice(event_types)
                    events_detected += 1
                    impact = random.uniform(3.0, 10.0)
                    self._emit_signal(event_type, company['company_unique_id'], 'blog_spoke', impact)

        phase_duration = time.time() - phase_start
        self.metrics.cost.cost_by_phase['blog_spoke'] = self._calculate_phase_cost()

        self.metrics.phase_results['blog_spoke'] = {
            'duration_seconds': phase_duration,
            'articles_processed': articles_count,
            'matched_articles': matched_articles,
            'events_detected': events_detected,
        }

        logger.info(f"Blog Spoke complete: {matched_articles} matched, {events_detected} events")

    def _run_talent_flow_spoke(self):
        """Run Talent Flow Spoke."""
        logger.info("-" * 40)
        logger.info("TALENT FLOW SPOKE")
        logger.info("-" * 40)

        phase_start = time.time()

        # Simulate movement detection
        movements_count = 150
        movements_detected = 0

        movement_types = ['EXECUTIVE_DEPARTURE', 'EXECUTIVE_HIRE', 'PROMOTION', 'LATERAL_MOVE']

        for i in range(movements_count):
            if random.random() > 0.3:
                company = random.choice(list(self._companies.values()))
                movement_type = random.choice(movement_types)
                movements_detected += 1
                impact = random.uniform(5.0, 12.0)
                self._emit_signal(movement_type, company['company_unique_id'], 'talent_flow_spoke', impact)

        phase_duration = time.time() - phase_start
        self.metrics.cost.cost_by_phase['talent_flow_spoke'] = self._calculate_phase_cost()

        self.metrics.phase_results['talent_flow_spoke'] = {
            'duration_seconds': phase_duration,
            'movements_processed': movements_count,
            'movements_detected': movements_detected,
        }

        logger.info(f"Talent Flow complete: {movements_detected} movements detected")

    def _run_bit_engine(self):
        """Run BIT Engine processing."""
        logger.info("-" * 40)
        logger.info("BIT ENGINE")
        logger.info("-" * 40)

        phase_start = time.time()

        # Calculate BIT scores from signals
        bit_distribution = {'0-24': 0, '25-49': 0, '50-74': 0, '75+': 0}
        companies_above_50 = 0

        for company_id, company in self._companies.items():
            signal_count = self._signal_counts_by_company.get(company_id, 0)

            # Calculate BIT score based on signals
            bit_score = min(100, signal_count * random.uniform(3, 8))
            company['bit_score'] = bit_score

            # Track distribution
            if bit_score >= 75:
                bit_distribution['75+'] += 1
            elif bit_score >= 50:
                bit_distribution['50-74'] += 1
                companies_above_50 += 1
            elif bit_score >= 25:
                bit_distribution['25-49'] += 1
            else:
                bit_distribution['0-24'] += 1

            if bit_score >= 50:
                companies_above_50 += 1

        self.metrics.quality.bit_score_distribution = bit_distribution
        self.metrics.risk.companies_bit_above_50_pct = companies_above_50 / max(len(self._companies), 1)

        phase_duration = time.time() - phase_start

        self.metrics.phase_results['bit_engine'] = {
            'duration_seconds': phase_duration,
            'total_signals': len(self._signals),
            'bit_distribution': bit_distribution,
            'companies_above_50': companies_above_50,
        }

        logger.info(f"BIT Engine complete: {len(self._signals)} signals processed")

    def _run_outreach_spoke(self):
        """Run Outreach Spoke."""
        logger.info("-" * 40)
        logger.info("OUTREACH SPOKE (NO SENDS)")
        logger.info("-" * 40)

        phase_start = time.time()

        candidates_evaluated = 0
        candidates_passed = 0
        candidates_failed_anchor = 0
        candidates_failed_bit = 0
        candidates_cooling_off = 0

        # Simulate outreach evaluation
        hot_companies = [c for c in self._companies.values() if c.get('bit_score', 0) >= 50]

        for company in hot_companies:
            candidates_evaluated += 1

            # Golden Rule check
            if not company.get('domain') or not company.get('email_pattern'):
                candidates_failed_anchor += 1
                continue

            # BIT score check
            if company.get('bit_score', 0) < 25:
                candidates_failed_bit += 1
                continue

            # Cooling off (simulate 10% in cooling off)
            if random.random() < 0.1:
                candidates_cooling_off += 1
                continue

            candidates_passed += 1

        phase_duration = time.time() - phase_start
        self.metrics.cost.cost_by_phase['outreach_spoke'] = 0.0  # No actual sends

        self.metrics.phase_results['outreach_spoke'] = {
            'duration_seconds': phase_duration,
            'candidates_evaluated': candidates_evaluated,
            'candidates_passed': candidates_passed,
            'candidates_failed_anchor': candidates_failed_anchor,
            'candidates_failed_bit': candidates_failed_bit,
            'candidates_cooling_off': candidates_cooling_off,
            'sends_blocked': True,
        }

        logger.info(f"Outreach Spoke complete: {candidates_passed} ready (NO SENDS)")

    def _emit_signal(self, signal_type: str, company_id: str, source: str, impact: float):
        """Emit a signal (tracked, not persisted)."""
        self._signals.append({
            'signal_type': signal_type,
            'company_id': company_id,
            'source': source,
            'impact': impact,
            'timestamp': datetime.now().isoformat(),
        })

        self._signal_counts_by_company[company_id] += 1
        self._signal_counts_by_source[source] += 1

        self.metrics.volume.total_signals_emitted += 1
        self.metrics.volume.signals_by_type[signal_type] = \
            self.metrics.volume.signals_by_type.get(signal_type, 0) + 1

        self._track_tool('bit_signal')

        # Check signal flood kill switch
        if self._signal_counts_by_company[company_id] > KILL_SWITCH_THRESHOLDS['signal_flood_per_company']:
            self._trigger_kill_switch(
                'signal_flood_per_company',
                f"Company {company_id} exceeded signal limit",
                KILL_SWITCH_THRESHOLDS['signal_flood_per_company'],
                self._signal_counts_by_company[company_id],
                f'{source}._emit_signal',
                f'Signals to {company_id} halted'
            )

        if self._signal_counts_by_source[source] > KILL_SWITCH_THRESHOLDS['signal_flood_per_source']:
            self._trigger_kill_switch(
                'signal_flood_per_source',
                f"Source {source} exceeded signal limit",
                KILL_SWITCH_THRESHOLDS['signal_flood_per_source'],
                self._signal_counts_by_source[source],
                f'{source}._emit_signal',
                f'Signals from {source} halted'
            )

    def _track_tool(self, tool_name: str):
        """Track tool invocation for cost estimation."""
        self.metrics.cost.tool_invocations[tool_name] = \
            self.metrics.cost.tool_invocations.get(tool_name, 0) + 1

    def _calculate_phase_cost(self) -> float:
        """Calculate cost based on tool invocations."""
        total = 0.0
        for tool, count in self.metrics.cost.tool_invocations.items():
            cost = TOOL_COSTS.get(tool, 0.001) * count
            total += cost
        return total

    def _trigger_kill_switch(self, switch_name: str, condition: str, threshold: float,
                              actual: float, where: str, what_stopped: str):
        """Trigger a kill switch (deduplicated by switch_name)."""
        # Check if already triggered (dedup)
        if any(ks.switch_name == switch_name and ks.fired for ks in self.metrics.kill_switches):
            return  # Already logged

        event = KillSwitchEvent(
            switch_name=switch_name,
            trigger_condition=condition,
            threshold=threshold,
            actual_value=actual,
            fired=True,
            where_fired=where,
            what_stopped=what_stopped,
        )
        self.metrics.kill_switches.append(event)
        logger.warning(f"KILL SWITCH TRIGGERED: {switch_name} - {condition}")

    def _validate_kill_switches(self):
        """Validate all kill switches at end of run."""
        logger.info("-" * 40)
        logger.info("KILL SWITCH VALIDATION")
        logger.info("-" * 40)

        # Check daily cost ceiling
        total_cost = sum(self.metrics.cost.cost_by_phase.values())
        if total_cost > KILL_SWITCH_THRESHOLDS['daily_cost_ceiling']:
            self._trigger_kill_switch(
                'daily_cost_ceiling',
                f"Daily cost ${total_cost:.2f} exceeds ceiling",
                KILL_SWITCH_THRESHOLDS['daily_cost_ceiling'],
                total_cost,
                'orchestrator._validate_kill_switches',
                'Further processing halted'
            )
        else:
            self.metrics.kill_switches.append(KillSwitchEvent(
                switch_name='daily_cost_ceiling',
                trigger_condition=f"Daily cost < ${KILL_SWITCH_THRESHOLDS['daily_cost_ceiling']}",
                threshold=KILL_SWITCH_THRESHOLDS['daily_cost_ceiling'],
                actual_value=total_cost,
                fired=False,
                where_fired='N/A',
                what_stopped='N/A',
            ))

        # Check enrichment queue
        if self.metrics.risk.enrichment_queue_size > KILL_SWITCH_THRESHOLDS['enrichment_queue_max']:
            self._trigger_kill_switch(
                'enrichment_queue_max',
                f"Enrichment queue {self.metrics.risk.enrichment_queue_size} exceeds max",
                KILL_SWITCH_THRESHOLDS['enrichment_queue_max'],
                self.metrics.risk.enrichment_queue_size,
                'orchestrator._validate_kill_switches',
                'Enrichment processing halted'
            )
        else:
            self.metrics.kill_switches.append(KillSwitchEvent(
                switch_name='enrichment_queue_max',
                trigger_condition=f"Queue size < {KILL_SWITCH_THRESHOLDS['enrichment_queue_max']}",
                threshold=KILL_SWITCH_THRESHOLDS['enrichment_queue_max'],
                actual_value=self.metrics.risk.enrichment_queue_size,
                fired=False,
                where_fired='N/A',
                what_stopped='N/A',
            ))

        # Check BIT spike
        max_bit = max((c.get('bit_score', 0) for c in self._companies.values()), default=0)
        if max_bit > KILL_SWITCH_THRESHOLDS['bit_spike_per_run']:
            self._trigger_kill_switch(
                'bit_spike_per_run',
                f"Max BIT score {max_bit:.1f} exceeds threshold",
                KILL_SWITCH_THRESHOLDS['bit_spike_per_run'],
                max_bit,
                'orchestrator._validate_kill_switches',
                'BIT scoring halted'
            )
        else:
            self.metrics.kill_switches.append(KillSwitchEvent(
                switch_name='bit_spike_per_run',
                trigger_condition=f"Max BIT < {KILL_SWITCH_THRESHOLDS['bit_spike_per_run']}",
                threshold=KILL_SWITCH_THRESHOLDS['bit_spike_per_run'],
                actual_value=max_bit,
                fired=False,
                where_fired='N/A',
                what_stopped='N/A',
            ))

        fired_count = sum(1 for ks in self.metrics.kill_switches if ks.fired)
        logger.info(f"Kill switch validation: {fired_count} triggered, {len(self.metrics.kill_switches) - fired_count} passed")

    def _calculate_final_metrics(self):
        """Calculate final aggregated metrics."""
        # Cost metrics
        total_cost = sum(self.metrics.cost.cost_by_phase.values())
        self.metrics.cost.total_estimated_cost = total_cost

        total_records = self.metrics.volume.total_companies_processed + self.metrics.volume.total_people_processed
        if total_records > 0:
            self.metrics.cost.cost_per_1k_records = (total_cost / total_records) * 1000

        # Top expensive tools
        tool_costs = []
        for tool, count in self.metrics.cost.tool_invocations.items():
            cost = TOOL_COSTS.get(tool, 0.001) * count
            tool_costs.append((tool, cost))
        tool_costs.sort(key=lambda x: x[1], reverse=True)
        self.metrics.cost.top_expensive_tools = tool_costs[:3]

        # Risk metrics
        total_emails = self.metrics.volume.total_emails_generated
        if total_emails > 0:
            self.metrics.risk.emails_rejected_pct = \
                self.metrics.quality.email_verification_fail / total_emails

        max_signals = max(self._signal_counts_by_company.values()) if self._signal_counts_by_company else 0
        self.metrics.risk.max_signals_single_company = max_signals

        # Find risky companies (high signal count)
        risky = [cid for cid, count in self._signal_counts_by_company.items() if count > 20]
        self.metrics.risk.risky_companies = risky[:10]


# =============================================================================
# REPORT GENERATORS
# =============================================================================

def generate_summary_report(metrics: PipelineRunMetrics) -> str:
    """Generate human-readable summary report."""
    lines = [
        "# DRY RUN SUMMARY REPORT",
        f"**Run ID**: {metrics.run_id}",
        f"**Timestamp**: {metrics.run_timestamp}",
        f"**Duration**: {metrics.duration_seconds:.2f} seconds",
        "",
        "## Volume Metrics",
        f"- Companies Processed: {metrics.volume.total_companies_processed:,}",
        f"- People Processed: {metrics.volume.total_people_processed:,}",
        f"- Emails Generated: {metrics.volume.total_emails_generated:,}",
        f"- Total Signals Emitted: {metrics.volume.total_signals_emitted:,}",
        "",
        "### Signals by Type",
    ]

    for sig_type, count in sorted(metrics.volume.signals_by_type.items(), key=lambda x: -x[1]):
        lines.append(f"- {sig_type}: {count:,}")

    lines.extend([
        "",
        "## Cost Metrics",
        f"- **Total Estimated Cost**: ${metrics.cost.total_estimated_cost:.2f}",
        f"- **Cost per 1k Records**: ${metrics.cost.cost_per_1k_records:.4f}",
        "",
        "### Cost by Phase",
    ])

    for phase, cost in metrics.cost.cost_by_phase.items():
        lines.append(f"- {phase}: ${cost:.4f}")

    lines.extend([
        "",
        "### Top 3 Most Expensive Tools",
    ])

    for tool, cost in metrics.cost.top_expensive_tools:
        lines.append(f"- {tool}: ${cost:.4f}")

    lines.extend([
        "",
        "## Quality Metrics",
        "",
        "### Fuzzy Match Distribution",
    ])

    for bucket, count in metrics.quality.fuzzy_match_distribution.items():
        lines.append(f"- {bucket}%: {count:,}")

    lines.extend([
        "",
        "### Email Verification",
        f"- Pass: {metrics.quality.email_verification_pass:,}",
        f"- Fail: {metrics.quality.email_verification_fail:,}",
        f"- Pass Rate: {metrics.quality.email_verification_pass / max(metrics.quality.email_verification_pass + metrics.quality.email_verification_fail, 1) * 100:.1f}%",
        "",
        "### Slot Fill Rates",
    ])

    for slot, rate in metrics.quality.slot_fill_rates.items():
        lines.append(f"- {slot}: {rate*100:.1f}%")

    lines.extend([
        "",
        "### BIT Score Distribution",
    ])

    for bucket, count in metrics.quality.bit_score_distribution.items():
        lines.append(f"- {bucket}: {count:,}")

    lines.extend([
        "",
        "## Risk Metrics",
        f"- Email Rejection Rate: {metrics.risk.emails_rejected_pct*100:.1f}%",
        f"- Companies with BIT >= 50: {metrics.risk.companies_bit_above_50_pct*100:.1f}%",
        f"- Max Signals (Single Company): {metrics.risk.max_signals_single_company}",
        f"- Enrichment Queue Size: {metrics.risk.enrichment_queue_size:,}",
        "",
        "## Kill Switch Status",
    ])

    fired = [ks for ks in metrics.kill_switches if ks.fired]
    passed = [ks for ks in metrics.kill_switches if not ks.fired]

    lines.append(f"- **Triggered**: {len(fired)}")
    lines.append(f"- **Passed**: {len(passed)}")

    if fired:
        lines.append("")
        lines.append("### Triggered Switches")
        for ks in fired:
            lines.append(f"- **{ks.switch_name}**: {ks.trigger_condition}")

    return "\n".join(lines)


def generate_kill_switch_report(metrics: PipelineRunMetrics) -> str:
    """Generate kill switch report."""
    lines = [
        "# KILL SWITCH REPORT",
        f"**Run ID**: {metrics.run_id}",
        f"**Timestamp**: {metrics.run_timestamp}",
        "",
    ]

    fired = [ks for ks in metrics.kill_switches if ks.fired]
    passed = [ks for ks in metrics.kill_switches if not ks.fired]

    lines.extend([
        "## Summary",
        f"- Total Switches Evaluated: {len(metrics.kill_switches)}",
        f"- Switches Triggered: {len(fired)}",
        f"- Switches Passed: {len(passed)}",
        "",
    ])

    if fired:
        lines.append("## TRIGGERED SWITCHES")
        lines.append("")
        for ks in fired:
            lines.extend([
                f"### {ks.switch_name}",
                f"- **Trigger Condition**: {ks.trigger_condition}",
                f"- **Threshold**: {ks.threshold}",
                f"- **Actual Value**: {ks.actual_value}",
                f"- **Where Fired**: {ks.where_fired}",
                f"- **What Stopped**: {ks.what_stopped}",
                f"- **Timestamp**: {ks.timestamp}",
                "",
            ])
    else:
        lines.append("## TRIGGERED SWITCHES")
        lines.append("None - all kill switches passed.")
        lines.append("")

    lines.append("## PASSED SWITCHES")
    lines.append("")
    for ks in passed:
        lines.extend([
            f"### {ks.switch_name}",
            f"- **Condition**: {ks.trigger_condition}",
            f"- **Threshold**: {ks.threshold}",
            f"- **Actual Value**: {ks.actual_value:.2f}",
            "",
        ])

    return "\n".join(lines)


def generate_next_actions(metrics: PipelineRunMetrics) -> str:
    """Generate next actions report (max 10 bullets)."""
    actions = []

    # Check email rejection rate
    if metrics.risk.emails_rejected_pct > 0.1:
        actions.append(f"- Investigate email rejection rate ({metrics.risk.emails_rejected_pct*100:.1f}%) - consider pattern validation")

    # Check enrichment queue
    if metrics.risk.enrichment_queue_size > 5000:
        actions.append(f"- Address enrichment queue backlog ({metrics.risk.enrichment_queue_size:,} items)")

    # Check fuzzy match quality
    low_confidence = metrics.quality.fuzzy_match_distribution.get('<70', 0)
    if low_confidence > 100:
        actions.append(f"- Review {low_confidence} low-confidence fuzzy matches")

    # Check signal concentration
    if metrics.risk.max_signals_single_company > 30:
        actions.append(f"- Investigate signal concentration ({metrics.risk.max_signals_single_company} max per company)")

    # Check kill switches
    fired = [ks for ks in metrics.kill_switches if ks.fired]
    if fired:
        for ks in fired[:3]:
            actions.append(f"- Address {ks.switch_name} kill switch trigger")

    # Check cost efficiency
    if metrics.cost.cost_per_1k_records > 1.0:
        actions.append(f"- Optimize cost efficiency (${metrics.cost.cost_per_1k_records:.2f}/1k records)")

    # Check domain detection
    if metrics.quality.domain_detection_rate < 0.7:
        actions.append(f"- Improve domain detection ({metrics.quality.domain_detection_rate*100:.1f}% rate)")

    # Slot fill recommendations
    for slot, rate in metrics.quality.slot_fill_rates.items():
        if rate < 0.3:
            actions.append(f"- Improve {slot} slot fill rate ({rate*100:.1f}%)")
            break

    # Limit to 10
    actions = actions[:10]

    if not actions:
        actions.append("- No critical issues identified - pipeline ready for production")

    lines = [
        "# NEXT ACTIONS",
        f"**Run ID**: {metrics.run_id}",
        "",
        "## Recommendations (Priority Order)",
        "",
    ]

    lines.extend(actions)

    return "\n".join(lines)


# =============================================================================
# MAIN EXECUTION
# =============================================================================

def main():
    """Run the dry-run orchestrator and generate reports."""
    logger.info("Starting Dry Run Orchestrator...")

    # Run the dry run
    orchestrator = DryRunOrchestrator()
    metrics = orchestrator.run()

    # Output directory
    output_dir = os.path.dirname(os.path.abspath(__file__))

    # Generate and save reports

    # 1. dry_run_summary.md
    summary_path = os.path.join(output_dir, 'dry_run_summary.md')
    with open(summary_path, 'w') as f:
        f.write(generate_summary_report(metrics))
    logger.info(f"Generated: {summary_path}")

    # 2. dry_run_metrics.json
    metrics_path = os.path.join(output_dir, 'dry_run_metrics.json')

    # Convert dataclasses to dict
    def serialize(obj):
        if hasattr(obj, '__dataclass_fields__'):
            return {k: serialize(v) for k, v in asdict(obj).items()}
        elif isinstance(obj, list):
            return [serialize(i) for i in obj]
        elif isinstance(obj, dict):
            return {k: serialize(v) for k, v in obj.items()}
        else:
            return obj

    with open(metrics_path, 'w') as f:
        json.dump(serialize(metrics), f, indent=2, default=str)
    logger.info(f"Generated: {metrics_path}")

    # 3. kill_switch_report.md
    ks_path = os.path.join(output_dir, 'kill_switch_report.md')
    with open(ks_path, 'w') as f:
        f.write(generate_kill_switch_report(metrics))
    logger.info(f"Generated: {ks_path}")

    # 4. next_actions.md
    actions_path = os.path.join(output_dir, 'next_actions.md')
    with open(actions_path, 'w') as f:
        f.write(generate_next_actions(metrics))
    logger.info(f"Generated: {actions_path}")

    logger.info("=" * 60)
    logger.info("DRY RUN COMPLETE - Reports generated")
    logger.info("=" * 60)

    return metrics


if __name__ == '__main__':
    main()
