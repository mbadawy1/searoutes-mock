import json
import os
from functools import lru_cache
from typing import Any, Dict, List

from fastapi import APIRouter, Query

router = APIRouter()


# Cache the carriers data in memory
@lru_cache(maxsize=1)
def load_carriers_data() -> List[Dict[str, Any]]:
    """Load carriers data from JSON file, cached in memory."""
    current_dir = os.path.dirname(os.path.abspath(__file__))
    carriers_file = os.path.join(current_dir, "../../../data/carriers.json")

    with open(carriers_file, "r", encoding="utf-8") as f:
        return json.load(f)


def score_carrier(carrier: Dict[str, Any], query: str) -> int:
    """
    Score a carrier based on query match relevance.
    Higher score = better match.

    Scoring priority:
    1. Exact SCAC match: 1000
    2. Exact name match: 900
    3. Partial name match: 800
    4. Partial SCAC match: 700
    """
    query_lower = query.lower().strip()

    # Exact SCAC match (highest priority)
    if carrier["scac"].lower() == query_lower:
        return 1000

    # Exact name match
    if carrier["name"].lower() == query_lower:
        return 900

    # Partial name match
    if query_lower in carrier["name"].lower():
        return 800

    # Partial SCAC match
    if query_lower in carrier["scac"].lower():
        return 700

    # No match
    return 0


@router.get("/api/carriers/search")
def search_carriers(
    q: str = Query(..., description="Search query"),
    limit: int = Query(15, description="Maximum number of results", ge=1, le=100),
) -> List[Dict[str, Any]]:
    """
    Search carriers by name or SCAC code.
    Returns results ordered by relevance.
    """
    carriers = load_carriers_data()

    # Score and filter carriers
    scored_carriers = []
    for carrier in carriers:
        score = score_carrier(carrier, q)
        if score > 0:  # Only include matches
            scored_carriers.append((score, carrier))

    # Sort by score (descending) and limit results
    scored_carriers.sort(key=lambda x: x[0], reverse=True)
    return [carrier for _, carrier in scored_carriers[:limit]]
