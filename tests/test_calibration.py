"""Tests for empirical calibration pipeline scaffold."""
import json
import os
import pytest

from aivarize_geo_score.calibration import (
    calibrate_from_results,
    save_calibration,
    load_calibration,
    validate_audit_results,
    validate_ai_test_results,
)


class TestCalibrateFromResults:
    """Test calibrate_from_results scaffold."""

    def test_returns_dict(self):
        """calibrate_from_results returns a dict."""
        audit_results = [
            {"url": "https://example.com", "scores": {"ai_citability": 50}, "geo_score": 50},
        ]
        ai_test_results = [
            {"url": "https://example.com", "cited_by": ["chatgpt"]},
        ]
        result = calibrate_from_results(audit_results, ai_test_results)
        assert isinstance(result, dict)

    def test_returns_status_insufficient_data(self):
        """With fewer than 100 paired results, status is 'insufficient_data'."""
        audit_results = [
            {"url": f"https://example{i}.com", "scores": {}, "geo_score": i}
            for i in range(10)
        ]
        ai_test_results = [
            {"url": f"https://example{i}.com", "cited_by": ["chatgpt"]}
            for i in range(10)
        ]
        result = calibrate_from_results(audit_results, ai_test_results)
        assert result["status"] == "insufficient_data"
        assert result["paired_count"] == 10
        assert result["minimum_required"] == 100

    def test_empty_inputs(self):
        """Empty inputs return insufficient_data."""
        result = calibrate_from_results([], [])
        assert result["status"] == "insufficient_data"
        assert result["paired_count"] == 0

    def test_returns_correlations_placeholder(self):
        """Result includes correlations placeholder."""
        result = calibrate_from_results([], [])
        assert "correlations" in result
        assert result["correlations"] is None

    def test_returns_weight_adjustments_placeholder(self):
        """Result includes weight_adjustments placeholder."""
        result = calibrate_from_results([], [])
        assert "weight_adjustments" in result
        assert result["weight_adjustments"] is None

    def test_paired_count_matches_url_intersection(self):
        """paired_count counts URLs that appear in both lists."""
        audit_results = [
            {"url": "https://a.com", "scores": {}, "geo_score": 50},
            {"url": "https://b.com", "scores": {}, "geo_score": 60},
            {"url": "https://c.com", "scores": {}, "geo_score": 70},
        ]
        ai_test_results = [
            {"url": "https://a.com", "cited_by": ["chatgpt"]},
            {"url": "https://c.com", "cited_by": []},
            {"url": "https://d.com", "cited_by": ["perplexity"]},
        ]
        result = calibrate_from_results(audit_results, ai_test_results)
        assert result["paired_count"] == 2  # a.com and c.com


class TestValidateInputs:
    """Test input validation functions."""

    def test_validate_audit_results_valid(self):
        """Valid audit results pass validation."""
        data = [
            {"url": "https://example.com", "scores": {"ai_citability": 50}, "geo_score": 50},
        ]
        assert validate_audit_results(data) is True

    def test_validate_audit_results_missing_url(self):
        """Audit result missing 'url' fails validation."""
        data = [{"scores": {}, "geo_score": 50}]
        assert validate_audit_results(data) is False

    def test_validate_audit_results_missing_geo_score(self):
        """Audit result missing 'geo_score' fails validation."""
        data = [{"url": "https://example.com", "scores": {}}]
        assert validate_audit_results(data) is False

    def test_validate_ai_test_results_valid(self):
        """Valid AI test results pass validation."""
        data = [
            {"url": "https://example.com", "cited_by": ["chatgpt", "perplexity"]},
        ]
        assert validate_ai_test_results(data) is True

    def test_validate_ai_test_results_missing_url(self):
        """AI test result missing 'url' fails validation."""
        data = [{"cited_by": ["chatgpt"]}]
        assert validate_ai_test_results(data) is False

    def test_validate_ai_test_results_missing_cited_by(self):
        """AI test result missing 'cited_by' fails validation."""
        data = [{"url": "https://example.com"}]
        assert validate_ai_test_results(data) is False


class TestSaveLoadCalibration:
    """Test calibration data persistence."""

    def test_save_and_load_roundtrip(self, tmp_path):
        """save_calibration and load_calibration roundtrip correctly."""
        cal_data = {
            "status": "insufficient_data",
            "paired_count": 10,
            "minimum_required": 100,
            "correlations": None,
            "weight_adjustments": None,
        }
        filepath = tmp_path / "calibration.json"
        save_calibration(cal_data, str(filepath))
        loaded = load_calibration(str(filepath))
        assert loaded == cal_data

    def test_save_creates_file(self, tmp_path):
        """save_calibration creates the file."""
        filepath = tmp_path / "cal.json"
        save_calibration({"test": True}, str(filepath))
        assert filepath.exists()

    def test_load_nonexistent_returns_none(self, tmp_path):
        """load_calibration returns None for nonexistent file."""
        filepath = tmp_path / "nonexistent.json"
        result = load_calibration(str(filepath))
        assert result is None

    def test_save_load_preserves_nested_data(self, tmp_path):
        """Complex nested data survives roundtrip."""
        cal_data = {
            "status": "calibrated",
            "correlations": {
                "ai_citability": 0.72,
                "brand_entity": 0.64,
            },
            "weight_adjustments": {
                "ai_citability": {"current": 0.20, "suggested": 0.22},
            },
        }
        filepath = tmp_path / "cal.json"
        save_calibration(cal_data, str(filepath))
        loaded = load_calibration(str(filepath))
        assert loaded["correlations"]["ai_citability"] == 0.72
        assert loaded["weight_adjustments"]["ai_citability"]["suggested"] == 0.22


class TestCalibrationDataDir:
    """Test default calibration data directory."""

    def test_default_path_uses_data_dir(self):
        """Default calibration path is in scripts/data/."""
        from aivarize_geo_score.calibration import DEFAULT_CALIBRATION_PATH
        assert "data" in DEFAULT_CALIBRATION_PATH
        assert DEFAULT_CALIBRATION_PATH.endswith("calibration.json")
