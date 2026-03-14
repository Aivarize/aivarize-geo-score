# aivarize-geo-score

Reference implementation of the Aivarize GEO Scoring methodology — a composite scoring framework for Generative Engine Optimization (GEO).

GEO measures how well a website is optimized for AI-powered search engines (ChatGPT, Perplexity, Google AI Overviews, Gemini, Claude) rather than traditional search rankings. This library calculates a weighted composite GEO Score (0-100) across 5 dimensions with industry-aware weight profiles.

**Zero dependencies** — stdlib only. Python 3.9+.

## Install

```bash
pip install aivarize-geo-score
```

## Quick Start

```python
from aivarize_geo_score import calculate_geo_score

result = calculate_geo_score({
    "brand_entity": 72,
    "content_quality": 65,
    "ai_citability": 58,
    "ai_discoverability": 45,
    "technical_foundation": 80,
}, industry="saas")

print(result["geo_score"])  # 64
print(result["label"])      # "Fair"
print(result["weighted"])   # per-dimension weighted contributions
```

## Scoring Model (v4.0)

The GEO Score is a weighted composite across 5 dimensions, calibrated from 230+ empirical studies:

| Dimension | Weight | What it measures |
|-----------|--------|------------------|
| Brand & Entity | 30% | Entity recognition, brand mentions, cross-platform authority |
| Content Quality | 24% | E-E-A-T signals, expertise, original research, freshness |
| AI Citability | 23% | Passage structure, factual density, quotability |
| AI Discoverability | 13% | AI crawler access, sitemap, SSR, schema quality |
| Technical Foundation | 10% | Crawlability, security, internal linking |

### Score Labels

| Score Range | Label |
|-------------|-------|
| 85-100 | Excellent |
| 70-84 | Good |
| 55-69 | Fair |
| 35-54 | Poor |
| 0-34 | Critical |

Note: Industry-specific thresholds may differ (e.g., local businesses: 70+ = Excellent).

## Industry-Aware Scoring

Pass an `industry` parameter to use industry-specific weight profiles and label thresholds:

```python
from aivarize_geo_score import calculate_geo_score, SUPPORTED_INDUSTRIES

print(SUPPORTED_INDUSTRIES)
# ('local', 'ecommerce', 'saas', 'publisher', 'healthcare',
#  'finance', 'legal', 'professional_services', 'education',
#  'hospitality', 'real_estate')

result = calculate_geo_score(scores, industry="healthcare")
```

## Industry Detection

Classify a website's industry from page data:

```python
from aivarize_geo_score import detect_industry

page_data = {
    "url": "https://example.com",
    "schema_types": ["LocalBusiness", "Restaurant"],
    "title": "Best Pizza in Brooklyn",
}

result = detect_industry(page_data)
print(result["industry"])    # "local"
print(result["confidence"])  # 0.85
```

## Benchmarks & Percentiles

Compare a score against synthetic benchmark distributions:

```python
from aivarize_geo_score import get_percentile, get_benchmark_context

percentile = get_percentile(72, industry="saas")  # e.g., 68
context = get_benchmark_context(72, industry="saas")
# "Score 72 = 68th percentile for SaaS / B2B Tech"
```

## Legacy Score Migration

Automatically migrate scores from older GEO scoring versions (v1-v3) to v4.0:

```python
from aivarize_geo_score import auto_migrate

# v3 7-dimension input
old_scores = {
    "ai_citability": 60, "ai_discoverability": 50,
    "brand_entity": 70, "content_quality": 65,
    "technical_foundation": 75, "structured_data": 55,
    "content_richness": 45,
}

migrated = auto_migrate(old_scores)
# Returns 5-dimension v4.0 format
```

## API Reference

### Core Functions

- **`calculate_geo_score(scores, industry=None, confidence_data=None)`** — Calculate weighted composite GEO score. Returns dict with `geo_score`, `label`, `weighted`, `industry`, `scoring_version`.
- **`get_score_label(score, industry=None)`** — Get the label (Excellent/Good/Fair/Poor/Critical) for a score.
- **`auto_migrate(scores)`** — Auto-detect and migrate v1/v2/v3 scores to v4.0 format.
- **`calculate_confidence(confidence_data)`** — Calculate confidence level (high/medium/low) for an audit.

### Benchmarks

- **`get_percentile(score, industry=None)`** — Estimate percentile ranking (0-100).
- **`get_benchmark_context(score, industry=None)`** — Human-readable percentile string.

### Industry Detection

- **`detect_industry(page_data)`** — Classify industry from page data. Returns `{industry, confidence, display_name, signals}`.
- **`IndustrySignal`** — Dataclass for individual detection signals.

### Constants

- **`WEIGHTS`** — Default dimension weights (dict).
- **`INDUSTRY_PROFILES`** — All industry weight profiles and thresholds.
- **`SUPPORTED_INDUSTRIES`** — Tuple of valid industry keys.
- **`KNOWN_LIMITATIONS`** — List of documented scoring limitations.

## License

MIT — see [LICENSE](LICENSE).
