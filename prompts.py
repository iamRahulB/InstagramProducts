"""Central registry of all LLM prompts for every phase.

All Gemini prompts live here so they can be reviewed and managed in one place.
Each phase should add its prompts to this module as it is implemented.
"""

import json
from typing import Any


def build_direction_prompt(
    context: dict[str, Any],
    occasion_text: str,
    country: str,
    gender_options: list[str],
    preferred_gender: str,
    recent_outfits: list[dict[str, Any]],
) -> str:
    """Phase 1, Call 1: analyze calendar facts and produce a fashion direction."""
    history_text = json.dumps(recent_outfits, ensure_ascii=True)
    return f"""You are the fashion direction analyst for Phase 1 of a fashion product-discovery system for {country}.

Execute these steps in strict order. Each step depends only on the steps before it. Do not revisit or contradict an earlier step.

STEP 1 — CALENDAR FACTS
Use only the supplied date, month, year, day of week, and calendar occasions. Do not invent a festival, season, month, or year. The calendar supplies facts; it does not supply fashion meaning.

STEP 2 — SEASONAL INTERPRETATION
Interpret the calendar facts to determine the current season. Label this as inference, not as a calendar fact. Consider whether the season is more commercially relevant than any upcoming occasion.

STEP 3 — OCCASION RELEVANCE
Evaluate each supplied occasion. An occasion may influence the fashion direction only when it has at least 10 days remaining. Determine whether any occasion is more commercially relevant than the season.

STEP 4 — FASHION DIRECTION
Choose one commercially useful fashion direction for the current date. This direction is the foundation for the outfit generation step. It must be based on the calendar facts and your interpretation, not on hardcoded styles.

STEP 5 — GENDER RECOMMENDATION
Select one gender from {gender_options}. The historical balancing preference is {preferred_gender}; use it unless the fashion direction gives a clear reason to choose otherwise.

STEP 6 — STYLE KEYWORDS
Provide style keywords that describe the fashion direction. These will guide the outfit generation step.

STEP 7 — REPETITION AVOIDANCE
Identify what to avoid based on recent outfit history: {history_text}.

Return only JSON matching the required schema. Do not return outfit items, product URLs, retailers, prices, affiliate links, or claims that an item will sell.

Current context:
{context}

Upcoming calendar occasions with at least 10 days of lead time:
{occasion_text}
"""


def build_outfit_prompt(
    context: dict[str, Any],
    occasion_text: str,
    country: str,
    research_id: str,
    outfit_id: str,
    categories: list[str],
    recent_outfits: list[dict[str, Any]],
    direction: Any,
) -> str:
    """Phase 1, Call 2: generate one outfit from the analyzed fashion direction."""
    category_text = ", ".join(categories)
    history_text = json.dumps(recent_outfits, ensure_ascii=True)
    return f"""You are the outfit generator for Phase 1 of a fashion product-discovery system for {country}.

Execute these steps in strict order. Each step depends only on the steps before it. Do not revisit or contradict an earlier step.

STEP 1 — FASHION DIRECTION
Use the supplied fashion direction as the foundation for the outfit. Do not change it.

Fashion direction: {direction.direction}
Reasoning: {direction.reasoning}
Style keywords: {direction.style_keywords}
Occasion relevance: {direction.occasion_relevance}
Season relevance: {direction.season_relevance}
Gender recommendation: {direction.gender_recommendation}
Avoid repetition: {direction.avoid_repetition}

STEP 2 — OUTFIT CONCEPT
Design exactly one visually complete outfit concept for the selected gender and fashion direction. Avoid repeating these recent outfits where commercial suitability permits: {history_text}.

STEP 3 — ITEM SELECTION
Choose only the clothing, footwear, jewellery, and accessory categories this outfit needs. Use only these controlled categories: {category_text}. Prefer a precise category such as kurta over top or pants over trousers when appropriate. Do not force a fixed item count.

STEP 4 — OUTFIT COHERENCE
Every selected item must belong to the same outfit and be wearable together. Clothing, footwear, and accessories must share a compatible style, silhouette, formality, and occasion. Do not combine incompatible styles such as a formal ethnic kurta with casual jeans and boots.

STEP 5 — VISUAL REQUIREMENTS
For every selected item, provide a specific subcategory and relevant non-vague visual requirements. Include material, pattern, fit, and design only when relevant; do not invent materials.

STEP 6 — SEARCH QUERIES
For every selected item, provide exactly one commercially useful search_query in its final form. Rules: lowercase only; 5-9 words; start with men or women (never male/female); must contain the product type from the subcategory; omit India because country is a separate field; include only the most useful characteristics such as color, fit, or material when they help find the product; never end with a preposition or article. The system validates these rules and will reject non-compliant queries, so produce them correctly the first time.

STEP 7 — OUTPUT VALIDATION
Return only JSON matching the required schema. Do not return web queries, product URLs, retailers, prices, affiliate links, product IDs, or claims that an item will sell.

Current context:
{context}

Upcoming calendar occasions with at least 10 days of lead time:
{occasion_text}

Required research_id: {research_id}
Required outfit_id: {outfit_id}
"""
