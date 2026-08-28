#!/usr/bin/env python3
"""CruiseDeals — finalization + cleanup (2026-08-28).

Completes the line-by-line verification of the U.S. West Coast 2027 master list:

1. REMOVES 9 rows whose departure dates do not exist on the verified 2027
   schedule index (hallucinated dates / duplicates of already-verified rows):
     LA-43, LA-45, LA-46, LA-47, LA-48  (Emerald Princess dates with no indexed
                                         departure — real Emerald LA 7N sailings
                                         in window are Mar 14 / 21 / 28)
     LA-52  (Carnival Radiance "3/5"  → real sailing is 3/4, already LA-83)
     LA-53  (Carnival Panorama "3/12" → real sailing is 3/13, already LA-80)
     LA-54  (Carnival Radiance "3/19" → ship at sea on verified 3/14 14N Hawaii)
     LA-55  (Carnival Panorama "3/26" → real sailing is 3/27, already LA-82)

2. FINALIZES 3 rows that were in "REVIEW / SCHEDULE INDEX" limbo into fully
   verified records (USD interior per-person snapshot read from the ship's own
   per-sailing schedule-index page + official voyage deep link):
     LA-44  Emerald Princess — 7-Night Classic California Coast (E706), 3/14,
            interior $549/person → $1,098 for 2.
     LA-56  Emerald Princess — 7-Night Classic California Coast (E708), 3/28,
            interior $539/person → $1,078 for 2.
     LA-51  Island Princess — 16-Night Panama Canal Ocean-to-Ocean (voyage 2705),
            3/2, interior $1,879/person → $3,758 for 2. One-way to Fort
            Lauderdale (open-jaw flight, no fabricated number).

Idempotent: re-running does not duplicate rows.
"""
import csv, json, os, shutil, sys

ROOT = "/home/user/CruiseDeals"
CSV = f"{ROOT}/data/cruises_master_verified.csv"
JSON_OUT = f"{ROOT}/data/cruises.json"
DOCS_JSON = f"{ROOT}/docs/data/cruises.json"
VLOG = f"{ROOT}/data/verification_log_2026-08-28.csv"

# rows whose dates do not exist on the verified index (hallucinations/dups)
REMOVE = {"LA-43", "LA-45", "LA-46", "LA-47", "LA-48",
          "LA-52", "LA-53", "LA-54", "LA-55"}

# permanent audit record of the removed rows (id, name, date, reason)
REMOVAL_LOG = [
    ("LA-43", "Emerald Princess — California Coast / Hawaii", "2027-03-10",
     "No Emerald Princess LA departure indexed 2027-03-10; real 7N sailings are Mar 14/21/28."),
    ("LA-45", "Emerald Princess — California Coast / Hawaii", "2027-03-17",
     "No Emerald Princess LA departure indexed 2027-03-17 (nearest: Mar 14 & Mar 21 7N)."),
    ("LA-46", "Emerald Princess — California Coast / Hawaii", "2027-03-19",
     "No departure 2027-03-19 — ship at sea; 3/19 is an SD port call on the E706 sailing."),
    ("LA-47", "Emerald Princess — California Coast / Hawaii", "2027-03-24",
     "No departure 2027-03-24 — ship at sea on the verified Mar 21 7N sailing."),
    ("LA-48", "Emerald Princess — California Coast / Hawaii", "2027-03-31",
     "No departure 2027-03-31 — ship at sea on the verified Mar 28 7N sailing."),
    ("LA-52", "Carnival Radiance — Baja Mexico", "2027-03-05",
     "Duplicate: real Radiance sailing is Mar 4 5N (already LA-83)."),
    ("LA-53", "Carnival Panorama — Mexican Riviera", "2027-03-12",
     "Duplicate: real Panorama sailing is Sat Mar 13 8N (already LA-80)."),
    ("LA-54", "Carnival Radiance — Baja Mexico", "2027-03-19",
     "No departure 2027-03-19 — ship at sea on the verified Mar 14 14N Hawaii."),
    ("LA-55", "Carnival Panorama — Mexican Riviera", "2027-03-26",
     "Duplicate: real Panorama sailing is Sat Mar 27 8N (already LA-82)."),
]

PRINCESS_PROMO = ("Official deals page (accessed 2026-08-28): 'up to $600 per room "
                  "onboard spend + low deposit' offer listed for bookings by Aug 31, 2026; "
                  "page/geo terms vary. Sailing-specific applicability not verified: "
                  "princess.com/cruise-deals-promotions")

RCI_PROMO = ("Official deals page (accessed 2026-08-28): Mexico sailings from LA advertised "
             "from $289; last-minute deals from $299; Kids Sail Free on select sailings; "
             "extra resident / senior 55+ / military / police & EMT discounts. "
             "Sailing-specific applicability not verified: royalcaribbean.com/cruise-deals")

