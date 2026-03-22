"""GEO Score calculator with correct weighted composite scoring.

Extracts scoring logic into a reusable module to ensure consistency
across audit reports, PDF generation, and historical tracking.
"""

# Known limitations of the scoring framework — see docs/SCORING-LIMITATIONS.md
KNOWN_LIMITATIONS = [
    "Regex-based entity detection: limited precision, not ML-calibrated",
    "Platform weights are evidence-derived (230+ studies) but not calibrated against own citation outcomes",
    "Benchmark percentiles are synthetic — based on estimated distributions, not measured data",
    "Freshness decay is a step function approximation",
    "Schema quality tiers (rich/generic/none) based on single study (Growth Marshal, 730 citations)",
    "Brand & Entity correlations are strong (ρ=0.664-0.737) but entirely correlational — no causal isolation",
    "Content front-loading detection uses simple pattern matching, not NLP-based position analysis",
    "Non-promotional tone uses keyword matching, not ML-based sentiment/tone classification",
    "Single-page quick audit has lower confidence than multi-page full audit",
]

import json
import sys

__all__ = [
    "calculate_geo_score",
    "calculate_confidence",
    "get_score_label",
    "auto_migrate",
    "migrate_scores",
    "migrate_5_to_7",
    "recalculate_historical",
    "GEOScorer",
    "WEIGHTS",
    "SCORING_VERSION",
    "REQUIRED_DIMENSIONS",
    "SCORE_LABELS",
    "SUPPORTED_INDUSTRIES",
    "INDUSTRY_PROFILES",
    "KNOWN_LIMITATIONS",
]

SCORING_VERSION = "4.2"

# Official GEO scoring weights (5-dimension model, v4.0)
# Evidence: 230+ studies, formula: effect_magnitude × study_quality × log10(sample_size)
WEIGHTS = {
    "brand_entity": 0.30,        # ρ=0.664-0.737, strongest measured correlations
    "content_quality": 0.24,     # OR=4.2 + causal freshness (22% + 2% absorbed richness)
    "ai_citability": 0.23,       # Passage structure, 44.2% front-loading signal
    "ai_discoverability": 0.13,  # Retrieval 7.7x but schema near-null
    "technical_foundation": 0.10, # Floor constraint model (ρ=-0.12 to -0.18)
}

# Industry alias map — historical keys that resolve to current industry keys
_INDUSTRY_ALIASES = {"finance_legal": "finance"}


def _resolve_industry(industry: str) -> str:
    """Resolve industry aliases to canonical keys.

    Returns the input unchanged if it's not an alias.
    None input returns None.
    """
    if industry is None:
        return None
    return _INDUSTRY_ALIASES.get(industry, industry)

# v2.0 weights (5-dimension model) — used for v2→v3 migration
_V2_WEIGHTS = {
    "ai_citability": 0.25,
    "brand_authority": 0.20,
    "content_eeat": 0.25,
    "technical": 0.20,
    "schema": 0.10,
}

# v1.0 weights (6-dimension model) — used for v1→v2 migration
_V1_WEIGHTS = {
    "ai_citability": 0.25,
    "brand_authority": 0.20,
    "content_eeat": 0.20,
    "technical": 0.15,
    "schema": 0.10,
    "platform_optimization": 0.10,
}

REQUIRED_DIMENSIONS = set(WEIGHTS.keys())

SCORE_LABELS = [
    (85, "Excellent"),
    (70, "Good"),
    (55, "Fair"),
    (35, "Poor"),
    (0, "Critical"),
]

# 13 industry categories + general default
SUPPORTED_INDUSTRIES = (
    "local",
    "ecommerce",
    "saas",
    "publisher",
    "healthcare",
    "finance",
    "legal",
    "professional_services",
    "education",
    "hospitality",
    "real_estate",
    "wellness",
    "food_beverage",
)

