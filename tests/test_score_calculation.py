"""Tests for GEO score calculation accuracy."""
import pytest
from aivarize_geo_score.score_calculator import (
    calculate_geo_score,
    calculate_confidence,
    GEOScorer,
    migrate_scores,
    migrate_5_to_7,
    auto_migrate,
    recalculate_historical,
    WEIGHTS,
    SCORING_VERSION,
    INDUSTRY_PROFILES,
    SUPPORTED_INDUSTRIES,
    KNOWN_LIMITATIONS,
    _V1_WEIGHTS,
    _V2_WEIGHTS,
    _resolve_industry,
    _INDUSTRY_ALIASES,
)


# v4.0 5-dimension weights
V4_WEIGHTS = {
    "brand_entity": 0.30,
    "content_quality": 0.24,
    "ai_citability": 0.23,
    "ai_discoverability": 0.13,
    "technical_foundation": 0.10,
}

# Legacy v3.2 6-dimension weights (for migration tests)
V3_WEIGHTS = {
    "ai_citability": 0.17,
    "ai_discoverability": 0.22,
    "brand_entity": 0.22,
    "content_quality": 0.20,
    "technical_foundation": 0.15,
    "content_richness": 0.04,
}

# v2.0 5-dimension weights (for legacy test references)
V2_WEIGHTS = {
    "ai_citability": 0.25,
    "brand_authority": 0.20,
    "content_eeat": 0.25,
    "technical": 0.20,
    "schema": 0.10,
}


class TestScoringVersion:
    """Test scoring version constants."""

    def test_scoring_version_is_3(self):
        assert SCORING_VERSION == "4.0"

    def test_result_includes_scoring_version(self):
        scores = {k: 50 for k in V3_WEIGHTS}
        result = calculate_geo_score(scores)
        assert result["scoring_version"] == "4.0"


class TestGeoScoreCalculation:
    """Test weighted composite score calculation with 5 dimensions."""

    def test_6dim_direct_input(self):
        """6-dimension (v3.2) input auto-migrates to 5-dim v4.0."""
        scores = {
            "ai_citability": 80,
            "ai_discoverability": 70,
            "brand_entity": 60,
            "content_quality": 75,
            "technical_foundation": 85,
            "content_richness": 65,
        }
        result = calculate_geo_score(scores)
        # After migration: content_quality = round(75*0.92 + 65*0.08) = round(69+5.2) = round(74.2) = 74
        # geo_score = round(80*0.23 + 70*0.13 + 60*0.30 + 74*0.24 + 85*0.10)
        # = round(18.4 + 9.1 + 18.0 + 17.76 + 8.5) = round(71.76) = 72
        assert result["geo_score"] == 72
        assert abs(result["raw_score"] - 71.76) < 0.01

    def test_6dim_input_auto_migrates(self):
        """6-dim input (v1) auto-migrates through v2 to v4.0."""
        scores = {
            "ai_citability": 12,
            "brand_authority": 5,
            "content_eeat": 8,
            "technical": 38,
            "schema": 5,
            "platform_optimization": 10,
        }
        result = calculate_geo_score(scores)
        assert "geo_score" in result
        assert 0 <= result["geo_score"] <= 100
        assert result["scoring_version"] == "4.0"

    def test_5dim_input_auto_migrates(self):
        """5-dim input (v2) auto-migrates to v4.0."""
        scores = {
            "ai_citability": 12,
            "brand_authority": 5,
            "content_eeat": 8,
            "technical": 38,
            "schema": 5,
        }
        result = calculate_geo_score(scores)
        assert "geo_score" in result
        assert 0 <= result["geo_score"] <= 100
        assert result["scoring_version"] == "4.0"

    def test_perfect_score(self):
        scores = {k: 100 for k in V3_WEIGHTS}
        result = calculate_geo_score(scores)
        assert result["geo_score"] == 100

    def test_zero_score(self):
        scores = {k: 0 for k in V3_WEIGHTS}
        result = calculate_geo_score(scores)
        assert result["geo_score"] == 0

    def test_weighted_contributions(self):
        """Each dimension's weighted contribution should be returned."""
        scores = {
            "ai_citability": 80,
            "ai_discoverability": 70,
            "brand_entity": 60,
            "content_quality": 75,
            "technical_foundation": 85,
            "content_richness": 65,
        }
        result = calculate_geo_score(scores)
        # After migration: content_quality = round(75*0.92 + 65*0.08) = 74
        # v4.0 weights: ai_citability=0.23, ai_discoverability=0.13, brand_entity=0.30, content_quality=0.24, technical_foundation=0.10
        assert abs(result["weighted"]["ai_citability"] - 18.4) < 0.01
        assert abs(result["weighted"]["ai_discoverability"] - 9.1) < 0.01
        assert abs(result["weighted"]["brand_entity"] - 18.0) < 0.01
        assert abs(result["weighted"]["content_quality"] - 17.76) < 0.01
        assert abs(result["weighted"]["technical_foundation"] - 8.5) < 0.01
        assert "content_richness" not in result["weighted"]

    def test_scores_clamped_to_0_100(self):
        """Scores outside 0-100 should be clamped."""
        scores = {
            "ai_citability": 150,
            "ai_discoverability": -10,
            "brand_entity": 70,
            "content_quality": 90,
            "technical_foundation": 50,
            "content_richness": -5,
        }
        result = calculate_geo_score(scores)
        assert 0 <= result["geo_score"] <= 100

    def test_missing_dimension_raises(self):
        """Missing a required dimension should raise ValueError."""
        scores = {"ai_citability": 80}  # Missing 6 dimensions
        with pytest.raises(ValueError, match="Unknown score format"):
            calculate_geo_score(scores)

    def test_score_label_good(self):
        scores = {k: 75 for k in V3_WEIGHTS}
        result = calculate_geo_score(scores)
        assert result["label"] == "Good"

    def test_score_label_excellent(self):
        scores = {k: 95 for k in V3_WEIGHTS}
        result = calculate_geo_score(scores)
        assert result["label"] == "Excellent"

    def test_score_label_critical(self):
        scores = {k: 15 for k in V3_WEIGHTS}
        result = calculate_geo_score(scores)
        assert result["label"] == "Critical"


