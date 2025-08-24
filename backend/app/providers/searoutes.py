import os
import random
import re
import time
import unicodedata
from datetime import datetime
from math import ceil
from typing import Dict, List, Optional, Tuple
from uuid import uuid4

import httpx
from pydantic import BaseModel

from ..models.schedule import ScheduleLeg
from .base import Page, Schedule, ScheduleFilter, ScheduleProvider


def _ascii_norm(s: str) -> str:
    """Normalize string: strip diacritics, collapse whitespace, casefold."""
    if not s:
        return ""
    # Strip diacritics -> ASCII, collapse whitespace, lowercase
    s = unicodedata.normalize("NFKD", s)
    s = "".join(ch for ch in s if not unicodedata.combining(ch))
    s = re.sub(r"\s+", " ", s)
    return s.strip().casefold()


def _alnum_only(s: str) -> str:
    """Extract only alphanumeric characters."""
    return re.sub(r"[^A-Za-z0-9]", "", s or "")


def _tokens(s: str) -> List[str]:
    """Split string into normalized alphanumeric tokens."""
    return [t for t in re.split(r"[^A-Za-z0-9]+", _ascii_norm(s)) if t]


PORT_NOISE_PREFIXES = (
    "port of ", "porto di ", "puerto de ", "puerto del ",
    "port ", "harbor of ", "harbour of ",
)


def _strip_port_noise(s: str) -> str:
    """Strip common port name prefixes to improve matching."""
    s2 = s
    for p in PORT_NOISE_PREFIXES:
        if s2.startswith(p):
            return s2[len(p):]
    return s2


def _port_name(p: dict) -> str:
    """Extract port name from various response formats."""
    for k in ("displayName", "name", "portName", "shortName"):
        v = p.get(k)
        if v:
            return str(v)
    # Sometimes nested:
    v = (p.get("attributes") or {}).get("name")
    return str(v) if v else ""


def _port_locode(p: dict) -> str:
    """Extract port LOCODE from various response formats."""
    for k in ("locode", "unLocode", "code", "unlocode"):
        v = p.get(k)
        if v:
            return str(v)
    v = (p.get("attributes") or {}).get("locode")
    return str(v) if v else ""


def _port_country(p: dict) -> str:
    """Extract port country from various response formats."""
    for k in ("countryCode", "country", "countryName", "country_code"):
        v = p.get(k)
        if v:
            return str(v)
    return ""


def _port_size(p: dict) -> int:
    """Extract port size with fallback."""
    v = p.get("size")
    try:
        return int(v) if v is not None else 0
    except (ValueError, TypeError):
        return 0


def _carrier_name(c: dict) -> str:
    """Extract carrier name from various response formats."""
    for k in ("displayName", "name", "shortName", "legalName", "carrierName", "companyName"):
        v = c.get(k)
        if v:
            return str(v)
    # Sometimes nested:
    v = (c.get("attributes") or {}).get("name")
    return str(v) if v else ""


def _carrier_scac(c: dict) -> str:
    """Extract carrier SCAC from various response formats."""
    for k in ("scac", "scacCode", "code"):
        v = c.get(k)
        if v:
            return str(v)
    return ""


def _carrier_id(c: dict) -> str:
    """Extract carrier ID from various response formats."""
    for k in ("id", "carrierId", "companyId"):
        v = c.get(k)
        if v:
            return str(v)
    return ""


class SearoutesError(Exception):
    """Base exception for Searoutes API errors."""

    def __init__(self, message: str, code: Optional[str] = None, request_id: Optional[str] = None):
        self.message = message
        self.code = code
        self.request_id = request_id
        super().__init__(message)

    def to_dict(self) -> Dict[str, str]:
        """Convert to dictionary for API responses."""
        result = {"code": self.code or "SEAROUTES_ERROR", "message": self.message}
        if self.request_id:
            result["request_id"] = self.request_id
        return result


class SearoutesRateLimitError(SearoutesError):
    """Exception for rate limit errors (429)."""

    def __init__(self, message: str = "Rate limit exceeded", request_id: Optional[str] = None):
        super().__init__(message, "RATE_LIMIT_EXCEEDED", request_id)


