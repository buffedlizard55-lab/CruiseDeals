#!/usr/bin/env python3
"""Print dated flight-search links for every in-window sailing.

2 adults, flying SFO -> port the day BEFORE embarkation and port -> SFO the
day AFTER disembarkation (open-jaw printed for voyages ending in Vancouver).
Use these to check live fares and track price movement over time.

Usage:
    python3 scripts/flight_search.py              # all rows
    python3 scripts/flight_search.py LA-64 SD-52  # selected rows
"""
import csv, sys, os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CSV = os.path.join(ROOT, "data", "cruises_master_verified.csv")

def links(r):
    out, back = r["flight_out_date"], r["flight_return_date"]
    route = r["flight_route"]
    if "No flight required" in route:
        return ["    (no flight needed — home-port departure)"]
    if "YVR" in route:  # open jaw: SFO->SAN one-way, then YVR->SFO one-way
        return [
            f"    Google Flights  SFO->SAN {out} (one-way, 2 adults): "
            f"https://www.google.com/travel/flights?q=Flights%20from%20SFO%20to%20SAN%20on%20{out}%20oneway%202%20adults",
            f"    Google Flights  YVR->SFO {back} (one-way, 2 adults): "
            f"https://www.google.com/travel/flights?q=Flights%20from%20YVR%20to%20SFO%20on%20{back}%20oneway%202%20adults",
            f"    KAYAK tracker   YVR-SFO: {r['flight_source_url']}",
        ]
    dest = "LAX" if "LAX" in route else "SAN"
    return [
        f"    Google Flights  SFO->{dest} {out} / back {back} (2 adults): {r['flight_search_url']}",
        f"    KAYAK tracker   {dest} dates: "
        f"https://www.kayak.com/flights/SFO-{dest}/{out}/{back}/2adults?sort=bestflight_a",
        f"    Route average   source: {r['flight_source_url']}",
    ]

def main(sel):
    with open(CSV, newline="") as f:
        rows = [r for r in csv.DictReader(f) if not r["status"].startswith("OUT OF WINDOW")]
    for r in rows:
        if sel and r["id"] not in sel:
            continue
        print(f"{r['id']}  {r['name']}  ({r['date']}, {r['duration']}, {r['port']})")
        print(f"    estimate: {r['flight_cost_2']} — {r['flight_source']}")
        for line in links(r):
            print(line)
        print()

if __name__ == "__main__":
    main(sys.argv[1:])
