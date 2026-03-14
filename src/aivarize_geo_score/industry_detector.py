"""Industry detection from page data for GEO scoring.

Analyzes structured data, URL patterns, content signals, and TLD
to classify a website into one of 11 industry categories with a
confidence score (0.0-1.0).
"""
import re
from dataclasses import dataclass
from urllib.parse import urlparse

from .score_calculator import SUPPORTED_INDUSTRIES, INDUSTRY_PROFILES

__all__ = ["detect_industry", "IndustrySignal"]


@dataclass
class IndustrySignal:
    """A detected signal pointing to a specific industry."""
    industry: str
    source: str  # 'schema', 'url', 'content', 'tld'
    detail: str
    weight: float


# Schema.org type -> industry mapping
_SCHEMA_INDUSTRY_MAP = {
    # Local
    "LocalBusiness": ("local", 0.4),
    "Store": ("local", 0.35),
    "AutoRepair": ("local", 0.4),
    "Dentist": ("local", 0.35),
    "HealthClub": ("local", 0.3),
    "HairSalon": ("local", 0.35),
    # Hospitality (remapped from local)
    "Restaurant": ("hospitality", 0.4),
    "Bakery": ("hospitality", 0.35),
    "BarOrPub": ("hospitality", 0.4),
    "LodgingBusiness": ("hospitality", 0.4),
    # Hospitality (new)
    "Hotel": ("hospitality", 0.4),
    "Motel": ("hospitality", 0.35),
    "Resort": ("hospitality", 0.4),
    "BedAndBreakfast": ("hospitality", 0.35),
    "Hostel": ("hospitality", 0.3),
    "CafeOrCoffeeShop": ("hospitality", 0.3),
    "FoodEstablishment": ("hospitality", 0.35),
    "TouristAttraction": ("hospitality", 0.3),
    "TravelAgency": ("hospitality", 0.35),
    # Real Estate
    "RealEstateAgent": ("real_estate", 0.4),
    "RealEstateListing": ("real_estate", 0.4),
    "Residence": ("real_estate", 0.3),
    "Apartment": ("real_estate", 0.3),
    "House": ("real_estate", 0.3),
    # E-commerce
    "Product": ("ecommerce", 0.35),
    "Offer": ("ecommerce", 0.2),
    "ShoppingCenter": ("ecommerce", 0.3),
    # SaaS
    "SoftwareApplication": ("saas", 0.4),
    "WebApplication": ("saas", 0.35),
    "MobileApplication": ("saas", 0.3),
    # Publisher
    "NewsArticle": ("publisher", 0.35),
    "Article": ("publisher", 0.25),
    "BlogPosting": ("publisher", 0.25),
    "NewsMediaOrganization": ("publisher", 0.4),
    # Healthcare
    "MedicalOrganization": ("healthcare", 0.4),
    "Physician": ("healthcare", 0.4),
    "Hospital": ("healthcare", 0.4),
    "MedicalCondition": ("healthcare", 0.3),
    "MedicalEntity": ("healthcare", 0.3),
    "Pharmacy": ("healthcare", 0.35),
    "MedicalClinic": ("healthcare", 0.4),
    # Finance
    "FinancialProduct": ("finance", 0.4),
    "BankOrCreditUnion": ("finance", 0.4),
    "InsuranceAgency": ("finance", 0.4),
    "AccountingService": ("finance", 0.35),
    # Legal
    "LegalService": ("legal", 0.4),
    "Attorney": ("legal", 0.4),
    "Notary": ("legal", 0.35),
    # Professional Services
    "ProfessionalService": ("professional_services", 0.35),
    # Education
    "EducationalOrganization": ("education", 0.4),
    "Course": ("education", 0.3),
    "CollegeOrUniversity": ("education", 0.4),
    "School": ("education", 0.35),
}

