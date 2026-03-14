"""Tests for industry_detector.py — automated business type detection."""
import pytest

from aivarize_geo_score.industry_detector import detect_industry, IndustrySignal


class TestDetectIndustry:
    """Test industry detection from page data."""

    def test_returns_dict_with_required_keys(self):
        result = detect_industry({})
        assert "industry" in result
        assert "confidence" in result
        assert "display_name" in result
        assert "signals" in result

    def test_empty_data_returns_general(self):
        result = detect_industry({})
        assert result["industry"] == "general"
        assert result["confidence"] < 0.5

    def test_local_business_schema_detection(self):
        page_data = {
            "structured_data": [{"@type": "LocalBusiness"}],
            "text": "Visit us at 123 Main Street. Call (555) 123-4567.",
        }
        result = detect_industry(page_data)
        assert result["industry"] == "local"
        assert result["confidence"] >= 0.6

    def test_ecommerce_product_schema(self):
        page_data = {
            "structured_data": [{"@type": "Product", "offers": {"price": "29.99"}}],
            "url": "https://example.com/products/widget",
            "text": "Add to cart. Free shipping on orders over $50.",
        }
        result = detect_industry(page_data)
        assert result["industry"] == "ecommerce"
        assert result["confidence"] >= 0.6

    def test_saas_pricing_and_docs(self):
        page_data = {
            "structured_data": [{"@type": "SoftwareApplication"}],
            "url": "https://example.com",
            "links": ["https://example.com/pricing", "https://example.com/docs"],
            "text": "Start your free trial today. API documentation available.",
        }
        result = detect_industry(page_data)
        assert result["industry"] == "saas"
        assert result["confidence"] >= 0.6

    def test_publisher_article_schema(self):
        page_data = {
            "structured_data": [{"@type": "NewsArticle", "author": {"name": "Jane"}}],
            "text": "Published March 5, 2026. By Jane Doe, Senior Reporter.",
            "links": [f"https://example.com/articles/{i}" for i in range(20)],
        }
        result = detect_industry(page_data)
        assert result["industry"] == "publisher"
        assert result["confidence"] >= 0.6

    def test_healthcare_medical_signals(self):
        page_data = {
            "structured_data": [{"@type": "MedicalOrganization"}],
            "text": "Board-certified physicians. HIPAA compliant. Schedule your appointment.",
        }
        result = detect_industry(page_data)
        assert result["industry"] == "healthcare"
        assert result["confidence"] >= 0.6

    def test_legal_signals(self):
        page_data = {
            "structured_data": [{"@type": "LegalService"}],
            "text": "Attorney at law. Free consultation. Practice areas include family law.",
        }
        result = detect_industry(page_data)
        assert result["industry"] == "legal"
        assert result["confidence"] >= 0.6

    def test_education_edu_tld(self):
        page_data = {
            "url": "https://www.example.edu",
            "structured_data": [{"@type": "EducationalOrganization"}],
            "text": "Admissions open for Fall 2026. Undergraduate programs.",
        }
        result = detect_industry(page_data)
        assert result["industry"] == "education"
        assert result["confidence"] >= 0.6

    def test_professional_services(self):
        page_data = {
            "structured_data": [{"@type": "ProfessionalService"}],
            "text": "Our portfolio includes 50+ clients. View our case studies.",
            "links": ["https://example.com/case-studies", "https://example.com/portfolio"],
        }
        result = detect_industry(page_data)
        assert result["industry"] == "professional_services"
        assert result["confidence"] >= 0.6

    def test_confidence_range_0_to_1(self):
        """Confidence is always between 0.0 and 1.0."""
        for data in [
            {},
            {"structured_data": [{"@type": "LocalBusiness"}]},
            {"url": "https://shop.example.com/products", "text": "Buy now"},
        ]:
            result = detect_industry(data)
            assert 0.0 <= result["confidence"] <= 1.0

    def test_signals_list_populated(self):
        page_data = {
            "structured_data": [{"@type": "SoftwareApplication"}],
            "url": "https://example.com",
            "links": ["https://example.com/pricing"],
            "text": "Start free trial.",
        }
        result = detect_industry(page_data)
        assert len(result["signals"]) > 0
        assert all(isinstance(s, IndustrySignal) for s in result["signals"])

    def test_manual_override(self):
        """When override is provided, it takes precedence regardless of signals."""
        page_data = {
            "structured_data": [{"@type": "LocalBusiness"}],
        }
        result = detect_industry(page_data, override="saas")
        assert result["industry"] == "saas"
        assert result["confidence"] == 1.0

    def test_invalid_override_raises(self):
        with pytest.raises(ValueError, match="Unknown industry"):
            detect_industry({}, override="cryptocurrency")


class TestIndustrySignal:
    """Test the IndustrySignal data class."""

    def test_signal_attributes(self):
        sig = IndustrySignal(industry="local", source="schema", detail="LocalBusiness", weight=0.4)
        assert sig.industry == "local"
        assert sig.source == "schema"
        assert sig.detail == "LocalBusiness"
        assert sig.weight == 0.4