INDUSTRY_PROFILES = {
    "general": {
        "display_name": "General",
        "weights": dict(WEIGHTS),
        "thresholds": list(SCORE_LABELS),
    },
    "local": {
        "display_name": "Local Business",
        "weights": {
            "brand_entity": 0.30,
            "content_quality": 0.20,  # 18% + 2% absorbed richness
            "ai_citability": 0.12,
            "ai_discoverability": 0.15,
            "technical_foundation": 0.23,  # local needs maps/NAP/technical
        },
        "thresholds": [
            (70, "Excellent"),
            (55, "Good"),
            (40, "Fair"),
            (25, "Poor"),
            (0, "Critical"),
        ],
    },
    "ecommerce": {
        "display_name": "E-commerce",
        "weights": {
            "brand_entity": 0.15,
            "content_quality": 0.22,  # 20% + 2% absorbed
            "ai_citability": 0.18,
            "ai_discoverability": 0.15,
            "technical_foundation": 0.30,  # speed/CWV critical for ecom
        },
        "thresholds": [
            (75, "Excellent"),
            (60, "Good"),
            (45, "Fair"),
            (30, "Poor"),
            (0, "Critical"),
        ],
    },
    "saas": {
        "display_name": "SaaS / B2B Tech",
        "weights": {
            "brand_entity": 0.25,
            "content_quality": 0.24,  # 22% + 2%
            "ai_citability": 0.25,
            "ai_discoverability": 0.13,
            "technical_foundation": 0.13,
        },
        "thresholds": [
            (80, "Excellent"),
            (65, "Good"),
            (50, "Fair"),
            (35, "Poor"),
            (0, "Critical"),
        ],
    },
    "publisher": {
        "display_name": "Publisher / Media",
        "weights": {
            "brand_entity": 0.25,
            "content_quality": 0.28,  # 25% + 3%
            "ai_citability": 0.25,
            "ai_discoverability": 0.12,
            "technical_foundation": 0.10,
        },
        "thresholds": [
            (85, "Excellent"),
            (70, "Good"),
            (55, "Fair"),
            (35, "Poor"),
            (0, "Critical"),
        ],
    },
    "healthcare": {
        "display_name": "Healthcare (YMYL)",
        "weights": {
            "brand_entity": 0.30,
            "content_quality": 0.30,  # 28% + 2%
            "ai_citability": 0.15,
            "ai_discoverability": 0.13,
            "technical_foundation": 0.12,
        },
        "thresholds": [
            (85, "Excellent"),
            (70, "Good"),
            (55, "Fair"),
            (40, "Poor"),
            (0, "Critical"),
        ],
    },
    "finance": {
        "display_name": "Finance (YMYL)",
        "weights": {
            "brand_entity": 0.28,
            "content_quality": 0.32,  # 30% + 2%
            "ai_citability": 0.15,
            "ai_discoverability": 0.13,
            "technical_foundation": 0.12,
        },
        "thresholds": [
            (85, "Excellent"),
            (70, "Good"),
            (55, "Fair"),
            (40, "Poor"),
            (0, "Critical"),
        ],
    },
    "legal": {
        "display_name": "Legal (YMYL)",
        "weights": {
            "brand_entity": 0.25,
            "content_quality": 0.30,  # 28% + 2%
            "ai_citability": 0.18,
            "ai_discoverability": 0.12,
            "technical_foundation": 0.15,
        },
        "thresholds": [
            (80, "Excellent"),
            (65, "Good"),
            (50, "Fair"),
            (35, "Poor"),
            (0, "Critical"),
        ],
    },
    "professional_services": {
        "display_name": "Professional Services",
        "weights": {
            "brand_entity": 0.30,
            "content_quality": 0.30,  # 25% + 5%
            "ai_citability": 0.15,
            "ai_discoverability": 0.10,
            "technical_foundation": 0.15,
        },
        "thresholds": [
            (75, "Excellent"),
            (60, "Good"),
            (45, "Fair"),
            (30, "Poor"),
            (0, "Critical"),
        ],
    },
    "education": {
        "display_name": "Education",
        "weights": {
            "brand_entity": 0.15,
            "content_quality": 0.35,  # 28% + 7%
            "ai_citability": 0.23,
            "ai_discoverability": 0.15,
            "technical_foundation": 0.12,
        },
        "thresholds": [
            (80, "Excellent"),
            (65, "Good"),
            (50, "Fair"),
            (35, "Poor"),
            (0, "Critical"),
        ],
    },
    "hospitality": {
        "display_name": "Hospitality & Tourism",
        "weights": {
            "brand_entity": 0.32,
            "content_quality": 0.25,  # 18% + 7%
            "ai_citability": 0.18,
            "ai_discoverability": 0.13,
            "technical_foundation": 0.12,
        },
        "thresholds": [
            (70, "Excellent"),
            (55, "Good"),
            (40, "Fair"),
            (25, "Poor"),
            (0, "Critical"),
        ],
    },
    "real_estate": {
        "display_name": "Real Estate",
        "weights": {
            "brand_entity": 0.35,
            "content_quality": 0.25,  # 22% + 3%
            "ai_citability": 0.20,
            "ai_discoverability": 0.05,
            "technical_foundation": 0.15,
        },
        "thresholds": [
            (75, "Excellent"),
            (60, "Good"),
            (45, "Fair"),
            (30, "Poor"),
            (0, "Critical"),
        ],
    },
    "wellness": {
        "display_name": "Wellness & Fitness",
        "weights": {
            "brand_entity": 0.28,
            "content_quality": 0.28,
            "ai_citability": 0.20,
            "ai_discoverability": 0.12,
            "technical_foundation": 0.12,
        },
        "thresholds": [
            (75, "Excellent"),
            (60, "Good"),
            (45, "Fair"),
            (30, "Poor"),
            (0, "Critical"),
        ],
    },
    "food_beverage": {
        "display_name": "Food & Beverage",
        "weights": {
            "brand_entity": 0.30,
            "content_quality": 0.22,
            "ai_citability": 0.15,
            "ai_discoverability": 0.13,
            "technical_foundation": 0.20,
        },
        "thresholds": [
            (70, "Excellent"),
            (55, "Good"),
            (40, "Fair"),
            (25, "Poor"),
            (0, "Critical"),
        ],
    },
}


