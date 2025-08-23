from typing import Protocol, List, Optional, Tuple
from pydantic import BaseModel, Field

from ..models.schedule import Schedule


class ScheduleFilter(BaseModel):
    origin: Optional[str] = None
    destination: Optional[str] = None
    date_from: Optional[str] = Field(default=None, alias="from")
    date_to: Optional[str] = Field(default=None, alias="to")
    equipment: Optional[str] = None
    routingType: Optional[str] = None
    carrier: Optional[str] = None
    sort: Optional[str] = "etd"

    model_config = {"validate_by_name": True, "populate_by_name": True}


class Page(BaseModel):
    total: int = 0
    page: int = 1
    pageSize: int = 50


class ScheduleProvider(Protocol):
    def list(self, flt: ScheduleFilter, page: Page) -> Tuple[List[Schedule], Page]:
        """Return (items, page_meta) after filtering/pagination."""
        ...