class SearoutesAPIError(SearoutesError):
    """Exception for general API errors (4xx/5xx)."""

    def __init__(self, status_code: int, message: str, request_id: Optional[str] = None):
        code = f"HTTP_{status_code}"
        super().__init__(message, code, request_id)


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
            # Note: We handle retries manually for better control over rate limits
        )

        # In-memory cache for carrier lookups (5 minute TTL)
        self._carrier_cache: Dict[str, Tuple[Dict[str, str], float]] = {}

    def _make_request(
        self, endpoint: str, params: Optional[Dict] = None, max_retries: int = 3
    ) -> httpx.Response:
        """Make HTTP request with retry logic and proper error handling."""
        last_exception = None

        for attempt in range(max_retries + 1):
            try:
                response = self.client.get(endpoint, params=params)

                # Handle rate limiting (429) with exponential backoff
                if response.status_code == 429:
                    if attempt < max_retries:
                        # Extract retry-after header if available
                        retry_after = response.headers.get("retry-after")
                        if retry_after and retry_after.isdigit():
                            delay = int(retry_after)
                        else:
                            # Exponential backoff with jitter
                            delay = (2**attempt) + random.uniform(0, 1)

                        time.sleep(delay)
                        continue
                    else:
                        # Final attempt - raise rate limit error
                        request_id = self._extract_request_id(response)
                        raise SearoutesRateLimitError(
                            f"Rate limit exceeded after {max_retries} retries", request_id
                        )

                # Handle other 4xx/5xx errors
                if response.status_code >= 400:
                    request_id = self._extract_request_id(response)
                    error_message = self._extract_error_message(response)

                    if response.status_code >= 500:
                        # 5xx errors - retry with backoff
                        if attempt < max_retries:
                            delay = (2**attempt) + random.uniform(0, 1)
                            time.sleep(delay)
                            continue

                    # Final attempt or 4xx error - raise API error
                    raise SearoutesAPIError(response.status_code, error_message, request_id)

                # Success - return response
                return response

            except httpx.RequestError as e:
                last_exception = e
                if attempt < max_retries:
                    # Network error - retry with backoff
                    delay = (2**attempt) + random.uniform(0, 1)
                    time.sleep(delay)
                    continue

        # All retries exhausted
        raise SearoutesError(f"Network error after {max_retries} retries: {last_exception}")

    def _extract_request_id(self, response: httpx.Response) -> Optional[str]:
        """Extract Searoutes request ID from response headers or body."""
        # Check common request ID header names
        for header_name in ["x-request-id", "request-id", "x-correlation-id", "correlation-id"]:
            request_id = response.headers.get(header_name)
            if request_id:
                return request_id

        # Try to extract from response body
        try:
            data = response.json()
            if isinstance(data, dict):
                return data.get("requestId") or data.get("request_id") or data.get("correlationId")
        except:
            pass

        return None

    def _extract_error_message(self, response: httpx.Response) -> str:
        """Extract error message from response."""
        try:
            data = response.json()
            if isinstance(data, dict):
                # Try various error message fields
                error_msg = (
                    data.get("message")
                    or data.get("error")
                    or data.get("detail")
                    or data.get("error_description")
                )
                if error_msg:
                    return str(error_msg)
        except:
            pass

        # Fallback to HTTP status text
        return f"HTTP {response.status_code}: {response.reason_phrase}"

    def resolve_port(self, port_query: str) -> Dict[str, str]:
        """Resolve port by UN/LOCODE or plain text query to {name, locode, country}.

        Smart ranking: Exact LOCODE > Exact name > startswith > contains (size as tiebreaker).

        Args:
            port_query: Either UN/LOCODE (5 chars: 2 letters + 3 alphanumerics) or plain text query

        Returns:
            Dict with keys: name, locode, country

        Raises:
            httpx.HTTPError: On API errors
            ValueError: If no results found
        """
        # Accept CC + XXX (last 3 can be alphanumeric), allow spaces/dashes in input
        clean_q = _alnum_only(port_query).upper()
        locode_pattern = re.compile(r"^[A-Z]{2}[A-Z0-9]{3}$")
        is_locode_query = bool(locode_pattern.fullmatch(clean_q))

        if is_locode_query:
            params = {"locode": clean_q}
        else:
            params = {"query": port_query}  # keep original for Searoutes' search semantics

        response = self._make_request("/geocoding/v2/port", params=params)

        data = response.json()

        # Extract ports list from various response formats
        ports_list = []
        if isinstance(data, list):
            ports_list = data
        elif isinstance(data, dict) and "results" in data:
            ports_list = data["results"]
        elif isinstance(data, dict) and (
            "name" in data or "portName" in data or "locode" in data or "unLocode" in data
        ):
            ports_list = [data]  # Single port result

        # Fallback for rare cases: if LOCODE lookup failed, try name query once
        if not ports_list and is_locode_query:
            try:
                resp2 = self._make_request("/geocoding/v2/port", params={"query": port_query})
                data2 = resp2.json()
                if isinstance(data2, list):
                    ports_list = data2
                elif isinstance(data2, dict) and "results" in data2:
                    ports_list = data2["results"]
            except:
                pass  # Continue with empty list

        if not ports_list:
            raise ValueError(f"No port found for query: {port_query}")

        # Apply smart ranking
        best_port = self._rank_ports(ports_list, port_query, is_locode_query)

        # Map to internal format using robust extraction
        return {
            "name": _port_name(best_port),
            "locode": _port_locode(best_port),
            "country": _port_country(best_port),
        }

    def _rank_ports(self, ports: List[dict], query: str, is_locode_query: bool) -> dict:
        """
        Rank ports strictly per Task 19:
        Exact LOCODE > Exact name > startswith > contains. Use size as tiebreaker.
        """
        if not ports:
            return {}

        q_norm = _ascii_norm(query)
        q_locode = _alnum_only(query).upper()
        q_tokens = _tokens(query)

        def extract(p: dict) -> Tuple[int, int, str, dict]:
            # Use robust field extraction
            name = _port_name(p)
            locode = _port_locode(p)
            size_num = _port_size(p)
            
            name_norm = _ascii_norm(name)
            name_tokens = _tokens(name)
            locode_up = _alnum_only(locode).upper()

            # Boolean features
            exact_locode = locode_up and q_locode and locode_up == q_locode
            exact_name = name_norm and q_norm and name_norm == q_norm

            # Improved startswith / contains logic
            # Strip port noise for better startswith matching
            name_for_sw = _strip_port_noise(name_norm)
            startswith = name_for_sw.startswith(q_norm)
            
            # Tighter contains: token-based and raw substring
            has_tokens = bool(q_tokens)
            token_contains = (
                has_tokens and all(
                    any(t.startswith(tok) or t == tok for t in name_tokens)
                    for tok in q_tokens
                )
            )
            contains = token_contains or (q_norm in name_norm)

            # Score strictly per spec
            if is_locode_query:
                # LOCODE-first
                if exact_locode:
                    score = 4
                elif exact_name:
                    score = 3
                elif startswith:
                    score = 2
                elif contains:
                    score = 1
                else:
                    score = 0
            else:
                # Name-first
                if exact_name:
                    score = 4
                elif startswith:
                    score = 3
                elif contains:
                    score = 2
                elif exact_locode:
                    score = 1  # allowed but lowest among the four
                else:
                    score = 0

            # Return a sorting key tuple and the object
            # Sort by: score desc, size desc, name asc (stable & deterministic)
            return (-score, -size_num, name_norm or name, p)

        ranked = [extract(p) for p in ports]
        ranked.sort()
        return ranked[0][3]

    def resolve_carrier(self, scac_or_name: str) -> Dict[str, str]:
        """Resolve carrier by SCAC or name to {name, scac, id}.

        Smart ranking: Exact SCAC > Exact name > startswith > contains

        Args:
            scac_or_name: Either SCAC code or carrier name

        Returns:
            Dict with keys: name, scac, id

        Raises:
            httpx.HTTPError: On API errors
            ValueError: If no results found
        """
        # Check cache first (5 minute TTL)
        cache_key = _ascii_norm(scac_or_name)  # Use normalized key for better cache hits
        current_time = time.time()

        if cache_key in self._carrier_cache:
            cached_result, cached_time = self._carrier_cache[cache_key]
            if current_time - cached_time < 300:  # 5 minutes = 300 seconds
                return cached_result
            else:
                # Remove expired entry
                del self._carrier_cache[cache_key]

        # Determine if this looks like a SCAC code
        clean_q = _alnum_only(scac_or_name).upper()
        scac_pattern = re.compile(r"^[A-Z0-9]{2,4}$")  # SCAC is typically 2-4 alphanumerics
        is_scac_query = bool(scac_pattern.fullmatch(clean_q))

        # Call Searoutes API
        params = {"query": scac_or_name}
        response = self._make_request("/search/v2/carriers", params=params)

        data = response.json()

        # Extract carriers list from various response formats
        carriers = []
        if isinstance(data, list):
            carriers = data
        elif isinstance(data, dict) and "results" in data:
            carriers = data["results"]
        elif isinstance(data, dict) and ("name" in data or "carrierName" in data or "scac" in data):
            carriers = [data]  # Single carrier result

        if not carriers:
            raise ValueError(f"No carrier found for query: {scac_or_name}")

        # Apply smart ranking
        best_carrier = self._rank_carriers(carriers, scac_or_name, is_scac_query)

        # Map to internal format using robust extraction
        result = {
            "name": _carrier_name(best_carrier),
            "scac": _carrier_scac(best_carrier),
            "id": _carrier_id(best_carrier),
        }

        # Cache the result
        self._carrier_cache[cache_key] = (result, current_time)

        return result

    def _rank_carriers(self, carriers: List[dict], query: str, is_scac_query: bool) -> dict:
        """
        Rank carriers strictly per Task 19:
        Exact SCAC > Exact name > startswith > contains
        """
        if not carriers:
            return {}

        q_norm = _ascii_norm(query)
        q_scac = _alnum_only(query).upper()
        q_tokens = _tokens(query)

        def extract(c: dict) -> Tuple[int, str, dict]:
            # Use robust field extraction
            name = _carrier_name(c)
            scac = _carrier_scac(c)
            
            name_norm = _ascii_norm(name)
            scac_up = _alnum_only(scac).upper()
            name_tokens = _tokens(name)

            exact_scac = scac_up and q_scac and scac_up == q_scac
            exact_name = name_norm and q_norm and name_norm == q_norm
            
            # Improved startswith / contains logic
            startswith = name_norm.startswith(q_norm)
            
            # Tighter contains: token-based and raw substring
            has_tokens = bool(q_tokens)
            token_contains = (
                has_tokens and all(
                    any(t.startswith(tok) or t == tok for t in name_tokens)
                    for tok in q_tokens
                )
            )
            contains = token_contains or (q_norm in name_norm)

            if is_scac_query:
                if exact_scac:
                    score = 4
                elif exact_name:
                    score = 3
                elif startswith:
                    score = 2
                elif contains:
                    score = 1
                else:
                    score = 0
            else:
                if exact_name:
                    score = 4
                elif startswith:
                    score = 3
                elif contains:
                    score = 2
                elif exact_scac:
                    score = 1
                else:
                    score = 0

            # No explicit tiebreaker specified; use name as stable deterministic sort
            return (-score, name_norm or name, c)

        ranked = [extract(c) for c in carriers]
        ranked.sort()
        return ranked[0][2]

    def list(self, flt: ScheduleFilter, page: Page) -> Tuple[List[Schedule], Page]:
        """Fetch live itineraries from Searoutes and map to internal Schedule format."""
        try:
            # 1) Resolve origin/destination to UN/LOCODE if not already in LOCODE format
            origin_port = None
            destination_port = None

            if flt.origin:
                try:
                    origin_port = self.resolve_port(flt.origin)
                except SearoutesError:
                    # Re-raise Searoutes API errors
                    raise
                except ValueError:
                    # Port not found - return empty results
                    return [], page

            if flt.destination:
                try:
                    destination_port = self.resolve_port(flt.destination)
                except SearoutesError:
                    # Re-raise Searoutes API errors
                    raise
                except ValueError:
                    # Port not found - return empty results
                    return [], page

            # 2) Resolve carrier to SCAC if provided
            carrier_scac = None
            if flt.carrier:
                try:
                    carrier_info = self.resolve_carrier(flt.carrier)
                    carrier_scac = carrier_info.get("scac")
                except SearoutesError:
                    # Re-raise Searoutes API errors
                    raise
                except ValueError:
                    # Carrier not found - continue without carrier filter
                    pass

            # 3) Call /itinerary/v2/execution with proper parameters
            params = {}

            if origin_port:
                params["fromLocode"] = origin_port["locode"]
            if destination_port:
                params["toLocode"] = destination_port["locode"]
            if carrier_scac:
                params["carrierScac"] = carrier_scac
            if flt.date_from:
                params["fromDate"] = flt.date_from
            if flt.date_to:
                params["toDate"] = flt.date_to

            response = self._make_request("/itinerary/v2/execution", params=params)

            data = response.json()

            # 4) Map response to Schedule items
            schedules = self._map_itineraries_to_schedules(data, origin_port, destination_port)

            # 5) Apply client-side filtering and sorting
            filtered_schedules = self._apply_filters(schedules, flt)
            sorted_schedules = self._apply_sorting(filtered_schedules, flt.sort or "etd")

            # 6) Apply pagination
            total = len(sorted_schedules)
            start_idx = (page.page - 1) * page.pageSize
            end_idx = start_idx + page.pageSize
            paginated_schedules = sorted_schedules[start_idx:end_idx]

            return paginated_schedules, Page(total=total, page=page.page, pageSize=page.pageSize)

        except SearoutesError:
            # Re-raise Searoutes-specific errors to be handled by the API layer
            raise
        except Exception as e:
            # Wrap other exceptions as generic Searoutes errors
            raise SearoutesError(f"Unexpected error: {str(e)}")

    def _map_itineraries_to_schedules(
        self, data: dict, origin_port: Optional[Dict], destination_port: Optional[Dict]
    ) -> List[Schedule]:
        """Map Searoutes itinerary response to internal Schedule format."""
        schedules = []

        # Handle various response formats
        itineraries = []
        if isinstance(data, list):
            itineraries = data
        elif isinstance(data, dict) and "results" in data:
            itineraries = data["results"]
        elif isinstance(data, dict) and "itineraries" in data:
            itineraries = data["itineraries"]
        elif isinstance(data, dict) and "data" in data:
            itineraries = data["data"]

        for itinerary in itineraries:
            try:
                schedule = self._map_single_itinerary(itinerary, origin_port, destination_port)
                if schedule:
                    schedules.append(schedule)
            except Exception as e:
                # Skip invalid itineraries but continue processing others
                print(f"Error mapping itinerary: {e}")
                continue

        return schedules

    def _map_single_itinerary(
        self, itinerary: dict, origin_port: Optional[Dict], destination_port: Optional[Dict]
    ) -> Optional[Schedule]:
        """Map a single itinerary to Schedule format."""
        # Extract legs from various possible locations
        legs_data = (
            itinerary.get("legs") or itinerary.get("route") or itinerary.get("segments") or []
        )

        if not legs_data:
            return None

        # Extract first and last leg for ETD/ETA
        first_leg = legs_data[0]
        last_leg = legs_data[-1]

        # Get ETD from first leg departure
        etd = first_leg.get("departure") or first_leg.get("etd") or first_leg.get("departureTime")
        # Get ETA from last leg arrival
        eta = last_leg.get("arrival") or last_leg.get("eta") or last_leg.get("arrivalTime")

        if not etd or not eta:
            return None

        # Determine routing type
        routing_type = "Direct" if len(legs_data) == 1 else "Transshipment"

        # Calculate transit days if not provided
        transit_days = itinerary.get("transitDays")
        if not transit_days:
            try:
                etd_dt = datetime.fromisoformat(etd.replace("Z", "+00:00"))
                eta_dt = datetime.fromisoformat(eta.replace("Z", "+00:00"))
                transit_days = ceil((eta_dt - etd_dt).total_seconds() / 86400)
            except:
                transit_days = 0

        # Extract vessel, voyage, carrier info (prefer from first leg)
        vessel = (
            first_leg.get("vessel") or first_leg.get("vesselName") or itinerary.get("vessel") or ""
        )
        voyage = (
            first_leg.get("voyage")
            or first_leg.get("voyageNumber")
            or itinerary.get("voyage")
            or ""
        )
        carrier = (
            first_leg.get("carrier")
            or first_leg.get("carrierName")
            or itinerary.get("carrier")
            or ""
        )
        imo = first_leg.get("imo") or first_leg.get("vesselImo") or itinerary.get("imo")
        service = itinerary.get("service") or itinerary.get("serviceName")

        # Build origin/destination strings
        origin = ""
        destination = ""

        if origin_port:
            origin = f"{origin_port['name']}, {origin_port['country']}"
        elif first_leg.get("fromPort"):
            origin = first_leg["fromPort"]

        if destination_port:
            destination = f"{destination_port['name']}, {destination_port['country']}"
        elif last_leg.get("toPort"):
            destination = last_leg["toPort"]

        # Map legs for detailed view
        mapped_legs = []
        for i, leg in enumerate(legs_data):
            try:
                leg_etd = leg.get("departure") or leg.get("etd") or leg.get("departureTime") or ""
                leg_eta = leg.get("arrival") or leg.get("eta") or leg.get("arrivalTime") or ""
                leg_transit = leg.get("transitDays", 0)

                if not leg_transit and leg_etd and leg_eta:
                    try:
                        leg_etd_dt = datetime.fromisoformat(leg_etd.replace("Z", "+00:00"))
                        leg_eta_dt = datetime.fromisoformat(leg_eta.replace("Z", "+00:00"))
                        leg_transit = ceil((leg_eta_dt - leg_etd_dt).total_seconds() / 86400)
                    except:
                        leg_transit = 0

                schedule_leg = ScheduleLeg(
                    legNumber=i + 1,
                    fromLocode=leg.get("fromLocode") or leg.get("originLocode") or "",
                    fromPort=leg.get("fromPort") or leg.get("originPort") or "",
                    toLocode=leg.get("toLocode") or leg.get("destinationLocode") or "",
                    toPort=leg.get("toPort") or leg.get("destinationPort") or "",
                    etd=leg_etd,
                    eta=leg_eta,
                    vessel=leg.get("vessel") or leg.get("vesselName") or vessel,
                    voyage=leg.get("voyage") or leg.get("voyageNumber") or voyage,
                    transitDays=leg_transit,
                )
                mapped_legs.append(schedule_leg)
            except Exception as e:
                print(f"Error mapping leg {i}: {e}")
                continue

        return Schedule(
            id=itinerary.get("id") or str(uuid4()),
            origin=origin,
            destination=destination,
            etd=etd,
            eta=eta,
            vessel=vessel,
            voyage=voyage,
            imo=imo,
            routingType=routing_type,
            transitDays=transit_days,
            carrier=carrier,
            service=service,
            legs=mapped_legs if len(mapped_legs) > 1 else None,
        )

    def _apply_filters(self, schedules: List[Schedule], flt: ScheduleFilter) -> List[Schedule]:
        """Apply client-side filters that weren't handled by the API."""
        filtered = schedules

        # Filter by equipment if specified
        if flt.equipment:
            # Note: Searoutes API may not return equipment info consistently
            # For now, we'll just pass through all results
            pass

        # Filter by routing type if specified
        if flt.routingType:
            filtered = [s for s in filtered if s.routingType.lower() == flt.routingType.lower()]

        return filtered

    def _apply_sorting(self, schedules: List[Schedule], sort_field: str) -> List[Schedule]:
        """Apply sorting to schedules."""
        if sort_field == "transit":
            return sorted(schedules, key=lambda s: s.transitDays)
        else:  # default to ETD
            return sorted(schedules, key=lambda s: s.etd)