def get_score_label(score: int, industry: str = None) -> str:
    """Return the label for a given score, optionally using industry thresholds."""
    industry = _resolve_industry(industry)
    if industry and industry in INDUSTRY_PROFILES:
        thresholds = INDUSTRY_PROFILES[industry]["thresholds"]
    else:
        thresholds = SCORE_LABELS
    for threshold, label in thresholds:
        if score >= threshold:
            return label
    return "Critical"


def migrate_scores(old_scores: dict) -> dict:
    """Migrate 6-dimension scores to 5-dimension model (v1 → v2).

    If platform_optimization is present, its weighted contribution is
    split 50/50 into content_eeat and technical. The new dimension
    scores are calculated so that the weighted contribution is preserved:
      new_content = (old_content * old_content_weight + platform * old_platform_weight * 0.5) / new_content_weight
      new_technical = (old_technical * old_technical_weight + platform * old_platform_weight * 0.5) / new_technical_weight

    If platform_optimization is not present, returns a copy unchanged.

    Args:
        old_scores: Dict mapping dimension names to scores (0-100).

    Returns:
        Dict with 5 dimensions (platform_optimization removed).
    """
    if "platform_optimization" not in old_scores:
        return dict(old_scores)

    platform_val = old_scores["platform_optimization"]
    old_platform_weight = _V1_WEIGHTS["platform_optimization"]
    half_platform_weight = old_platform_weight * 0.5

    old_content_weight = _V1_WEIGHTS["content_eeat"]
    new_content_weight = _V2_WEIGHTS["content_eeat"]
    new_content = (old_scores["content_eeat"] * old_content_weight + platform_val * half_platform_weight) / new_content_weight

    old_technical_weight = _V1_WEIGHTS["technical"]
    new_technical_weight = _V2_WEIGHTS["technical"]
    new_technical = (old_scores["technical"] * old_technical_weight + platform_val * half_platform_weight) / new_technical_weight

    return {
        "ai_citability": old_scores["ai_citability"],
        "brand_authority": old_scores["brand_authority"],
        "content_eeat": round(new_content, 2),
        "technical": round(new_technical, 2),
        "schema": old_scores["schema"],
    }


