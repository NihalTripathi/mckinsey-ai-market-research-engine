"""Source credibility from the domain name.

Tiers (score is a starting point, tune in validate.py or here):
  official       government, regulators, universities, intergovernmental bodies
  reputable      established news, business media, consulting and data firms
  unknown        anything we do not recognise
  report_seller  market-research sellers and press-release wires: they sell or
                 advertise reports, and often repeat each other's numbers
  user_content   user-uploaded or self-published platforms (anyone can post)

Domains are matched exactly or as a real suffix, so "x.education.com" is NOT
treated as an ".edu" site.
"""
from dataclasses import dataclass
from urllib.parse import urlparse

SCORES = {
    "official": 0.95,
    "reputable": 0.75,
    "unknown": 0.50,
    "report_seller": 0.45,
    "user_content": 0.25,
}

REASONS = {
    "official": "official or institutional source",
    "reputable": "established news or research source",
    "unknown": "unrecognised source",
    "report_seller": "market-research seller page (marketing summary; may repeat other sellers)",
    "user_content": "user-generated or self-published content",
}

# Patterns starting with "." are suffixes; others match the domain or any subdomain of it.
OFFICIAL = [
    ".gov", ".gov.in", ".nic.in", ".gov.uk", ".gov.au", ".gc.ca", ".edu", ".ac.in", ".ac.uk",
    "rbi.org.in", "sebi.gov.in", "niti.gov.in", "ibef.org", "siam.in",
    "iea.org", "worldbank.org", "imf.org", "oecd.org", "un.org", "wto.org", "who.int",
    "europa.eu", "bis.org",
]
REPUTABLE = [
    "reuters.com", "bloomberg.com", "ft.com", "wsj.com", "economist.com", "bbc.com", "bbc.co.uk",
    "economictimes.indiatimes.com", "livemint.com", "business-standard.com",
    "thehindubusinessline.com", "thehindu.com", "moneycontrol.com", "financialexpress.com",
    "autocarindia.com", "mckinsey.com", "bcg.com", "deloitte.com", "pwc.com", "kpmg.com",
    "ey.com", "bain.com", "gartner.com", "forrester.com", "nature.com", "sciencedirect.com", "ieefa.org", "evinfrastructurenews.com",
]
REPORT_SELLER = [
    "marketsandmarkets.com", "researchandmarkets.com", "mordorintelligence.com",
    "grandviewresearch.com", "imarcgroup.com", "marketresearchfuture.com",
    "knowledge-sourcing.com", "fortunebusinessinsights.com", "alliedmarketresearch.com",
    "expertmarketresearch.com", "precedenceresearch.com", "technavio.com", "ibisworld.com",
    "gminsights.com", "straitsresearch.com", "coherentmarketinsights.com",
    "verifiedmarketresearch.com", "polarismarketresearch.com", "kenresearch.com",
    "businesswire.com", "globenewswire.com", "prnewswire.com", "openpr.com", "marknteladvisors.com", "nextmsc.com", "imarcengineering.com",
]
USER_CONTENT = [
    "scribd.com", "medium.com", "blogspot.com", "blogspot.in", "wordpress.com", "quora.com",
    "reddit.com", "slideshare.net", "linkedin.com", "facebook.com", "substack.com",
    "wixsite.com", "x.com", "twitter.com", "youtube.com", "youtu.be",
]

_SECOND_LEVEL = {"co", "com", "org", "net", "gov", "ac", "edu", "nic"}


@dataclass
class Credibility:
    domain: str
    tier: str
    score: float
    group: str      # sources in the same group count as ONE independent source
    reason: str


def get_domain(value: str) -> str:
    """Accept a URL or a bare domain; return the host without 'www.'."""
    if not value:
        return ""
    host = urlparse(value if "//" in value else f"//{value}").netloc.lower()
    host = host.split("@")[-1].split(":")[0]
    return host[4:] if host.startswith("www.") else host


def _matches(domain: str, pattern: str) -> bool:
    if pattern.startswith("."):
        return domain.endswith(pattern)
    return domain == pattern or domain.endswith("." + pattern)


def _any(domain: str, patterns: list[str]) -> bool:
    return any(_matches(domain, p) for p in patterns)


def _site_name(domain: str) -> str:
    """Registered-style name: 'a.b.example.co.uk' -> 'example.co.uk'."""
    parts = domain.split(".")
    if len(parts) >= 3 and len(parts[-1]) == 2 and parts[-2] in _SECOND_LEVEL:
        return ".".join(parts[-3:])
    return ".".join(parts[-2:]) if len(parts) >= 2 else domain


def assess(url_or_domain: str) -> Credibility:
    domain = get_domain(url_or_domain)
    if not domain:
        return Credibility("", "unknown", SCORES["unknown"], "", REASONS["unknown"])

    # Order matters: check the weakest tiers first so they cannot hide behind a strong one.
    if _any(domain, USER_CONTENT):
        tier = "user_content"
    elif _any(domain, REPORT_SELLER):
        tier = "report_seller"
    elif _any(domain, OFFICIAL):
        tier = "official"
    elif _any(domain, REPUTABLE):
        tier = "reputable"
    else:
        tier = "unknown"

    # All report sellers share one group: three sellers quoting one figure is one voice.
    # User-content sites host many unrelated authors, so each host is its own group.
    if tier == "report_seller":
        group = "report_sellers"
    elif tier == "user_content":
        group = domain
    else:
        group = _site_name(domain)
    return Credibility(domain, tier, SCORES[tier], group, REASONS[tier])