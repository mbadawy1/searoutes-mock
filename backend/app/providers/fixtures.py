import json
from pathlib import Path
from datetime import datetime, timezone
from typing import List, Tuple

from .base import Schedule, ScheduleFilter, Page, ScheduleProvider

class FixturesProvider(ScheduleProvider):
    def __init__(self, path: str = "data/fixtures/schedules.sample.json") -> None:
        self.path = Path(path)

    def _load(self) -> List[Schedule]:
        data = json.loads(self.path.read_text(encoding="utf-8"))
        return [Schedule(**item) for item in data]

    def list(self, flt: ScheduleFilter, page: Page) -> Tuple[List[Schedule], int]:
        items = self._load()

        def dt(s: str) -> datetime:
            # robust parse for Z dates
            return datetime.fromisoformat(s.replace("Z", "+00:00")).astimezone(timezone.utc)

        # Filtering
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
        if flt.date_from:
            df = dt(flt.date_from)
            items = [x for x in items if dt(x.etd) >= df]
        if flt.date_to:
            dt_to = dt(flt.date_to)
            items = [x for x in items if dt(x.etd) <= dt_to]

        # Sort by ETD asc
        items.sort(key=lambda x: dt(x.etd))

        total = len(items)
        start = max(0, (page.page - 1) * page.pageSize)
        end = start + page.pageSize
        return items[start:end], total