def migrate_5_to_7(old_scores: dict, sub_scores: dict = None) -> dict:
    """Migrate 5-dimension (v2) scores to 7-dimension (v3) model.

    Mapping:
      - ai_citability (v2) → ai_citability (v3): citability component
      - ai_citability (v2) → ai_discoverability (v3): crawler/llms.txt component
      - brand_authority (v2) → brand_entity (v3): absorb entity sub-score
      - content_eeat (v2) → content_quality (v3): absorb content gap sub-score
      - technical (v2) → technical_foundation (v3): absorb link analysis sub-score
      - schema (v2) → structured_data (v3): entity piece moved to brand_entity
      - NEW: content_richness = 50 (neutral default, no historical data)

    The split uses the internal ratio from audit_runner._score_ai_citability():
      - citability part (50%) stays → ai_citability
      - crawler+llms.txt part (50%) → ai_discoverability

    Args:
        old_scores: Dict with 5 v2 dimension keys.
        sub_scores: Optional dict with link_analysis, content_gaps,
                    entity_recognition sub-scores for absorption.

    Returns:
        Dict with 7 v3 dimension keys.
    """
    sub_scores = sub_scores or {}

    old_cit = old_scores.get("ai_citability", 0)
    # Split ai_citability 50/50 into citability and discoverability
    new_citability = old_cit
    new_discoverability = old_cit

    # brand_authority → brand_entity (absorb entity sub-score if available)
    new_brand = old_scores.get("brand_authority", 0)
    entity_data = sub_scores.get("entity_recognition", {})
    if entity_data and "entity_score" in entity_data:
        # Blend: 75% brand_authority + 25% entity_score
        new_brand = round(new_brand * 0.75 + entity_data["entity_score"] * 0.25, 2)

    # content_eeat → content_quality (absorb content gap sub-score if available)
    new_content = old_scores.get("content_eeat", 0)
    gap_data = sub_scores.get("content_gaps", {})
    if gap_data and "gap_score" in gap_data:
        # Blend: 80% content_eeat + 20% gap_score
        new_content = round(new_content * 0.80 + gap_data["gap_score"] * 0.20, 2)

    # technical → technical_foundation (absorb link analysis sub-score if available)
    new_technical = old_scores.get("technical", 0)
    link_data = sub_scores.get("link_analysis", {})
    if link_data and "link_score" in link_data:
        # Blend: 80% technical + 20% link_score
        new_technical = round(new_technical * 0.80 + link_data["link_score"] * 0.20, 2)

    # schema → structured_data
    new_schema = old_scores.get("schema", 0)

    # content_richness: neutral 50 (no historical data)
    new_richness = 50

    return {
        "ai_citability": new_citability,
        "ai_discoverability": new_discoverability,
        "brand_entity": new_brand,
        "content_quality": new_content,
        "technical_foundation": new_technical,
        "structured_data": new_schema,
        "content_richness": new_richness,
    }