# URL path patterns -> industry
_URL_PATTERNS = [
    (r"/products?/", "ecommerce", 0.2),
    (r"/shop/", "ecommerce", 0.2),
    (r"/cart", "ecommerce", 0.15),
    (r"/checkout", "ecommerce", 0.15),
    (r"/collections/", "ecommerce", 0.15),
    (r"/pricing", "saas", 0.2),
    (r"/docs?/", "saas", 0.15),
    (r"/api/", "saas", 0.15),
    (r"/changelog", "saas", 0.1),
    (r"/integrations", "saas", 0.1),
    (r"/blog/", "publisher", 0.1),
    (r"/news/", "publisher", 0.15),
    (r"/articles?/", "publisher", 0.15),
    (r"/practice-areas?/", "legal", 0.2),
    (r"/attorneys?/", "legal", 0.2),
    (r"/legal-services/", "legal", 0.2),
    (r"/rates/", "finance", 0.15),
    (r"/loans?/", "finance", 0.15),
    (r"/mortgages?/", "finance", 0.15),
    (r"/invest", "finance", 0.15),
    (r"/case-stud", "professional_services", 0.15),
    (r"/portfolio", "professional_services", 0.15),
    (r"/our-work", "professional_services", 0.1),
    (r"/appointments?", "healthcare", 0.1),
    (r"/patients?", "healthcare", 0.15),
    (r"/admissions", "education", 0.15),
    (r"/courses?/", "education", 0.15),
    (r"/programs?/", "education", 0.1),
    # Hospitality URL patterns (remapped from local)
    (r"/menu/|/our-menu/", "hospitality", 0.2),
    (r"/reservat", "hospitality", 0.15),
    # Hospitality (new)
    (r"/rooms?/|/suites?/", "hospitality", 0.2),
    (r"/book-?(now|stay|room)?", "hospitality", 0.15),
    (r"/dining/|/restaurant/", "hospitality", 0.15),
    (r"/amenities/|/spa/|/pool/", "hospitality", 0.1),
    # Real Estate URL patterns
    (r"/listings?/", "real_estate", 0.2),
    (r"/properties/|/property/", "real_estate", 0.2),
    (r"/for-sale/|/for-rent/", "real_estate", 0.2),
    (r"/open-house", "real_estate", 0.15),
    (r"/mls/|/idx/", "real_estate", 0.15),
    (r"/neighborhoods?/|/communities/", "real_estate", 0.1),
    # Local business URL patterns
    (r"/locations?/|/find-us/|/stores?/", "local", 0.2),
    (r"/contact/", "local", 0.1),
]

# Content text patterns -> industry (case-insensitive)
_CONTENT_PATTERNS = [
    (r"add to cart|buy now|free shipping|shop now", "ecommerce", 0.15),
    (r"free trial|sign up|get started|api key|developer", "saas", 0.15),
    (r"published|by\s+\w+\s+\w+,?\s+(reporter|editor|journalist)", "publisher", 0.1),
    (r"board.certified|hipaa|medical|physician|patient", "healthcare", 0.15),
    (r"attorney|lawyer|legal\s+advice|practice\s+areas|law\s+firm|paralegal|litigation|jurisdiction", "legal", 0.15),
    (r"annual\s+percentage|interest\s+rate|fdic|finra|fiduciary|mortgage|investment|banking|insurance\s+policy", "finance", 0.15),
    (r"our\s+portfolio|case\s+stud|our\s+clients|years\s+of\s+experience", "professional_services", 0.1),
    (r"visit\s+us\s+at|call\s+us|directions|open\s+(monday|daily|hours)", "local", 0.1),
    (r"curriculum|enrollment|semester|gpa|accredit", "education", 0.15),
    # Hospitality content patterns (remapped from local)
    (r"menu|restaurant|reserv|take.?away|delivery|dine.?in", "hospitality", 0.15),
    # Hospitality (new)
    (r"check.?in|check.?out|per\s+night|book\s+(your\s+)?stay|room\s+rate", "hospitality", 0.15),
    (r"concierge|valet|resort|all.?inclusive|bed\s+and\s+breakfast", "hospitality", 0.1),
    # Real Estate content patterns
    (r"mls\s*#|sq\s*ft|square\s+feet|bedrooms?|listing\s+price", "real_estate", 0.15),
    (r"open\s+house|showing|mortgage|home\s+value|real\s+estate\s+agent", "real_estate", 0.15),
    (r"for\s+sale|for\s+rent|property\s+management|hoa|escrow", "real_estate", 0.1),
    # Multilingual local business patterns (restaurant/food/location)
    (r"ravintola|lounas|ruokalista|tilaa|nouto", "local", 0.15),  # Finnish
    (r"restaurang|meny|boka\s+bord|ta\s+med", "local", 0.1),  # Swedish
    (r"speisekarte|reservierung|lieferung|abholung", "local", 0.1),  # German
    (r"carte|r[eé]servation|livraison|commander", "local", 0.1),  # French
    (r"menú|reserva|pedido|entrega", "local", 0.1),  # Spanish
]


