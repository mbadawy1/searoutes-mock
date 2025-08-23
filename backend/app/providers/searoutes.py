import os
import re
import time
from math import ceil
from typing import List, Tuple, Optional, Dict

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
        
        # Add Accept-Version header if configured
        accept_version = os.getenv("SEAROUTES_ACCEPT_VERSION")
        if accept_version:
            headers["Accept-Version"] = accept_version
            
        self.client = client or httpx.Client(
            base_url=SEAROUTES_BASE_URL,
            headers=headers,
            timeout=API_TIMEOUT_SECONDS,
            transport=httpx.HTTPTransport(retries=2)  # 2 retries on 429/5xx
        )
        
        # In-memory cache for carrier lookups (5 minute TTL)
        self._carrier_cache: Dict[str, Tuple[Dict[str, str], float]] = {}

    def resolve_port(self, port_query: str) -> Dict[str, str]:
        """Resolve port by UN/LOCODE or plain text query to {name, locode, country}.
        
        Args:
            port_query: Either UN/LOCODE (5 chars: 2 letters + 3 letters) or plain text query
            
        Returns:
            Dict with keys: name, locode, country
            
        Raises:
            httpx.HTTPError: On API errors
            ValueError: If no results found
        """
        # Check if input is UN/LOCODE format (^[A-Z]{2}[A-Z]{3}$)
        locode_pattern = re.compile(r'^[A-Z]{2}[A-Z]{3}$')
        
        if locode_pattern.match(port_query.upper()):
            # Query by UN/LOCODE
            params = {"locode": port_query.upper()}
        else:
            # Query by name
            params = {"query": port_query}
            
        response = self.client.get("/geocoding/v2/port", params=params)
        response.raise_for_status()
        
        data = response.json()
        
        # Searoutes response format may vary - handle common structures
        if isinstance(data, list) and len(data) > 0:
            port = data[0]  # Take first/best result
        elif isinstance(data, dict) and 'results' in data and len(data['results']) > 0:
            port = data['results'][0]
        elif isinstance(data, dict) and ('name' in data or 'portName' in data or 'locode' in data or 'unLocode' in data):
            port = data  # Single port result
        else:
            raise ValueError(f"No port found for query: {port_query}")
            
        # Map to internal format - handle various response structures
        return {
            "name": port.get("name") or port.get("portName") or "",
            "locode": port.get("locode") or port.get("unLocode") or port.get("code") or "",  
            "country": port.get("country") or port.get("countryCode") or port.get("countryName") or ""
        }

    def resolve_carrier(self, scac_or_name: str) -> Dict[str, str]:
        """Resolve carrier by SCAC or name to {name, scac, id}.
        
        Args:
            scac_or_name: Either SCAC code or carrier name
            
        Returns:
            Dict with keys: name, scac, id
            
        Raises:
            httpx.HTTPError: On API errors
            ValueError: If no results found
        """
        # Check cache first (5 minute TTL)
        cache_key = scac_or_name.upper()
        current_time = time.time()
        
        if cache_key in self._carrier_cache:
            cached_result, cached_time = self._carrier_cache[cache_key]
            if current_time - cached_time < 300:  # 5 minutes = 300 seconds
                return cached_result
            else:
                # Remove expired entry
                del self._carrier_cache[cache_key]
        
        # Call Searoutes API
        params = {"query": scac_or_name}
        response = self.client.get("/search/v2/carriers", params=params)
        response.raise_for_status()
        
        data = response.json()
        
        # Handle various response formats
        if isinstance(data, list) and len(data) > 0:
            carrier = data[0]  # Take first/best result
        elif isinstance(data, dict) and 'results' in data and len(data['results']) > 0:
            carrier = data['results'][0]
        elif isinstance(data, dict) and ('name' in data or 'carrierName' in data or 'scac' in data):
            carrier = data  # Single carrier result
        else:
            raise ValueError(f"No carrier found for query: {scac_or_name}")
            
        # Map to internal format - handle various response structures
        result = {
            "name": carrier.get("name") or carrier.get("carrierName") or carrier.get("companyName") or "",
            "scac": carrier.get("scac") or carrier.get("scacCode") or carrier.get("code") or "",
            "id": str(carrier.get("id") or carrier.get("carrierId") or carrier.get("companyId") or "")
        }
        
        # Cache the result
        self._carrier_cache[cache_key] = (result, current_time)
        
        return result

    def list(self, flt: ScheduleFilter, page: Page) -> Tuple[List[Schedule], Page]:
        # TODO(Codex):
        # 1) Resolve origin/destination to UN/LOCODE via /geocoding/v2/port if not already locode
        # 2) Resolve carrier to SCAC via /search/v2/carriers when needed
        # 3) Call /itinerary/v2/execution with fromLocode, toLocode, carrierScac, fromDate, toDate
        # 4) Map response legs -> Schedule items according to AGENTS.md mapping rules
        # 5) Apply paging on the client-side (Searoutes limits may differ)
        # 6) Compute transitDays = ceil((eta - etd) / 1d) if not provided
        # 7) Return (items, page_metadata)
        
        # Placeholder implementation for Task 14 - return empty list until Tasks 15-17 implemented
        return [], page