def recalculate_historical(old_entry: dict) -> dict:
    """Recalculate a historical audit entry with current v3 weights.

    Takes a history entry (with timestamp, geo_score, scores, label)
    and returns a new entry with migrated scores and recalculated geo_score.
    Auto-migrates from v1 (6-dim) or v2 (5-dim) to v3 (7-dim).

    Args:
        old_entry: Dict with at least 'scores' key. May have 5, 6, or 7 dims.

    Returns:
        New dict with 7-dim scores and recalculated geo_score/label.
    """
    migrated = _auto_migrate(old_entry["scores"])
    result = calculate_geo_score(migrated)

    new_entry = dict(old_entry)
    new_entry["scores"] = migrated
    new_entry["geo_score"] = result["geo_score"]
    new_entry["raw_score"] = result["raw_score"]
    new_entry["label"] = result["label"]
    return new_entry


def auto_migrate(scores: dict, sub_scores: dict = None) -> dict:
    """Auto-detect scoring version and migrate to v4.0 (5-dim).

    Detection:
    - 5 keys matching v4.0 dims → already current, pass through
    - 6 keys with content_richness (v3.2) → absorb richness into content_quality
    - 7 keys matching v3 dims → merge structured_data, then v3.2→v4
    - 5 keys matching v2 dims → migrate_5_to_7() then chain through
    - 6 keys with platform_optimization → migrate_scores() then chain through
    - Unknown format → raise ValueError

    Args:
        scores: Dict mapping dimension names to scores (0-100).
        sub_scores: Optional dict with link_analysis, content_gaps,
                    entity_recognition sub-scores for absorption during
                    v2→v3 migration.

    Returns:
        Dict with 5 v4.0 dimension keys.

    Raises:
        ValueError: If the score format cannot be detected.
    """
    score_keys = set(scores.keys())

    # Already 5-dim (v4.0)
    if score_keys == REQUIRED_DIMENSIONS:
        return dict(scores)

    # v3.2/v3.1 (6-dim with content_richness) → v4.0 (5-dim)
    _V32_KEYS = {"ai_citability", "ai_discoverability", "brand_entity",
                 "content_quality", "technical_foundation", "content_richness"}
    if score_keys == _V32_KEYS:
        scores = dict(scores)
        cr = scores.pop("content_richness")
        # Absorb richness into content_quality (92% CQ + 8% CR)
        scores["content_quality"] = round(scores["content_quality"] * 0.92 + cr * 0.08)
        return scores

    # v3 (7-dim with structured_data) → v3.2 (6-dim) → v4.0 (5-dim)
    _V3_KEYS = {"ai_citability", "ai_discoverability", "brand_entity",
                "content_quality", "technical_foundation", "structured_data",
                "content_richness"}
    if score_keys == _V3_KEYS:
        scores = dict(scores)
        sd = scores.pop("structured_data")
        scores["ai_discoverability"] = round(
            scores["ai_discoverability"] * 0.75 + sd * 0.25
        )
        # Now it's v3.2 format, recurse to absorb content_richness
        return auto_migrate(scores)

    # v1 (6-dim with platform_optimization) → v2 → v3 → v4
    if "platform_optimization" in scores:
        v2_scores = migrate_scores(scores)
        v3_scores = migrate_5_to_7(v2_scores, sub_scores=sub_scores)
        return auto_migrate(v3_scores)  # recurse through v3→v3.2→v4

    # v2 (5-dim) → v3 → v4
    v2_keys = set(_V2_WEIGHTS.keys())
    if score_keys == v2_keys:
        v3_scores = migrate_5_to_7(scores, sub_scores=sub_scores)
        return auto_migrate(v3_scores)  # recurse through v3→v3.2→v4

    raise ValueError(
        f"Unknown score format with keys: {sorted(score_keys)}. "
        f"Expected 5-dim v4.0 ({sorted(REQUIRED_DIMENSIONS)}), "
        f"6-dim v3.2 ({sorted(_V32_KEYS)}), "
        f"7-dim v3 ({sorted(_V3_KEYS)}), "
        f"5-dim v2 ({sorted(v2_keys)}), or 6-dim v1 (v2 + platform_optimization)."
    )


# Keep private alias for internal backward compatibility
_auto_migrate = auto_migrate


