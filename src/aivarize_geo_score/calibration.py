"""Empirical calibration pipeline for GEO scoring.

Fetches full audit results from Supabase, computes per-dimension Pearson
correlations with AI citation outcomes, and recommends weight adjustments.
Requires >= 100 paired results for meaningful statistical analysis.

Usage:
    from calibration import calibrate_from_results, save_calibration, load_calibration

    result = calibrate_from_results(audit_results, ai_test_results)
    save_calibration(result, "data/calibration.json")

See also: docs/SCORING-LIMITATIONS.md for context on current heuristic weights.
"""
import json
import logging
import os

__all__ = [
    "calibrate_from_results",
    "save_calibration",
    "load_calibration",
    "validate_audit_results",
    "validate_ai_test_results",
    "MINIMUM_PAIRED_RESULTS",
    "DEFAULT_CALIBRATION_PATH",
    "fetch_calibration_data",
    "calibrate_from_supabase_data",
    "_pearson_correlation",
]

logger = logging.getLogger(__name__)

_DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
DEFAULT_CALIBRATION_PATH = os.path.join(_DATA_DIR, "calibration.json")

# Minimum paired results needed for meaningful correlation analysis
MINIMUM_PAIRED_RESULTS = 100

try:
    from supabase import create_client
except ImportError:
    create_client = None

_cal_client = None


def _get_calibration_client():
    """Return lazily-initialized Supabase client for calibration queries."""
    global _cal_client
    if _cal_client is not None:
        return _cal_client

    if create_client is None:
        return None

    url = os.environ.get("SUPABASE_URL", "")
    key = os.environ.get("SUPABASE_SERVICE_KEY", "")
    if not url or not key:
        return None

    _cal_client = create_client(url, key)
    return _cal_client


def fetch_calibration_data() -> list:
    """Fetch full audit results from Supabase for calibration.

    Returns only rows where DataForSEO data is present (aio_queries_tested > 0),
    since calibration needs the citation outcome side.

    Returns:
        List of row dicts from geo_full_audits, or empty list on failure.
    """
    client = _get_calibration_client()
    if client is None:
        return []
    try:
        response = (
            client.table("geo_full_audits")
            .select("*")
            .gt("aio_queries_tested", 0)
            .execute()
        )
        return response.data or []
    except Exception:
        return []


def _pearson_correlation(x: list, y: list) -> float:
    """Compute Pearson correlation coefficient between two lists.

    Returns 0.0 if insufficient variance or mismatched lengths.
    Uses stdlib only (no numpy dependency).
    """
    n = min(len(x), len(y))
    if n < 3:
        return 0.0

    x, y = x[:n], y[:n]
    mean_x = sum(x) / n
    mean_y = sum(y) / n

    cov = sum((xi - mean_x) * (yi - mean_y) for xi, yi in zip(x, y))
    std_x = (sum((xi - mean_x) ** 2 for xi in x)) ** 0.5
    std_y = (sum((yi - mean_y) ** 2 for yi in y)) ** 0.5

    if std_x == 0 or std_y == 0:
        return 0.0

    return round(cov / (std_x * std_y), 4)


def calibrate_from_supabase_data(rows: list) -> dict:
    """Compute per-dimension correlations with AI citation outcomes.

    Takes rows from geo_full_audits and correlates each dimension score
    with a composite citation outcome: aio_client_cited + ai_mode_client_cited
    + llm_mentions_total (normalized).

    Args:
        rows: List of dicts from geo_full_audits table.

    Returns:
        Dict with status, row_count, correlations, weight_adjustments.
    """
    if len(rows) < MINIMUM_PAIRED_RESULTS:
        return {
            "status": "insufficient_data",
            "row_count": len(rows),
            "minimum_required": MINIMUM_PAIRED_RESULTS,
            "correlations": None,
            "weight_adjustments": None,
        }

    dimensions = [
        "ai_citability", "ai_discoverability", "brand_entity",
        "content_quality", "technical_foundation",
    ]

    # Build citation outcome score per row
    # Composite: AIO citations + AI Mode citations + LLM mentions (capped at 10)
    citation_outcomes = []
    for row in rows:
        outcome = (
            (row.get("aio_client_cited") or 0)
            + (row.get("ai_mode_client_cited") or 0)
            + min(row.get("llm_mentions_total") or 0, 10)
        )
        citation_outcomes.append(outcome)

    # Compute per-dimension correlations
    correlations = {}
    for dim in dimensions:
        dim_scores = []
        for row in rows:
            scores = row.get("scores", {})
            if isinstance(scores, str):
                scores = json.loads(scores)
            dim_scores.append(scores.get(dim, 0))
        correlations[dim] = _pearson_correlation(dim_scores, citation_outcomes)

    # Compute weight adjustments: proportional to absolute correlation strength
    # Stronger correlation → higher weight
    abs_corrs = {dim: abs(c) for dim, c in correlations.items()}
    total_abs = sum(abs_corrs.values())
    if total_abs == 0:
        # No correlation signal — return current weights unchanged
        weight_adjustments = {dim: 0.20 for dim in dimensions}
    else:
        weight_adjustments = {
            dim: round(abs_c / total_abs, 4)
            for dim, abs_c in abs_corrs.items()
        }

    return {
        "status": "calibrated",
        "row_count": len(rows),
        "minimum_required": MINIMUM_PAIRED_RESULTS,
        "correlations": correlations,
        "weight_adjustments": weight_adjustments,
    }


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
