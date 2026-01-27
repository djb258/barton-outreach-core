"""
Hub Status Truthfulness Validation
===================================

Tests that all hub status computations are truthful and deterministic.

Validation Rules (LOCKED):
    1. NO PASS without valid company_unique_id
    2. NO PASS without meeting minimum criteria
    3. NO PASS with expired freshness
    4. Deterministic: same input MUST produce same output
    5. Status reasons must be accurate and specific
"""

import pytest
from datetime import datetime, timedelta
import uuid
import sys
from pathlib import Path
import importlib.util

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


# =============================================================================
# LOAD MODULES (avoiding hyphenated directory issues)
# =============================================================================

# Load People Intelligence hub_status module
people_hub_status_spec = importlib.util.spec_from_file_location(
    "people_hub_status",
    PROJECT_ROOT / "hubs" / "people-intelligence" / "imo" / "middle" / "hub_status.py"
)
people_hub_status = importlib.util.module_from_spec(people_hub_status_spec)
people_hub_status_spec.loader.exec_module(people_hub_status)

compute_people_hub_status = people_hub_status.compute_people_hub_status
PeopleHubStatusResult = people_hub_status.PeopleHubStatusResult
PEOPLE_FRESHNESS_DAYS = people_hub_status.FRESHNESS_DAYS
MIN_VERIFIED_SLOTS = people_hub_status.MIN_VERIFIED_SLOTS

# Load Blog Content hub_status module
blog_hub_status_spec = importlib.util.spec_from_file_location(
    "blog_hub_status",
    PROJECT_ROOT / "hubs" / "blog-content" / "imo" / "middle" / "hub_status.py"
)
blog_hub_status = importlib.util.module_from_spec(blog_hub_status_spec)
blog_hub_status_spec.loader.exec_module(blog_hub_status)

compute_blog_hub_status = blog_hub_status.compute_blog_hub_status
BlogHubStatusResult = blog_hub_status.BlogHubStatusResult
generate_blog_signal_hash = blog_hub_status.generate_blog_signal_hash
BLOG_FRESHNESS_DAYS = blog_hub_status.FRESHNESS_DAYS
MIN_SIGNALS = blog_hub_status.MIN_SIGNALS

# Load Talent Flow hub_status module
talent_hub_status_spec = importlib.util.spec_from_file_location(
    "talent_hub_status",
    PROJECT_ROOT / "hubs" / "talent-flow" / "imo" / "middle" / "hub_status.py"
)
talent_hub_status = importlib.util.module_from_spec(talent_hub_status_spec)
talent_hub_status_spec.loader.exec_module(talent_hub_status)

compute_talent_flow_hub_status = talent_hub_status.compute_talent_flow_hub_status
TalentFlowHubStatusResult = talent_hub_status.TalentFlowHubStatusResult
generate_movement_signal_hash = talent_hub_status.generate_movement_signal_hash
TALENT_FRESHNESS_DAYS = talent_hub_status.FRESHNESS_DAYS
MIN_MOVEMENTS = talent_hub_status.MIN_MOVEMENTS
CONFIDENCE_THRESHOLD = talent_hub_status.CONFIDENCE_THRESHOLD


# =============================================================================
# PEOPLE INTELLIGENCE HUB TESTS
# =============================================================================