def calculate_confidence(confidence_data: dict) -> dict:
    """Calculate confidence level for a GEO score based on data availability.

    # Heuristic: confidence levels are based on data availability, not outcome validation

    Args:
        confidence_data: Dict with:
            - pages_analyzed (int): Number of pages analyzed
            - data_completeness (float): Fraction of dimensions with real data (0-1)
            - brand_data_available (bool): Whether brand scanner ran

    Returns:
        Dict with 'level' (high/medium/low) and 'factors' (original data).
    """
    pages = confidence_data.get("pages_analyzed", 0)
    completeness = confidence_data.get("data_completeness", 0.0)

    if pages >= 10 and completeness >= 0.9:
        level = "high"
    elif pages >= 1 and completeness >= 0.7:
        level = "medium"
    else:
        level = "low"

    return {
        "level": level,
        "factors": dict(confidence_data),
    }


def calculate_geo_score(scores: dict, industry: str = None,
                        confidence_data: dict = None) -> dict:
    """Calculate the weighted composite GEO score.

    Accepts 5-dimension (v4.0) input. Legacy inputs (v1 6-dim, v2 5-dim,
    v3 7-dim, v3.2 6-dim) are auto-migrated to v4.0 before calculating.

    Args:
        scores: Dict mapping dimension names to scores (0-100).
                Required keys (v4.0): ai_citability, ai_discoverability,
                brand_entity, content_quality, technical_foundation.
                Also accepts legacy v1/v2/v3/v3.2 input (auto-migrated).
        industry: Optional industry key (e.g. 'local', 'saas', 'publisher').
                  Uses industry-specific weights and thresholds.
                  None or 'general' uses default weights.
        confidence_data: Optional dict with pages_analyzed, data_completeness,
                         brand_data_available. When provided, a 'confidence'
                         key is added to the result.

    Returns:
        Dict with geo_score (rounded int), raw_score (float),
        weighted (per-dimension contributions), label, industry,
        industry_display, scoring_version, and optionally confidence.

    Raises:
        ValueError: If required dimensions are missing or industry is unknown.
    """
    industry = _resolve_industry(industry)
    if industry is not None and industry != "general" and industry not in INDUSTRY_PROFILES:
        raise ValueError(
            f"Unknown industry: '{industry}'. "
            f"Supported: {', '.join(SUPPORTED_INDUSTRIES)}"
        )

    scores = _auto_migrate(scores)

    for dim, val in scores.items():
        if not isinstance(val, (int, float)):
            raise TypeError(
                f"Score for '{dim}' must be numeric, got {type(val).__name__}: {val!r}"
            )
        if val != val:  # NaN check (NaN != NaN)
            raise ValueError(f"Score for '{dim}' is NaN")

    missing = REQUIRED_DIMENSIONS - set(scores.keys())
    if missing:
        raise ValueError(f"Missing required dimensions: {', '.join(sorted(missing))}")

    # Select weights based on industry
    effective_industry = industry if industry and industry in INDUSTRY_PROFILES else "general"
    profile = INDUSTRY_PROFILES[effective_industry]
    active_weights = profile["weights"]

    weighted = {}
    explanations = {}
    raw_total = 0.0

    for dimension, weight in active_weights.items():
        clamped = max(0, min(100, scores[dimension]))
        contribution = clamped * weight
        weighted[dimension] = round(contribution, 2)
        raw_total += contribution
        explanations[dimension] = {
            "score": clamped,
            "weight": weight,
            "contribution": round(contribution, 2),
            "signals": [],  # Populated by dimension scorers in Phase 2b
        }

    geo_score = round(raw_total)
    geo_score = max(0, min(100, geo_score))

    label = get_score_label(geo_score, effective_industry)

    result = {
        "geo_score": geo_score,
        "raw_score": round(raw_total, 2),
        "weighted": weighted,
        "explanations": explanations,
        "label": label,
        "industry": effective_industry,
        "industry_display": profile["display_name"],
        "scoring_version": SCORING_VERSION,
    }

    if confidence_data is not None:
        result["confidence"] = calculate_confidence(confidence_data)

    return result


