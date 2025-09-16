from __future__ import annotations

"""Deterministic rule-based scoring (0–50).

This module implements a simple, transparent heuristic to assign up to 50 points
to a lead before the AI layer contributes additional points. The breakdown is:

- Role relevance (0–20): Decision-makers score higher than influencers.
- ICP/industry token overlap (0–20): More overlap implies better fit.
- Data completeness (0–10): Encourages fully populated lead records.

These rules are intentionally lightweight and auditable for assignment scope.
"""

from typing import List

from .models import Lead, ProductOffer


# Keywords that generally indicate a decision maker. We use substring matching
# (case-insensitive) for a pragmatic heuristic rather than exact titles.
DECISION_MAKER_KEYWORDS = [
    "head",
    "director",
    "vp",
    "vice president",
    "cxo",
    "ceo",
    "coo",
    "cto",
    "cpo",
    "cmo",
    "founder",
    "owner",
    "lead",
]

# Titles that often influence decisions but may not be final approvers.
INFLUENCER_KEYWORDS = [
    "manager",
    "specialist",
    "analyst",
    "coordinator",
    "associate",
]


def _contains_any(text: str, keywords: List[str]) -> bool:
    """Return True if any keyword is a substring of the given text (case-insensitive)."""
    t = text.lower()
    return any(k in t for k in keywords)


def calculate_rule_score(lead: Lead, offer: ProductOffer) -> int:
    """Calculate deterministic rule score out of 50.

    - Role relevance: decision maker +20, influencer +10, else +0
    - Industry/ICP match: exact/close +20, adjacent +10, else +0
    - Data completeness: all fields present +10
    """

    score = 0

    # Role relevance (max 20)
    if _contains_any(lead.role, DECISION_MAKER_KEYWORDS):
        score += 20
    elif _contains_any(lead.role, INFLUENCER_KEYWORDS):
        score += 10

    # Industry/ICP match vs offer.ideal_use_cases (max 20)
    industry = lead.industry.lower()
    icp_tokens = set()
    for use_case in offer.ideal_use_cases:
        icp_tokens.update(token.strip().lower() for token in use_case.split())

    # naive token overlap heuristic
    overlap = len([t for t in icp_tokens if t in industry])
    if overlap >= 2:
        score += 20
    elif overlap == 1:
        score += 10

    # Data completeness (max 10)
    fields = [
        lead.name,
        lead.role,
        lead.company,
        lead.industry,
        lead.location,
        lead.linkedin_bio,
    ]
    if all(str(f or "").strip() for f in fields):
        score += 10

    # Bound to 0..50 to avoid accidental drift if rules change
    return max(0, min(50, score))
