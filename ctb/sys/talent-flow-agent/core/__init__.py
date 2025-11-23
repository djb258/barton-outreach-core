"""
Talent Flow Agent - Core Modules
Barton Doctrine ID: 04.04.02.04.60000.001

Modular architecture for easy corrections:
- neon_connector.py - Database operations
- diff_engine.py - Hash comparison
- movement_classifier.py - Movement detection
- confidence_scorer.py - Confidence calculation
"""

from .neon_connector import NeonConnector
from .diff_engine import DiffEngine
from .movement_classifier import MovementClassifier
from .confidence_scorer import ConfidenceScorer

__all__ = [
    'NeonConnector',
    'DiffEngine',
    'MovementClassifier',
    'ConfidenceScorer'
]