class GEOScorer:
    """Pluggable dimension registry for GEO scoring.

    Wraps calculate_geo_score() with the ability to register custom dimensions
    or replace existing ones. The standalone calculate_geo_score() function
    remains the primary API for backwards compatibility.

    Usage:
        scorer = GEOScorer(industry="saas")
        scorer.register_dimension("voice_readiness", weight=0.10)
        result = scorer.score(scores_dict)
    """

    def __init__(self, industry=None):
        self._industry = _resolve_industry(industry)
        profile_key = self._industry if self._industry and self._industry in INDUSTRY_PROFILES else "general"
        self._dimensions = dict(INDUSTRY_PROFILES[profile_key]["weights"])

    @property
    def dimensions(self):
        """Return a copy of the current dimension weights."""
        return dict(self._dimensions)

    def register_dimension(self, name, weight, rebalance=True):
        """Add a custom dimension.

        Args:
            name: Dimension key (must not already exist).
            weight: Weight for this dimension (0-1).
            rebalance: If True, existing weights are proportionally reduced
                       to make room for the new weight (total stays 1.0).
                       If False, weight is added as-is (total may exceed 1.0).

        Raises:
            ValueError: If dimension name already exists.
        """
        if name in self._dimensions:
            raise ValueError(
                f"Dimension '{name}' already registered. "
                f"Use replace_dimension() to override."
            )

        if rebalance:
            remaining = 1.0 - weight
            current_total = sum(self._dimensions.values())
            if current_total > 0:
                factor = remaining / current_total
                for dim in self._dimensions:
                    self._dimensions[dim] *= factor

        self._dimensions[name] = weight

    def replace_dimension(self, name, weight=None):
        """Override the weight for an existing dimension.

        Args:
            name: Dimension key (must already exist).
            weight: New weight value. If None, keeps current weight.

        Raises:
            ValueError: If dimension doesn't exist.
        """
        if name not in self._dimensions:
            raise ValueError(
                f"Dimension '{name}' not registered. "
                f"Use register_dimension() to add new dimensions."
            )
        if weight is not None:
            self._dimensions[name] = weight

    def score(self, scores_dict):
        """Calculate composite GEO score using registered dimensions.

        Args:
            scores_dict: Dict mapping dimension names to scores (0-100).

        Returns:
            Dict with geo_score, raw_score, weighted, label, etc.
        """
        # If using default dimensions, delegate to calculate_geo_score
        default_key = self._industry if self._industry and self._industry in INDUSTRY_PROFILES else "general"
        default_dims = INDUSTRY_PROFILES[default_key]["weights"]
        if self._dimensions == default_dims:
            return calculate_geo_score(scores_dict, industry=self._industry)

        # Custom dimensions: calculate manually
        weighted = {}
        raw_total = 0.0
        explanations = {}

        for dimension, weight in self._dimensions.items():
            value = scores_dict.get(dimension, 0)
            clamped = max(0, min(100, value))
            contribution = clamped * weight
            weighted[dimension] = round(contribution, 2)
            raw_total += contribution
            explanations[dimension] = {
                "score": clamped,
                "weight": weight,
                "contribution": round(contribution, 2),
                "signals": [],
            }

        geo_score = round(raw_total)
        geo_score = max(0, min(100, geo_score))

        profile_key = self._industry if self._industry and self._industry in INDUSTRY_PROFILES else "general"
        label = get_score_label(geo_score, profile_key)

        return {
            "geo_score": geo_score,
            "raw_score": round(raw_total, 2),
            "weighted": weighted,
            "explanations": explanations,
            "label": label,
            "industry": profile_key,
            "industry_display": INDUSTRY_PROFILES[profile_key]["display_name"],
            "scoring_version": SCORING_VERSION,
        }