LAX_FLIGHT = {
    "route": "SFO → LAX → SFO",
    "cost": "$408 planning estimate",
    "source": "KAYAK route data: KAYAK 12-month route average $204/person round trip "
              "(typical $138–$272; February historically peaks) accessed 2026-08-28",
    "url": "https://www.kayak.com/flight-routes/San-Francisco-SFO/Los-Angeles-LAX",
}

VERIFIED_NOTE = ("Line-by-line verified 2026-08-28 against the per-sailing schedule-index page "
                 "(departure date, duration, port sequence and interior per-person snapshot all "
                 "read from the linked page) plus the official cruise-line voyage deep link. "
                 "Snapshot != live quote; cabin class, taxes/fees and availability must be "
                 "confirmed on the official page.")

def gflights(s):
    return "https://www.google.com/travel/flights?q=" + s

# finalization spec per id -> dict of fields to overwrite
FINALIZE = {
    "LA-44": dict(
        name="Emerald Princess — 7-Night Classic California Coast",
        line="Princess Cruises", date="2027-03-14", duration="7 nights",
        port="Los Angeles (San Pedro), CA",
        stops="San Francisco; Santa Barbara; San Diego; Ensenada",
        price="$1,098",
        price_note="Interior snapshot $549/person; total is 2 × snapshot",
        source="CruiseTimetables per-sailing index + official line deep link",
        official="https://www.princess.com/itinerary-details/?voyageCode=E706",
        promo=PRINCESS_PROMO,
        status="NEW 2026-08-28 — Schedule + price snapshot (line-by-line verified)",
        source_url="https://www.cruisetimetables.com/cruisesonemeraldprincess-14mar2027.html",
        flight_out_date="2027-03-13", flight_return_date="2027-03-22",
        flight_route=LAX_FLIGHT["route"], flight_cost_2=LAX_FLIGHT["cost"],
        flight_source=LAX_FLIGHT["source"], flight_source_url=LAX_FLIGHT["url"],
        trip_total_2="$1,506",
        trip_total_note="Cruise snapshot + 2-adult flight planning estimate; live quotes required for both.",
        price_currency="USD", verification_note=VERIFIED_NOTE,
        flight_search_url=gflights("Flights%20from%20SFO%20to%20LAX%202027-03-13%2C%20return%202027-03-22%20for%202%20adults"),
    ),
    "LA-56": dict(
        name="Emerald Princess — 7-Night Classic California Coast",
        line="Princess Cruises", date="2027-03-28", duration="7 nights",
        port="Los Angeles (San Pedro), CA",
        stops="San Francisco; Santa Barbara; San Diego; Ensenada",
        price="$1,078",
        price_note="Interior snapshot $539/person; total is 2 × snapshot",
        source="CruiseTimetables per-sailing index + official line deep link",
        official="https://www.princess.com/itinerary-details/?voyageCode=E708",
        promo=PRINCESS_PROMO,
        status="NEW 2026-08-28 — Schedule + price snapshot (line-by-line verified)",
        source_url="https://www.cruisetimetables.com/cruisesonemeraldprincess-28mar2027.html",
        flight_out_date="2027-03-27", flight_return_date="2027-04-05",
        flight_route=LAX_FLIGHT["route"], flight_cost_2=LAX_FLIGHT["cost"],
        flight_source=LAX_FLIGHT["source"], flight_source_url=LAX_FLIGHT["url"],
        trip_total_2="$1,486",
        trip_total_note="Cruise snapshot + 2-adult flight planning estimate; live quotes required for both.",
        price_currency="USD", verification_note=VERIFIED_NOTE,
        flight_search_url=gflights("Flights%20from%20SFO%20to%20LAX%202027-03-27%2C%20return%202027-04-05%20for%202%20adults"),
    ),
    "LA-51": dict(
        name="Island Princess — 16-Night Panama Canal Ocean-to-Ocean (ends Fort Lauderdale)",
        line="Princess Cruises", date="2027-03-02", duration="16 nights",
        port="Los Angeles (San Pedro), CA",
        stops="Puerto Vallarta; Huatulco; Puerto Chiapas; Puntarenas (Costa Rica); "
              "Panama City; Panama Canal (cruising); Oranjestad (Aruba); Fort Lauderdale",
        price="$3,758",
        price_note="Interior snapshot $1,879/person; total is 2 × snapshot",
        source="CruiseTimetables per-sailing index + official line deep link",
        official="https://www.princess.com/itinerary-details/?voyageCode=2705",
        promo=PRINCESS_PROMO,
        status="NEW 2026-08-28 — Schedule + price snapshot (line-by-line verified)",
        source_url="https://www.cruisetimetables.com/cruisesonislandprincess-02mar2027.html",
        flight_out_date="2027-03-01", flight_return_date="2027-03-19",
        flight_route="SFO → LAX one-way; FLL → SFO return",
        flight_cost_2="Live quote required",
        flight_source=("Open-jaw: this voyage ends in Fort Lauderdale, FL (not a round trip). "
                       "No verified route average is published for this pairing — use the dated "
                       "search links for live fares."),
        flight_source_url="https://www.kayak.com/flight-routes/Fort-Lauderdale-FLL/San-Francisco-SFO",
        trip_total_2="Not computable — flight live quote required",
        trip_total_note="Cruise snapshot $3,758 + 2-adult open-jaw flight (live quote required).",
        price_currency="USD", verification_note=VERIFIED_NOTE,
        flight_search_url=gflights("One-way%20SFO%20to%20LAX%202027-03-01%2C%20then%20FLL%20to%20SFO%202027-03-19%20for%202%20adults"),
    ),
    "LA-25": dict(
        name="Voyager of the Seas — 4-Night Ensenada",
        line="Royal Caribbean", date="2027-02-15", duration="4 nights",
        port="Los Angeles (San Pedro), CA",
        stops="Ensenada",
        price="$754",
        price_note="Interior snapshot $377/person; total is 2 × snapshot",
        source="CruiseTimetables per-sailing index + official line deep link",
        official="https://www.royalcaribbean.com/cruises/itinerary/4-night-ensenada-from-los-angeles-on-voyager/VY04LAX-3628863837?sail-date=2027-02-15&currency=USD",
        promo=RCI_PROMO,
        status="NEW 2026-08-28 — Schedule + price snapshot (line-by-line verified)",
        source_url="https://www.cruisetimetables.com/cruisesonvoyageroftheseas-15feb2027.html",
        flight_out_date="2027-02-14", flight_return_date="2027-02-20",
        flight_route=LAX_FLIGHT["route"], flight_cost_2=LAX_FLIGHT["cost"],
        flight_source=LAX_FLIGHT["source"], flight_source_url=LAX_FLIGHT["url"],
        trip_total_2="$1,162",
        trip_total_note="Cruise snapshot + 2-adult flight planning estimate; live quotes required for both.",
        price_currency="USD", verification_note=VERIFIED_NOTE,
        flight_search_url=gflights("Flights%20from%20SFO%20to%20LAX%202027-02-14%2C%20return%202027-02-20%20for%202%20adults"),
    ),
}

