from __future__ import annotations

"""LLM layer for intent classification and reasoning (up to 50 points).

This module wires up a concise prompt to Gemini and parses its two-line
response of the form:

    Intent: <High|Medium|Low>
    Reasoning: <short explanation>

The parsed intent maps to points via a simple lookup, and the reasoning is
returned verbatim for transparency.
"""

import os
import re
from typing import Tuple

from dotenv import load_dotenv
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnableLambda
from langchain_google_genai import ChatGoogleGenerativeAI

from .models import Lead, ProductOffer


load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    # Defer raising until first invocation to not break imports
    pass


def _build_llm() -> ChatGoogleGenerativeAI:
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError(
            "GEMINI_API_KEY not set. Define it in environment or .env file."
        )
    return ChatGoogleGenerativeAI(
        model="gemini-2.5-flash",
        google_api_key=api_key,
    )


# Prompt is intentionally short and deterministic to simplify downstream parsing.
prompt_template = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "You are an expert B2B sales analyst. Classify prospect buying intent (High/Medium/Low) based on the product/offer and prospect data. Respond in exactly two lines: 'Intent: <High|Medium|Low>' and 'Reasoning: <one or two concise sentences>'.",
        ),
        (
            "human",
            "Product/Offer Context\nName: {offer_name}\nValue Propositions: {offer_value_props}\nIdeal Use Cases: {offer_ideal_use_cases}\n\nProspect Data\nName: {lead_name}\nRole: {lead_role}\nCompany: {lead_company}\nIndustry: {lead_industry}\nLocation: {lead_location}\nLinkedIn Bio: {lead_linkedin_bio}\n\nClassify intent and explain.",
        ),
    ]
)


def _map_inputs(inputs: dict) -> dict:
    lead: Lead = inputs["lead"]
    offer: ProductOffer = inputs["offer"]
    return {
        "offer_name": offer.name,
        "offer_value_props": ", ".join(offer.value_props) if offer.value_props else "",
        "offer_ideal_use_cases": (
            ", ".join(offer.ideal_use_cases) if offer.ideal_use_cases else ""
        ),
        "lead_name": lead.name,
        "lead_role": lead.role,
        "lead_company": lead.company,
        "lead_industry": lead.industry,
        "lead_location": lead.location,
        "lead_linkedin_bio": lead.linkedin_bio,
    }


def build_ai_chain():
    """Return a runnable chain: (inputs)->prompt->llm->string."""
    llm = _build_llm()
    return RunnableLambda(_map_inputs) | prompt_template | llm | StrOutputParser()


def parse_ai_response(response_text: str) -> Tuple[str, str, int]:
    """Parse 'Intent: X' and 'Reasoning: Y' and map intent to points.

    Returns: (intent_label, reasoning, ai_points)
    """
    # Normalize line endings
    text = response_text.strip()
    # Try to extract intent
    intent_match = re.search(r"Intent\s*:\s*(High|Medium|Low)", text, re.I)
    reasoning_match = re.search(r"Reasoning\s*:\s*(.*)", text, re.I | re.S)
    intent = intent_match.group(1).capitalize() if intent_match else "Low"
    reasoning = reasoning_match.group(1).strip() if reasoning_match else text

    # Map discrete intent to a bounded point contribution (0–50 range used in total score)
    points_map = {
        "High": 50,
        "Medium": 30,
        "Low": 10,
    }
    return intent, reasoning, points_map.get(intent, 10)