class TestPeopleIntelligenceHubStatus:
    """Tests for People Intelligence hub status computation."""

    def test_no_pass_without_company_id(self):
        """CRITICAL: No PASS without company_unique_id."""
        result = compute_people_hub_status(
            company_unique_id=None,
            people_records=[{
                'full_name': 'John Doe',
                'title': 'CEO',
                'linkedin_url': 'https://linkedin.com/in/johndoe'
            }],
            last_update=datetime.utcnow()
        )
        assert result.status == 'FAIL'
        assert 'NULL' in result.status_reason

    def test_no_pass_without_company_id_empty_string(self):
        """CRITICAL: No PASS with empty string company_unique_id."""
        result = compute_people_hub_status(
            company_unique_id='',
            people_records=[{
                'full_name': 'John Doe',
                'title': 'CEO',
                'linkedin_url': 'https://linkedin.com/in/johndoe'
            }],
            last_update=datetime.utcnow()
        )
        assert result.status == 'FAIL'

    def test_pass_with_valid_data(self):
        """PASS with valid company_id, verified slot, and freshness."""
        company_id = str(uuid.uuid4())
        result = compute_people_hub_status(
            company_unique_id=company_id,
            people_records=[{
                'full_name': 'John Doe',
                'title': 'CEO',
                'linkedin_url': 'https://linkedin.com/in/johndoe'
            }],
            last_update=datetime.utcnow()
        )
        assert result.status == 'PASS'
        assert result.company_unique_id == company_id

    def test_in_progress_without_verified_slots(self):
        """IN_PROGRESS when no verified slots (missing linkedin_url)."""
        result = compute_people_hub_status(
            company_unique_id=str(uuid.uuid4()),
            people_records=[{
                'full_name': 'John Doe',
                'title': 'CEO',
                'linkedin_url': None  # Missing!
            }],
            last_update=datetime.utcnow()
        )
        assert result.status == 'IN_PROGRESS'
        assert 'Insufficient' in result.status_reason

    def test_in_progress_when_freshness_expired(self):
        """IN_PROGRESS when freshness has expired."""
        expired_date = datetime.utcnow() - timedelta(days=PEOPLE_FRESHNESS_DAYS + 10)
        result = compute_people_hub_status(
            company_unique_id=str(uuid.uuid4()),
            people_records=[{
                'full_name': 'John Doe',
                'title': 'CEO',
                'linkedin_url': 'https://linkedin.com/in/johndoe'
            }],
            last_update=expired_date
        )
        assert result.status == 'IN_PROGRESS'
        assert 'expired' in result.status_reason.lower()

    def test_deterministic_same_input_same_output(self):
        """Deterministic: Same input produces same output."""
        company_id = str(uuid.uuid4())
        records = [{
            'full_name': 'John Doe',
            'title': 'CEO',
            'linkedin_url': 'https://linkedin.com/in/johndoe'
        }]
        last_update = datetime.utcnow()

        result1 = compute_people_hub_status(company_id, records, last_update)
        result2 = compute_people_hub_status(company_id, records, last_update)

        assert result1.status == result2.status
        assert result1.status_reason == result2.status_reason
        assert result1.metric_value == result2.metric_value

    def test_in_progress_with_no_records(self):
        """IN_PROGRESS when no people records exist."""
        result = compute_people_hub_status(
            company_unique_id=str(uuid.uuid4()),
            people_records=[],
            last_update=datetime.utcnow()
        )
        assert result.status == 'IN_PROGRESS'
        assert 'No people records' in result.status_reason


# =============================================================================
# BLOG CONTENT HUB TESTS
# =============================================================================

class TestBlogContentHubStatus:
    """Tests for Blog Content hub status computation."""

    def test_no_pass_without_company_id(self):
        """CRITICAL: No PASS without company_unique_id."""
        result = compute_blog_hub_status(
            company_unique_id=None,
            blog_signals=[{
                'source_url': 'https://example.com/blog/post1',
                'event_type': 'mentioned',
                'created_at': datetime.utcnow()
            }]
        )
        assert result.status == 'FAIL'
        assert 'NULL' in result.status_reason

    def test_pass_with_fresh_signal(self):
        """PASS with valid company_id and fresh signal."""
        company_id = str(uuid.uuid4())
        result = compute_blog_hub_status(
            company_unique_id=company_id,
            blog_signals=[{
                'source_url': 'https://example.com/blog/post1',
                'event_type': 'mentioned',
                'created_at': datetime.utcnow()
            }]
        )
        assert result.status == 'PASS'
        assert result.company_unique_id == company_id

    def test_in_progress_with_expired_signals(self):
        """IN_PROGRESS when all signals have expired."""
        expired_date = datetime.utcnow() - timedelta(days=BLOG_FRESHNESS_DAYS + 10)
        result = compute_blog_hub_status(
            company_unique_id=str(uuid.uuid4()),
            blog_signals=[{
                'source_url': 'https://example.com/blog/post1',
                'event_type': 'mentioned',
                'created_at': expired_date
            }]
        )
        assert result.status == 'IN_PROGRESS'
        assert 'No fresh signals' in result.status_reason

    def test_deduplication_hash_unique(self):
        """Deduplication hash is unique for different signals."""
        hash1 = generate_blog_signal_hash('company1', 'url1', 'mentioned')
        hash2 = generate_blog_signal_hash('company1', 'url2', 'mentioned')
        hash3 = generate_blog_signal_hash('company2', 'url1', 'mentioned')

        assert hash1 != hash2
        assert hash1 != hash3
        assert hash2 != hash3

    def test_deduplication_hash_consistent(self):
        """Deduplication hash is consistent for same input."""
        hash1 = generate_blog_signal_hash('company1', 'url1', 'mentioned')
        hash2 = generate_blog_signal_hash('company1', 'url1', 'mentioned')

        assert hash1 == hash2

    def test_duplicates_filtered(self):
        """Duplicate signals are filtered by hash."""
        company_id = str(uuid.uuid4())
        now = datetime.utcnow()
        result = compute_blog_hub_status(
            company_unique_id=company_id,
            blog_signals=[
                {
                    'source_url': 'https://example.com/blog/post1',
                    'event_type': 'mentioned',
                    'created_at': now
                },
                {
                    'source_url': 'https://example.com/blog/post1',  # Same URL
                    'event_type': 'mentioned',  # Same type
                    'created_at': now
                },
            ]
        )
        assert result.status == 'PASS'
        assert result.details['fresh_signals'] == 1  # Deduplicated to 1

    def test_in_progress_with_no_signals(self):
        """IN_PROGRESS when no blog signals exist."""
        result = compute_blog_hub_status(
            company_unique_id=str(uuid.uuid4()),
            blog_signals=[]
        )
        assert result.status == 'IN_PROGRESS'
        assert 'No blog signals' in result.status_reason


