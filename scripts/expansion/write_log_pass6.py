#!/usr/bin/env python3
"""Write the pass-6 verification/evidence log."""
import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MASTER = ROOT / "data" / "cruises_master_verified.csv"
OUT = ROOT / "data" / "verification_log_2026-08-30_national_expansion_pass6.csv"

COLS = ["id", "port", "ship", "date", "duration_nights", "lead_in_pp_usd", "cruise_total_2",
        "flight_route", "flight_2", "trip_total_2", "official_deep_link", "schedule_source",
        "independent_crosscheck_or_note", "result"]

BASIS = ("Primary source read line by line: cruisetimetables PER-DAY from-port 2027 page "
         "(official cruise-line fare feed) + the official cruise-line deep link carried on "
         "that same page; targeted by a per-port date-coverage audit of all 45 in-window "
         "dates; dedup-checked against master by (port, ship, date, nights)")

# Sailing-specific notes layered on top of BASIS.
NOTES = {
    "GAL6-01": ("PRICE CONVENTION CORRECTED. The cruisetimetables feed publishes Disney fares "
                "as a PER-STATEROOM total for 2 guests, not per person. Independent cross-check: "
                "icruise.com Disney Magic March 2027 itinerary lists 'Mar 21, 2027 ... $1,480 "
                "Interior Stateroom (double occupancy)' and cdoe.cruiseone.com lists "
                "'March 21-26, 2027 Interior $1,480 / $296 per night' - exactly half the $2,961 "
                "in the feed, which magicguides.com quotes as the party-of-two 'From' price. "
                "Row therefore stores $1,480 pp and a $2,960 two-person cruise total. MATCH"),
    "MIA6-16": ("Independent cross-check of the same-day/different-duration pair: HollandAmerica "
                "official page for cruise code U724A (14-DAY EASTERN & SOUTHERN CARIBBEAN: KEY "
                "WEST & ABC ISLANDS) confirms SailingDate 2027-03-24 from MIA, and cruiseweb.com "
                "separately lists BOTH a 14-night (Mar 24) and the short Zuiderdam Miami "
                "getaway - two distinct bookable products, not a duplicate. MATCH"),
    "MIA6-15": ("Independent cross-check: southamptoncruisecentre.com lists Zuiderdam "
                "'24 Mar 2027, 4 nights, Miami - Key West - At Sea - Half Moon Cay - Miami', "
                "matching the captured port sequence exactly. MATCH"),
    "MIA6-03": ("Independent cross-check: cruisebound.com/sailing/81527 confirms Carnival Magic "
                "6-day Eastern Caribbean departing Miami 28 Feb 2027 returning 6 Mar with "
                "Celebration Key / Amber Cove / Grand Turk. NOTE PRICE VOLATILITY: feed Interior "
                "$439 pp vs cruisetimetables ship page $467, icruise $408 and cruisesonly $403 - "
                "schedule verified, price indicative only"),
    "FLL6-04": ("Independent cross-check: princess.com itinerary page for the 6-Day Eastern "
                "Caribbean with Turks & Caicos & Celebration Key lists 'Sun, Feb 28, 2027' among "
                "available sailings with ports Ft. Lauderdale / Celebration Key / Grand Turk / "
                "Nassau, and cruisecompete.com lists the same product '2027 Sails: ... Feb 28'. "
                "MATCH (cruisecritic shows $699 pp vs feed $449 - price indicative only)"),
    "FLL6-05": ("Independent cross-check: cruisecompete.com Regal Princess listings show a "
                "'14 Night - Southern / Eastern Caribbean Adventurer with Celebration Key' "
                "sailing Feb 28 2027 from Fort Lauderdale, distinct from the 6-night G710 "
                "departing the same day. MATCH"),
}

