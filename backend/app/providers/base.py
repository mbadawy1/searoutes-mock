from typing import Protocol, List, Optional, Tuple
from pydantic import BaseModel

class Schedule(BaseModel):
    id: str
    origin: str
    destination: str
    etd: str  # ISO8601 UTC
    eta: str  # ISO8601 UTC
    vessel: str
    voyage: str
    routingType: str  # "Direct" | "Transshipment"
    transitDays: int
    carrier: str

class ScheduleFilter(BaseModel):
    origin: Optional[str] = None
    destination: Optional[str] = None
    date_from: Optional[str] = None  # ISO date or datetime
    date_to: Optional[str] = None
    routingType: Optional[str] = None
    carrier: Optional[str] = None

class Page(BaseModel):
    page: int = 1
    pageSize: int = 25

class ScheduleProvider(Protocol):
    def list(self, flt: ScheduleFilter, page: Page) -> Tuple[List[Schedule], int]:
        """Return (items, total) after filtering/pagination."""
        ...
