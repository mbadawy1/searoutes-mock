import json
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Tuple

from ..models.schedule import Schedule
from .base import Page, ScheduleFilter, ScheduleProvider


class FixturesProvider(ScheduleProvider):
    def __init__(self, path: str = "data/fixtures/schedules.sample.json") -> None:
        # Make path relative to project root
        project_root = Path(__file__).parent.parent.parent.parent
        self.path = project_root / path

    def _load(self) -> List[Schedule]:
        data = json.loads(self.path.read_text(encoding="utf-8"))
        # Handle missing fields by providing defaults
        items = []
        for item in data:
            # Add missing fields with defaults if not present
            if "imo" not in item:
                item["imo"] = None
            if "service" not in item:
                item["service"] = None
            if "equipment" not in item:
                item["equipment"] = None
            items.append(Schedule(**item))
        return items

    def list(self, flt: ScheduleFilter, page: Page) -> Tuple[List[Schedule], Page]:
        items = self._load()

        def dt(s: str) -> datetime:
            # robust parse for Z dates
            return datetime.fromisoformat(s.replace("Z", "+00:00")).astimezone(timezone.utc)

        # Filtering (for now, Task 3 says ignore filters, but existing code has them)
        if flt.origin:
            q = flt.origin.lower()
            items = [x for x in items if q in x.origin.lower()]
        if flt.destination:
            q = flt.destination.lower()
            items = [x for x in items if q in x.destination.lower()]
        if flt.routingType:
            items = [x for x in items if x.routingType.lower() == flt.routingType.lower()]
        if flt.carrier:
            q = flt.carrier.lower()
            items = [x for x in items if q in x.carrier.lower()]
        if flt.equipment:
            items = [
                x for x in items if x.equipment and x.equipment.lower() == flt.equipment.lower()
            ]
        if flt.date_from:
            df = dt(flt.date_from)
            items = [x for x in items if dt(x.etd) >= df]
        if flt.date_to:
            dt_to = dt(flt.date_to)
            items = [x for x in items if dt(x.etd) <= dt_to]

        # Sort by specified field (default: ETD asc)
        if flt.sort == "transit":
            items.sort(key=lambda x: x.transitDays)
        else:  # Default to "etd" or any other value
            items.sort(key=lambda x: dt(x.etd))

        total = len(items)
        start = max(0, (page.page - 1) * page.pageSize)
        end = start + page.pageSize

        # Return page metadata with total populated
        page_meta = Page(total=total, page=page.page, pageSize=page.pageSize)
        return items[start:end], page_meta
