# Bicycle Wheel Doctrine

## Official Diagramming & Architecture Standard for Barton Systems

```
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│                                                                                         │
│                     BICYCLE WHEEL DOCTRINE                                              │
│                     "Everything is a wheel. Wheels have wheels."                        │
│                                                                                         │
└─────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## Core Philosophy

We diagram AND program using a **bicycle-wheel hub-and-spoke model** — extended fractally.

This is not just a visual metaphor. It is a **programming paradigm** and **architectural standard** that governs how we:
1. Design systems
2. Document systems
3. Debug systems
4. Extend systems

---

## The Bicycle Wheel Mental Model

```
                                    THE WHEEL

                                         │
                               ╲         │         ╱
                                 ╲       │       ╱
                                   ╲     │     ╱
                                     ╲   │   ╱
                                       ╲ │ ╱
                              ═══════════●═══════════     ←── SPOKES (Functions/Domains)
                                       ╱ │ ╲
                                     ╱   │   ╲
                                   ╱     │     ╲
                                 ╱       │       ╲
                               ╱         │         ╲
                                         │

                                         ●  ←── HUB (Central Entity/Axle)
```

### Key Concepts

| Component | Definition | Example |
|-----------|------------|---------|
| **Hub (Axle)** | The central entity that everything anchors to | Company, Person, Order |
| **Spokes** | Major domains/functions connected to the hub | People Node, DOL Node, Email Module |
| **Rim** | The outer boundary where sub-wheels connect | External APIs, User interfaces |
| **Sub-wheels** | Smaller bicycle wheels at spoke endpoints | Email Verification (sub-wheel of People Node) |
| **Failure Spokes** | Small secondary spokes for error states | failed_company_match, invalid_email |

---

## Structural Rules

### Rule 1: Every System is a Wheel

```python
# WRONG - Thinking hierarchically
class System:
    def __init__(self):
        self.parent = None
        self.children = []

# RIGHT - Thinking in wheels
class Wheel:
    def __init__(self, hub_entity):
        self.hub = hub_entity           # The axle - what everything anchors to
        self.spokes = []                # Major connections radiating out
        self.failure_spokes = []        # Error states for this wheel
        self.sub_wheels = {}            # Smaller wheels at spoke endpoints
```

### Rule 2: Hubs Contain Core Metrics

Every hub should contain:
- The **core entity** (company_id, person_id, etc.)
- The **core metric** (BIT score, health score, etc.)
- The **anchor fields** (domain, pattern, slots)

```python
class CompanyHub:
    """The Company Hub - Central Axle of the Barton System"""

    def __init__(self):
        # Core entity
        self.company_id = None

        # Core metric (BIT lives INSIDE the hub)
        self.bit_score = 0

        # Anchor fields - required for spokes to function
        self.domain = None
        self.email_pattern = None
        self.slots = {'CEO': None, 'CFO': None, 'HR': None}
```

### Rule 3: Spokes Feed the Hub

All spokes ultimately provide data that feeds back to the hub:

```python
class PeopleNode:
    """A spoke of the Company Hub"""

    def process(self, person_data):
        # Do spoke-specific work
        matched_company = self.fuzzy_match(person_data)
        verified_email = self.verify_email(person_data)

        # ALWAYS feed back to hub
        return {
            'feeds_hub': True,
            'hub_field': 'bit_score',
            'signal': 'slot_filled',
            'impact': +10
        }
```

### Rule 4: Failures are Spokes, Not Exceptions

Failures are not exceptions to handle - they are **legitimate spokes** of the wheel:

```python
class PeopleNode:
    def __init__(self):
        # Main spokes
        self.fuzzy_matching = FuzzyMatchingSpoke()
        self.slot_assignment = SlotAssignmentSpoke()
        self.email_generation = EmailGenerationSpoke()

        # Failure spokes (equally important!)
        self.failed_company_match = FailureSpoke('failed_company_match')
        self.failed_slot_assignment = FailureSpoke('failed_slot_assignment')
        self.failed_low_confidence = FailureSpoke('failed_low_confidence')
        self.failed_no_pattern = FailureSpoke('failed_no_pattern')
        self.failed_email_verification = FailureSpoke('failed_email_verification')

    def process(self, data):
        result = self.fuzzy_matching.execute(data)

        if result.score < 0.80:
            # Route to failure spoke - NOT an exception!
            return self.failed_company_match.route(data, result)

        # Continue to next spoke...
```

### Rule 5: Sub-Wheels are Fractal

A spoke can have its own wheel at the endpoint:

```python
class EmailVerificationSubWheel:
    """A wheel within the People Node spoke"""

    def __init__(self):
        # This wheel's hub
        self.hub = MillionVerifierAPI()

        # This wheel's spokes
        self.pattern_guesser = PatternGuesserSpoke()  # FREE
        self.bulk_verifier = BulkVerifierSpoke()      # CHEAP
        self.pattern_saver = PatternSaverSpoke()

        # This wheel's failure spokes
        self.invalid_email = FailureSpoke('invalid_email')
        self.timeout_error = FailureSpoke('timeout_error')
```

### Rule 6: Layout is Radial, Not Hierarchical

```
# WRONG - Top-down hierarchy
System
├── Module A
│   ├── Function 1
│   └── Function 2
├── Module B
└── Module C

# RIGHT - Radial wheel
         Module B
            │
Module A ───●─── Module C
            │
         Module D
