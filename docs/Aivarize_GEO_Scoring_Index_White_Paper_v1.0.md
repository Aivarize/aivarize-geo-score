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
   - [Content Quality (25%)](#42-content-quality-25)
   - [AI Citability (23%)](#43-ai-citability-23)
   - [AI Discoverability (12%)](#44-ai-discoverability-12)
   - [Technical Foundation (10%)](#45-technical-foundation-10)
5. [Industry-Adaptive Profiles](#5-industry-adaptive-profiles)
6. [Key Design Decisions](#6-key-design-decisions)
7. [Methodology Context — Where AGSI Sits](#7-methodology-context--where-agsi-sits)
8. [Limitations & Future Work](#8-limitations--future-work)
9. [Bibliography](#9-bibliography)

---

## 1. What This Paper Covers

The Aivarize GEO Scoring Index (AGSI) is a composite 0–100 score that measures how visible a website is to AI-powered search engines — ChatGPT, Perplexity, Google AI Overviews, Gemini, Bing Copilot, Google AI Mode, Claude, Grok, Meta AI, and DeepSeek. As these systems replace traditional search results with generated answers, the industry lacks a standardized way to measure optimization for this new paradigm. Traditional SEO metrics — Domain Authority, PageRank, keyword density — were designed for ranked blue links, not for AI systems that cite passages, synthesize answers, and recommend brands.

The AGSI addresses this gap. Calibrated from a review of 230+ studies — with 43 sources cited across 7 peer-reviewed papers, 8 academic preprints, and 28 large-scale industry studies — it synthesizes the available evidence into a five-dimension weighted composite with industry-adaptive profiles across 13 verticals.

This paper describes the two core formulas, the five scoring dimensions and their sub-scores, the industry-adaptive weight profiles, and the reasoning behind each design choice — including where the methodology is standard, where it is novel, and where its limitations lie.

---

## 2. How We Built the Weights — The Evidence Calibration

### The Problem

We needed to decide how much each dimension should matter in the final score. Should brand recognition count more than content quality? Should technical health matter as much as AI citability? Rather than guessing, we derived the weights from research.

### The Evidence Base

We reviewed 230+ studies across six research areas. Of these, 43 are cited in this paper (see Bibliography), from which we extracted 68 discrete, scoreable findings. The evidence spans:

- **7 peer-reviewed papers** from top venues: NeurIPS [1], KDD [3], SIGIR [7], PNAS [5], ACM WWW [6][13], and ICLR [11] — including causal experiments, benchmarks, and perturbation studies.
- **8 academic preprints** covering citation behavior [8][9][10], e-commerce GEO [12], retrieval optimization [2][4][14], and multimodal retrieval [15].
- **28 large-scale industry studies** with sample sizes ranging from 1,000 prompts [10] to 304,000 URLs [16] and 500 million+ crawler fetches [22].

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
| Content Quality | 25% | 22% | 45% | 24% | 22–45% |
| AI Citability | 23% | 19% | 18% | 25% | 18–25% |
| AI Discoverability | 12% | 13% | 7% | 21% | 7–21% |
| Technical Foundation | 10% | 12% | 15% | 9% | 9–15% |

*The Quality ≥ 3 column was re-normalized after merging Content Richness (formerly a separate dimension at 2%) into Content Quality. Original six-dimension values are preserved in the evidence extraction document.*

The Full Method column reflects the v5.0 weights after recalibration. The sensitivity analysis columns (Quality ≥ 3, Causal Only, Count Only) remain from the original v4.0 analysis for historical context.

The sensitivity analysis reveals a central tension: **Brand & Entity** produces the strongest measured correlations but has zero causal evidence — its weight ranges from 9% (causal-only) to 34% (quality-filtered). **Content Quality** shows the inverse: the strongest causal evidence but weaker correlations, ranging from 22% to 45%.

### Calibration Approach

The AGSI did not adopt a purely data-driven weight assignment. The process started from practitioner-informed weights and adjusted them toward the evidence, applying editorial judgment in four cases:

1. **Brand & Entity** was capped at 30% (not the 34% suggested by quality-filtered evidence) because all brand evidence is correlational — no study has causally isolated brand-building as a citation driver.
2. **Content Quality** was set at 24% (above the 22% Full Method output) to absorb the Content Richness sub-dimension that was previously a separate dimension. The 2-percentage-point increase reflects this consolidation, not a re-evaluation of the evidence.
3. **AI Citability** was set at 23% (above the 18% causal-only figure) because passage structure is the most directly actionable lever for practitioners.
4. **Technical Foundation** was held at 10% (above the 9% count-only floor) because severe technical failures are citation killers that must register in the composite score.

#### v5.0 Recalibration (March 2026)

The v5.0 recalibration incorporated 18 new scoring signals (GAP-01 through GAP-25) while refining weights based on expanded signal coverage:

1. **Content Quality** increased from 24% to **25%** — the dimension absorbed 7 new sub-scores (information gain, semantic completeness, visible freshness, terminology precision, audience specificity, podcast availability, and enhanced freshness with industry-aware decay curves [7][33][34]). The additional signal density justified a 1-point increase.
2. **AI Discoverability** decreased from 13% to **12%** — the dimension lost llms.txt from scoring entirely (DEAD-01: zero measurable citation impact found across 6 research papers). As a proxy signal for site quality rather than a direct citation driver [23], its effective weight was reduced.
3. **Industry profiles** received ±1–3% adjustments informed by industry-specific evidence from e-commerce divergence studies [11][12] and YMYL citation patterns [31][32].
4. **Freshness** was upgraded from a fixed step function to **industry-aware decay curves** — SaaS/publisher content decays faster than healthcare/education, reflecting observed citation patterns [7][33][34][35].
5. **llms.txt** was removed from scoring (DEAD-01) — zero evidence of citation impact across all 6 research papers reviewed. Retained in audit data for qualitative analysis only.

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
| Content Quality | 65 | × 0.25 | = 16.25 |
| AI Citability | 70 | × 0.23 | = 16.1 |
| AI Discoverability | 80 | × 0.12 | = 9.6 |
| Technical Foundation | 75 | × 0.10 | = 7.5 |
| **Total** | | | **= 61.45 → 61** |

The sub-scores within each dimension work the same way — they're point budgets that add up to 100 for that dimension. The Content Quality score of 65 might break down as: Freshness 18/22 + Visible Freshness 4/5 + Expertise 12/15 + Info Gain 5/8 + Completeness 4/8 + Trust 8/12 + Structure 6/8 + Tone 4/6 + Richness 4/8 = 65.

### Final Weights

| Dimension | Weight | Confidence |
|-----------|:------:|:----------:|
| Brand & Entity | **30%** | High |
| Content Quality | **25%** | High |
| AI Citability | **23%** | Medium |
| AI Discoverability | **12%** | High |
| Technical Foundation | **10%** | Medium |

Confidence reflects evidence convergence: **High** means three or more independent studies agree on the directional finding. **Medium** means evidence supports the weight but with limited replication or conflicting methodologies.

---

## 4. The Five Dimensions

### 4.1 Brand & Entity (30%)

**What it measures.** Whether AI models recognize a brand as a known entity — not just whether a website mentions its own name, but whether the brand exists as a node in the information graph that large language models internalize during pre-training. Evaluates entity recognition across knowledge bases, brand mentions on third-party platforms, review presence, community discussion presence (Reddit and Quora), and cross-platform authority signals.

**Why 30%.** Brand-level signals show the strongest measured correlations with AI citation rates in the entire evidence base. Branded web mentions correlate at ρ=0.664 for AI Overviews, ρ=0.709 for AI Mode, and ρ=0.656 for ChatGPT [18]. YouTube brand mentions produced the single strongest signal at ρ=0.737 [18]. Entity-level signals are 2–4x stronger than page-level signals: branded mentions ρ=0.664 versus URL rating ρ=0.18 and content length ρ=0.04 [18]. The gap between top-quartile and second-quartile brands is a 10x difference in average AI mentions (169 vs. 14) [18].

**Why not higher.** All evidence is correlational. No causal study has isolated brand-building as a direct citation driver. Cross-platform citation instability is extreme: less than 1 in 100 chance that ChatGPT produces the same brand list in any two responses to the same query [25]. Capped at 30% rather than the 34% the quality-filtered evidence suggests.

**Why not lower.** The 10x gap between top and second-quartile brands [18] and the dominance of earned media in citation results (92.1% in US Consumer Electronics [10]) mean the evidence suggests brand recognition functions as a primary correlate of AI citation — not one factor among equals, though the causal mechanism remains unestablished. In B2B SaaS, brand-site domains are notably absent from AI citation results, with third-party sources dominating [29].

#### Sub-Scores (v5.0 Dynamic Blend)

v5.0 replaced the fixed 55/35/10 split with a dynamic blend that normalizes to 100% based on available signals. This enables graceful degradation — sites without YouTube or earned media data are scored on the signals that are available, without artificial zeros.

| Sub-Score | Base Weight | Evidence Basis |
|-----------|:----------:|----------------|
| Brand Scanner Authority | 30% | YouTube ρ=0.737, branded mentions ρ=0.664 [18]; review profiles 3x citation [17]. Measures presence across 8 platforms: YouTube, Reddit, Wikipedia, LinkedIn, G2, X/Twitter, Crunchbase, and GitHub — with industry-specific platform weighting (see Section 5). Review presence is scored across 8 review platforms — G2, Capterra, Trustpilot, Yelp, BBB, Clutch, TripAdvisor, and Sitejabber — with business-type routing (SaaS prioritizes G2/Capterra; local prioritizes Yelp/BBB; hospitality prioritizes Yelp/TripAdvisor) [17] |
| Entity Recognition | 20% | 16% of ranked entities lack snippet support [9]; Wikipedia 47.9% of ChatGPT top-10 [30] |
| YouTube Channel Presence | 12% | YouTube mentions ρ=0.737 — strongest single brand signal [18]; How-To videos +651% in AI Overviews [43]. Evaluates channel presence via subscriber reach, content volume, and audience engagement (total views) |
| Entity Density (per page) | 8% | 20.6% proper nouns in cited text vs 5-8% in normal English [21]; entity-level signals 2–4x stronger than page-level [18] |
| On-Page Brand Signals | 8% | Off-page signals dominate on-page by a wide margin [18]. Retained for sites without off-page data. Evaluates Organization schema presence, sameAs cross-platform entity links, and institutional identity markers |
| Earned Media Presence | 7% | Earned media "overwhelming" — 70–92% of AI results [10]; brands 6.5x more likely cited through third-party [10] |
| Site Reputation | 5% | Traditional SEO position 7.7x more effective than content optimization [1]; institutional credibility markers — about page, editorial standards, corrections policy, press/newsroom presence, and organizational provenance signals |
| Topical Authority | 5% | Fan-out query breadth — sites cited across related sub-queries demonstrate authority [4]; ≥12 pillar hits = 78% cross-engine citation [4]. Detects 6 query types across headings: definitional ("what"), procedural ("how"), explanatory ("why"), comparative ("vs/alternative"), transactional ("pricing/cost"), and evaluative ("best/top/review") |
| Backlink Quality | 5% | Referring domains = #1 SHAP feature importance in ChatGPT ranking model [17]; API-gated enrichment |

Weights are normalized to sum to 1.0 based on which signals have data. For example, a site without YouTube data or earned media will have the remaining signals re-weighted proportionally.

Within the Brand Scanner Authority sub-score, platform weights are also industry-adaptive. Each of 14 industry profiles (general, local, SaaS, e-commerce, publisher, healthcare, finance, legal, professional services, education, hospitality, real estate, wellness, food & beverage) assigns different importance to the 8 brand platforms — for example, SaaS profiles weight GitHub (16%) and G2 (15%) heavily, while hospitality profiles prioritize Yelp (20%) and TripAdvisor (15%). Review platforms (Yelp, BBB, Trustpilot, Clutch, TripAdvisor) receive non-zero weights only in industry profiles where they are relevant. All platform weights within a profile sum to 100 for percentage interpretation.

---

### 4.2 Content Quality (25%)

**What it measures.** Whether a page meets the quality, expertise, and freshness threshold that AI systems use when selecting citation sources. Assesses E-E-A-T signals (experience, expertise, authoritativeness, trustworthiness), content depth, non-promotional tone, author entity strength, content freshness with industry-aware decay, information originality, semantic completeness, and multimedia richness. Readability is assessed qualitatively by the analysis agent but not scored — it is too tightly correlated with existing sub-scores (structural readability within passage citability, content structure) to justify independent point allocation. Experience signals (first-hand accounts, case studies, process documentation) are evaluated qualitatively — no reliable heuristic exists for detecting genuine experience versus claimed experience, so these remain in the qualitative analysis layer.

**Why 25%.** Page quality yields an odds ratio of 4.2 for citation — pages scoring ≥0.70 on a 16-pillar quality framework reach a 78% cross-engine citation rate [4]. E-E-A-T composite scores are 30.64% higher on cited versus non-cited pages across 304,000 URLs [16]. Content freshness has causal evidence across 7 LLMs [7], with four independent studies converging on the magnitude: 35.2% of cited pages are less than three months old [33], 85% of AI Overview citations come from 2023–2025 content [34], cited content is 25.7% fresher on average [20], and recently updated pages are 1.6x more likely to be cited [32]. v5.0 increased from 24% to 25% to reflect the absorption of 7 new sub-scores (information gain, semantic completeness, visible freshness, terminology precision, audience specificity, podcast availability, and industry-aware freshness decay) that expanded the dimension's signal coverage.

**Why not higher.** Most gameable dimension. Over-weighting rewards surface-level optimization, and AI content retrieval collapse degrades system quality when creators over-optimize [13]. E-E-A-T heuristic detection operates at limited precision — LLMs can confuse linguistic form with genuine expertise, reliably detecting unreliable sources 85–97% of the time [5] but with weaker precision for positive quality signals.

**Why not lower.** The 4.2x odds ratio [4] and 30.64% E-E-A-T gap [16] are too large to subordinate below 20%. Content quality is the factor most directly within a practitioner's control, and the causal evidence for freshness [7] provides a stronger empirical foundation than most other signals.

#### Sub-Scores (v5.0 — 12 components, sum = 100)

| Sub-Score | Points | Evidence Basis |
|-----------|:------:|----------------|
| Freshness | 22 | Industry-aware decay curve across 7 LLMs [7]; 4-study convergence [33][34][20][32]. Seven industry-specific freshness profiles: SaaS and publisher content decays fastest (decay onset at 30 days), e-commerce and finance decay moderately, healthcare, legal, and education content remains citable longest. When no publish or modified date is detectable, falls back to recent year mention detection (e.g., "2025", "2026" in page text) as a weaker freshness proxy |
| Expertise & Authority | 15 | E-E-A-T composite +30.64% on cited pages [16]; author credentials — Person schema, byline presence, and author bio (capped — null as isolated signal [5]); topical depth via question-type coverage and content volume |
| Trustworthiness | 12 | 85–97% unreliable source detection by LLMs [5]. Evaluates meta description presence and length (tiered: optimal 120–160 chars, acceptable 50–200 chars, minimal otherwise), HTTPS protocol as trust baseline, outbound citation transparency, and institutional schema signals. Asymmetric ceiling gate: pages with very thin content and excessive outbound links are capped at 70% of sub-score — untrustworthiness is penalized more heavily than trustworthiness is rewarded |
| Information Gain | 8 | At 67% AI-generated retrieval pool, 80%+ retrieved results are AI-generated [13]; differentiation benefits lower-ranked sources +98–115% [3]; first-party data and proprietary research detection |
| Semantic Completeness | 8 | Pages with ≥12/16 pillar hits = 78% cross-engine citation rate (OR=4.2) [4]; Perplexity evaluates "completeness" as half of content assessment. Scores question-type diversity across H2 headings (what/how/why/when/who/where/which), heading breadth (distinct H2 count), and content depth threshold |
| Content Structure | 8 | Section structure +22.91% [16]; heading hierarchy aids retrieval chunking — single H1 scores higher than multiple H1s, reflecting both SEO convention and retrieval clarity; H2 depth and total heading count; Q&A format +25.45% [16] |
| Content Richness | 8 | Tables 2.5x citation rate [38]; format extraction by AI systems [40]; image presence and alt text quality; video embeds (YouTube, Vimeo, Wistia, HTML5 video); list+table diversity bonus with combo multiplier |
| Non-Promotional Tone | 6 | Promotional content −26.19% on cited pages [16]; neutral tone +15–25% [3]; optimal subjectivity ~0.47 [21] |
| Visible Freshness | 5 | Date injection reversed 25% of rankings [7]; AI systems add current year to 28.1% of sub-queries [35]; "Last updated" and "Reviewed by" detection |
| Terminology Precision | 3 | Technical language quality — precise terminology vs vague hedging; penalizes "kind of", "basically" patterns |
| Audience Specificity | 3 | Targeted content signals ("for developers", "for enterprise"); intent alignment = dominant success factor [12] |
| Podcast/Transcript | 2 | Audio content availability; podcast platform links and transcript detection |

---

### 4.3 AI Citability (23%)

**What it measures.** How readily AI systems can extract, quote, or paraphrase specific passages from a page. Measures mechanical retrievability — whether a passage survives the embedding, chunking, and retrieval pipeline that LLMs use to select source material. Covers answer-first structure (front-loading key claims), definitional language patterns, heading-anchored passages, and factual density.

**Why 23%.** 44.2% of AI citations originate from the first 30% of content, with definitional language and Q&A headings each doubling citation probability [21]. Clarity and summarizability show +32.83% differential between cited and non-cited pages across 304,000 URLs [16]. HTML structure preservation improves retrieval quality [6], and structural information boosts retrieval hit rates by +22% [2]. The underlying mechanism is well-established: dense passage retrieval, ColBERT, and RAG architectures all demonstrate that well-structured passages retrieve more reliably due to embedding boundary alignment.

**Why not higher.** Causal benchmarking found only 3 of 54 content-level optimization scenarios showed statistically significant effects in production [1]. Statistical formatting actually decreased rankings in 19 of 24 configurations [1]. Lab gains of +30–40% [3] have not replicated at scale in live AI systems. Caption injection techniques showed only marginal gains (+1.85%) in controlled experiments [14].

**Why not lower.** The most accessible optimization lever — practitioners can restructure headings and front-load answers within days, requiring no infrastructure changes or authority building. Allocating less than 20% would underweight the single most accessible improvement pathway available.

#### Sub-Scores (v5.0 — 7 components, sum = 100)

| Sub-Score | Points | Evidence Basis |
|-----------|:------:|----------------|
| Passage Citability | 30 | Core retrievability: 44.2% of citations from first 30% [21]; definitional patterns 2x citation [21]; clarity +32.83% [16]. Reduced from 65 to make room for new citation-quality signals. Decomposes into 5 weighted sub-scores: answer block quality (30%), self-containment (25%), structural readability (20%), statistical density (15%), and uniqueness signals (10%) |
| Front-Loading | 15 | Answer-first positioning via 4-signal detection [21]: answer keyword patterns in the first 30% of content, concise opening sentences, numeric/data density front-loading, and H2 answer capsule detection (concise answer blocks immediately following H2 headings). 78.4% of Q&A citations from H2 headings [21]. Increased from 10 to reflect the strength of the 44.2% front-loading finding |
| Source Citation Density | 15 | "Cite Sources" = ~40% improvement — single strongest optimization strategy [3]; evidence & citations pillar r=0.61, +37% [4]; citations per 1,000 words scored |
| Heading Structure | 10 | 78.4% of Q&A citations anchor to H2 headings [21]; section structure +22.91% [16] |
| Content Modularity | 10 | Self-contained passages with clear topic sentences retrieve best (DPR, EMNLP 2020); Q&A format +25.45% [16]; independently retrievable sections matching RAG chunk boundaries (75–600 words) |
| Conversational Patterns | 10 | Generative intent = 37.5% of ChatGPT queries [30]; definitional language ~2x citation [21]. Three pattern groups: Q&A pairs (question-then-answer sequences), definition sentences ("X is a Y", "X refers to"), and direct answer markers ("the answer is", "in short", "to summarize", "simply put") |
| Content Depth | 10 | Content length ρ=0.04 (near null [18]) — length alone barely matters, but a hard floor gate applies: pages with fewer than 50 words score 0 for the entire citability dimension, reflecting the reality that AI systems cannot extract citable passages from content that is too thin to contain them |

---

### 4.4 AI Discoverability (12%)

**What it measures.** Whether AI crawlers can find, access, and parse a site's content — the technical accessibility layer that determines whether content enters the AI knowledge pipeline at all. Covers server-side rendering, crawler access policies, structured data quality, sitemaps, and content behind interactions (tabs, accordions, lazy-loaded elements).

**Why 12%.** Access is fundamentally binary. A site is either crawlable or not, and once basic thresholds are met, additional improvements yield sharply diminishing returns. Six of eight major AI crawlers cannot execute JavaScript [22]. Schema shows near-null citation impact (OR=0.678, p=.296 [23]), and no major AI system parses JSON-LD for answer generation [24]. Crawler blocking is porous with 30–40% bypass rates [36]. v5.0 reduced from 13% to 12% after removing llms.txt from scoring — zero measurable citation impact found across 6 research papers.

**Why not higher.** Schema's citation impact is statistically insignificant [23]. Once content is server-side rendered and not actively blocked, discoverability ceases to differentiate. Allocating more than 15% would inflate scores for hygiene compliance rather than genuine citation readiness.

**Why not lower.** 37% of domains cited by AI are absent from traditional search entirely [8] — AI discoverability is its own independent pathway to visibility. Blocking all AI crawlers guarantees zero citations regardless of content quality, brand authority, or technical excellence.

#### Sub-Scores (v5.0 — 4 components, sum = 100)

| Sub-Score | Points | Evidence Basis |
|-----------|:------:|----------------|
| SSR / Rendering | 35 | Binary gate: 6/8 major AI crawlers cannot render JavaScript [22]. Includes hidden content penalty — tabs, accordions, and lazy-loaded content invisible to crawlers are detected and penalized. CDN/WAF blocking detection: when infrastructure-level blocking is detected (e.g., Cloudflare challenge pages), an additional penalty is applied |
| Crawler Access | 35 | 30–40% bypass floor means blocking is leaky [36]; 6 key crawlers checked (GPTBot, ClaudeBot, PerplexityBot, Google-Extended, OAI-SearchBot, ChatGPT-User) |
| Schema Quality | 15 | Rich (61.7%) > none (59.8%) > generic (41.6%) — generic actively harms [23]; 0/5 AI systems parse JSON-LD [24]. Rich types: Article, FAQPage, HowTo, Product, Recipe, VideoObject, LocalBusiness, Event, Review, and 6 others. Generic types (penalized): Organization, WebSite, WebPage, Corporation, Person — these score below "no schema" unless attribute-rich |
| Sitemap / Indexability | 15 | Retrieval rank 7.7x more important than content optimization [1]. Three signals: canonical URL presence, absence of noindex meta directive, and sitemap declaration in robots.txt |

**llms.txt removed from scoring (v5.0).** Previously a +3 bonus for the emerging standard. Removed in v5.0 (DEAD-01) — zero measurable citation impact found across all 6 research papers reviewed. The llms.txt file is still detected and reported in qualitative audit analysis, but it no longer affects the GEO Score.

**Note on schema scoring.** Most frameworks score schema as present or absent. The AGSI uses a three-tier model — rich > none > generic — because generic schema actively harms citation odds (41.6% vs 59.8% for no schema at all [23]). Boilerplate markup is penalized, not rewarded.

**Note on hidden content (v5.0).** Content behind interactive elements — tabs, accordions, modals, `display:none` sections, and lazy-loaded blocks — is invisible to the 6/8 AI crawlers that cannot execute JavaScript [22]. The SSR component now detects these patterns and applies a penalty, reflecting the reality that content not present in the initial HTML response is never indexed by most AI systems.

---

### 4.5 Technical Foundation (10%)

**What it measures.** Baseline technical health that affects AI crawler behavior and content accessibility — crawlability, rendering, internal linking, web quality signals, and page performance. Operates as a floor constraint: severe failures are citation killers, but technical excellence beyond baseline provides negligible citation uplift.

**Why 10%.** Page speed shows only weak negative correlation (ρ=−0.12 to −0.18 across 107,352 URLs [42]). A broader technical SEO analysis across 5M cited URLs confirmed that technical factors are necessary but not differentiating [41]. Security headers have zero documented relationship to AI citation. Internal linking has zero empirical studies connecting it to AI citation — two widely-cited claims — "2.7x citation improvement" (attributed to Yext) and "100–150% visibility uplift" (attributed to LLMVisibility) — could not be traced to any peer-reviewed or verifiable source during our evidence review.

**Why not higher.** Traditional SEO positioning is 7.7x more effective than content-level GEO optimization [1], but this reflects accumulated authority over time, not technical factors in isolation. Allocating 15%+ would reward basic web hygiene at the expense of dimensions that actually differentiate.

**Why not lower.** Severe failures — absent HTTPS, full client-side rendering, broken link structures — are absolute citation barriers. The 10% floor ensures they register meaningfully in the composite score.

#### Sub-Scores

| Sub-Score | Points | Evidence Basis |
|-----------|:------:|----------------|
| Crawlability | 50 | Retrieval 7.7x more effective than content optimization [1]; mechanical necessity. Evaluates canonical URL presence, absence of noindex meta directives, title tag presence, and error-free page response — the baseline indexability signals that determine whether content enters the retrieval pipeline at all |
| Internal Linking | 20 | Zero empirical citation studies; 2 fabricated claims identified; retained as hygiene. Evaluates internal link density (tiered: 10+ links = full marks, 5+ = partial, 1+ = minimal), semantic HTML heading structure (single H1, H2 hierarchy), and navigational coherence |
| Web Quality | 15 | HTTPS (+8), title tag (+3), and meta description (+4) — the three baseline web quality signals. Security headers show 0 evidence findings and are not scored |
| Page Speed Floor | 15 | ρ=−0.12 to −0.18 [42]; floor constraint only — no uplift beyond baseline. Scores three Core Web Vitals (LCP, INP, CLS) using Google's official thresholds: each vital contributes equally, with "good" ratings earning full points, "average" earning half, and "poor" earning zero. Prefers CrUX field data over Lighthouse lab data. When CWV data is unavailable, defaults to full marks unless CDN/WAF blocking is detected (full penalty) |

---

## 5. Industry-Adaptive Profiles

A single set of weights cannot serve all industries. The signals that drive AI citation for e-commerce diverge 60–66% from open-domain search [11], and 10 of 15 standard GEO heuristics fail in e-commerce contexts [12]. The AGSI addresses this through industry-adaptive weight profiles across 13 verticals. In addition to dimension-level weight profiles, the Brand & Entity dimension applies industry-specific platform weights within its Brand Scanner Authority sub-score (Section 4.1) — the platforms that matter for SaaS brand authority differ substantially from those that matter for hospitality or healthcare.

### Weight Profiles

| Industry | Brand | Content | Citability | Discoverability | Technical |
|----------|:-----:|:-------:|:----------:|:---------------:|:---------:|
| **General** | 30% | 25% | 23% | 12% | 10% |
| Local | 30% | 21% | 12% | 14% | 23% |
| E-commerce | 15% | 23% | 18% | 14% | 30% |
| SaaS / B2B Tech | 25% | 25% | 25% | 12% | 13% |
| Publisher / Media | 25% | 29% | 25% | 11% | 10% |
| Healthcare (YMYL) | 30% | 31% | 15% | 12% | 12% |
| Finance (YMYL) | 28% | 33% | 15% | 12% | 12% |
| Legal (YMYL) | 25% | 31% | 18% | 11% | 15% |
| Professional Services | 30% | 31% | 15% | 9% | 15% |
| Education | 15% | 36% | 23% | 14% | 12% |
| Hospitality & Tourism | 32% | 26% | 18% | 12% | 12% |
| Real Estate | 35% | 26% | 20% | 4% | 15% |
| Wellness & Fitness | 28% | 29% | 20% | 11% | 12% |
| Food & Beverage | 30% | 23% | 15% | 12% | 20% |

### Why Profiles Differ — Five Examples

**E-commerce: Technical Foundation at 30%.** The only profile where Technical exceeds Brand. Page speed, Core Web Vitals, and rendering performance are critical for product discovery in AI-assisted shopping. Standard GEO optimization rules diverge 60–66% from what works in e-commerce [11], and 10 of 15 general heuristics fail in this context [12]. Analysis of 36M AI Overviews confirms that citation patterns vary substantially by vertical [26].

**Healthcare, Finance, Legal (YMYL): Content Quality at 31–33%.** Trust signals dominate citation selection. AI-generated responses to health, financial, and legal queries show elevated trust signal requirements — 83% of healthcare AI Overview responses include disclaimers [31]. Content Quality absorbs this trust burden, with freshness, expertise, and editorial credibility carrying the bulk of the weight.

**Hospitality: Brand & Entity at 32%.** Online travel agencies capture 55.3% of hotel AI citations, and branded/group hotels receive a +4.43 percentage point advantage over independent properties [37]. Brand recognition is the primary filter through which AI systems select accommodation recommendations. Multimodal signals (images, visual content) further strengthen hotel retrieval in LLM-powered search [15].

**Real Estate: Brand at 35%, Discoverability at 4%.** AI Overviews trigger for only 3–5.8% of real estate queries [19][28], making discoverability nearly irrelevant — AI systems simply don't generate answers for most real estate searches. Brand recognition (Zillow, Redfin, local brokerages) drives the few citations that occur [39].

**Education: Content Quality at 36%.** Education experienced the most dramatic AI Overview growth, surging from 18% to 83% of search results [27]. This explosion puts a premium on content depth, freshness, and authoritative sourcing — institutions that publish comprehensive, current material dominate these citations.

### Evidence Caveat

Industry weight profiles are formula-informed but partially qualitative. The sector-specific evidence base is thinner than the general profile, drawing primarily from six key industry studies [11][12][27][28][31][37]. Profiles will be refined through the same calibration methodology as more industry-specific citation research becomes available.

The general profile has a documented derivation process (Section 2). Industry profiles apply directional adjustments based on sector-specific research but lack equivalent per-weight formula derivation. They should be interpreted as informed starting points, not formula outputs.

---

## 6. Key Design Decisions

Nine architectural choices warrant explanation:

1. **Passage Citability was reduced from 65 to 30 points** in AI Citability in v5.0 to make room for three new citation-quality signals: source citation density (15 pts [3][4]), content modularity (10 pts), and conversational query patterns (10 pts [30]). The total dimension still sums to 100, but the point budget is now distributed across 7 components rather than 4, reflecting the broader evidence base for what makes content citable.

2. **Freshness was reduced from 30 to 22 points** in Content Quality but upgraded with industry-aware decay curves. The reduction makes room for 6 new sub-scores. The industry-specific decay (SaaS content decays faster than healthcare) better reflects observed citation patterns [7][33][34].

3. **Schema quality uses a three-tier model** — rich > none > generic — because generic schema actively harms citation odds (41.6% vs 59.8% for no schema [23]). Most frameworks treat schema as present/absent; the AGSI penalizes boilerplate.

4. **Off-page brand signals dominate on-page signals** by a wide margin in the citation research base [18]. In the v5.0 dynamic blend, off-page signals (brand authority, entity recognition, YouTube, earned media, backlinks, reputation, topical authority) collectively hold ~84% of base weight versus ~16% for on-page signals (on-page brand signals and entity density).

5. **CSR-aware scoring measures what AI crawlers actually see.** When a page relies on client-side JavaScript rendering, AI crawlers receive a near-empty HTML shell. The AGSI scores based on server-side rendered content (`ssr_word_count`), not the full JavaScript-rendered page (`word_count`). This means a page with 2,000 words of JS-rendered content but only 50 words in the raw HTML scores as a 50-word page — reflecting the reality that six of eight major AI search crawlers cannot execute JavaScript [22]. The gap between SSR and full content is surfaced as a visibility deficit in qualitative analysis. SSR is scored exclusively in AI Discoverability (35 pts); it was removed from Technical Foundation in v4.2 to eliminate double-counting.

6. **Derived statistics enforce numerical integrity.** All aggregate metrics (total word counts, crawler access ratios, per-page invisibility percentages) are pre-computed once during the scoring phase and carried forward as immutable reference values. Downstream analysis quotes these values rather than independently recalculating — eliminating rounding drift, denominator mismatches, and arithmetic errors across the audit pipeline.

7. **llms.txt was removed from scoring in v5.0 (DEAD-01).** Across all 6 research papers reviewed, zero evidence was found linking llms.txt presence to AI citation outcomes. The file is still detected and reported qualitatively, but assigning it even a 3-point bonus was unsupported by evidence.

8. **Brand & Entity switched from fixed weights to dynamic blend in v5.0.** The v4.0 fixed 55/35/10 split (brand authority / entity / on-page) could not accommodate new signals (YouTube channel, earned media, entity density, topical authority, backlinks) without artificial compression. The dynamic blend assigns base weights to all available signals and normalizes to 100%, enabling graceful degradation when data sources are missing.

9. **Five dimensions were retained despite 18 new signals.** Rather than creating new dimensions for information gain, topical authority, or earned media, all new signals were absorbed into existing dimensions. This preserves the interpretability of a 5-dimension model while expanding signal coverage. Each dimension remains self-contained — practitioners can still identify which lever to pull.

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

Transparency about what the AGSI does not capture is as important as what it does. Eleven limitations bound its current claims:

1. **Regex-based entity detection.** Entity detection uses regex heuristics with limited precision, not ML-calibrated NER models. Limited support for non-Latin scripts (CJK, Arabic, Cyrillic).

2. **Correlational, not causal.** Platform weights are evidence-derived (230+ studies) but not calibrated against own citation outcomes. Brand & Entity (30%) has the strongest correlations (ρ=0.664–0.737 [18]) but no causal isolation — brand mentions may proxy for unmeasured confounds such as overall content ecosystem quality.

3. **Benchmark percentiles are synthetic.** Initial percentile distributions are estimated from expected score distributions, not measured from real audit data.

4. **Freshness decay uses industry-aware step function, not continuous curve.** v5.0 introduced industry-specific decay rates (SaaS decays faster than healthcare [7][33][34]) but still uses discrete day boundaries (30/60/90/120/180/365 depending on industry decay profile) rather than a continuous ML-predicted decay curve.

5. **Schema evidence is thin.** The three-tier model derives from a single 730-citation study [23] with no independent replication. Effective weight is ~1.8% of total score (15% of 12%), limiting impact — but the finding that generic schema harms citation odds requires further validation.

6. **Content front-loading uses pattern matching with H2 answer capsule detection, not full NLP.** v5.0 upgraded front-loading to detect answer capsules (40–60 words after H2 headings) and uses language-agnostic structural signals for non-English content, but still cannot perform full NLP-based position analysis.

7. **Non-promotional tone uses keyword matching, not ML-based sentiment/tone classification.** The 13 promotional trigger patterns cannot detect subtle promotional framing, advertorial content, or brand-favourable slant.

8. **Single-page quick audit has lower confidence than multi-page full audit.** Quick audits miss internal linking, cross-site content depth, brand presence, and topical authority signals.

9. **Information gain scoring detects originality signals but cannot compare against competitor content at scale.** First-party data and proprietary research markers are detected via regex, but true information gain requires comparing against the corpus of competing pages — which is computationally prohibitive at audit time.

10. **Semantic similarity to fan-out sub-queries requires embedding model.** The full GAP-14 implementation (computing semantic similarity between page passages and predicted fan-out sub-queries) was deferred because it requires an external embedding model not included in base scoring.

11. **Topical authority scoring uses heuristic proxies.** v5.0 integrated topical authority into Brand & Entity using heading diversity, content page ratio, and fan-out query type coverage as proxies — but the full signal (ρ=0.77 in a 173,902-URL study) requires third-party topical authority data not yet available in the scoring pipeline.

### Future Work

Four research directions would strengthen the framework:

- **Empirical calibration** from accumulated audit data — the calibration infrastructure is live (audit results are uploaded to a central database with per-dimension Pearson correlation analysis against AI citation outcomes), but requires 100+ full audits before producing statistically meaningful weight adjustments. Until then, the formula-derived weights remain in effect.
- **NLP-based tone and expertise detection** to replace heuristic pattern-matching, improving precision on non-promotional tone and front-loading signals.
- **Continuous freshness decay curves** derived from observed citation-age relationships, replacing the industry-aware step function with ML-predicted continuous decay.
- **Cross-platform citation tracking** to enable causal isolation studies — measuring whether specific interventions produce measurable citation changes across AI systems.

---

## 9. Bibliography

### Academic Papers (Peer-Reviewed & Preprints)

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

[41] Semrush (Technical SEO), "Technical SEO Impact on AI Search," 5M cited URLs. [Semrush Blog](https://www.semrush.com/blog/technical-seo-impact-on-ai-search-study/)

[42] Dan Taylor / SALT.agency, "Core Web Vitals and AI Search Visibility Analysis," N=107,352 URLs (ρ=−0.12 to −0.18 weak negative correlation). [Search Engine Land](https://searchengineland.com/core-web-vitals-ai-search-visibility-analysis-467456)

[43] NP Digital (Neil Patel), "YouTube Citations in AI Overviews: How-To Videos +651%," 2025. [NP Digital](https://neilpatel.com/marketing-stats/youtube-citations-ai-overviews/)
