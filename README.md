# aivarize-geo-score

Reference implementation of the Aivarize GEO Scoring methodology — a composite scoring framework for Generative Engine Optimization (GEO).

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
```

## License

MIT
