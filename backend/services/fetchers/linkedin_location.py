"""Location helpers for US-focused JobSpy job fetching."""
import re

_US_MARKERS = re.compile(
    r"\b(united states|usa|u\.s\.|u\.s\.a\.)\b|,\s*[A-Z]{2}\b",
    re.IGNORECASE,
)

_NON_US_COUNTRIES = re.compile(
    r"\b("
    r"india|indian|canada|mexico|uk|united kingdom|england|scotland|wales|"
    r"germany|france|spain|italy|netherlands|australia|singapore|japan|china|"
    r"brazil|pakistan|bangladesh|sri lanka|nepal|philippines|indonesia|vietnam|"
    r"karnataka|telangana|maharashtra|tamil nadu|kerala|haryana|uttar pradesh|"
    r"hyderabad|bengaluru|bangalore|chennai|mumbai|delhi|pune|gurugram|gurgaon|"
    r"kochi|noida|kolkata|ahmedabad|jaipur|lucknow"
    r")\b",
    re.IGNORECASE,
)

_US_STATE_NAMES = re.compile(
    r"\b(alabama|alaska|arizona|arkansas|california|colorado|connecticut|"
    r"delaware|florida|georgia|hawaii|idaho|illinois|indiana|iowa|kansas|"
    r"kentucky|louisiana|maine|maryland|massachusetts|michigan|minnesota|"
    r"mississippi|missouri|montana|nebraska|nevada|new hampshire|new jersey|"
    r"new mexico|new york|north carolina|north dakota|ohio|oklahoma|oregon|"
    r"pennsylvania|rhode island|south carolina|south dakota|tennessee|texas|"
    r"utah|vermont|virginia|washington|west virginia|wisconsin|wyoming)\b",
    re.IGNORECASE,
)


def resolve_linkedin_location(search_location: str | None, default: str = "United States") -> str:
    loc = (search_location or "").strip()
    if not loc:
        return default
    if loc.lower() in ("remote", "any", "worldwide"):
        return default
    return loc


def resolve_scrape_location(search_location: str | None, default: str = "United States") -> str:
    return resolve_linkedin_location(search_location, default=default)


def scrape_location_for_site(location: str, jobspy_site: str) -> str:
    """Indeed needs a city — broad 'United States' often fails to parse."""
    broad = location.lower() in ("united states", "usa", "us", "u.s.", "u.s.a.")
    if jobspy_site == "indeed" and broad:
        return "New York, NY"
    return location


def is_us_job_location(location: str | None) -> bool:
    if not location or not location.strip():
        return True

    text = location.strip()
    if _NON_US_COUNTRIES.search(text):
        return False
    if _US_MARKERS.search(text) or _US_STATE_NAMES.search(text):
        return True

    us_city_hints = (
        "san francisco", "new york", "seattle", "austin", "boston", "chicago",
        "denver", "atlanta", "dallas", "houston", "miami", "portland",
        "los angeles", "silicon valley", "bay area", "washington dc",
        "arlington", "remote - us", "remote us", "us remote",
    )
    lower = text.lower()
    if any(h in lower for h in us_city_hints):
        return True

    return False
