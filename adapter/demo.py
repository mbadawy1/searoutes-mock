import os, argparse
from searoutes_adapter import SearoutesAdapter

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--from", dest="from_locode", default="EGALY")
    ap.add_argument("--to", dest="to_locode", default="MATNG")
    ap.add_argument("--from-date", default="2025-08-20")
    ap.add_argument("--to-date", default="2025-09-05")
    ap.add_argument("--carrier", dest="carrier_scac", default=None)
    ap.add_argument("--equipment", default="40RF")
    ap.add_argument("--real", action="store_true")
    args = ap.parse_args()

    base_url = os.getenv("SEAROUTES_URL", "https://api.searoutes.com") if args.real else os.getenv("SEAROUTES_URL", "http://localhost:4010")
    adapter = SearoutesAdapter(base_url=base_url, api_key=os.getenv("SEAROUTES_API_KEY"))

    rows = adapter.search(args.from_locode, args.to_locode, args.from_date, args.to_date, args.carrier_scac, args.equipment)
    if not rows:
        print("No itineraries found."); return
    print(f"Found {len(rows)} itineraries for {args.from_locode} → {args.to_locode} ({args.equipment})\n")
    for i, r in enumerate(rows, start=1):
        print(f"{i:02d}. {r['carrier']} [{r['carrierScac']}] | Service {r['serviceId']} | {r['vesselName']} {r['voyage']} (IMO {r['imo']})")
        print(f"    ETD {r['fromLocode']} {r['etd_local']}  →  ETA {r['toLocode']} {r['eta_local']}  | Transit {r['transit_days']} days")
        print("    Legs:")
        for leg in r["legs"]:
            print(f"      {leg['seq']}: {leg['portLocodeFrom']} {leg['timeFrom']} → {leg['portLocodeTo']} {leg['timeTo']} ({leg['transitDays']}d)")
        print()

if __name__ == "__main__":
    main()
