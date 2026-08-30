#!/usr/bin/env python3
"""
Fold LIVE flight quotes into the master table's trip totals.
============================================================

For every sailing whose (airport, out_date, return_date) has a real recorded
Google Flights quote for 2 adults, this script rewrites:

    flight_cost_2        -> "$818 live quote (Google Flights, 2 adults)"
    flight_source        -> airline / stops / observation timestamp
    flight_source_url    -> the exact Google Flights search URL that produced it
    trip_total_2         -> cruise price for 2 + live flight cost
    trip_total_note      -> states the flight leg is a live dated quote
    verification_note    -> appends the quote provenance

Sailings WITHOUT a live quote are left completely untouched and keep their
KAYAK route-average estimate. Nothing is invented or extrapolated: a route
average is never relabelled as a quote, and a quote for one date is never
reused for a different date.

Run `--dry-run` to preview. Re-running is safe and idempotent.
"""
from __future__ import annotations

import csv
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from flight_tracker import (MASTER, ROOT, Itinerary, _airport_of,  # noqa: E402
                            latest, sailings)

JSON_FEED = ROOT / "data" / "cruises.json"
DOCS_JSON = ROOT / "docs" / "data" / "cruises.json"
DOCS_CSV = ROOT / "docs" / "data" / "cruises_master_verified.csv"

LIVE_TAG = "live quote (Google Flights, 2 adults)"
# NOTE: match on the FULL tag. Some legacy rows contain the bare words "live quote
# required" (open-jaw placeholders) and must never be counted as quoted.


def money(n: int) -> str:
    return "$" + format(int(n), ",")


def parse_money(s: str) -> int | None:
    d = re.sub(r"[^0-9]", "", s or "")
    return int(d) if d else None


def main(dry: bool) -> int:
    quotes = latest()
    with MASTER.open(newline="") as f:
        reader = csv.DictReader(f)
        fields = reader.fieldnames
        rows = list(reader)

    changed = 0
    for r in rows:
        if r["status"].startswith("AUDIT"):
            continue
        apt = _airport_of(r["flight_route"])
        if apt is None:
            continue
        key = Itinerary(apt, r["flight_out_date"], r["flight_return_date"]).key
        q = quotes.get(key)
        if not q or q["cheapest_2_adults"] is None:
            continue

        cruise_2 = parse_money(r["price"])
        if cruise_2 is None:
            continue                     # "Not published" -> leave alone
        flight_2 = int(q["cheapest_2_adults"])

        best = q["offers"][0] if q["offers"] else None
        detail = (f"{best['airline']}, {best['stops']}" if best else "cheapest listed itinerary")

        new_flight = f"{money(flight_2)} {LIVE_TAG}"
        if r["flight_cost_2"] == new_flight and LIVE_TAG in r.get("flight_source", ""):
            continue                     # already applied, idempotent

        r["flight_cost_2"] = new_flight
        r["flight_source"] = (
            f"Google Flights live dated search, 2 adults, round trip, USD; cheapest listed "
            f"fare {money(flight_2)} total for 2 ({detail}); observed {q['observed_utc']}")
        r["flight_source_url"] = q["source_url"]
        r["trip_total_2"] = money(cruise_2 + flight_2)
        r["trip_total_note"] = (
            "Cruise snapshot (2 x lead-in cabin) + LIVE dated Google Flights fare for 2 adults "
            "(arrive 1 day before embarkation, return 1 day after disembarkation). Airfare is a "
            "real quote observed on the date shown, not a route average; fares move, so reconfirm "
            "before booking.")
        note = r["verification_note"].split(" FLIGHT:")[0]
        r["verification_note"] = (
            note + f" FLIGHT: airfare replaced with a live Google Flights quote for 2 adults "
            f"({money(flight_2)} round trip, {detail}) observed {q['observed_utc']} for "
            f"SFO->{apt} {r['flight_out_date']} / return {r['flight_return_date']}; the page "
            f"explicitly stated 'for 2 adults'.")
        changed += 1

    print(f"sailings updated with live quotes: {changed}")
    if dry:
        print("(dry run - nothing written)")
        return 0

    with MASTER.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)
    with JSON_FEED.open("w") as f:
        json.dump(rows, f, indent=1, ensure_ascii=False)
    DOCS_JSON.write_bytes(JSON_FEED.read_bytes())
    DOCS_CSV.write_bytes(MASTER.read_bytes())
    print("wrote master CSV, JSON feed and both docs/ mirrors")
    return 0


if __name__ == "__main__":
    raise SystemExit(main("--dry-run" in sys.argv))