class TestNewWeights:
    """Verify the new 5-dimension weight model (v4.0)."""

    def test_new_weights_sum_to_one(self):
        """New WEIGHTS must sum to exactly 1.0."""
        assert abs(sum(WEIGHTS.values()) - 1.0) < 1e-9

    def test_new_weights_have_six_dimensions(self):
        """New model has exactly 5 dimensions."""
        assert len(WEIGHTS) == 5

    def test_platform_optimization_not_in_weights(self):
        """platform_optimization is removed from the weight model."""
        assert "platform_optimization" not in WEIGHTS

    def test_v2_keys_not_in_v3_weights(self):
        """Old v2 dimension keys should not be in v3 WEIGHTS."""
        assert "brand_authority" not in WEIGHTS
        assert "content_eeat" not in WEIGHTS
        assert "technical" not in WEIGHTS
        assert "schema" not in WEIGHTS

    def test_seven_dim_scores_accepted(self):
        """calculate_geo_score accepts 6-dim v3.2 input (auto-migrated to 5-dim)."""
        scores = {k: 75 for k in V3_WEIGHTS}
        result = calculate_geo_score(scores)
        # After migration: content_quality = round(75*0.92 + 75*0.08) = 75
        # geo_score with all 75: round(75*0.23 + 75*0.13 + 75*0.30 + 75*0.24 + 75*0.10) = 75
        assert result["geo_score"] == 75

    def test_seven_dim_perfect_score(self):
        """Perfect 6-dim v3.2 scores produce 100 after migration."""
        scores = {k: 100 for k in V3_WEIGHTS}
        result = calculate_geo_score(scores)
        assert result["geo_score"] == 100

    def test_six_dim_weighted_contributions(self):
        """Verify weighted contributions with v4.0 weights after migration."""
        scores = {
            "ai_citability": 80,
            "ai_discoverability": 70,
            "brand_entity": 60,
            "content_quality": 75,
            "technical_foundation": 85,
            "content_richness": 65,
        }
        result = calculate_geo_score(scores)
        # After migration: content_quality = round(75*0.92 + 65*0.08) = 74
        # 80*0.23=18.4, 70*0.13=9.1, 60*0.30=18.0, 74*0.24=17.76, 85*0.10=8.5
        # total = 71.76 → 72
        assert result["geo_score"] == 72

    def test_v1_weights_preserved(self):
        """Legacy _V1_WEIGHTS (6-dim) still accessible."""
        assert len(_V1_WEIGHTS) == 6
        assert "platform_optimization" in _V1_WEIGHTS

    def test_v2_weights_preserved(self):
        """Legacy _V2_WEIGHTS (5-dim) still accessible."""
        assert len(_V2_WEIGHTS) == 5
        assert "ai_citability" in _V2_WEIGHTS


class TestMigrateScores:
    """Test v1→v2 migration (6-dim to 5-dim)."""

    def test_migrate_scores_function(self):
        """migrate_scores converts 6-dim to 5-dim scores dict."""
        old = {
            "ai_citability": 80,
            "brand_authority": 60,
            "content_eeat": 70,
            "technical": 90,
            "schema": 50,
            "platform_optimization": 40,
        }
        migrated = migrate_scores(old)
        assert "platform_optimization" not in migrated
        assert len(migrated) == 5
        assert migrated["ai_citability"] == 80
        assert migrated["brand_authority"] == 60
        assert migrated["schema"] == 50

    def test_migrate_scores_blends_platform(self):
        """migrate_scores merges platform into content_eeat and technical."""
        old = {
            "ai_citability": 50,
            "brand_authority": 50,
            "content_eeat": 60,
            "technical": 80,
            "schema": 50,
            "platform_optimization": 40,
        }
        migrated = migrate_scores(old)
        # content_eeat: (60*0.20 + 40*0.05) / 0.25 = (12+2)/0.25 = 56.0
        # technical: (80*0.15 + 40*0.05) / 0.20 = (12+2)/0.20 = 70.0
        assert abs(migrated["content_eeat"] - 56.0) < 0.1
        assert abs(migrated["technical"] - 70.0) < 0.1

    def test_migrate_scores_noop_on_5dim(self):
        """migrate_scores returns 5-dim input unchanged."""
        scores = {
            "ai_citability": 80,
            "brand_authority": 60,
            "content_eeat": 70,
            "technical": 90,
            "schema": 50,
        }
        migrated = migrate_scores(scores)
        assert migrated == scores


class TestMigrate5to7:
    """Test v2→v3 migration (5-dim to 7-dim)."""

    def test_basic_migration(self):
        """Basic 5→7 migration produces all 7 intermediate keys."""
        v2 = {
            "ai_citability": 80,
            "brand_authority": 60,
            "content_eeat": 70,
            "technical": 90,
            "schema": 50,
        }
        v3 = migrate_5_to_7(v2)
        expected_keys = {"ai_citability", "ai_discoverability", "brand_entity",
                         "content_quality", "technical_foundation", "structured_data",
                         "content_richness"}
        assert set(v3.keys()) == expected_keys

    def test_citability_split(self):
        """ai_citability maps to both ai_citability and ai_discoverability."""
        v2 = {
            "ai_citability": 80,
            "brand_authority": 60,
            "content_eeat": 70,
            "technical": 90,
            "schema": 50,
        }
        v3 = migrate_5_to_7(v2)
        # Both get the same value from the old ai_citability
        assert v3["ai_citability"] == 80
        assert v3["ai_discoverability"] == 80

    def test_brand_authority_maps_to_brand_entity(self):
        v2 = {
            "ai_citability": 50,
            "brand_authority": 60,
            "content_eeat": 70,
            "technical": 80,
            "schema": 40,
        }
        v3 = migrate_5_to_7(v2)
        assert v3["brand_entity"] == 60

    def test_content_eeat_maps_to_content_quality(self):
        v2 = {
            "ai_citability": 50,
            "brand_authority": 60,
            "content_eeat": 70,
            "technical": 80,
            "schema": 40,
        }
        v3 = migrate_5_to_7(v2)
        assert v3["content_quality"] == 70

    def test_technical_maps_to_technical_foundation(self):
        v2 = {
            "ai_citability": 50,
            "brand_authority": 60,
            "content_eeat": 70,
            "technical": 80,
            "schema": 40,
        }
        v3 = migrate_5_to_7(v2)
        assert v3["technical_foundation"] == 80

    def test_schema_maps_to_structured_data(self):
        v2 = {
            "ai_citability": 50,
            "brand_authority": 60,
            "content_eeat": 70,
            "technical": 80,
            "schema": 40,
        }
        v3 = migrate_5_to_7(v2)
        assert v3["structured_data"] == 40

    def test_content_richness_default(self):
        """content_richness gets neutral default of 50."""
        v2 = {
            "ai_citability": 50,
            "brand_authority": 60,
            "content_eeat": 70,
            "technical": 80,
            "schema": 40,
        }
        v3 = migrate_5_to_7(v2)
        assert v3["content_richness"] == 50

    def test_sub_scores_entity_absorption(self):
        """Entity sub-score is absorbed into brand_entity."""
        v2 = {
            "ai_citability": 50,
            "brand_authority": 60,
            "content_eeat": 70,
            "technical": 80,
            "schema": 40,
        }
        sub = {"entity_recognition": {"entity_score": 80}}
        v3 = migrate_5_to_7(v2, sub_scores=sub)
        # 75% of 60 + 25% of 80 = 45 + 20 = 65
        assert abs(v3["brand_entity"] - 65.0) < 0.1

    def test_sub_scores_gap_absorption(self):
        """Content gap sub-score is absorbed into content_quality."""
        v2 = {
            "ai_citability": 50,
            "brand_authority": 60,
            "content_eeat": 70,
            "technical": 80,
            "schema": 40,
        }
        sub = {"content_gaps": {"gap_score": 90}}
        v3 = migrate_5_to_7(v2, sub_scores=sub)
        # 80% of 70 + 20% of 90 = 56 + 18 = 74
        assert abs(v3["content_quality"] - 74.0) < 0.1

    def test_sub_scores_link_absorption(self):
        """Link analysis sub-score is absorbed into technical_foundation."""
        v2 = {
            "ai_citability": 50,
            "brand_authority": 60,
            "content_eeat": 70,
            "technical": 80,
            "schema": 40,
        }
        sub = {"link_analysis": {"link_score": 40}}
        v3 = migrate_5_to_7(v2, sub_scores=sub)
        # 80% of 80 + 20% of 40 = 64 + 8 = 72
        assert abs(v3["technical_foundation"] - 72.0) < 0.1

    def test_no_sub_scores_no_blending(self):
        """Without sub_scores, no absorption blending happens."""
        v2 = {
            "ai_citability": 50,
            "brand_authority": 60,
            "content_eeat": 70,
            "technical": 80,
            "schema": 40,
        }
        v3_no_sub = migrate_5_to_7(v2)
        v3_empty_sub = migrate_5_to_7(v2, sub_scores={})
        assert v3_no_sub == v3_empty_sub


