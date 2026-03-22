---
title: "The Aivarize GEO Scoring Index — Methodology & Scoring Architecture"
author: "Aivarize"
date: "March 2026"
version: "1.0"
---

# The Aivarize GEO Scoring Index — Methodology & Scoring Architecture

## Table of Contents

1. [What This Paper Covers](#1-what-this-paper-covers)
2. [How We Built the Weights — The Evidence Calibration](#2-how-we-built-the-weights--the-evidence-calibration)
3. [How We Calculate a Site's GEO Score — The Composite Formula](#3-how-we-calculate-a-sites-geo-score--the-composite-formula)
4. [The Five Dimensions](#4-the-five-dimensions)
   - [Brand & Entity (30%)](#41-brand--entity-30)
   - [Content Quality (24%)](#42-content-quality-24)
   - [AI Citability (23%)](#43-ai-citability-23)
   - [AI Discoverability (13%)](#44-ai-discoverability-13)
   - [Technical Foundation (10%)](#45-technical-foundation-10)
5. [Industry-Adaptive Profiles](#5-industry-adaptive-profiles)
6. [Key Design Decisions](#6-key-design-decisions)
7. [Methodology Context — Where AGSI Sits](#7-methodology-context--where-agsi-sits)
8. [Limitations & Future Work](#8-limitations--future-work)
9. [Bibliography](#9-bibliography)

---

## 1. What This Paper Covers

The Aivarize GEO Scoring Index (AGSI) is a composite 0–100 score that measures how visible a website is to AI-powered search engines — ChatGPT, Perplexity, Google AI Overviews, Gemini, and Bing Copilot. As these systems replace traditional search results with generated answers, the industry lacks a standardized way to measure optimization for this new paradigm. Traditional SEO metrics — Domain Authority, PageRank, keyword density — were designed for ranked blue links, not for AI systems that cite passages, synthesize answers, and recommend brands.

The AGSI addresses this gap. Calibrated from 230+ studies, 68 extracted findings, and 15 peer-reviewed papers across NeurIPS, KDD, SIGIR, PNAS, and WWW, it synthesizes the available evidence into a five-dimension weighted composite with industry-adaptive profiles across 13 verticals.

This paper describes the two core formulas, the five scoring dimensions and their sub-scores, the industry-adaptive weight profiles, and the reasoning behind each design choice — including where the methodology is standard, where it is novel, and where its limitations lie.

---

## 2. How We Built the Weights — The Evidence Calibration

### The Problem

We needed to decide how much each dimension should matter in the final score. Should brand recognition count more than content quality? Should technical health matter as much as AI citability? Rather than guessing, we derived the weights from research.

### The Evidence Base

We collected 230+ studies across six research areas and extracted 68 discrete, scoreable findings. The evidence spans:

- **15 peer-reviewed papers** from top venues: NeurIPS [1], KDD [3], SIGIR [7], PNAS [5], ACM WWW [6][13], ICLR [11], EMNLP, and TACL — including causal experiments, benchmarks, and perturbation studies.
- **40+ large-scale industry studies** with sample sizes ranging from 1,000 prompts [10] to 304,000 URLs [16] and 500 million+ crawler fetches [22].
- **Crawler audits and regulatory reviews** covering AI bot behavior [36], content licensing dynamics, and quality rater guidelines.

### The Formula

For each of the 68 findings, we calculated:

> **weighted_evidence_score = Σ (effect_magnitude × study_quality × log₁₀(sample_size))**

This formula asks three questions about each finding:

**How big was the effect?** If a study found brand mentions correlate with AI citations at ρ=0.664, that's a large effect. If page speed correlates at ρ=0.12, that's small. Bigger effects contribute more to the dimension's total weight.

**How trustworthy is the study?** Each study is scored on a 1–5 scale. A peer-reviewed causal experiment from NeurIPS (5) carries the most weight, followed by peer-reviewed correlational (4), large-scale industry studies (3), single-source analyses (2), and editorial commentary (1). This ensures that a rigorous experiment with 1,000 subjects outweighs a correlational analysis with 100,000.

**How many data points?** Larger studies are more reliable, but we apply a logarithmic scale so a 300,000-URL study doesn't overpower a 1,000-subject experiment. The log scaling makes the larger study ~1.8x heavier, not 300x heavier. This keeps study quality and effect size as the primary drivers.

We multiply these three numbers for each finding, sum all findings per dimension, and the dimension with the highest total earns the highest weight. That process is how Brand & Entity landed at 30% — it accumulated the strongest combined evidence across the entire research base.

**Important framing note.** This formula established the directional evidence strength per dimension — it determined which dimensions deserved more weight and roughly by how much. It is not a fully reproducible meta-analytic calculation: effect magnitudes from different statistical methods (correlations, odds ratios, percentage differences) were compared on an ordinal scale rather than normalized through a formal transform. The formula produced evidence-informed starting weights that are more rigorous than pure intuition (which is what every other GEO framework uses) but less rigorous than formal meta-analysis. These starting weights are designed to be replaced over time by empirical calibration from accumulated audit data (see Section 8, Future Work).

### Sensitivity Check

To verify the weights aren't an artifact of one particular methodology, we re-ran the analysis four ways:

| Dimension | Full Method | Quality ≥ 3 | Causal Only | Count Only | Range |
|-----------|:-----------:|:-----------:|:-----------:|:----------:|:-----:|
| Brand & Entity | 30% | 34% | 9% | 19% | 9–34% |
| Content Quality | 22% | 22% | 45% | 24% | 22–45% |
| AI Citability | 23% | 19% | 18% | 25% | 18–25% |
| AI Discoverability | 13% | 13% | 7% | 21% | 7–21% |
| Technical Foundation | 10% | 12% | 15% | 9% | 9–15% |

*The Quality ≥ 3 column was re-normalized after merging Content Richness (formerly a separate dimension at 2%) into Content Quality. Original six-dimension values are preserved in the evidence extraction document.*

The Full Method column reflects raw formula output before editorial adjustments. Final weights incorporate the four adjustments described below.

The sensitivity analysis reveals a central tension: **Brand & Entity** produces the strongest measured correlations but has zero causal evidence — its weight ranges from 9% (causal-only) to 34% (quality-filtered). **Content Quality** shows the inverse: the strongest causal evidence but weaker correlations, ranging from 22% to 45%.

### Calibration Approach

The AGSI did not adopt a purely data-driven weight assignment. The process started from practitioner-informed weights and adjusted them toward the evidence, applying editorial judgment in four cases:

1. **Brand & Entity** was capped at 30% (not the 34% suggested by quality-filtered evidence) because all brand evidence is correlational — no study has causally isolated brand-building as a citation driver.
2. **Content Quality** was set at 24% (above the 22% Full Method output) to absorb the Content Richness sub-dimension that was previously a separate dimension. The 2-percentage-point increase reflects this consolidation, not a re-evaluation of the evidence.
3. **AI Citability** was set at 23% (above the 18% causal-only figure) because passage structure is the most directly actionable lever for practitioners.
4. **Technical Foundation** was held at 10% (above the 9% count-only floor) because severe technical failures are citation killers that must register in the composite score.

---

## 3. How We Calculate a Site's GEO Score — The Composite Formula

### The Formula

Each of the five dimensions is scored independently on a 0–100 scale. The composite GEO Score is:

> **AGSI = round( Σ dimension_score × dimension_weight )**

The weighted sum is rounded to the nearest integer, clamped to 0–100. The sub-score decomposition within each dimension ensures actionability — practitioners can identify which specific lever to pull, rather than receiving a single opaque number.

### Worked Example

A site scores:

| Dimension | Score | Weight | Contribution |
|-----------|:-----:|:------:|:------------:|
| Brand & Entity | 40 | × 0.30 | = 12.0 |
| Content Quality | 65 | × 0.24 | = 15.6 |
| AI Citability | 70 | × 0.23 | = 16.1 |
| AI Discoverability | 80 | × 0.13 | = 10.4 |
| Technical Foundation | 75 | × 0.10 | = 7.5 |
| **Total** | | | **= 61.6 → 62** |

The sub-scores within each dimension work the same way — they're point budgets that add up to 100 for that dimension. The Content Quality score of 65 might break down as: Freshness 25/30 + Expertise 14/23 + Trustworthiness 10/18 + Structure 8/12 + Tone 5/8 + Richness 3/9 = 65.

### Final Weights

| Dimension | Weight | Confidence |
|-----------|:------:|:----------:|
| Brand & Entity | **30%** | High |
| Content Quality | **24%** | High |
| AI Citability | **23%** | Medium |
| AI Discoverability | **13%** | High |
| Technical Foundation | **10%** | Medium |

Confidence reflects evidence convergence: **High** means three or more independent studies agree on the directional finding. **Medium** means evidence supports the weight but with limited replication or conflicting methodologies.

---

## 4. The Five Dimensions

### 4.1 Brand & Entity (30%)

**What it measures.** Whether AI models recognize a brand as a known entity — not just whether a website mentions its own name, but whether the brand exists as a node in the information graph that large language models internalize during pre-training. Evaluates entity recognition across knowledge bases, brand mentions on third-party platforms, review presence, and cross-platform authority signals.

**Why 30%.** Brand-level signals show the strongest measured correlations with AI citation rates in the entire evidence base. Branded web mentions correlate at ρ=0.664 for AI Overviews, ρ=0.709 for AI Mode, and ρ=0.656 for ChatGPT [18]. YouTube brand mentions produced the single strongest signal at ρ=0.737 [18]. Entity-level signals are 2–4x stronger than page-level signals: branded mentions ρ=0.664 versus URL rating ρ=0.18 and content length ρ=0.04 [18]. The gap between top-quartile and second-quartile brands is a 10x difference in average AI mentions (169 vs. 14) [18].

**Why not higher.** All evidence is correlational. No causal study has isolated brand-building as a direct citation driver. Cross-platform citation instability is extreme: less than 1 in 100 chance that ChatGPT produces the same brand list in any two responses to the same query [25]. Capped at 30% rather than the 34% the quality-filtered evidence suggests.

**Why not lower.** The 10x gap between top and second-quartile brands [18] and the dominance of earned media in citation results (92.1% in US Consumer Electronics [10]) mean the evidence suggests brand recognition functions as a primary correlate of AI citation — not one factor among equals, though the causal mechanism remains unestablished.

#### Sub-Scores

| Sub-Score | Weight | Evidence Basis |
|-----------|:------:|----------------|
| Brand Scanner Authority | 55% | YouTube ρ=0.737, branded mentions ρ=0.664 [18]; review profiles 3x citation [17] |
| Entity Signals | 35% | 16% of ranked entities lack snippet support — suggesting pre-training knowledge may influence citation [9]; Wikipedia 47.9% of ChatGPT top-10 [30] |
| On-Page Brand Signals | 10% | Off-page signals dominate on-page signals by a wide margin [18]. Retained for sites without off-page data |

---

### 4.2 Content Quality (24%)

**What it measures.** Whether a page meets the quality, expertise, and freshness threshold that AI systems use when selecting citation sources. Assesses E-E-A-T signals (experience, expertise, authoritativeness, trustworthiness), content depth, non-promotional tone, author entity strength, content freshness, and multimedia richness.

**Why 24%.** Page quality yields an odds ratio of 4.2 for citation — pages scoring ≥0.70 on a 16-pillar quality framework reach a 78% cross-engine citation rate [4]. E-E-A-T composite scores are 30.64% higher on cited versus non-cited pages across 304,000 URLs [16]. Content freshness has causal evidence across 7 LLMs [7], with four independent studies converging on the magnitude: 35.2% of cited pages are less than three months old [33], 85% of AI Overview citations come from 2023–2025 content [34], cited content is 25.7% fresher on average [20], and recently updated pages are 1.6x more likely to be cited [32].

**Why not higher.** Most gameable dimension. Over-weighting rewards surface-level optimization, and AI content retrieval collapse degrades system quality when creators over-optimize [13]. E-E-A-T heuristic detection operates at limited precision — LLMs can confuse linguistic form with genuine expertise, reliably detecting unreliable sources 85–97% of the time [5] but with weaker precision for positive quality signals.

**Why not lower.** The 4.2x odds ratio [4] and 30.64% E-E-A-T gap [16] are too large to subordinate below 20%. Content quality is the factor most directly within a practitioner's control, and the causal evidence for freshness [7] provides a stronger empirical foundation than most other signals.

#### Sub-Scores

| Sub-Score | Points | Evidence Basis |
|-----------|:------:|----------------|
| Freshness | 30 | Causal recency bias across 7 LLMs [7]; 4-study convergence [33][34][20][32] |
| Expertise & Authority | 23 | E-E-A-T composite +30.64% on cited pages [16]; author credentials and topical depth |
| Trustworthiness | 18 | 85–97% unreliable source detection by LLMs [5]; asymmetric gate — untrustworthiness caps the dimension |
| Structure | 12 | Section structure +22.91% [16]; heading hierarchy aids retrieval chunking |
| Non-Promotional Tone | 8 | Promotional content −26.19% on cited pages [16]; neutral tone +15–25% [3]; optimal subjectivity ~0.47 [21] |
| Content Richness | 9 | Tables 2.5x citation rate [38]; format extraction by AI systems [40]; list+table diversity bonus |

---

### 4.3 AI Citability (23%)

**What it measures.** How readily AI systems can extract, quote, or paraphrase specific passages from a page. Measures mechanical retrievability — whether a passage survives the embedding, chunking, and retrieval pipeline that LLMs use to select source material. Covers answer-first structure (front-loading key claims), definitional language patterns, heading-anchored passages, and factual density.

**Why 23%.** 44.2% of AI citations originate from the first 30% of content, with definitional language and Q&A headings each doubling citation probability [21]. Clarity and summarizability show +32.83% differential between cited and non-cited pages across 304,000 URLs [16]. HTML structure preservation improves retrieval quality [6], and structural information boosts retrieval hit rates by +22% [2]. The underlying mechanism is well-established: dense passage retrieval, ColBERT, and RAG architectures all demonstrate that well-structured passages retrieve more reliably due to embedding boundary alignment.

**Why not higher.** Causal benchmarking found only 3 of 54 content-level optimization scenarios showed statistically significant effects in production [1]. Statistical formatting actually decreased rankings in 19 of 24 configurations [1]. Lab gains of +30–40% [3] have not replicated at scale in live AI systems.

**Why not lower.** The most accessible optimization lever — practitioners can restructure headings and front-load answers within days, requiring no infrastructure changes or authority building. Allocating less than 20% would underweight the single most accessible improvement pathway available.

#### Sub-Scores

| Sub-Score | Points | Evidence Basis |
|-----------|:------:|----------------|
| Passage Citability | 65 | Core retrievability: 44.2% of citations from first 30% [21]; definitional patterns 2x citation [21]; clarity +32.83% [16] |
| Heading Structure | 15 | 78.4% of Q&A citations anchor to H2 headings [21]; section structure +22.91% [16] |
| Content Depth | 10 | Content length ρ=0.04 (near null [18]) — length alone barely matters, but thin content is penalized |
| Front-Loading | 10 | Answer-first positioning within the high-citation first 30% of content [21] |

---

### 4.4 AI Discoverability (13%)

**What it measures.** Whether AI crawlers can find, access, and parse a site's content — the technical accessibility layer that determines whether content enters the AI knowledge pipeline at all. Covers server-side rendering, crawler access policies, structured data quality, sitemaps, and the emerging llms.txt standard.

**Why 13%.** Access is fundamentally binary. A site is either crawlable or not, and once basic thresholds are met, additional improvements yield sharply diminishing returns. Six of eight major AI crawlers cannot execute JavaScript [22]. Schema shows near-null citation impact (OR=0.678, p=.296 [23]), and no major AI system parses JSON-LD for answer generation [24]. Crawler blocking is porous with 30–40% bypass rates [36].

**Why not higher.** Schema's citation impact is statistically insignificant [23]. Once content is server-side rendered and not actively blocked, discoverability ceases to differentiate. Allocating more than 15% would inflate scores for hygiene compliance rather than genuine citation readiness.

**Why not lower.** 37% of domains cited by AI are absent from traditional search entirely [8] — AI discoverability is its own independent pathway to visibility. Blocking all AI crawlers guarantees zero citations regardless of content quality, brand authority, or technical excellence.

#### Sub-Scores

| Sub-Score | Points | Evidence Basis |
|-----------|:------:|----------------|
| SSR / Rendering | 35 | Binary gate: 5/6 major AI search crawlers cannot render JavaScript [22] |
| Crawler Access | 35 | 30–40% bypass floor means blocking is leaky [36]; 12 AI crawlers checked |
| Schema Quality | 15 | Rich (61.7%) > none (59.8%) > generic (41.6%) — generic actively harms [23]; 0/5 AI systems parse JSON-LD [24] |
| Sitemap / Indexability | 15 | Retrieval rank 7.7x more important than content optimization [1] |
| llms.txt | +3 bonus | Emerging standard; too early for weighted scoring |

**Note on schema scoring.** Most frameworks score schema as present or absent. The AGSI uses a three-tier model — rich > none > generic — because generic schema actively harms citation odds (41.6% vs 59.8% for no schema at all [23]). Boilerplate markup is penalized, not rewarded.

---

### 4.5 Technical Foundation (10%)

**What it measures.** Baseline technical health that affects AI crawler behavior and content accessibility — crawlability, rendering, internal linking, web quality signals, and page performance. Operates as a floor constraint: severe failures are citation killers, but technical excellence beyond baseline provides negligible citation uplift.

**Why 10%.** Page speed shows only weak negative correlation (ρ=−0.12 to −0.18 across 107,352 URLs [41]). Security headers have zero documented relationship to AI citation. Internal linking has zero empirical studies connecting it to AI citation — two widely-cited claims — "2.7x citation improvement" (attributed to Yext) and "100–150% visibility uplift" (attributed to LLMVisibility) — could not be traced to any peer-reviewed or verifiable source during our evidence review.

**Why not higher.** Traditional SEO positioning is 7.7x more effective than content-level GEO optimization [1], but this reflects accumulated authority over time, not technical factors in isolation. Allocating 15%+ would reward basic web hygiene at the expense of dimensions that actually differentiate.

**Why not lower.** Severe failures — absent HTTPS, full client-side rendering, broken link structures — are absolute citation barriers. The 10% floor ensures they register meaningfully in the composite score.

#### Sub-Scores

| Sub-Score | Points | Evidence Basis |
|-----------|:------:|----------------|
| Crawlability | 35 | Retrieval 7.7x more effective than content optimization [1]; mechanical necessity |
| SSR / Rendering | 25 | Binary gate (allocation reduced to limit overlap with Discoverability) [22] |
| Internal Linking | 20 | Zero empirical citation studies; 2 fabricated claims identified; retained as hygiene |
| Web Quality | 10 | HTTPS enforcement only — security headers show 0 evidence findings |
| Page Speed Floor | 10 | ρ=−0.12 to −0.18 [41]; penalty for severe slowness, no uplift beyond baseline |

---

## 5. Industry-Adaptive Profiles

A single set of weights cannot serve all industries. The signals that drive AI citation for e-commerce diverge 60–66% from open-domain search [11], and 10 of 15 standard GEO heuristics fail in e-commerce contexts [12]. The AGSI addresses this through industry-adaptive weight profiles across 13 verticals.

### Weight Profiles

| Industry | Brand | Content | Citability | Discoverability | Technical |
|----------|:-----:|:-------:|:----------:|:---------------:|:---------:|
| **General** | 30% | 24% | 23% | 13% | 10% |
| Local | 30% | 20% | 12% | 15% | 23% |
| E-commerce | 15% | 22% | 18% | 15% | 30% |
| SaaS / B2B Tech | 25% | 24% | 25% | 13% | 13% |
| Publisher / Media | 25% | 28% | 25% | 12% | 10% |
| Healthcare (YMYL) | 30% | 30% | 15% | 13% | 12% |
| Finance (YMYL) | 28% | 32% | 15% | 13% | 12% |
| Legal (YMYL) | 25% | 30% | 18% | 12% | 15% |
| Professional Services | 30% | 30% | 15% | 10% | 15% |
| Education | 15% | 35% | 23% | 15% | 12% |
| Hospitality & Tourism | 32% | 25% | 18% | 13% | 12% |
| Real Estate | 35% | 25% | 20% | 5% | 15% |
| Wellness & Fitness | 28% | 28% | 20% | 12% | 12% |
| Food & Beverage | 30% | 22% | 15% | 13% | 20% |

### Why Profiles Differ — Five Examples

**E-commerce: Technical Foundation at 30%.** The only profile where Technical exceeds Brand. Page speed, Core Web Vitals, and rendering performance are critical for product discovery in AI-assisted shopping. Standard GEO optimization rules diverge 60–66% from what works in e-commerce [11], and 10 of 15 general heuristics fail in this context [12].

**Healthcare, Finance, Legal (YMYL): Content Quality at 30–32%.** Trust signals dominate citation selection. AI-generated responses to health, financial, and legal queries show elevated trust signal requirements — 83% of healthcare AI Overview responses include disclaimers [31]. Content Quality absorbs this trust burden, with freshness, expertise, and editorial credibility carrying the bulk of the weight.

**Hospitality: Brand & Entity at 32%.** Online travel agencies capture 55.3% of hotel AI citations, and branded/group hotels receive a +4.43 percentage point advantage over independent properties [37]. Brand recognition is the primary filter through which AI systems select accommodation recommendations.

**Real Estate: Brand at 35%, Discoverability at 5%.** AI Overviews trigger for only 3–5.8% of real estate queries [19][28], making discoverability nearly irrelevant — AI systems simply don't generate answers for most real estate searches. Brand recognition (Zillow, Redfin, local brokerages) drives the few citations that occur [39].

**Education: Content Quality at 35%.** Education experienced the most dramatic AI Overview growth, surging from 18% to 83% of search results [27]. This explosion puts a premium on content depth, freshness, and authoritative sourcing — institutions that publish comprehensive, current material dominate these citations.

### Evidence Caveat

Industry weight profiles are formula-informed but partially qualitative. The sector-specific evidence base is thinner than the general profile, drawing primarily from six key industry studies [11][12][27][28][31][37]. Profiles will be refined through the same calibration methodology as more industry-specific citation research becomes available.

The general profile has a documented derivation process (Section 2). Industry profiles apply directional adjustments based on sector-specific research but lack equivalent per-weight formula derivation. They should be interpreted as informed starting points, not formula outputs.

---

## 6. Key Design Decisions

Seven architectural choices warrant explanation:

1. **Passage Citability receives 65 of 100 points** in AI Citability because passage structure is strongly correlated with how AI systems select source material — not word count, not keyword density [21][16].

2. **Freshness receives 30 of 100 points** in Content Quality — the largest sub-score in the dimension — because it is the only content signal with causal evidence across multiple LLMs [7].

3. **SSR is scored in both Discoverability (35 pts) and Technical Foundation (25 pts).** Server-side rendering serves two distinct roles: an access gate (can crawlers see the content?) and a hygiene indicator (is the site built for broad compatibility?). The Technical allocation is reduced to limit double-counting.

4. **Schema quality uses a three-tier model** — rich > none > generic — because generic schema actively harms citation odds (41.6% vs 59.8% for no schema [23]). Most frameworks treat schema as present/absent; the AGSI penalizes boilerplate.

5. **Brand Scanner Authority at 55%** reflects the evidence that off-page signals dominate on-page signals by a wide margin in the citation research base [18].

6. **CSR-aware scoring measures what AI crawlers actually see.** When a page relies on client-side JavaScript rendering, AI crawlers receive a near-empty HTML shell. The AGSI scores based on server-side rendered content (`ssr_word_count`), not the full JavaScript-rendered page (`word_count`). This means a page with 2,000 words of JS-rendered content but only 50 words in the raw HTML scores as a 50-word page — reflecting the reality that five of six major AI search crawlers cannot execute JavaScript [22]. The gap between SSR and full content is surfaced as a visibility deficit in qualitative analysis. SSR is scored exclusively in AI Discoverability (35 pts); it was removed from Technical Foundation in v4.2 to eliminate double-counting.

7. **Derived statistics enforce numerical integrity.** All aggregate metrics (total word counts, crawler access ratios, per-page invisibility percentages) are pre-computed once during the scoring phase and carried forward as immutable reference values. Downstream analysis quotes these values rather than independently recalculating — eliminating rounding drift, denominator mismatches, and arithmetic errors across the audit pipeline.

---

## 7. Methodology Context — Where AGSI Sits

### The Composite Formula Is Standard

Weighted-sum composites are the most widely used approach for multi-dimensional indices. FICO credit scores, ESG ratings, Google Lighthouse performance scores, Moz Domain Authority, and the Global Innovation Index all use the same fundamental structure: score each dimension independently on a common scale, multiply by its weight, sum the results.

This architecture is well-understood, transparent, and interpretable. No methodological novelty is claimed here.

### The Evidence Calibration Is Novel

The formula for deriving dimension weights — `effect_magnitude × study_quality × log₁₀(sample_size)` — is a pragmatic hybrid, not a recognized meta-analysis methodology. Standard academic approaches for synthesizing research findings include:

- **Inverse-variance weighting** — weights studies by the precision of their estimates (1/SE²)
- **Random-effects meta-analysis** — accounts for between-study heterogeneity
- **Bayesian meta-analysis** — prior-informed pooling
- **Vote counting** — simple tally of directional findings

The AGSI approach is closer to **structured expert judgment with quantitative inputs** than a formal meta-analysis. We lack access to raw data, standard errors, and confidence intervals for most studies — particularly industry reports — which precludes standard meta-analytic techniques.

### The Defense

The sensitivity analysis across four methodologies (Section 2) is the strongest validation. It demonstrates that the weights are reasonably stable regardless of the specific formula used, which matters more than the formula itself.

The honest framing: the composite formula is industry-standard. The evidence calibration is more rigorous than pure intuition — which is what every other GEO framework uses — but less rigorous than formal meta-analysis. This paper is transparent about where editorial judgment was applied and why.

Critically, the evidence-derived weights are starting weights, not final weights. An empirical calibration pipeline is live: each full audit uploads results to a central database, where per-dimension Pearson correlations are computed against actual AI citation outcomes (AI Overview citations, AI Mode citations, and LLM mention totals). Once the dataset reaches statistical significance (100+ audits with citation outcome data), the empirical correlations will progressively replace the literature-derived weights. The evidence formula established the best starting point available; the calibration pipeline ensures the weights converge toward ground truth over time.

---

## 8. Limitations & Future Work

### Known Limitations

Transparency about what the AGSI does not capture is as important as what it does. Six limitations bound its current claims:

1. **Correlational, not causal.** Brand & Entity (30%) has the strongest correlations (ρ=0.664–0.737 [18]) but no causal isolation. Brand mentions may proxy for unmeasured confounds such as overall content ecosystem quality.

2. **Heuristic detection precision.** Entity detection, tone scoring, and front-loading detection use pattern-matching heuristics with limited precision (not ML models). Edge cases — superlatives in non-promotional contexts, answer-first structures that are technically promotional — will be misclassified.

3. **Schema evidence is thin.** The three-tier model derives from a single 730-citation study [23] with no independent replication. Effective weight is ~2% of total score (15% of 13%), limiting impact — but the finding that generic schema harms citation odds requires further validation.

4. **Freshness is a step function.** Day boundaries (30, 90, 180, 365) rather than a continuous decay curve. Content at 29 days and 31 days scores differently despite being nearly identical in age. Step boundaries are heuristic, not derived from observed citation decay patterns.

5. **Single-page vs. multi-page confidence gap.** Quick single-page assessments miss internal linking, cross-site content depth, and brand presence beyond on-page signals, producing meaningfully different scores than comprehensive multi-page audits.

6. **Strongest known signal excluded.** Topical authority (fan-out query breadth) shows ρ=0.77 in a 173,902-URL study — stronger than any signal currently in the framework (YouTube brand mentions ρ=0.737 is the highest included). Google has confirmed the "query fan-out" mechanism, where AI systems issue multiple related searches across subtopics. Integration requires third-party topical authority data not yet available in the scoring pipeline. The AGSI remains useful because its five dimensions are independently measurable and actionable, but practitioners should be aware that topical authority may account for more citation variance than any single included dimension.

### Future Work

Five research directions would strengthen the framework:

- **Empirical calibration** from accumulated audit data — the calibration infrastructure is live (audit results are uploaded to a central database with per-dimension Pearson correlation analysis against AI citation outcomes), but requires 100+ full audits before producing statistically meaningful weight adjustments. Until then, the formula-derived weights remain in effect.
- **Continuous freshness decay curves** derived from observed citation-age relationships, replacing the current step function.
- **NLP-based tone and expertise detection** to replace heuristic pattern-matching, improving precision on non-promotional tone and front-loading signals.
- **Topical authority integration** — fan-out query breadth shows ρ=0.77 correlation with citation, the strongest unmeasured signal identified in our evidence review, but requires third-party data integration.
- **Cross-platform citation tracking** to enable causal isolation studies — measuring whether specific interventions produce measurable citation changes across AI systems.

---

## 9. Bibliography

### Peer-Reviewed & Conference Papers

[1] Puerto et al., "C-SEO Bench: Does Conversational SEO Work?" NeurIPS 2025. [arXiv](https://arxiv.org/abs/2506.11097)

[2] Kim et al., "SAGEO Arena: Realistic Environment for Evaluating GEO," Feb 2026. [arXiv](https://arxiv.org/abs/2602.12187)

[3] Aggarwal et al., "GEO: Generative Engine Optimization," KDD 2024. [arXiv](https://arxiv.org/abs/2311.09735)

[4] Kumar & Palkhouski, "GEO-16 Framework: AI Answer Engine Citation Behavior," Sep 2025. [arXiv](https://arxiv.org/abs/2509.10762)

[5] Loru et al., "The Simulation of Judgment in LLMs," PNAS 2025. [arXiv](https://arxiv.org/abs/2502.04426) · [DOI](https://doi.org/10.1073/pnas.2518443122)

[6] Tan et al., "HtmlRAG: HTML Structure Preservation Improves RAG Quality," ACM WWW 2025. [arXiv](https://arxiv.org/abs/2411.02959)

[7] Fang et al., "Recency Bias in LLM Reranking," SIGIR 2025. [arXiv](https://arxiv.org/abs/2509.11353)

[8] Zhang et al., "Source Coverage and Citation Bias in LLM-Powered Search Engines," Dec 2025. [arXiv](https://arxiv.org/abs/2512.09483)

[9] Chen et al., "Navigating the Shift: Comparative Analysis of Web Search and AI Response Generation," Jan 2026. [arXiv](https://arxiv.org/abs/2601.16858)

[10] Chen et al., "Generative Engine Optimization: How to Dominate AI Search," Sep 2025. [arXiv](https://arxiv.org/abs/2509.08919)

[11] Wu et al., "What Generative Search Engines Like and How to Optimize Web Content Cooperatively," ICLR 2026. [arXiv](https://arxiv.org/abs/2510.11438)

[12] Bagga et al., "E-GEO: E-commerce GEO Testbed," Nov 2025. [arXiv](https://arxiv.org/abs/2511.20867)

[13] Yu et al., "Retrieval Collapses When AI Pollutes the Web," WWW 2026. [arXiv](https://arxiv.org/abs/2602.16136)

[14] Chen et al., "Caption Injection for Optimization in Generative Search Engine," Nov 2025. [arXiv](https://arxiv.org/abs/2511.04080)

[15] Askari et al., "HotelMatch-LLM: Images Improve Hotel Retrieval," Jun 2025. [arXiv](https://arxiv.org/abs/2506.07296)

### Large-Scale Industry Studies

[16] Semrush (Harsel et al.), "Content Optimization for AI Search," 304K URLs. [Semrush Blog](https://www.semrush.com/blog/content-optimization-ai-search-study/)

[17] SE Ranking, "ChatGPT Ranking Factors," 129K domains. [SE Ranking Blog](https://seranking.com/blog/ranking-factors-for-chatgpt)

[18] Ahrefs (Linehan & Guan), "Brand Visibility Correlations in AI Search," 75K brands. [Ahrefs Blog](https://ahrefs.com/blog/ai-brand-visibility-correlations/) · [Branded Mentions](https://ahrefs.com/blog/branded-web-mentions-visibility-ai-search/)

[19] Ahrefs, "AI Overview Trigger Rates by Industry," 146M SERPs. [Ahrefs Blog](https://ahrefs.com/blog/ai-overview-triggers/)

[20] Ahrefs, "AI Overview Citations: 90% from Pages Ranking #21+." [Ahrefs Blog](https://ahrefs.com/blog/ai-overview-citations-top-10/)

[21] Kevin Indig, "1.2M ChatGPT Response Analysis," Feb 2026. [Search Engine Land](https://searchengineland.com/chatgpt-citations-content-study-469483) · [Growth Memo](https://www.growth-memo.com/p/the-science-of-how-ai-pays-attention)

[22] Vercel/MERJ, "The Rise of the AI Crawler," 2025. [Vercel Blog](https://vercel.com/blog/the-rise-of-the-ai-crawler)

[23] Growth Marshal (Fischman), "Schema Markup Prediction Study," n=1,006 pages, 730 citations. [Growth Marshal](https://www.growthmarshal.io/field-notes/your-generic-schema-is-useless)

[24] searchVIU, "Schema Markup & AI in 2025: 0/5 Systems Parse JSON-LD." [searchVIU](https://www.searchviu.com/en/schema-markup-and-ai-in-2025-what-chatgpt-claude-perplexity-gemini-really-see/)

[25] SparkToro/Zyppy, "Brand Inconsistency in AI Recommendations." [SparkToro Blog](https://sparktoro.com/blog/new-research-ais-are-highly-inconsistent-when-recommending-brands-or-products-marketers-should-take-care-when-tracking-ai-visibility/)

[26] Surfer SEO, "AI Citation Report: 36M AI Overviews, 46M Citations." [Surfer SEO](https://surferseo.com/blog/ai-citation-report/)

[27] BrightEdge, "AI Search Insights: Education AIO 18%→83%." [BrightEdge](https://www.brightedge.com/news/press-releases/brightedge-data-shows-industry-specific-improvements-google-ai-overviews)

[28] Conductor, "AEO/GEO Benchmarks Report: 13,770 Domains." [Conductor](https://www.conductor.com/academy/aeo-geo-benchmarks-report/)

[29] Goodie, "B2B SaaS Most-Cited Domains in AI Search," 5.7M citations. [Goodie](https://higoodie.com/blog/most-cited-b2b-saas-domains-in-ai-search)

[30] Profound, "AI Platform Citation Patterns," 680M citations. [Profound](https://www.tryprofound.com/blog/ai-platform-citation-patterns)

[31] SE Ranking (YMYL), "AI Overviews & YMYL Topics," 1,200 keywords. [SE Ranking](https://seranking.com/blog/ai-overviews-and-ymyl-topics-research/)

[32] Digital Applied, "AI Search Citations: Recently Updated 1.6x More Cited." [Digital Applied](https://www.digitalapplied.com/blog/ai-search-citations-drop-38-percent-top-10-pages)

[33] AirOps, "Impact of Stale Content on AI Visibility." [AirOps](https://www.airops.com/report/the-impact-of-stale-content-on-ai-visibility)

[34] Seer Interactive, "AI Brand Visibility & Content Recency." [Seer Interactive](https://www.seerinteractive.com/insights/study-ai-brand-visibility-and-content-recency)

[35] Qwairy, "Provider Citation Behavior Q3 2025." [Qwairy](https://www.qwairy.co/blog/provider-citation-behavior-q3-2025)

[36] TollBit, "State of the Bots Q2 2025." [TollBit](https://tollbit.com/bots/25q2/)

[37] Cloudbeds, "Hotel AI Recommendations: OTAs 55.3% of Citations." [Cloudbeds](https://www.cloudbeds.com/hotel-ai-recommendations/)

[38] Onely, "Semantic SEO for AI Search: Tables 2.5x More Cited." [Onely](https://www.onely.com/blog/semantic-seo-for-ai-search/)

[39] Zillow, "ChatGPT Exclusive App Integration." [Zillow](https://zillow.mediaroom.com/2025-10-06-Zillow-debuts-the-only-real-estate-app-in-ChatGPT)

[40] Brave, "LLM Context API: Table/Format Extraction for AI Systems." [Brave Blog](https://brave.com/blog/most-powerful-search-api-for-ai/)

[41] Semrush (Technical SEO), "Technical SEO Impact on AI Search," 107K URLs. [Semrush Blog](https://www.semrush.com/blog/technical-seo-impact-on-ai-search-study/)
