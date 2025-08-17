import os, requests
from typing import List, Dict, Any
from dateutil import parser as dtparser

class SearoutesAdapter:
    def __init__(self, base_url: str | None = None, api_key: str | None = None, timeout: int = 30):
        self.base_url = base_url or os.getenv("SEAROUTES_URL", "http://localhost:4010")
        self.api_key  = api_key  or os.getenv("SEAROUTES_API_KEY")
        self.timeout  = timeout
    def search(self, from_locode: str, to_locode: str, from_date: str | None = None, to_date: str | None = None, carrier_scac: str | None = None, equipment: str | None = None) -> List[Dict[str, Any]]:
        params = {"fromLocode": from_locode, "toLocode": to_locode}
        if from_date: params["fromDate"] = from_date
        if to_date:   params["toDate"]   = to_date
        if carrier_scac: params["carrierScac"] = carrier_scac
        if equipment: params["equipment"] = equipment
        headers = {}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        r = requests.get(f"{self.base_url}/itinerary/v2/execution", params=params, headers=headers, timeout=self.timeout)
        r.raise_for_status()
        payload = r.json()
        return [self._map_item(item) for item in payload.get("items", [])]
    def _map_item(self, item: Dict[str, Any]) -> Dict[str, Any]:
        features = item.get("features", [])
        legs = []
        for i, f in enumerate(features, start=1):
            p = f.get("properties", {})
            legs.append({
                "seq": i,
                "portLocodeFrom": p.get("departure", {}).get("locode"),
                "timeFrom": p.get("departure", {}).get("time"),
                "portLocodeTo": p.get("arrival", {}).get("locode"),
                "timeTo": p.get("arrival", {}).get("time"),
                "carrier": p.get("carrier"),
                "carrierScac": p.get("carrierScac"),
                "serviceId": p.get("serviceId"),
                "vesselName": (p.get("vessel") or {}).get("name"),
                "imo": (p.get("vessel") or {}).get("imo"),
                "voyage": (p.get("vessel") or {}).get("voyage"),
                "transitDays": p.get("transitTimeDays"),
            })
        total_transit_days = sum(l.get("transitDays") or 0 for l in legs)
        first_dep = legs[0]["timeFrom"] if legs else None
        last_arr  = legs[-1]["timeTo"]  if legs else None
        return {
            "hash": item.get("hash"),
            "carrier": legs[0]["carrier"] if legs else None,
            "carrierScac": legs[0]["carrierScac"] if legs else None,
            "serviceId": legs[0]["serviceId"] if legs else None,
            "vesselName": legs[0]["vesselName"] if legs else None,
            "imo": legs[0]["imo"] if legs else None,
            "voyage": legs[0]["voyage"] if legs else None,
            "fromLocode": legs[0]["portLocodeFrom"] if legs else None,
            "toLocode": legs[-1]["portLocodeTo"] if legs else None,
            "etd_local": first_dep,
            "eta_local": last_arr,
            "legs": legs,
            "transit_days": total_transit_days
        }
