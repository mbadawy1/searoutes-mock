import os
from math import ceil
from typing import List, Tuple, Optional

import httpx
from pydantic import BaseModel

from .base import Schedule, ScheduleFilter, Page, ScheduleProvider

SEAROUTES_BASE_URL = os.getenv("SEAROUTES_BASE_URL", "https://api.searoutes.com")
SEAROUTES_API_KEY = os.getenv("SEAROUTES_API_KEY")
API_TIMEOUT_SECONDS = float(os.getenv("API_TIMEOUT_SECONDS", "10"))

class SearoutesProvider(ScheduleProvider):
    """Provider that queries Searoutes v2 endpoints and maps them into our Schedule schema.

    NOTE: This is a scaffold. Codex should implement the real HTTP calls and mapping
    following AGENTS.md (Milestone 2 section). Keep frontend/API schema unchanged.
    """

    def __init__(self, client: Optional[httpx.Client] = None) -> None:
        headers = {"x-api-key": SEAROUTES_API_KEY} if SEAROUTES_API_KEY else {}
        self.client = client or httpx.Client(
            base_url=SEAROUTES_BASE_URL,
            headers=headers,
            timeout=API_TIMEOUT_SECONDS,
        )

    def list(self, flt: ScheduleFilter, page: Page) -> Tuple[List[Schedule], int]:
        # TODO(Codex):
        # 1) Resolve origin/destination to UN/LOCODE via /geocoding/v2/port if not already locode
        # 2) Resolve carrier to SCAC via /search/v2/carriers when needed
        # 3) Call /itinerary/v2/execution with fromLocode, toLocode, carrierScac, fromDate, toDate
        # 4) Map response legs -> Schedule items according to AGENTS.md mapping rules
        # 5) Apply paging on the client-side (Searoutes limits may differ)
        # 6) Compute transitDays = ceil((eta - etd) / 1d) if not provided
        # 7) Return (items, total)
        raise NotImplementedError("Implement via AGENTS.md — Searoutes v2 mapping")