def _extract_schema_types(structured_data: list) -> list:
    """Extract @type values from structured data entries."""
    types = []
    for entry in structured_data:
        if isinstance(entry, dict):
            t = entry.get("@type", "")
            if isinstance(t, list):
                types.extend(t)
            elif t:
                types.append(t)
    return types


def detect_industry(page_data: dict, override: str = None) -> dict:
    """Detect the industry of a website from page data.

    Args:
        page_data: Dict with optional keys: structured_data (list),
                   url (str), links (list of str), text (str).
        override: Manual industry override. Must be a valid industry key.

    Returns:
        Dict with: industry (str), confidence (float 0-1),
        display_name (str), signals (list of IndustrySignal).

    Raises:
        ValueError: If override is not a valid industry key.
    """
    if override:
        if override not in SUPPORTED_INDUSTRIES and override != "general":
            raise ValueError(
                f"Unknown industry: '{override}'. "
                f"Supported: {', '.join(SUPPORTED_INDUSTRIES)}"
            )
        profile = INDUSTRY_PROFILES[override]
        return {
            "industry": override,
            "confidence": 1.0,
            "display_name": profile["display_name"],
            "signals": [],
        }

    signals = []

    # 1. Schema.org type signals
    structured_data = page_data.get("structured_data", [])
    if structured_data:
        schema_types = _extract_schema_types(structured_data)
        for stype in schema_types:
            if stype in _SCHEMA_INDUSTRY_MAP:
                industry, weight = _SCHEMA_INDUSTRY_MAP[stype]
                signals.append(IndustrySignal(
                    industry=industry, source="schema",
                    detail=stype, weight=weight,
                ))

    # 2. URL pattern signals
    url = page_data.get("url", "")
    # Support both plain string lists and fetch_page's internal_links dicts
    raw_links = page_data.get("links", page_data.get("internal_links", []))
    links = []
    for link in raw_links:
        if isinstance(link, dict):
            links.append(link.get("url", ""))
        else:
            links.append(link)
    all_urls = [url] + links
    for pattern, industry, weight in _URL_PATTERNS:
        for u in all_urls:
            if re.search(pattern, u, re.IGNORECASE):
                signals.append(IndustrySignal(
                    industry=industry, source="url",
                    detail=pattern, weight=weight,
                ))
                break  # one match per pattern is enough

    # 3. TLD signals
    if url:
        parsed = urlparse(url)
        hostname = parsed.hostname or ""
        if hostname.endswith(".edu"):
            signals.append(IndustrySignal(
                industry="education", source="tld",
                detail=".edu", weight=0.35,
            ))
        elif hostname.endswith(".gov"):
            signals.append(IndustrySignal(
                industry="education", source="tld",
                detail=".gov", weight=0.3,
            ))
        elif hostname.endswith(".org"):
            signals.append(IndustrySignal(
                industry="education", source="tld",
                detail=".org", weight=0.1,
            ))

    # 4. Content pattern signals
    text = page_data.get("text", page_data.get("text_content", ""))
    if text:
        for pattern, industry, weight in _CONTENT_PATTERNS:
            if re.search(pattern, text, re.IGNORECASE):
                signals.append(IndustrySignal(
                    industry=industry, source="content",
                    detail=pattern[:40], weight=weight,
                ))

    # 5. Aggregate signals by industry
    industry_scores = {}
    for sig in signals:
        industry_scores[sig.industry] = industry_scores.get(sig.industry, 0) + sig.weight

    if not industry_scores:
        return {
            "industry": "general",
            "confidence": 0.0,
            "display_name": "General",
            "signals": signals,
        }

    # Pick highest-scoring industry
    best_industry = max(industry_scores, key=industry_scores.get)
    best_score = industry_scores[best_industry]

    # Confidence: normalize to 0-1 (cap at 1.0, strong signals around 0.6-0.8)
    confidence = min(1.0, best_score / 0.8)

    profile = INDUSTRY_PROFILES.get(best_industry, INDUSTRY_PROFILES["general"])

    return {
        "industry": best_industry,
        "confidence": round(confidence, 2),
        "display_name": profile["display_name"],
        "signals": signals,
    }