class TestScoreExplanations:
    """Test score explanations / audit trail in calculate_geo_score()."""

    def test_explanations_key_present(self):
        """Result should include 'explanations' dict."""
        scores = {k: 50 for k in V3_WEIGHTS}
        result = calculate_geo_score(scores)
        assert "explanations" in result
        assert isinstance(result["explanations"], dict)

    def test_explanations_has_all_dimensions(self):
        """Explanations should have entries for all 5 v4.0 dimensions."""
        scores = {k: 50 for k in V3_WEIGHTS}
        result = calculate_geo_score(scores)
        for dim in V4_WEIGHTS:
            assert dim in result["explanations"], f"Missing explanation for {dim}"

    def test_explanation_structure(self):
        """Each explanation should have score, weight, contribution, signals."""
        scores = {k: 75 for k in V3_WEIGHTS}
        result = calculate_geo_score(scores)
        for dim, explanation in result["explanations"].items():
            assert "score" in explanation, f"{dim} missing 'score'"
            assert "weight" in explanation, f"{dim} missing 'weight'"
            assert "contribution" in explanation, f"{dim} missing 'contribution'"
            assert "signals" in explanation, f"{dim} missing 'signals'"

    def test_explanation_score_matches_input(self):
        """Explanation score should match the clamped input score after migration."""
        scores = {
            "ai_citability": 80,
            "ai_discoverability": 70,
            "brand_entity": 60,
            "content_quality": 75,
            "technical_foundation": 85,
            "content_richness": 65,
        }
        result = calculate_geo_score(scores)
        # After migration, content_richness is gone and content_quality is blended
        assert result["explanations"]["ai_citability"]["score"] == 80
        assert result["explanations"]["ai_discoverability"]["score"] == 70
        assert result["explanations"]["brand_entity"]["score"] == 60
        assert result["explanations"]["content_quality"]["score"] == 74  # round(75*0.92+65*0.08)
        assert result["explanations"]["technical_foundation"]["score"] == 85
        assert "content_richness" not in result["explanations"]

    def test_explanation_weight_matches_profile(self):
        """Explanation weight should match the active industry profile."""
        scores = {k: 50 for k in V3_WEIGHTS}
        result = calculate_geo_score(scores, industry="saas")
        saas_weights = INDUSTRY_PROFILES["saas"]["weights"]
        for dim, explanation in result["explanations"].items():
            assert abs(explanation["weight"] - saas_weights[dim]) < 1e-9

    def test_contributions_sum_to_geo_score(self):
        """Sum of all contributions should approximately equal geo_score."""
        scores = {
            "ai_citability": 80,
            "ai_discoverability": 70,
            "brand_entity": 60,
            "content_quality": 75,
            "technical_foundation": 85,
            "content_richness": 65,
        }
        result = calculate_geo_score(scores)
        total_contributions = sum(
            e["contribution"] for e in result["explanations"].values()
        )
        assert abs(total_contributions - result["raw_score"]) < 0.1

    def test_signals_is_empty_list(self):
        """Signals should be empty list at scoring level (populated by scorers later)."""
        scores = {k: 50 for k in V3_WEIGHTS}
        result = calculate_geo_score(scores)
        for dim, explanation in result["explanations"].items():
            assert explanation["signals"] == []

    def test_scoring_version_in_result(self):
        """scoring_version key should always be in result."""
        scores = {k: 50 for k in V3_WEIGHTS}
        result = calculate_geo_score(scores)
        assert result["scoring_version"] == "4.0"


class TestAutoMigrationChain:
    """Test the full auto-migration chain: v1→v2→v3."""

    def test_6dim_to_6dim_chain(self):
        """6-dim (v1) input chains through v2 to v4.0 (5-dim)."""
        v1 = {
            "ai_citability": 50,
            "brand_authority": 50,
            "content_eeat": 50,
            "technical": 50,
            "schema": 50,
            "platform_optimization": 50,
        }
        result = calculate_geo_score(v1)
        assert len(result["weighted"]) == 5
        assert result["scoring_version"] == "4.0"

    def test_5dim_to_6dim_auto(self):
        """5-dim (v2) input auto-migrates to v4.0 (5-dim)."""
        v2 = {
            "ai_citability": 80,
            "brand_authority": 60,
            "content_eeat": 70,
            "technical": 90,
            "schema": 50,
        }
        result = calculate_geo_score(v2)
        assert len(result["weighted"]) == 5
        # ai_citability and ai_discoverability both present
        assert result["weighted"]["ai_citability"] > 0
        assert result["weighted"]["ai_discoverability"] > 0

    def test_7dim_passthrough(self):
        """6-dim v3.2 input migrates to 5-dim v4.0; uniform scores stay uniform."""
        v3 = {k: 60 for k in V3_WEIGHTS}
        result = calculate_geo_score(v3)
        # All inputs uniform 60 → after CQ blend: round(60*0.92+60*0.08)=60 → geo=60
        assert result["geo_score"] == 60

    def test_chain_6_to_5_to_6_known_values(self):
        """Full chain with known values: v1(6)→v2(5)→v3(7)→v4.0(5)."""
        v1 = {
            "ai_citability": 12,
            "brand_authority": 5,
            "content_eeat": 8,
            "technical": 38,
            "schema": 5,
            "platform_optimization": 10,
        }
        # Full chain through v2→v3→v3.2→v4.0 migration
        result = calculate_geo_score(v1)
        assert result["scoring_version"] == "4.0"
        assert 0 <= result["geo_score"] <= 100


