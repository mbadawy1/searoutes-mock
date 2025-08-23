# backend/app/routes/ports.py
from fastapi import APIRouter, Query
from typing import Optional, List, Dict, Any
from pathlib import Path
import json

router = APIRouter()

# Expected data layout:
# backend/
#   app/
#     routes/
#       ports.py   <-- this file
#   data/
#     ports.json   <-- put your ports list here

DATA_DIR = Path(__file__).resolve().parents[2] / "data"
PORTS_PATH = DATA_DIR / "ports.json"

# Load once on startup; tiny file so it's fine
def _read_ports() -> List[Dict[str, Any]]:
    if not PORTS_PATH.exists():
        # Minimal fallback to avoid 500s if file is missing
        return [{"name": "Alexandria", "locode": "EGALY", "country": "EG", "countryName": "Egypt", "aliases": ["ALX"]}]
    return json.loads(PORTS_PATH.read_text(encoding="utf-8"))

PORTS = _read_ports()

@router.get("/search")
def ports_search(
    q: str = Query(..., min_length=1, description="Name, alias, LOCODE or country"),
    country: Optional[str] = Query(None, description="2-letter ISO (e.g., EG, MA)"),
    limit: int = Query(15, ge=1, le=50)
):
    ql = q.strip().lower()
    cc = country.upper() if country else None

    results: List[Dict[str, Any]] = []
    for p in PORTS:
        if cc and p.get("country", "").upper() != cc:
            continue
        hay = [p.get("name",""), p.get("locode",""), p.get("countryName","")] + (p.get("aliases") or [])
        hay_l = [h.lower() for h in hay]
        if any(ql in h for h in hay_l):
            # simple score: exact locode match best, then name match
            score = 0
            if ql == p.get("locode","").lower(): score -= 30
            if ql in p.get("name","").lower():  score -= 10
            results.append({"_score": score, **p})

    results.sort(key=lambda r: r["_score"])
    for r in results:
        r.pop("_score", None)

    # Return uniform shape; frontend expects: { items: [...] }
    return {"items": results[:limit]}
