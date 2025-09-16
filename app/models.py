from __future__ import annotations

from typing import List, Optional, TypedDict
from pydantic import BaseModel, Field


class ProductOffer(BaseModel):
    """Represents the current product/offer context used for scoring."""

    name: str = Field(..., description="Name of the product/offer")
    value_props: List[str] = Field(
        default_factory=list,
        description="Key value propositions of the offer",
    )
    ideal_use_cases: List[str] = Field(
        default_factory=list,
        description="Ideal use cases / ICP descriptors",
    )


class Lead(BaseModel):
    name: str
    role: str
    company: str
    industry: str
    location: str
    linkedin_bio: str


class ScoredLead(BaseModel):
    name: str
    role: str
    company: str
    industry: str
    location: str
    linkedin_bio: str
    intent: str = Field(..., description="High | Medium | Low")
    score: int = Field(..., ge=0, le=100)
    reasoning: str


# In-memory storage for the assignment scope
current_offer: Optional[ProductOffer] = None
uploaded_leads: List[Lead] = []
scored_leads: List[ScoredLead] = []


class ScoringState(TypedDict, total=False):
    """State shape passed through the LangGraph workflow."""

    lead: Lead
    offer: ProductOffer
    rule_score: int
    ai_intent: str
    ai_reasoning: str
    ai_points: int
    final_score: int
    error_message: Optional[str]