class TestScoreRecalculation:
    """Test recalculating historical entries to v3."""

    def test_recalculate_6dim_to_6dim(self):
        """Recalculate a 6-dim (v1) historical entry to v4.0 5-dim."""
        old_entry = {
            "timestamp": "2026-01-15T10:00:00Z",
            "geo_score": 58,
            "scores": {
                "ai_citability": 45,
                "brand_authority": 62,
                "content_eeat": 70,
                "technical": 55,
                "schema": 30,
                "platform_optimization": 48,
            },
            "label": "Fair",
        }
        result = recalculate_historical(old_entry)
        assert "geo_score" in result
        assert "scores" in result
        assert "platform_optimization" not in result["scores"]
        assert len(result["scores"]) == 5

    def test_recalculate_5dim_to_6dim(self):
        """Recalculate a 5-dim historical entry to v4.0 5-dim."""
        old_entry = {
            "timestamp": "2026-02-01T10:00:00Z",
            "geo_score": 50,
            "scores": {
                "ai_citability": 50,
                "brand_authority": 50,
                "content_eeat": 50,
                "technical": 50,
                "schema": 50,
            },
            "label": "Fair",
        }
        result = recalculate_historical(old_entry)
        assert len(result["scores"]) == 5
        assert set(result["scores"].keys()) == set(V4_WEIGHTS.keys())

    def test_recalculate_preserves_timestamp(self):
        """Recalculation preserves the original timestamp."""
        old_entry = {
            "timestamp": "2026-01-15T10:00:00Z",
            "geo_score": 58,
            "scores": {
                "ai_citability": 45,
                "brand_authority": 62,
                "content_eeat": 70,
                "technical": 55,
                "schema": 30,
                "platform_optimization": 48,
            },
            "label": "Fair",
        }
        result = recalculate_historical(old_entry)
        assert result["timestamp"] == "2026-01-15T10:00:00Z"

    def test_recalculate_7dim_migrates_to_6dim(self):
        """7-dim entry gets migrated to v4.0 5-dim and recomputed."""
        entry = {
            "timestamp": "2026-03-01T10:00:00Z",
            "geo_score": 75,
            "scores": {
                "ai_citability": 80,
                "ai_discoverability": 70,
                "brand_entity": 60,
                "content_quality": 75,
                "technical_foundation": 85,
                "structured_data": 50,
                "content_richness": 65,
            },
            "label": "Good",
        }
        result = recalculate_historical(entry)
        assert len(result["scores"]) == 5
        # v3(7)→v3.2(6): ai_discoverability = round(0.75*70 + 0.25*50) = 65
        # v3.2(6)→v4.0(5): content_quality = round(75*0.92 + 65*0.08) = round(69+5.2) = 74
        # geo = round(80*0.23 + 65*0.13 + 60*0.30 + 74*0.24 + 85*0.10)
        #     = round(18.4 + 8.45 + 18.0 + 17.76 + 8.5) = round(71.11) = 71
        assert result["geo_score"] == 71


class TestBackwardsCompat:
    """Test that old input still works via auto-migration."""

    def test_six_dim_input_auto_migrates(self):
        """calculate_geo_score auto-migrates 6-dim input to 7-dim."""
        scores = {
            "ai_citability": 80,
            "brand_authority": 60,
            "content_eeat": 70,
            "technical": 90,
            "schema": 50,
            "platform_optimization": 40,
        }
        result = calculate_geo_score(scores)
        assert "geo_score" in result
        assert 0 <= result["geo_score"] <= 100

    def test_five_dim_input_auto_migrates(self):
        """calculate_geo_score auto-migrates 5-dim input to v4.0 5-dim."""
        scores = {
            "ai_citability": 80,
            "brand_authority": 60,
            "content_eeat": 70,
            "technical": 90,
            "schema": 50,
        }
        result = calculate_geo_score(scores)
        assert "geo_score" in result
        assert 0 <= result["geo_score"] <= 100
        assert len(result["weighted"]) == 5

    def test_six_dim_weighted_has_6_dims(self):
        """Weighted contributions from v1 6-dim input should have 5 v4.0 dimensions."""
        scores = {
            "ai_citability": 80,
            "brand_authority": 60,
            "content_eeat": 70,
            "technical": 90,
            "schema": 50,
            "platform_optimization": 40,
        }
        result = calculate_geo_score(scores)
        assert "platform_optimization" not in result["weighted"]
        assert len(result["weighted"]) == 5

    def test_migrate_scores_still_works(self):
        """migrate_scores (v1→v2) still works correctly."""
        old = {
            "ai_citability": 80,
            "brand_authority": 60,
            "content_eeat": 70,
            "technical": 90,
            "schema": 50,
            "platform_optimization": 40,
        }
        migrated = migrate_scores(old)
        assert "platform_optimization" not in migrated
        assert len(migrated) == 5

    def test_missing_dimension_still_raises(self):
        """Incomplete dimension sets still raise ValueError."""
        scores = {"ai_citability": 80, "brand_entity": 60}
        with pytest.raises(ValueError, match="Unknown score format"):
            calculate_geo_score(scores)


