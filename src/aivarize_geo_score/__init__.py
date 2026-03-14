"""Aivarize GEO Score — composite scoring for Generative Engine Optimization.

Reference implementation of the GEO Scoring methodology described in
the Aivarize GEO Scoring white paper. Calculates weighted composite
scores across 5 dimensions with industry-aware weight profiles.

Usage:
    from aivarize_geo_score import calculate_geo_score

    scores = {
        "brand_entity": 72,
        "content_quality": 65,
        "ai_citability": 58,
        "ai_discoverability": 45,
        "technical_foundation": 80,
    }
    result = calculate_geo_score(scores, industry="saas")
    print(result["geo_score"])  # 64
    print(result["label"])      # "Fair"
"""

__version__ = "1.0.0"

from .score_calculator import (
    calculate_geo_score,
    calculate_confidence,
    get_score_label,
    GEOScorer,
    WEIGHTS,
    SCORING_VERSION,
    REQUIRED_DIMENSIONS,
    SCORE_LABELS,
    SUPPORTED_INDUSTRIES,
    INDUSTRY_PROFILES,
    KNOWN_LIMITATIONS,
)
from .benchmarks import get_percentile, get_benchmark_context
from .calibration import (
    calibrate_from_results,
    save_calibration,
    load_calibration,
    validate_audit_results,
    validate_ai_test_results,
    MINIMUM_PAIRED_RESULTS,
)
from .industry_detector import detect_industry, IndustrySignal

__all__ = [
    # Core scoring
    "calculate_geo_score",
    "calculate_confidence",
    "get_score_label",
    "GEOScorer",
    # Constants
    "WEIGHTS",
    "SCORING_VERSION",
    "REQUIRED_DIMENSIONS",
    "SCORE_LABELS",
    "SUPPORTED_INDUSTRIES",
    "INDUSTRY_PROFILES",
    "KNOWN_LIMITATIONS",
    # Benchmarks
    "get_percentile",
    "get_benchmark_context",
    # Calibration
    "calibrate_from_results",
    "save_calibration",
    "load_calibration",
    "validate_audit_results",
    "validate_ai_test_results",
    "MINIMUM_PAIRED_RESULTS",
    # Industry detection
    "detect_industry",
    "IndustrySignal",
    # Version
    "__version__",
]
