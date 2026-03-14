"""Empirical calibration pipeline scaffold for GEO scoring.

Scaffold — active calibration requires > 100 paired audit+citation results.
This module provides the data structures and persistence layer for future
weight calibration based on real audit outcomes.

Usage:
    from calibration import calibrate_from_results, save_calibration, load_calibration

    result = calibrate_from_results(audit_results, ai_test_results)
    save_calibration(result, "data/calibration.json")

See also: docs/SCORING-LIMITATIONS.md for context on current heuristic weights.
"""
import json
import os

__all__ = [
    "calibrate_from_results",
    "save_calibration",
    "load_calibration",
    "validate_audit_results",
    "validate_ai_test_results",
    "MINIMUM_PAIRED_RESULTS",
]

_DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
DEFAULT_CALIBRATION_PATH = os.path.join(_DATA_DIR, "calibration.json")

# Minimum paired results needed for meaningful correlation analysis
MINIMUM_PAIRED_RESULTS = 100


def validate_audit_results(audit_results: list) -> bool:
    """Validate that audit results have the required structure.

    Each entry must have 'url', 'scores', and 'geo_score' keys.

    Args:
        audit_results: List of audit result dicts.

    Returns:
        True if all entries are valid, False otherwise.
    """
    for entry in audit_results:
        if "url" not in entry or "geo_score" not in entry:
            return False
    return True


def validate_ai_test_results(ai_test_results: list) -> bool:
    """Validate that AI test results have the required structure.

    Each entry must have 'url' and 'cited_by' keys.

    Args:
        ai_test_results: List of AI test result dicts.

    Returns:
        True if all entries are valid, False otherwise.
    """
    for entry in ai_test_results:
        if "url" not in entry or "cited_by" not in entry:
            return False
    return True


def calibrate_from_results(audit_results: list, ai_test_results: list) -> dict:
    """Correlate GEO scores with actual AI citation outcomes.

    Scaffold — implementation pending. Requires > 100 paired audit+citation
    results for meaningful statistical analysis.

    Args:
        audit_results: List of {url, scores, geo_score} dicts from completed audits.
        ai_test_results: List of {url, cited_by: ["chatgpt", "perplexity", ...]} dicts
                         from AI response testing.

    Returns:
        Dict with:
          - status: "insufficient_data" or "calibrated"
          - paired_count: Number of URLs appearing in both lists
          - minimum_required: Minimum paired results needed (100)
          - correlations: Per-dimension correlation coefficients (None until sufficient data)
          - weight_adjustments: Recommended weight changes (None until sufficient data)
    """
    # Count paired results (URLs in both lists)
    audit_urls = {entry["url"] for entry in audit_results if "url" in entry}
    ai_urls = {entry["url"] for entry in ai_test_results if "url" in entry}
    paired_urls = audit_urls & ai_urls
    paired_count = len(paired_urls)

    # Implementation pending — requires > 100 paired results
    if paired_count < MINIMUM_PAIRED_RESULTS:
        return {
            "status": "insufficient_data",
            "paired_count": paired_count,
            "minimum_required": MINIMUM_PAIRED_RESULTS,
            "correlations": None,
            "weight_adjustments": None,
        }

    # Future: compute per-dimension Pearson correlation with citation rates
    # Future: suggest weight adjustments based on correlation strength
    return {
        "status": "calibrated",
        "paired_count": paired_count,
        "minimum_required": MINIMUM_PAIRED_RESULTS,
        "correlations": None,  # TODO: compute when implementation is active
        "weight_adjustments": None,  # TODO: compute when implementation is active
    }


def save_calibration(calibration_data: dict, filepath: str = None) -> None:
    """Save calibration results to a JSON file.

    Args:
        calibration_data: Dict with calibration results.
        filepath: Path to save to. Defaults to scripts/data/calibration.json.
    """
    filepath = filepath or DEFAULT_CALIBRATION_PATH
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, "w") as f:
        json.dump(calibration_data, f, indent=2)


def load_calibration(filepath: str = None) -> dict:
    """Load calibration results from a JSON file.

    Args:
        filepath: Path to load from. Defaults to scripts/data/calibration.json.

    Returns:
        Dict with calibration data, or None if file doesn't exist.
    """
    filepath = filepath or DEFAULT_CALIBRATION_PATH
    if not os.path.exists(filepath):
        return None
    with open(filepath) as f:
        return json.load(f)