class TestIndustryProfiles:
    """Test industry profile data structures."""

    def test_industry_profiles_exist(self):
        """INDUSTRY_PROFILES contains all 11 industries plus general."""
        assert "general" in INDUSTRY_PROFILES
        assert len(INDUSTRY_PROFILES) == 12

    def test_supported_industries_tuple(self):
        """SUPPORTED_INDUSTRIES is a tuple of the 11 industry keys."""
        assert isinstance(SUPPORTED_INDUSTRIES, tuple)
        assert len(SUPPORTED_INDUSTRIES) == 11
        assert "local" in SUPPORTED_INDUSTRIES
        assert "ecommerce" in SUPPORTED_INDUSTRIES
        assert "saas" in SUPPORTED_INDUSTRIES
        assert "publisher" in SUPPORTED_INDUSTRIES
        assert "healthcare" in SUPPORTED_INDUSTRIES
        assert "finance" in SUPPORTED_INDUSTRIES
        assert "legal" in SUPPORTED_INDUSTRIES
        assert "professional_services" in SUPPORTED_INDUSTRIES
        assert "education" in SUPPORTED_INDUSTRIES
        assert "hospitality" in SUPPORTED_INDUSTRIES
        assert "real_estate" in SUPPORTED_INDUSTRIES

    def test_all_profiles_have_weights(self):
        """Every profile has a 'weights' dict with all 5 v4.0 dimensions."""
        for industry, profile in INDUSTRY_PROFILES.items():
            assert "weights" in profile, f"{industry} missing 'weights'"
            for dim in WEIGHTS:
                assert dim in profile["weights"], f"{industry} missing weight for '{dim}'"

    @pytest.mark.parametrize("industry", list(INDUSTRY_PROFILES.keys()))
    def test_profile_weights_sum_to_one(self, industry):
        """Every profile's weights must sum to exactly 1.0."""
        profile = INDUSTRY_PROFILES[industry]
        total = sum(profile["weights"].values())
        assert abs(total - 1.0) < 1e-9, f"{industry} weights sum to {total}"

    def test_all_profiles_have_thresholds(self):
        """Every profile has a 'thresholds' list with 5 entries."""
        for industry, profile in INDUSTRY_PROFILES.items():
            assert "thresholds" in profile, f"{industry} missing 'thresholds'"
            assert len(profile["thresholds"]) == 5, f"{industry} has {len(profile['thresholds'])} thresholds"

    def test_thresholds_are_descending(self):
        """Thresholds must be in descending order (Excellent first)."""
        for industry, profile in INDUSTRY_PROFILES.items():
            scores = [t[0] for t in profile["thresholds"]]
            assert scores == sorted(scores, reverse=True), f"{industry} thresholds not descending"

    def test_general_profile_matches_current_weights(self):
        """The 'general' profile must match the existing WEIGHTS constant."""
        for dim, weight in WEIGHTS.items():
            assert abs(INDUSTRY_PROFILES["general"]["weights"][dim] - weight) < 1e-9

    def test_general_profile_matches_current_thresholds(self):
        """The 'general' thresholds must match the existing SCORE_LABELS."""
        from aivarize_geo_score.score_calculator import SCORE_LABELS
        assert INDUSTRY_PROFILES["general"]["thresholds"] == SCORE_LABELS

    def test_all_profiles_have_display_name(self):
        """Every profile has a human-readable display_name."""
        for industry, profile in INDUSTRY_PROFILES.items():
            assert "display_name" in profile, f"{industry} missing 'display_name'"
            assert isinstance(profile["display_name"], str)
            assert len(profile["display_name"]) > 0

    def test_all_threshold_labels_valid(self):
        """All threshold labels are one of the 5 valid labels."""
        valid = {"Excellent", "Good", "Fair", "Poor", "Critical"}
        for industry, profile in INDUSTRY_PROFILES.items():
            labels = {t[1] for t in profile["thresholds"]}
            assert labels == valid, f"{industry} has unexpected labels: {labels}"

    @pytest.mark.parametrize("industry", list(INDUSTRY_PROFILES.keys()))
    def test_profile_has_exactly_6_weights(self, industry):
        """Every profile must have exactly 5 dimension weights (v4.0)."""
        profile = INDUSTRY_PROFILES[industry]
        assert len(profile["weights"]) == 5, f"{industry} has {len(profile['weights'])} weights"

    def test_hospitality_profile_exists(self):
        """Hospitality profile has weights summing to 1.0 and thresholds."""
        profile = INDUSTRY_PROFILES["hospitality"]
        assert profile["display_name"] == "Hospitality & Tourism"
        weights = profile["weights"]
        assert len(weights) == 5
        assert abs(sum(weights.values()) - 1.0) < 0.001
        assert len(profile["thresholds"]) == 5

    def test_real_estate_profile_exists(self):
        """Real estate profile has weights summing to 1.0 and thresholds."""
        profile = INDUSTRY_PROFILES["real_estate"]
        assert profile["display_name"] == "Real Estate"
        weights = profile["weights"]
        assert len(weights) == 5
        assert abs(sum(weights.values()) - 1.0) < 0.001
        assert len(profile["thresholds"]) == 5

    def test_hospitality_scoring(self):
        """Hospitality profile produces valid GEO score."""
        scores = {
            "ai_citability": 50, "ai_discoverability": 60,
            "brand_entity": 70, "content_quality": 55,
            "technical_foundation": 45, "content_richness": 65,
        }
        result = calculate_geo_score(scores, industry="hospitality")
        assert result["industry"] == "hospitality"
        assert 0 <= result["geo_score"] <= 100

    def test_real_estate_scoring(self):
        """Real estate profile produces valid GEO score."""
        scores = {
            "ai_citability": 50, "ai_discoverability": 60,
            "brand_entity": 70, "content_quality": 55,
            "technical_foundation": 45, "content_richness": 65,
        }
        result = calculate_geo_score(scores, industry="real_estate")
        assert result["industry"] == "real_estate"
        assert 0 <= result["geo_score"] <= 100