class TestEdgeCases:
    """Test edge cases and ambiguous sites."""

    def test_competing_signals_picks_strongest(self):
        """When multiple industries have signals, pick the one with highest total weight."""
        page_data = {
            "structured_data": [
                {"@type": "SoftwareApplication"},
                {"@type": "Article"},
            ],
            "links": ["https://example.com/pricing", "https://example.com/blog"],
            "text": "SaaS platform with industry-leading blog.",
        }
        result = detect_industry(page_data)
        assert result["industry"] in ("saas", "publisher")

    def test_restaurant_subtype_detects_hospitality(self):
        page_data = {
            "structured_data": [{"@type": "Restaurant"}],
            "text": "Menu. Reservations. Open 11am-10pm.",
        }
        result = detect_industry(page_data)
        assert result["industry"] == "hospitality"

    def test_hospitality_hotel_schema(self):
        """Hotel schema detects hospitality."""
        page_data = {
            "structured_data": [{"@type": "Hotel"}],
            "text": "Book your stay. Check-in 3pm. Pool and spa available.",
        }
        result = detect_industry(page_data)
        assert result["industry"] == "hospitality"
        assert result["confidence"] >= 0.5

    def test_hospitality_restaurant_schema(self):
        """Restaurant schema detects hospitality (remapped from local)."""
        page_data = {
            "structured_data": [{"@type": "Restaurant"}],
            "url": "https://example.com",
            "links": ["https://example.com/menu", "https://example.com/reservations"],
            "text": "Fine dining restaurant. Reserve your table today.",
        }
        result = detect_industry(page_data)
        assert result["industry"] == "hospitality"
        assert result["confidence"] >= 0.5

    def test_hospitality_url_patterns(self):
        """Hospitality URL patterns like /rooms/ and /book/."""
        page_data = {
            "url": "https://hotel.example.com",
            "links": ["https://hotel.example.com/rooms", "https://hotel.example.com/book-now"],
            "text": "Luxury rooms starting at $199/night. Book your stay.",
        }
        result = detect_industry(page_data)
        assert result["industry"] == "hospitality"

    def test_real_estate_schema(self):
        """RealEstateAgent schema detects real_estate."""
        page_data = {
            "structured_data": [{"@type": "RealEstateAgent"}],
            "text": "Browse listings. Find your dream home.",
        }
        result = detect_industry(page_data)
        assert result["industry"] == "real_estate"
        assert result["confidence"] >= 0.5

    def test_real_estate_url_patterns(self):
        """Real estate URL patterns like /listings/ and /properties/."""
        page_data = {
            "url": "https://realty.example.com",
            "links": [
                "https://realty.example.com/listings",
                "https://realty.example.com/properties/123",
            ],
            "text": "3 bed, 2 bath. MLS# 12345. Schedule a showing.",
        }
        result = detect_industry(page_data)
        assert result["industry"] == "real_estate"

    def test_real_estate_content_signals(self):
        """Real estate content patterns (MLS, sq ft, listing)."""
        page_data = {
            "text": "2,400 sq ft. 4 bedrooms. Listed at $450,000. MLS# 98765. Open house Saturday.",
        }
        result = detect_industry(page_data)
        assert result["industry"] == "real_estate"

    def test_financial_product_schema(self):
        page_data = {
            "structured_data": [{"@type": "FinancialProduct"}],
            "text": "Annual percentage rate. Terms and conditions apply.",
        }
        result = detect_industry(page_data)
        assert result["industry"] == "finance"

    def test_gov_tld_detects_education(self):
        page_data = {
            "url": "https://www.example.gov",
            "text": "Government services.",
        }
        result = detect_industry(page_data)
        assert result["industry"] == "education"

    def test_fetch_page_text_content_key(self):
        """detect_industry should read text_content (fetch_page key), not just text."""
        page_data = {
            "text_content": "Visit us at 123 Main Street. Open Monday to Friday.",
        }
        result = detect_industry(page_data)
        assert result["industry"] == "local"
        assert any(s.source == "content" for s in result["signals"])

    def test_fetch_page_internal_links_key(self):
        """detect_industry should read internal_links (fetch_page dict format)."""
        page_data = {
            "internal_links": [
                {"url": "https://example.com/pricing", "text": "Pricing"},
                {"url": "https://example.com/docs/api", "text": "Docs"},
            ],
            "text_content": "Start your free trial. API documentation available.",
        }
        result = detect_industry(page_data)
        assert result["industry"] == "saas"
        assert any(s.source == "url" for s in result["signals"])

    def test_finnish_restaurant_detection(self):
        """Finnish restaurant content should trigger local industry detection."""
        page_data = {
            "url": "https://picnic.fi",
            "internal_links": [
                {"url": "https://picnic.fi/our-menu/", "text": "Menu"},
                {"url": "https://picnic.fi/contact/", "text": "Ota yhteyttä"},
            ],
            "text_content": "Ravintola Picnic. Tutustu ruokalistaan. Tilaa nouto.",
        }
        result = detect_industry(page_data)
        assert result["industry"] == "local"
        assert result["confidence"] >= 0.3
