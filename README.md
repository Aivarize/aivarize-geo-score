# aivarize-geo-score

Reference implementation of the **Aivarize GEO Scoring Index (AGSI)** — a composite scoring framework for Generative Engine Optimization (GEO).

AGSI measures how well a website is optimized for AI-powered search engines (ChatGPT, Perplexity, Google AI Overviews, Gemini, Claude) rather than traditional search rankings. This library calculates a weighted composite GEO Score (0-100) across 5 dimensions with industry-aware weight profiles.

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

## Scoring Model (v5.0)

The GEO Score is a weighted composite across 5 dimensions, calibrated from 230+ empirical studies:

| Dimension | Weight | What it measures |
|-----------|--------|------------------|
| Brand & Entity | 30% | Entity recognition, brand mentions, cross-platform authority |
| Content Quality | 25% | E-E-A-T signals, expertise, original research, freshness |
| AI Citability | 23% | Passage structure, factual density, quotability |
| AI Discoverability | 12% | AI crawler access, sitemap, SSR, schema quality |
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

### What Each Dimension Measures

**Brand & Entity (30%)** — Does the brand exist as a recognized entity? Scores platform presence (YouTube, Reddit, Wikipedia, LinkedIn, G2, X, Crunchbase, GitHub), Wikidata/Knowledge Panel signals, and on-page Organization schema. Strongest measured correlation with AI citation rates.

**Content Quality (25%)** — 12 sub-scores: Freshness (22), Visible Freshness (5), Expertise (15), Information Gain (8), Semantic Completeness (8), Trustworthiness (12), Structure (8), Non-Promotional Tone (6), Content Richness (8), Terminology Precision (3), Audience Specificity (3), Podcast/Transcript (2). Industry-aware freshness decay.

**AI Citability (23%)** — Can AI models extract and quote passages? Sub-scores: Passage Citability (30), Content Depth (10), Heading Structure (10), Front-Loading (15), Source Citations (15), Content Modularity (10), Conversational Patterns (10). H2 answer capsule detection.

**AI Discoverability (12%)** — Can AI crawlers find and parse the content? Sub-scores: SSR/Rendering (35%), Crawler Access (35%), Schema Quality (15%), Sitemap/Indexability (15%). llms.txt removed from scoring (DEAD-01). Checks access for GPTBot, ClaudeBot, PerplexityBot, Google-Extended, OAI-SearchBot, ChatGPT-User.

**Technical Foundation (10%)** — Floor constraint: severe failures cap citation potential. Sub-scores: Crawlability (35%), SSR (25%), Internal Linking (20%), Web Quality (10%), Page Speed (10%).

## Industry-Aware Scoring

Pass an `industry` parameter to use industry-specific weight profiles and label thresholds:

```python
from aivarize_geo_score import calculate_geo_score, SUPPORTED_INDUSTRIES

print(SUPPORTED_INDUSTRIES)
# ('local', 'ecommerce', 'saas', 'publisher', 'healthcare',
#  'finance', 'legal', 'professional_services', 'education',
#  'hospitality', 'real_estate', 'wellness', 'food_beverage')

result = calculate_geo_score(scores, industry="healthcare")
```

### Industry Weight Matrix

| Industry | Brand | Content | Citability | Discoverability | Technical |
|----------|-------|---------|------------|-----------------|-----------|
| **General** | 30% | 24% | 23% | 13% | 10% |
| Local | 30% | 20% | 12% | 15% | 23% |
| E-commerce | 15% | 22% | 18% | 15% | 30% |
| SaaS | 25% | 24% | 25% | 13% | 13% |
| Publisher | 25% | 28% | 25% | 12% | 10% |
| Healthcare | 30% | 30% | 15% | 13% | 12% |
| Finance | 28% | 32% | 15% | 13% | 12% |
| Legal | 25% | 30% | 18% | 12% | 15% |
| Professional Services | 30% | 30% | 15% | 10% | 15% |
| Education | 15% | 35% | 23% | 15% | 12% |
| Hospitality | 32% | 25% | 18% | 13% | 12% |
| Real Estate | 35% | 25% | 20% | 5% | 15% |
| Wellness | 28% | 28% | 20% | 12% | 12% |
| Food & Beverage | 30% | 22% | 15% | 13% | 20% |

## Industry Detection

Classify a website's industry from page data:

```python
from aivarize_geo_score import detect_industry

page_data = {
    "url": "https://example.com",
    "structured_data": [{"@type": "LocalBusiness"}, {"@type": "Restaurant"}],
    "title": "Best Pizza in Brooklyn",
}

result = detect_industry(page_data)
print(result["industry"])    # "hospitality"
print(result["confidence"])  # 0.5
```

## Benchmarks & Percentiles

Compare a score against synthetic benchmark distributions:

```python
from aivarize_geo_score import get_percentile, get_benchmark_context

percentile = get_percentile(72, industry="saas")  # e.g., 68
context = get_benchmark_context(72, industry="saas")
# "Score 72 = 68th percentile for SaaS / B2B Tech"
```

## API Reference

### Core Functions

- **`calculate_geo_score(scores, industry=None, confidence_data=None)`** — Calculate weighted composite GEO score. Returns dict with `geo_score`, `label`, `weighted`, `industry`, `scoring_version`.
- **`get_score_label(score, industry=None)`** — Get the label (Excellent/Good/Fair/Poor/Critical) for a score.
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

## Known Limitations

1. **Brand correlations are observational** — Brand & Entity has the strongest measured correlations with AI citation rates, but no causal isolation study has been run
2. **Benchmark percentiles are synthetic** — estimated distributions, not measured from real audit data
3. **Freshness decay is a step function** — discrete jumps at 30/90/180/365 day boundaries
4. **Schema quality tiers from single study** — Growth Marshal (n=730); effective composite weight ~2%
5. **Regex-based entity detection** — limited precision, not ML-calibrated
6. **Front-loading uses pattern matching** — not NLP-based position analysis
7. **Non-promotional tone uses keyword matching** — not ML-based classification

Full details: `KNOWN_LIMITATIONS` constant in the package.

## License

MIT — see [LICENSE](LICENSE).
