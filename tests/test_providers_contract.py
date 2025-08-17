import os
import pytest
from backend.app.providers.base import ScheduleFilter, Page
from backend.app.providers.fixtures import FixturesProvider

REQUIRED_KEYS = {
    "origin","destination","etd","eta","vessel","voyage","routingType","transitDays","carrier"
}

def test_fixtures_provider_contract():
    p = FixturesProvider()
    items, total = p.list(ScheduleFilter(), Page())
    assert isinstance(items, list) and isinstance(total, int)
    assert total >= 1
    first = items[0].model_dump()
    assert REQUIRED_KEYS.issubset(first.keys())

@pytest.mark.skipif(not os.getenv("SEAROUTES_API_KEY"), reason="requires SEAROUTES_API_KEY")
def test_searoutes_provider_contract():
    from backend.app.providers.searoutes import SearoutesProvider
    p = SearoutesProvider()
    # Minimal smoke test — Codex should flesh this out using a small query
    items, total = p.list(ScheduleFilter(origin="Port Said", destination="Valencia"), Page(pageSize=5))
    assert isinstance(items, list) and isinstance(total, int)