class TestIndustryAwareScoring:
    """Test industry-aware score calculation."""

    def test_general_industry_matches_default(self):
        """industry='general' produces same result as industry=None."""
        scores = {k: 80 for k in V3_WEIGHTS}
        default = calculate_geo_score(scores)
        general = calculate_geo_score(scores, industry="general")
        assert default["geo_score"] == general["geo_score"]
        assert default["label"] == general["label"]

    def test_none_industry_uses_general(self):
        """industry=None uses general weights (backwards compat)."""
        scores = {k: 75 for k in V3_WEIGHTS}
        result = calculate_geo_score(scores, industry=None)
        assert result["geo_score"] == 75
        assert result["industry"] == "general"

    def test_local_industry_uses_local_weights(self):
        """Local business weights emphasize brand and technical."""
        scores = {
            "ai_citability": 40,
            "ai_discoverability": 40,
            "brand_entity": 90,
            "content_quality": 30,
            "technical_foundation": 50,
        }
        general = calculate_geo_score(scores, industry=None)
        local = calculate_geo_score(scores, industry="local")
        # Local emphasizes brand_entity(0.30) and technical_foundation(0.23)
        # vs general brand_entity(0.30) and technical_foundation(0.10)
        assert local["geo_score"] != general["geo_score"]

    def test_industry_affects_label(self):
        """Industry-specific thresholds change the label."""
        scores = {k: 60 for k in V3_WEIGHTS}
        general = calculate_geo_score(scores, industry=None)
        local = calculate_geo_score(scores, industry="local")
        # General 60 -> "Fair" (threshold: 60)
        assert general["label"] == "Fair"
        # Local 60 -> "Good" (threshold: 55)
        assert local["label"] == "Good"

    def test_result_includes_industry(self):
        """Result dict includes the industry used."""
        scores = {k: 50 for k in V3_WEIGHTS}
        result = calculate_geo_score(scores, industry="saas")
        assert result["industry"] == "saas"
        assert result["industry_display"] == "SaaS / B2B Tech"

    def test_invalid_industry_raises(self):
        """Unknown industry raises ValueError."""
        scores = {k: 50 for k in V3_WEIGHTS}
        with pytest.raises(ValueError, match="Unknown industry"):
            calculate_geo_score(scores, industry="cryptocurrency")

    def test_publisher_high_citability_rewarded(self):
        """Publisher weights reward high citability more than general."""
        scores = {
            "ai_citability": 95,
            "ai_discoverability": 50,
            "brand_entity": 40,
            "content_quality": 80,
            "technical_foundation": 30,
        }
        general = calculate_geo_score(scores, industry=None)
        publisher = calculate_geo_score(scores, industry="publisher")
        assert publisher["geo_score"] > general["geo_score"]

    def test_ecommerce_technical_rewarded(self):
        """E-commerce weights reward technical excellence more than general."""
        scores = {
            "ai_citability": 40,
            "ai_discoverability": 40,
            "brand_entity": 40,
            "content_quality": 40,
            "technical_foundation": 95,
        }
        general = calculate_geo_score(scores, industry=None)
        ecommerce = calculate_geo_score(scores, industry="ecommerce")
        assert ecommerce["geo_score"] > general["geo_score"]

    def test_six_dim_input_with_industry(self):
        """6-dim input auto-migrates then applies industry weights."""
        scores = {
            "ai_citability": 80,
            "brand_authority": 60,
            "content_eeat": 70,
            "technical": 90,
            "schema": 50,
            "platform_optimization": 40,
        }
        result = calculate_geo_score(scores, industry="saas")
        assert result["industry"] == "saas"
        assert 0 <= result["geo_score"] <= 100

    def test_weighted_contributions_use_industry_weights(self):
        """Weighted contributions reflect industry-specific weights."""
        scores = {k: 100 for k in V4_WEIGHTS}
        result = calculate_geo_score(scores, industry="local")
        assert result["geo_score"] == 100
        # local brand_entity=0.30, ai_discoverability=0.15
        assert abs(result["weighted"]["brand_entity"] - 30.0) < 0.01
        assert abs(result["weighted"]["ai_discoverability"] - 15.0) < 0.01


class TestAutoMigrate:
    """Test the public auto_migrate() entry point."""

    def test_6dim_v31_passthrough(self):
        """6-dim v3.2 input migrates to 5-dim v4.0 (content_richness absorbed)."""
        v32 = {k: 75 for k in V3_WEIGHTS}
        result = auto_migrate(v32)
        assert set(result.keys()) == set(V4_WEIGHTS.keys())
        # All values were 75; content_quality = round(75*0.92 + 75*0.08) = 75
        assert result["ai_citability"] == 75
        assert result["content_quality"] == 75

    def test_5dim_migrates_to_6(self):
        """5-dim v2 input migrates to 5-dim v4.0."""
        v2 = {
            "ai_citability": 80,
            "brand_authority": 60,
            "content_eeat": 70,
            "technical": 90,
            "schema": 50,
        }
        result = auto_migrate(v2)
        assert set(result.keys()) == set(V4_WEIGHTS.keys())
        assert result["ai_citability"] == 80
        assert result["brand_entity"] == 60
        assert result["technical_foundation"] == 90
        assert "structured_data" not in result
        assert "content_richness" not in result

    def test_v1_6dim_migrates_to_6(self):
        """6-dim v1 input chains through v2→v3→v3.2→v4.0."""
        v1 = {
            "ai_citability": 50,
            "brand_authority": 50,
            "content_eeat": 50,
            "technical": 50,
            "schema": 50,
            "platform_optimization": 50,
        }
        result = auto_migrate(v1)
        assert set(result.keys()) == set(V4_WEIGHTS.keys())
        assert len(result) == 5

    def test_5dim_with_sub_scores(self):
        """5-dim input with sub_scores passes them to migrate_5_to_7 during v4 migration."""
        v2 = {
            "ai_citability": 50,
            "brand_authority": 60,
            "content_eeat": 70,
            "technical": 80,
            "schema": 40,
        }
        sub = {"entity_recognition": {"entity_score": 80}}
        result = auto_migrate(v2, sub_scores=sub)
        # brand_entity: 75% of 60 + 25% of 80 = 65 (during v2→v3 step)
        assert abs(result["brand_entity"] - 65.0) < 0.1

    def test_unknown_format_raises(self):
        """Unknown score format raises ValueError."""
        weird = {"foo": 50, "bar": 60, "baz": 70}
        with pytest.raises(ValueError, match="Unknown score format"):
            auto_migrate(weird)

    def test_unknown_3_keys_raises(self):
        """3-key dict that doesn't match any version raises ValueError."""
        scores = {"ai_citability": 80, "brand_entity": 60, "technical_foundation": 50}
        with pytest.raises(ValueError, match="Unknown score format"):
            auto_migrate(scores)

    def test_returns_copy_not_original(self):
        """auto_migrate returns a copy, not the original dict."""
        v4 = {k: 75 for k in V4_WEIGHTS}
        result = auto_migrate(v4)
        assert result is not v4
        result["ai_citability"] = 999
        assert v4["ai_citability"] == 75

    def test_auto_migrate_v2_superset_raises(self):
        """A dict with v2 keys plus extra unknown keys should raise ValueError, not match v2."""
        weird_scores = {
            "ai_citability": 50, "brand_authority": 50, "content_eeat": 50,
            "technical": 50, "schema": 50,
            "unknown_future_dimension": 50,  # Extra key — superset of v2
        }
        with pytest.raises(ValueError, match="Unknown score format"):
            auto_migrate(weird_scores)