# =============================================================================
# TALENT FLOW HUB TESTS
# =============================================================================

class TestTalentFlowHubStatus:
    """Tests for Talent Flow hub status computation."""

    def test_no_pass_without_company_id(self):
        """CRITICAL: No PASS without company_unique_id."""
        result = compute_talent_flow_hub_status(
            company_unique_id=None,
            movement_signals=[{
                'person_id': str(uuid.uuid4()),
                'event_type': 'joined',
                'confidence': 0.85,
                'detected_at': datetime.utcnow()
            }]
        )
        assert result.status == 'FAIL'
        assert 'NULL' in result.status_reason

    def test_pass_with_valid_movement(self):
        """PASS with valid company_id and fresh movement."""
        company_id = str(uuid.uuid4())
        result = compute_talent_flow_hub_status(
            company_unique_id=company_id,
            movement_signals=[{
                'person_id': str(uuid.uuid4()),
                'event_type': 'joined',
                'confidence': 0.85,
                'detected_at': datetime.utcnow()
            }]
        )
        assert result.status == 'PASS'
        assert result.company_unique_id == company_id

    def test_blocked_when_upstream_blocked(self):
        """BLOCKED when upstream People Intelligence is BLOCKED."""
        result = compute_talent_flow_hub_status(
            company_unique_id=str(uuid.uuid4()),
            movement_signals=[{
                'person_id': str(uuid.uuid4()),
                'event_type': 'joined',
                'confidence': 0.85,
                'detected_at': datetime.utcnow()
            }],
            people_hub_status='BLOCKED'
        )
        assert result.status == 'BLOCKED'
        assert 'People Intelligence' in result.status_reason

    def test_in_progress_with_low_confidence(self):
        """IN_PROGRESS when movements are below confidence threshold."""
        result = compute_talent_flow_hub_status(
            company_unique_id=str(uuid.uuid4()),
            movement_signals=[{
                'person_id': str(uuid.uuid4()),
                'event_type': 'joined',
                'confidence': 0.50,  # Below 0.70 threshold
                'detected_at': datetime.utcnow()
            }]
        )
        assert result.status == 'IN_PROGRESS'
        assert 'confidence' in result.status_reason.lower() or 'No valid' in result.status_reason

    def test_in_progress_with_expired_movements(self):
        """IN_PROGRESS when all movements have expired."""
        expired_date = datetime.utcnow() - timedelta(days=TALENT_FRESHNESS_DAYS + 10)
        result = compute_talent_flow_hub_status(
            company_unique_id=str(uuid.uuid4()),
            movement_signals=[{
                'person_id': str(uuid.uuid4()),
                'event_type': 'joined',
                'confidence': 0.85,
                'detected_at': expired_date
            }]
        )
        assert result.status == 'IN_PROGRESS'
        assert 'No fresh movements' in result.status_reason

    def test_movement_types_valid(self):
        """All valid movement types contribute to PASS."""
        company_id = str(uuid.uuid4())
        for event_type in ['joined', 'left', 'title_change']:
            result = compute_talent_flow_hub_status(
                company_unique_id=company_id,
                movement_signals=[{
                    'person_id': str(uuid.uuid4()),
                    'event_type': event_type,
                    'confidence': 0.85,
                    'detected_at': datetime.utcnow()
                }]
            )
            assert result.status == 'PASS', f"Expected PASS for {event_type}"

    def test_invalid_movement_type_ignored(self):
        """Invalid movement types are ignored."""
        result = compute_talent_flow_hub_status(
            company_unique_id=str(uuid.uuid4()),
            movement_signals=[{
                'person_id': str(uuid.uuid4()),
                'event_type': 'invalid_type',
                'confidence': 0.85,
                'detected_at': datetime.utcnow()
            }]
        )
        assert result.status == 'IN_PROGRESS'

    def test_movement_deduplication(self):
        """Movement signals are deduplicated correctly."""
        company_id = str(uuid.uuid4())
        person_id = str(uuid.uuid4())
        now = datetime.utcnow()

        result = compute_talent_flow_hub_status(
            company_unique_id=company_id,
            movement_signals=[
                {
                    'person_id': person_id,
                    'event_type': 'joined',
                    'confidence': 0.85,
                    'detected_at': now
                },
                {
                    'person_id': person_id,  # Same person
                    'event_type': 'joined',  # Same event type
                    'confidence': 0.85,
                    'detected_at': now  # Same day
                },
            ]
        )
        assert result.status == 'PASS'
        assert result.details['fresh_movements'] == 1  # Deduplicated

    def test_in_progress_with_no_movements(self):
        """IN_PROGRESS when no movement signals exist."""
        result = compute_talent_flow_hub_status(
            company_unique_id=str(uuid.uuid4()),
            movement_signals=[]
        )
        assert result.status == 'IN_PROGRESS'
        assert 'No movement signals' in result.status_reason


