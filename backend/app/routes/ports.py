import json
import os
from functools import lru_cache
from typing import Any, Dict, List

from fastapi import APIRouter, Query

router = APIRouter()


# Cache the ports data in memory
@lru_cache(maxsize=1)
def load_ports_data() -> List[Dict[str, Any]]:
    """Load ports data from JSON file, cached in memory."""
    current_dir = os.path.dirname(os.path.abspath(__file__))
    ports_file = os.path.join(current_dir, "../../../data/ports.json")

    with open(ports_file, "r", encoding="utf-8") as f:
        return json.load(f)


def score_port(port: Dict[str, Any], query: str) -> int:
    """
    Score a port based on query match relevance.
    Higher score = better match.

    Scoring priority:
    1. Exact LOCODE match: 1000
    2. Exact name match: 900
    3. Partial name match: 800
    4. Exact alias match: 700
    5. Partial alias match: 600
    6. Country code match: 500
    7. Country name match: 400
    """
    query_lower = query.lower().strip()

    # Exact LOCODE match (highest priority)
    if port["locode"].lower() == query_lower:
        return 1000

    # Exact name match
    if port["name"].lower() == query_lower:
        return 900

    # Partial name match
    if query_lower in port["name"].lower():
        return 800

    # Check aliases
    for alias in port.get("aliases", []):
        # Exact alias match
        if alias.lower() == query_lower:
            return 700
        # Partial alias match
        if query_lower in alias.lower():
            return 600

    # Country code match
    if port["country"].lower() == query_lower:
        return 500

    # Country name match
    if port.get("countryName", "").lower() == query_lower:
        return 400

    # Partial country name match
    if query_lower in port.get("countryName", "").lower():
        return 300

    # No match
    return 0


@router.get("/api/ports/search")
def search_ports(
    q: str = Query(..., description="Search query"),
    limit: int = Query(15, description="Maximum number of results", ge=1, le=100),
) -> List[Dict[str, Any]]:
    """
    Search ports by name, locode, aliases, country code, or country name.
    Returns results ordered by relevance.
    """
    ports = load_ports_data()

    # Score and filter ports
    scored_ports = []
    for port in ports:
        score = score_port(port, q)
        if score > 0:  # Only include matches
            scored_ports.append((score, port))

    # Sort by score (descending) and limit results
    scored_ports.sort(key=lambda x: x[0], reverse=True)
    return [port for _, port in scored_ports[:limit]]