class TestConfidenceIndicators:
    """Test confidence level calculation for GEO scores."""

    def test_calculate_confidence_high(self):
        """High confidence when many pages analyzed and high data completeness."""
        data = {
            "pages_analyzed": 15,
            "data_completeness": 0.95,
            "brand_data_available": True,
        }
        result = calculate_confidence(data)
        assert result["level"] == "high"
        assert result["factors"] == data

    def test_calculate_confidence_medium(self):
        """Medium confidence with single page and decent completeness."""
        data = {
            "pages_analyzed": 1,
            "data_completeness": 0.85,
            "brand_data_available": False,
        }
        result = calculate_confidence(data)
        assert result["level"] == "medium"

    def test_calculate_confidence_low(self):
        """Low confidence with no pages or low completeness."""
        data = {
            "pages_analyzed": 0,
            "data_completeness": 0.5,
            "brand_data_available": False,
        }
        result = calculate_confidence(data)
        assert result["level"] == "low"

    def test_calculate_confidence_low_completeness(self):
        """Low confidence when completeness is below 0.7 even with pages."""
        data = {
            "pages_analyzed": 5,
            "data_completeness": 0.6,
            "brand_data_available": True,
        }
        result = calculate_confidence(data)
        assert result["level"] == "low"

    def test_confidence_in_geo_score_output(self):
        """calculate_geo_score includes confidence when confidence_data provided."""
        scores = {k: 50 for k in V3_WEIGHTS}
        confidence_data = {
            "pages_analyzed": 1,
            "data_completeness": 0.85,
            "brand_data_available": False,
        }
        result = calculate_geo_score(scores, confidence_data=confidence_data)
        assert "confidence" in result
        assert result["confidence"]["level"] == "medium"

    def test_confidence_absent_when_no_data(self):
        """calculate_geo_score omits confidence when no confidence_data."""
        scores = {k: 50 for k in V3_WEIGHTS}
        result = calculate_geo_score(scores)
        assert "confidence" not in result

    def test_confidence_high_threshold_boundary(self):
        """Boundary: exactly 10 pages and 0.9 completeness = high."""
        data = {
            "pages_analyzed": 10,
            "data_completeness": 0.9,
            "brand_data_available": True,
        }
        result = calculate_confidence(data)
        assert result["level"] == "high"

    def test_confidence_medium_threshold_boundary(self):
        """Boundary: exactly 1 page and 0.7 completeness = medium."""
        data = {
            "pages_analyzed": 1,
            "data_completeness": 0.7,
            "brand_data_available": False,
        }
        result = calculate_confidence(data)
        assert result["level"] == "medium"

    def test_confidence_factors_preserved(self):
        """Confidence factors dict is preserved in output."""
        data = {
            "pages_analyzed": 5,
            "data_completeness": 0.8,
            "brand_data_available": True,
        }
        result = calculate_confidence(data)
        assert result["factors"]["pages_analyzed"] == 5
        assert result["factors"]["data_completeness"] == 0.8
        assert result["factors"]["brand_data_available"] is True


class TestGEOScorer:
    """Test the pluggable GEOScorer dimension registry."""

    def test_default_scorer_matches_calculate_geo_score(self):
        """Default GEOScorer produces same result as calculate_geo_score."""
        scores = {
            "ai_citability": 80,
            "ai_discoverability": 70,
            "brand_entity": 60,
            "content_quality": 75,
            "technical_foundation": 85,
            "structured_data": 50,
            "content_richness": 65,
        }
        scorer = GEOScorer()
        result = scorer.score(scores)
        expected = calculate_geo_score(scores)
        assert result["geo_score"] == expected["geo_score"]
        assert result["label"] == expected["label"]

    def test_scorer_with_industry(self):
        """GEOScorer with industry uses industry weights."""
        scores = {k: 50 for k in V3_WEIGHTS}
        scorer = GEOScorer(industry="local")
        result = scorer.score(scores)
        expected = calculate_geo_score(scores, industry="local")
        assert result["geo_score"] == expected["geo_score"]
        assert result["industry"] == "local"

    def test_register_dimension(self):
        """register_dimension adds a new dimension with rebalancing."""
        scorer = GEOScorer()
        scorer.register_dimension("voice_readiness", weight=0.10)
        dims = scorer.dimensions
        assert "voice_readiness" in dims
        # Weights must still sum to 1.0
        assert abs(sum(dims.values()) - 1.0) < 1e-9

    def test_register_dimension_rebalance_proportional(self):
        """Rebalancing reduces existing weights proportionally."""
        scorer = GEOScorer()
        original_weights = dict(scorer.dimensions)
        scorer.register_dimension("new_dim", weight=0.10)
        # Each original weight should be reduced by the same factor
        factor = 0.90  # 1.0 - 0.10 = 0.90 left for original dims
        for dim, orig_weight in original_weights.items():
            expected = orig_weight * factor
            assert abs(scorer.dimensions[dim] - expected) < 1e-9

    def test_register_dimension_no_rebalance(self):
        """register_dimension with rebalance=False just adds (weights won't sum to 1.0)."""
        scorer = GEOScorer()
        scorer.register_dimension("extra", weight=0.10, rebalance=False)
        assert "extra" in scorer.dimensions
        assert scorer.dimensions["extra"] == 0.10
        # Weights sum to > 1.0
        assert sum(scorer.dimensions.values()) > 1.0

    def test_register_existing_dimension_raises(self):
        """Cannot register a dimension that already exists."""
        scorer = GEOScorer()
        with pytest.raises(ValueError, match="already registered"):
            scorer.register_dimension("ai_citability", weight=0.10)

    def test_replace_dimension(self):
        """replace_dimension overrides weight for an existing dimension."""
        scorer = GEOScorer()
        scorer.replace_dimension("ai_citability", weight=0.30)
        assert scorer.dimensions["ai_citability"] == 0.30

    def test_replace_nonexistent_raises(self):
        """Cannot replace a dimension that doesn't exist."""
        scorer = GEOScorer()
        with pytest.raises(ValueError, match="not registered"):
            scorer.replace_dimension("nonexistent", weight=0.10)

    def test_score_with_custom_dimension(self):
        """Scoring works with a registered custom dimension."""
        scorer = GEOScorer()
        scorer.register_dimension("voice_readiness", weight=0.10)
        scores = {k: 50 for k in V3_WEIGHTS}
        scores["voice_readiness"] = 80
        result = scorer.score(scores)
        assert 0 <= result["geo_score"] <= 100

    def test_dimensions_property_returns_copy(self):
        """dimensions property returns a copy, not the internal dict."""
        scorer = GEOScorer()
        dims = scorer.dimensions
        dims["fake"] = 0.5
        assert "fake" not in scorer.dimensions


