"""Title keyword filtering, US-location filtering, and role categorization.

All three are driven by title/location strings coming back from the various
sources -- see config/keywords.yml for the tunable keyword lists.
"""
import re

import yaml

US_STATE_ABBR = {
    "AL", "AK", "AZ", "AR", "CA", "CO", "CT", "DE", "FL", "GA", "HI", "ID",
    "IL", "IN", "IA", "KS", "KY", "LA", "ME", "MD", "MA", "MI", "MN", "MS",
    "MO", "MT", "NE", "NV", "NH", "NJ", "NM", "NY", "NC", "ND", "OH", "OK",
    "OR", "PA", "RI", "SC", "SD", "TN", "TX", "UT", "VT", "VA", "WA", "WV",
    "WI", "WY", "DC", "PR", "VI", "GU",
}

US_STATE_NAMES = {
    "alabama", "alaska", "arizona", "arkansas", "california", "colorado",
    "connecticut", "delaware", "florida", "georgia", "hawaii", "idaho",
    "illinois", "indiana", "iowa", "kansas", "kentucky", "louisiana",
    "maine", "maryland", "massachusetts", "michigan", "minnesota",
    "mississippi", "missouri", "montana", "nebraska", "nevada",
    "new hampshire", "new jersey", "new mexico", "new york",
    "north carolina", "north dakota", "ohio", "oklahoma", "oregon",
    "pennsylvania", "rhode island", "south carolina", "south dakota",
    "tennessee", "texas", "utah", "vermont", "virginia", "washington",
    "west virginia", "wisconsin", "wyoming", "district of columbia",
    "puerto rico",
}

# Bare terms with no country qualifier -- ambiguous, default to including
# them since most of our sources are US-headquartered companies.
AMBIGUOUS_REMOTE_TERMS = {"remote", "anywhere", "hybrid", "flexible"}


def _is_us_fragment(fragment: str) -> bool:
    f = fragment.strip()
    if not f:
        return False
    fl = f.lower()

    if fl.startswith("remote in "):
        country = fl[len("remote in "):].strip()
        return country in {"us", "usa", "united states"}

    if fl in AMBIGUOUS_REMOTE_TERMS:
        return True

    if "united states" in fl:
        return True

    last = f.split(",")[-1].strip()
    if last.upper() in US_STATE_ABBR:
        return True
    if last.lower() in US_STATE_NAMES:
        return True
    if last.lower() in {"usa", "us", "nyc"}:
        return True

    return False


def is_us_location(location) -> bool:
    """location can be a single string or a list of location strings."""
    if not location:
        return False
    if isinstance(location, str):
        fragments = re.split(r"[•|;]", location)
    else:
        fragments = location
    return any(_is_us_fragment(f) for f in fragments)


# Ordered so more specific terms are checked before generic ones.
CATEGORY_RULES = [
    ("Data Engineering", ["data engineer", "data engineering", "mlops"]),
    ("Machine Learning", ["machine learning", "ml engineer"]),
    ("AI Engineering", ["ai engineer", "artificial intelligence engineer", "ai/ml", "ai researcher", "applied ai"]),
    ("NLP", ["nlp engineer", "natural language processing"]),
    ("Computer Vision", ["computer vision engineer"]),
    ("Deep Learning", ["deep learning"]),
    ("Research / Applied Science", ["applied scientist", "research scientist"]),
    ("Data Science", ["data scientist", "data science"]),
]


def categorize(title: str) -> str:
    t = title.lower()
    for label, terms in CATEGORY_RULES:
        if any(term in t for term in terms):
            return label
    return "Other"


def load_keywords(path: str) -> dict:
    with open(path) as f:
        data = yaml.safe_load(f)
    return {
        "role_terms": [t.lower() for t in data.get("role_terms", [])],
        "level_terms": [t.lower() for t in data.get("level_terms", [])],
        "exclude_terms": [t.lower() for t in data.get("exclude_terms", [])],
    }


def matches(title: str, keywords: dict) -> bool:
    if not title:
        return False
    t = title.lower()

    if any(term in t for term in keywords["exclude_terms"]):
        return False
    if not any(term in t for term in keywords["level_terms"]):
        return False
    return any(term in t for term in keywords["role_terms"])
