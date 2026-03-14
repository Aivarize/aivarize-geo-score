"""GEO score benchmark percentile system.

# Heuristic: initial percentiles are synthetic estimates —
# will calibrate with real audit data
"""
import json
import os

__all__ = ["get_percentile", "get_benchmark_context"]

_DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
_BENCHMARKS = None


def _load_benchmarks():
    """Load benchmark data from JSON file."""
    global _BENCHMARKS
    if _BENCHMARKS is None:
        path = os.path.join(_DATA_DIR, "benchmarks.json")
        try:
            with open(path) as f:
                _BENCHMARKS = json.load(f)
        except FileNotFoundError:
            raise FileNotFoundError(
                f"Benchmark data not found at {path}. "
                f"This usually means the package was not installed correctly."
            )
    return _BENCHMARKS


def get_percentile(score: int, industry: str = None) -> int:
    """Estimate the percentile ranking for a GEO score.

    Uses linear interpolation between benchmark buckets.

    Args:
        score: GEO score (0-100).
        industry: Optional industry key. Defaults to "general".

    Returns:
        Estimated percentile (0-100).
    """
    benchmarks = _load_benchmarks()
    industry = industry or "general"
    if industry not in benchmarks or industry == "metadata":
        industry = "general"

    buckets = benchmarks[industry]
    # Percentile points sorted
    points = sorted([(v, int(k[1:])) for k, v in buckets.items()])
    # points = [(score_at_p10, 10), (score_at_p25, 25), ...]

    if score <= points[0][0]:
        # Below p10
        return max(1, round(points[0][1] * score / max(points[0][0], 1)))

    if score >= points[-1][0]:
        # Above p90
        # Linear extrapolation from p90 to 100
        remaining = 100 - points[-1][0]
        if remaining > 0:
            pct = points[-1][1] + (100 - points[-1][1]) * (score - points[-1][0]) / remaining
        else:
            pct = 99
        return min(99, max(points[-1][1], round(pct)))

    # Interpolate between two adjacent points
    for i in range(len(points) - 1):
        s1, p1 = points[i]
        s2, p2 = points[i + 1]
        if s1 <= score <= s2:
            if s2 == s1:
                return p1
            ratio = (score - s1) / (s2 - s1)
            return round(p1 + ratio * (p2 - p1))

    return 50  # fallback


def get_benchmark_context(score: int, industry: str = None) -> str:
    """Get human-readable benchmark context for a score.

    Args:
        score: GEO score (0-100).
        industry: Optional industry key.

    Returns:
        String like "Score 65 = 73rd percentile for SaaS / B2B Tech"
    """
    from .score_calculator import INDUSTRY_PROFILES

    percentile = get_percentile(score, industry)
    industry_key = industry or "general"
    if industry_key in INDUSTRY_PROFILES:
        display = INDUSTRY_PROFILES[industry_key]["display_name"]
    else:
        display = "General"

    # Ordinal suffix
    if 11 <= percentile % 100 <= 13:
        suffix = "th"
    elif percentile % 10 == 1:
        suffix = "st"
    elif percentile % 10 == 2:
        suffix = "nd"
    elif percentile % 10 == 3:
        suffix = "rd"
    else:
        suffix = "th"

    return f"Score {score} = {percentile}{suffix} percentile for {display}"