# =============================================================================
# CROSS-HUB CONSISTENCY TESTS
# =============================================================================

class TestCrossHubConsistency:
    """Tests for cross-hub consistency and doctrine compliance."""

    def test_all_hubs_fail_without_company_id(self):
        """All hubs must FAIL without company_unique_id."""
        results = [
            compute_people_hub_status(None, [{'full_name': 'Test', 'title': 'CEO', 'linkedin_url': 'url'}]),
            compute_blog_hub_status(None, [{'source_url': 'url', 'event_type': 'mentioned', 'created_at': datetime.utcnow()}]),
            compute_talent_flow_hub_status(None, [{'person_id': 'id', 'event_type': 'joined', 'confidence': 0.85, 'detected_at': datetime.utcnow()}]),
        ]

        for result in results:
            assert result.status == 'FAIL', f"Expected FAIL for hub without company_id"
            assert 'NULL' in result.status_reason

    def test_all_hubs_in_progress_with_empty_data(self):
        """All hubs must be IN_PROGRESS with empty data (not PASS)."""
        company_id = str(uuid.uuid4())
        results = [
            compute_people_hub_status(company_id, [], datetime.utcnow()),
            compute_blog_hub_status(company_id, []),
            compute_talent_flow_hub_status(company_id, []),
        ]

        for result in results:
            assert result.status == 'IN_PROGRESS', f"Expected IN_PROGRESS for hub with empty data"

    def test_all_hubs_return_correct_company_id(self):
        """All hubs must return the input company_unique_id."""
        company_id = str(uuid.uuid4())
        results = [
            compute_people_hub_status(company_id, [], datetime.utcnow()),
            compute_blog_hub_status(company_id, []),
            compute_talent_flow_hub_status(company_id, []),
        ]

        for result in results:
            assert result.company_unique_id == company_id

    def test_freshness_windows_documented(self):
        """Freshness windows are properly documented."""
        assert PEOPLE_FRESHNESS_DAYS == 90, "People Intelligence freshness should be 90 days"
        assert BLOG_FRESHNESS_DAYS == 30, "Blog Content freshness should be 30 days"
        assert TALENT_FRESHNESS_DAYS == 60, "Talent Flow freshness should be 60 days"


# =============================================================================
# DIRECT EXECUTION
# =============================================================================

if __name__ == '__main__':
    """
    Run hub status truthfulness tests directly.

    Usage:
        python tests/hubs/test_hub_status_truthfulness.py

    Or with pytest:
        pytest tests/hubs/test_hub_status_truthfulness.py -v
    """
    print("=" * 70)
    print("HUB STATUS TRUTHFULNESS VALIDATION")
    print("=" * 70)
    print()

    # Run all tests
    all_passed = True
    test_classes = [
        TestPeopleIntelligenceHubStatus,
        TestBlogContentHubStatus,
        TestTalentFlowHubStatus,
        TestCrossHubConsistency,
    ]

    for test_class in test_classes:
        print(f"\n--- {test_class.__name__} ---")
        instance = test_class()

        for method_name in dir(instance):
            if method_name.startswith('test_'):
                try:
                    getattr(instance, method_name)()
                    print(f"  [PASS] {method_name}")
                except AssertionError as e:
                    print(f"  [FAIL] {method_name}: {e}")
                    all_passed = False
                except Exception as e:
                    print(f"  [ERROR] {method_name}: {e}")
                    all_passed = False

    print()
    print("=" * 70)
    if all_passed:
        print("ALL TESTS PASSED - Hub statuses are truthful")
    else:
        print("SOME TESTS FAILED - Review output above")
        sys.exit(1)
    print("=" * 70)