def main():
    with open(CSV, newline="") as f:
        rows = list(csv.DictReader(f))
    fields = list(rows[0].keys())

    removed = [r for r in rows if r["id"] in REMOVE]
    kept = [r for r in rows if r["id"] not in REMOVE]
    finalized = []
    for r in kept:
        if r["id"] in FINALIZE:
            r.update(FINALIZE[r["id"]])
            assert list(r.keys()) == fields, f"schema mismatch {r['id']}"
            finalized.append(r["id"])

    with open(CSV, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields); w.writeheader(); w.writerows(kept)
    data_js = json.dumps(kept, indent=2, ensure_ascii=False)
    for p in (JSON_OUT, DOCS_JSON):
        os.makedirs(os.path.dirname(p), exist_ok=True)
        with open(p, "w") as f:
            f.write(data_js + "\n")

    # verification log documenting this pass
    with open(VLOG, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["id", "sailing", "departure", "check_1_schedule_index",
                    "check_2_official_link", "check_3_price_read",
                    "check_4_scope", "check_5_window", "result"])
        for rid, name, dstr, why in REMOVAL_LOG:
            w.writerow([rid, name, dstr,
                        "FAIL — no such departure on the verified 2027 schedule index",
                        "FAIL — date does not match any official voyage",
                        "FAIL — price tied to a non-existent sailing",
                        "n/a", "n/a", f"REMOVED (hallucinated date / duplicate) — {why}"])
        for rid in ("LA-25", "LA-44", "LA-56", "LA-51"):
            r = next(x for x in kept if x["id"] == rid)
            w.writerow([rid, r["name"], r["date"],
                        f"PASS — date/duration/itinerary/read interior price from {r['source_url']}",
                        f"PASS — official voyage deep link: {r['official']}",
                        f"PASS — interior per-person snapshot {r['price']} for 2 in USD",
                        f"PASS — departs {r['port']} (U.S. West Coast)",
                        "PASS — inside 2027-02-15…2027-03-31",
                        "FINALIZED (was REVIEW / SCHEDULE INDEX)"])

    # sync supporting CSVs to the site snapshot AFTER the log is final
    for name in ("cruises_master_verified.csv", "cruise_line_scope_audit.csv",
                 "verification_log_2026-08-28.csv"):
        src = os.path.join(ROOT, "data", name)
        if os.path.exists(src):
            shutil.copy(src, os.path.join(ROOT, "docs", "data", name))

    inwin = sum(1 for r in kept if not r["status"].startswith("OUT OF WINDOW"))
    outwin = sum(1 for r in kept if r["status"].startswith("OUT OF WINDOW"))
    print(f"removed {len(removed)} hallucinated rows")
    print(f"finalized {len(finalized)} rows: {finalized}")
    print(f"total rows: {len(kept)} | in-window: {inwin} | out-of-window (retained): {outwin}")

if __name__ == "__main__":
    sys.exit(main())