FLAGS = [
    ["FLAG-P6-01", "Miami, FL", "Norwegian Jewel", "2027-03-15", "4", "", "", "", "", "", "",
     "https://www.cruisetimetables.com/cruises-from-miami-florida-2027.html",
     "'4 Night Keeping The Blues Alive At Sea XII' is a full-ship CHARTER (bluesaliveatsea.com); "
     "the fare feed publishes 'NA' for every cabin grade - no public interior fare exists",
     "EXCLUDED - charter"],
    ["FLAG-P6-02", "Miami, FL", "Azamara Journey", "2027-03-29", "37 / 12", "", "", "", "", "", "",
     "https://www.cruisetimetables.com/cruises-from-miami-florida-2027.html",
     "Both 29 Mar Azamara Journey voyages are OPEN JAW (37N ending Chioggia/Venice, 12N ending "
     "Lisbon). A single SFO round-trip airfare cannot honestly be applied",
     "EXCLUDED - open jaw"],
    ["FLAG-P6-03", "Miami, FL", "Explora III", "2027-03-29", "7", "", "", "", "", "", "",
     "https://www.cruisetimetables.com/cruises-from-miami-florida-2027.html",
     "7N Miami -> San Juan is OPEN JAW. (The 28 Feb 14N round-trip Explora III IS included as "
     "MIA6-05, flagged ultra-luxury: lead-in $9,675 per guest)",
     "EXCLUDED - open jaw"],
    ["FLAG-P6-04", "Miami, FL", "Carnival Firenze", "2027-03-22", "13", "", "", "", "", "", "",
     "https://www.cruisetimetables.com/cruises-from-miami-florida-2027.html",
     "13N Southern Caribbean departs 22 Mar 2027 (in window) but RETURNS 4 Apr 2027. Eligible "
     "under the departure-date rule; captured but not added this pass - surfaced for review",
     "FLAGGED - returns after window"],
    ["FLAG-P6-05", "Miami, FL", "Margaritaville at Sea Beachcomber", "2027-03-15", "5", "429",
     "$858", "SFO -> MIA -> SFO", "$844 planning estimate", "$1,702",
     "https://margaritavilleatsea.com/",
     "https://www.cruisetimetables.com/cruises-from-miami-florida-2027.html",
     "NEW LINE this pass. IRREGULARITY: the fare feed carries only a generic homepage link, not "
     "a per-sailing deep link, so the itinerary/price cannot be deep-link verified. Schedule and "
     "Inside $429 pp read line by line from the per-day page. Added but flagged",
     "ADDED - flagged, no deep link"],
    ["FLAG-P6-06", "Miami, FL", "Explora III", "2027-02-28", "14", "9675", "$19,350",
     "SFO -> MIA -> SFO", "$844 planning estimate", "$20,194",
     "https://www.explorajourneys.com/us/en/destinations-globe/car/journeys/miamia-14-v10?id-journey=EL20270228MIAMIA&id-offer=airinclusa",
     "https://www.cruisetimetables.com/cruises-from-miami-florida-2027.html",
     "ULTRA-LUXURY outlier: lead-in 'From $9,675 per guest'. Far outside the mainstream/"
     "contemporary price band; retained for completeness but flagged so it is not read as a deal",
     "ADDED - flagged ultra-luxury"],
    ["FLAG-P6-07", "Fort Lauderdale, FL", "(various)", "2027-02-28", "", "", "", "", "", "", "",
     "https://www.cruisetimetables.com/cruises-from-fort-lauderdale-florida-2027.html",
     "DEDUP GUARD FIRED: Celebrity Beyond 7N, Celebrity Eclipse 12N, Legend of the Seas 6N and "
     "Nieuw Amsterdam 21N (all FLL 28 Feb 2027) were already in the master from pass 4 "
     "(FLL4-05/06/07/08). All four candidates were dropped before writing",
     "DEDUP - 4 candidates removed"],
    ["FLAG-P6-08", "Tampa, FL", "(various)", "various", "", "", "", "", "", "", "",
     "https://www.cruisetimetables.com/cruises-from-tampa-florida-2027.html",
     "DEDUP GUARD FIRED: all 10 Tampa candidates captured this pass (20/27 Feb, 6/13 Mar) were "
     "already in the master. A corrected date-coverage re-audit confirmed those Tampa dates were "
     "already held; the whole Tampa block was removed before writing",
     "DEDUP - 10 candidates removed"],
    ["FLAG-P6-09", "Fort Lauderdale, FL", "(none)", "2027-03-11", "", "", "", "", "", "", "",
     "https://www.cruisetimetables.com/cruises-from-fort-lauderdale-florida-2027.html",
     "ZERO-SAILING DAY: the 11 Mar 2027 day URL redirects to the port landing page, the site's "
     "signal for no departures", "NO SAILINGS"],
    ["FLAG-P6-10", "Galveston, TX", "(none)", "2027-03-04", "", "", "", "", "", "", "",
     "https://www.cruisetimetables.com/cruises-from-galveston-texas-2027.html",
     "ZERO-SAILING DAY: the 4 Mar 2027 day URL redirects to the port landing page",
     "NO SAILINGS"],
    ["FLAG-P6-11", "New Orleans, LA", "(none)", "2027-03-08", "", "", "", "", "", "", "",
     "https://www.cruisetimetables.com/cruises-from-new-orleans-louisiana-2027.html",
     "ZERO-SAILING DAY: the 8 Mar 2027 day URL redirects to the port landing page",
     "NO SAILINGS"],
    ["FLAG-P6-12", "(all)", "(same-day pairs)", "various", "", "", "", "", "", "", "",
     "https://www.cruisetimetables.com/",
     "Six same (port, ship, date) pairs with DIFFERENT durations retained as distinct bookable "
     "voyages: Zuiderdam MIA 3/24 4N+14N; MSC Seaside MIA 3/15, 3/22, 3/29 each 4N+7N; "
     "Nieuw Statendam FLL 2/28 7N+14N; Regal Princess FLL 2/28 6N+14N",
     "RETAINED - distinct voyages"],
]


def main():
    rows = list(csv.DictReader(MASTER.open(newline="")))
    new = [r for r in rows if r["id"].split("-")[0].endswith("6")]
    assert len(new) == 50, len(new)
    out = []
    for r in new:
        pp = r["price_note"].split("$")[1].split("/")[0].replace(",", "")
        note = BASIS
        if r["id"] in NOTES:
            note = BASIS + " || " + NOTES[r["id"]]
        out.append({
            "id": r["id"], "port": r["port"], "ship": r["name"].split("\u2014")[0].strip(),
            "date": r["date"], "duration_nights": r["duration"].split()[0],
            "lead_in_pp_usd": pp, "cruise_total_2": r["price"],
            "flight_route": r["flight_route"], "flight_2": r["flight_cost_2"],
            "trip_total_2": r["trip_total_2"], "official_deep_link": r["official"],
            "schedule_source": r["source_url"], "independent_crosscheck_or_note": note,
            "result": "VERIFIED",
        })
    with OUT.open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(COLS)
        for o in out:
            w.writerow([o[c] for c in COLS])
        for fl in FLAGS:
            w.writerow(fl)
    print(f"wrote {OUT.name}: {len(out)} verified + {len(FLAGS)} flag/annotation rows")


if __name__ == "__main__":
    main()