```

---

## Applying to Code Architecture

### File Structure

```
project/
├── hub/                        # The central hub
│   ├── company_hub.py
│   └── bit_engine.py          # Core metric lives in hub
│
├── spokes/                     # Major domain spokes
│   ├── people_node/
│   │   ├── fuzzy_matching.py
│   │   ├── slot_assignment.py
│   │   ├── email_generation.py
│   │   └── sub_wheels/         # Fractal sub-wheels
│   │       └── email_verification/
│   │           ├── pattern_guesser.py
│   │           └── bulk_verifier.py
│   │
│   ├── dol_node/
│   │   ├── form_5500.py
│   │   └── schedule_a.py
│   │
│   └── talent_flow/
│       ├── movement_detection.py
│       └── job_changes.py
│
├── failures/                   # Failure spoke tables
│   ├── failed_company_match.py
│   ├── failed_slot_assignment.py
│   ├── failed_low_confidence.py
│   ├── failed_no_pattern.py
│   └── failed_email_verification.py
│
└── adapters/                   # External rim connections
    ├── millionverifier_adapter.py
    ├── neon_adapter.py
    └── firecrawl_adapter.py
```

### Class Design

```python
class BicycleWheel:
    """Base class for all wheel structures"""

    def __init__(self, hub_entity_name: str):
        self.hub = Hub(hub_entity_name)
        self.spokes = {}
        self.failure_spokes = {}
        self.sub_wheels = {}

    def add_spoke(self, name: str, spoke: 'Spoke'):
        self.spokes[name] = spoke

    def add_failure_spoke(self, name: str, table_name: str):
        self.failure_spokes[name] = FailureSpoke(table_name)

    def add_sub_wheel(self, spoke_name: str, wheel: 'BicycleWheel'):
        self.sub_wheels[spoke_name] = wheel

    def rotate(self, data):
        """Process data through the wheel (clockwise)"""
        for spoke_name, spoke in self.spokes.items():
            result = spoke.process(data)

            if result.failed:
                # Route to appropriate failure spoke
                return self.failure_spokes[result.failure_type].route(data, result)

            # Check if this spoke has a sub-wheel
            if spoke_name in self.sub_wheels:
                data = self.sub_wheels[spoke_name].rotate(data)

        # Feed results back to hub
        return self.hub.receive(data)
```

---

## Diagramming Standards

When creating diagrams, ALWAYS use the bicycle wheel model:

### Required Elements

1. **Central Hub** - Double-bordered box with core entity and metric
2. **Spokes** - Lines radiating from hub to domain boxes
3. **Failure Spokes** - Smaller boxes attached to each hub/sub-hub
4. **Sub-Wheels** - Nested wheel structures at spoke endpoints
5. **Feedback Arrows** - Show how spokes feed back to hub

### Template

```
                           ┌─────────────────────────────────┐
                           │     FAILURE_SPOKE_1             │
                           │     • condition                 │
                           │     • resolution                │
                           └─────────────────────────────────┘
                                          ╲
                                            ╲
        ┌─────────────────────┐               ╲
        │    SPOKE_A          │                 ╲
        │    • function 1     │───────────────────────────────────────┐
        │    • function 2     │                                       │
        └─────────────────────┘                                       │
                                                                      │
                                    ╔═════════════════════════════════════════╗
                                    ║                                         ║
        ┌─────────────────────┐     ║            HUB NAME                     ║     ┌─────────────────────┐
        │    SPOKE_B          │═════╣      ┌───────────────────┐              ║═════│    SPOKE_C          │
        │    • function 1     │     ║      │   CORE METRIC     │              ║     │    • function 1     │
        │    • function 2     │     ║      │   (inside hub)    │              ║     │    • function 2     │
        └─────────────────────┘     ║      └───────────────────┘              ║     └─────────────────────┘
                                    ║                                         ║
                                    ║      • anchor_field_1                   ║
                                    ║      • anchor_field_2                   ║
                                    ║      • anchor_field_3                   ║
                                    ║                                         ║
                                    ╚═════════════════════════════════════════╝
                                                      │
                                                      │
                           ┌─────────────────────────────────┐
                           │     FAILURE_SPOKE_2             │
                           │     • condition                 │
                           │     • resolution                │
                           └─────────────────────────────────┘
```

---

## Why Bicycle Wheels?

### 1. Everything Connects to a Center
Just like a bicycle wheel, every component in a system connects to a central hub. This prevents orphaned code and ensures data integrity.

### 2. Load Distribution
In a bicycle wheel, load is distributed across all spokes. In our systems, processing is distributed across domain spokes, with failures handled by their own spokes.

### 3. Fractal Scalability
Wheels can have sub-wheels. As systems grow, we don't add hierarchy - we add wheels within wheels.

### 4. Rotation = Flow
Data flows through the system like a wheel rotating. Each spoke gets its turn, and the wheel keeps spinning.

### 5. Visible Failures
Failure spokes are just as visible as success spokes. Failures are not hidden in catch blocks - they are first-class citizens with their own tables and resolutions.

---

## Checklist for New Features

When adding any new feature, ask:

- [ ] What **wheel** does this belong to?
- [ ] Is it a **spoke** of an existing wheel, or a new **sub-wheel**?
- [ ] What **failure spokes** does it need?
- [ ] How does it **feed back** to the central hub?
- [ ] Does it need its own **core metric** in the hub?

---

## Summary

```
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│                                                                                         │
│   "Think in wheels. Code in wheels. Diagram in wheels."                                │
│                                                                                         │
│   • Every system is a bicycle wheel with a hub, spokes, and sub-wheels               │
│   • Failures are spokes, not exceptions                                                │
│   • All spokes feed the central hub                                                    │
│   • Wheels can contain wheels (fractal)                                                │
│   • Layout is radial, not hierarchical                                                 │
│                                                                                         │
│   This is the Barton way.                                                              │
│                                                                                         │
└─────────────────────────────────────────────────────────────────────────────────────────┘
```

---

*Adopted: December 2024*
*Version: 1.0*
*Applies to: All Barton Outreach systems, IMO Creator, and future projects*