class TestKnownLimitations:
    """Test KNOWN_LIMITATIONS list is present and valid."""

    def test_known_limitations_exists(self):
        """KNOWN_LIMITATIONS should be a non-empty list."""
        assert isinstance(KNOWN_LIMITATIONS, list)
        assert len(KNOWN_LIMITATIONS) == 9

    def test_all_limitations_are_strings(self):
        """Each limitation should be a non-empty string."""
        for limitation in KNOWN_LIMITATIONS:
            assert isinstance(limitation, str)
            assert len(limitation) > 0


class TestScoringV4:
    """Tests for v4.0 scoring (5 dimensions)."""

    def test_weights_sum_to_one(self):
        from aivarize_geo_score.score_calculator import WEIGHTS
        assert abs(sum(WEIGHTS.values()) - 1.0) < 1e-9

    def test_weights_have_six_dimensions(self):
        from aivarize_geo_score.score_calculator import WEIGHTS
        assert len(WEIGHTS) == 5
        assert "structured_data" not in WEIGHTS
        assert "content_richness" not in WEIGHTS

    def test_ai_discoverability_weight_is_13(self):
        from aivarize_geo_score.score_calculator import WEIGHTS
        assert WEIGHTS["ai_discoverability"] == 0.13

    def test_scoring_version_is_4_0(self):
        from aivarize_geo_score.score_calculator import SCORING_VERSION
        assert SCORING_VERSION == "4.0"

    def test_five_dimension_scores_produce_valid_result(self):
        from aivarize_geo_score.score_calculator import calculate_geo_score
        scores = {
            "ai_citability": 70,
            "ai_discoverability": 60,
            "brand_entity": 50,
            "content_quality": 80,
            "technical_foundation": 65,
        }
        result = calculate_geo_score(scores)
        assert 0 <= result["geo_score"] <= 100
        assert result["scoring_version"] == "4.0"
        assert len(result["explanations"]) == 5

    def test_all_industry_profiles_have_six_dimensions(self):
        from aivarize_geo_score.score_calculator import INDUSTRY_PROFILES
        for industry, profile in INDUSTRY_PROFILES.items():
            weights = profile["weights"]
            assert len(weights) == 5, f"{industry} has {len(weights)} dims"
            assert "structured_data" not in weights, f"{industry} still has structured_data"
            assert "content_richness" not in weights, f"{industry} still has content_richness"
            assert abs(sum(weights.values()) - 1.0) < 1e-9, f"{industry} weights don't sum to 1.0"

    def test_industry_scoring_works_with_five_dims(self):
        from aivarize_geo_score.score_calculator import calculate_geo_score, INDUSTRY_PROFILES
        scores = {
            "ai_citability": 70,
            "ai_discoverability": 60,
            "brand_entity": 50,
            "content_quality": 80,
            "technical_foundation": 65,
        }
        for industry in INDUSTRY_PROFILES:
            result = calculate_geo_score(scores, industry=industry)
            assert 0 <= result["geo_score"] <= 100, f"{industry} failed"

    def test_auto_migrate_v3_to_v4(self):
        """v3 (7-dim) scores migrate to v4.0 (5-dim) via v3.2 chain."""
        from aivarize_geo_score.score_calculator import auto_migrate
        v3_scores = {
            "ai_citability": 70,
            "ai_discoverability": 60,
            "brand_entity": 50,
            "content_quality": 80,
            "technical_foundation": 65,
            "structured_data": 40,
            "content_richness": 55,
        }
        result = auto_migrate(v3_scores)
        assert len(result) == 5
        assert "structured_data" not in result
        assert "content_richness" not in result
        # ai_discoverability = round(0.75*60 + 0.25*40) = 55 (v3→v3.2 step)
        assert result["ai_discoverability"] == 55
        # content_quality = round(80*0.92 + 55*0.08) = round(73.6+4.4) = 78 (v3.2→v4 step)
        assert result["content_quality"] == 78

    def test_auto_migrate_v32_to_v4(self):
        """v3.2 (6-dim) scores migrate to v4.0 (5-dim) by absorbing content_richness."""
        from aivarize_geo_score.score_calculator import auto_migrate
        v32_scores = {
            "ai_citability": 70,
            "ai_discoverability": 60,
            "brand_entity": 50,
            "content_quality": 80,
            "technical_foundation": 65,
            "content_richness": 55,
        }
        result = auto_migrate(v32_scores)
        assert len(result) == 5
        assert "content_richness" not in result
        # content_quality = round(80*0.92 + 55*0.08) = round(73.6+4.4) = 78
        assert result["content_quality"] == 78

    def test_auto_migrate_v1_to_v4(self):
        """v1 (6-dim old format) migrates all the way to v4.0."""
        from aivarize_geo_score.score_calculator import auto_migrate
        v1_scores = {
            "ai_citability": 70,
            "brand_authority": 50,
            "content_eeat": 80,
            "technical": 65,
            "schema": 40,
            "platform_optimization": 60,
        }
        result = auto_migrate(v1_scores)
        assert len(result) == 5
        assert "structured_data" not in result
        assert "schema" not in result
        assert "platform_optimization" not in result
        assert "content_richness" not in result

    def test_auto_migrate_v2_to_v4(self):
        """v2 (5-dim) migrates all the way to v4.0."""
        from aivarize_geo_score.score_calculator import auto_migrate
        v2_scores = {
            "ai_citability": 70,
            "brand_authority": 50,
            "content_eeat": 80,
            "technical": 65,
            "schema": 40,
        }
        result = auto_migrate(v2_scores)
        assert len(result) == 5
        assert "structured_data" not in result
        assert "content_richness" not in result


class TestIndustryAliases:
    """Test industry alias resolution (v3.2 finance/legal split)."""

    def test_resolve_finance_legal_alias(self):
        """_resolve_industry maps finance_legal to finance."""
        assert _resolve_industry("finance_legal") == "finance"

    def test_industry_aliases_dict(self):
        """_INDUSTRY_ALIASES contains finance_legal mapping."""
        assert "finance_legal" in _INDUSTRY_ALIASES
        assert _INDUSTRY_ALIASES["finance_legal"] == "finance"

    def test_calculate_geo_score_with_finance_legal(self):
        """calculate_geo_score accepts finance_legal for backwards compat."""
        scores = {k: 50 for k in V3_WEIGHTS}
        result = calculate_geo_score(scores, industry="finance_legal")
        assert result["industry"] == "finance"
        assert 0 <= result["geo_score"] <= 100

    def test_finance_and_legal_profiles_exist(self):
        """Both finance and legal profiles exist separately."""
        assert "finance" in INDUSTRY_PROFILES
        assert "legal" in INDUSTRY_PROFILES
