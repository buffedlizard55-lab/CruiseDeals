#!/usr/bin/env python3
"""Emit the pass-3 per-row verification log from the rows actually written to master."""
import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MASTER = ROOT / "data" / "cruises_master_verified.csv"
LOG = ROOT / "data" / "verification_log_2026-08-30_national_expansion_pass3.csv"

# Independent (second-source) cross-checks actually performed this pass.
XCHECK = {
    ("Jacksonville, FL", "Carnival Elation", "2027-03-20"):
        "jacksonvillecruiseguide.com Carnival page lists the 5-day Princess Cays + Celebration Key "
        "itinerary with a 2027 departure on March 20 - MATCH (date, duration, port sequence)",
    ("Mobile, AL", "Carnival Spirit", "2027-03-20"):
        "cruisecheap.com sailing 14114690: Carnival Spirit 9 Night Western Caribbean, departs Sat "
        "Mar 20 2027, returns Mon Mar 29 2027, Cozumel/Roatan(Mahogany Bay)/Georgetown/Montego Bay, "
        "Interior $869 incl. taxes vs $1,024 cruise-fare-only feed - itinerary & dates MATCH; "
        "price differs because cruisecheap quotes a tax-inclusive promo rate (noted, not merged)",
    ("Jacksonville, FL", "Norwegian Dawn", "2027-03-30"):
        "cruisebound.com sailing 116213 + cruiseweb.com + jacksonvillecruiseguide.com all list "
        "Norwegian Dawn 5-Night Bahamas ex-Jacksonville departing Mar 30 2027 with Key West & "
        "Great Stirrup Cay - MATCH (date, duration, port sequence)",
    ("Miami, FL", "Carnival Magic", "2027-03-20"):
        "cruisesheet.com carnival-magic-8-night-miami-roundtrip-march-20-2027: 8 night round trip "
        "Miami, Celebration Key / Oranjestad Aruba / Willemstad Curacao, returns Mar 28 2027, "
        "Inside $749 vs feed Interior $773 - itinerary & dates MATCH, price within normal feed drift",
}

FLAGGED = [
    ("FLAG-01", "Mobile, AL", "Carnival Spirit", "2027-03-29", "16",
     "", "", "", "", "",
     "https://www.carnival.com/itinerary/16-day-panama-canal-cruise/mobile/spirit/16-days/jp1/?sailDate=03292027",
     "cruisetimetables frommobilealabama-mar2027",
     "NOT ADDED - OPEN JAW: 16 Night Panama Canal departs Mobile 29 Mar 2027 but ENDS IN SEATTLE "
     "(14 Apr). A single SFO round-trip airfare cannot honestly be applied; interior $976pp is real "
     "but the trip total would require two separately-quoted legs. FLAGGED FOR REVIEW."),
    ("FLAG-02", "Jacksonville, FL", "Norwegian Dawn", "2027-04-04", "15",
     "", "", "", "", "",
     "https://www.cruisetimetables.com/fromjacksonvilleflorida-apr2027.html",
     "cruisetimetables fromjacksonvilleflorida-2027",
     "NOT ADDED - OUT OF WINDOW: 15 Night Transatlantic Jacksonville -> Lisbon departs 4 Apr 2027, "
     "after the 31 Mar cutoff. Also open-jaw / non-U.S. end port."),
    ("FLAG-03", "Charleston, SC", "(none)", "", "",
     "", "", "", "", "",
     "https://www.cruisetimetables.com/cruises-from-charleston-south-carolina.html",
     "cruisetimetables port page",
     "PORT SWEPT - ZERO RESULT: Charleston has NO published 2027 departures (Carnival exited the "
     "port); the port page carries an empty calendar and there is no 2027 year page. Nothing to add."),
    ("FLAG-04", "Cape Liberty / Bayonne, NJ", "(none)", "", "",
     "", "", "", "", "",
     "https://cruisedig.com/cruises/departing_from/1307239/departure_date/2027-09",
     "cruisedig + cayole 2027 Cape Liberty listings",
     "PORT SWEPT - NO IN-WINDOW SAILINGS: Royal Caribbean's 2027 Cape Liberty season (Independence "
     "of the Seas, Oasis of the Seas, Celebrity Silhouette) starts in JUNE 2027. No Feb 15 - Mar 31 "
     "2027 departures exist. cruisetimetables publishes no Cape Liberty/Bayonne 2027 page. Not added."),
    ("FLAG-05", "Honolulu, HI", "(none)", "", "",
     "", "", "", "", "",
     "https://www.cruisetimetables.com/",
     "cruisetimetables slug probe",
     "PORT SWEPT - NO INDEXED PAGE: no cruises-from-honolulu-hawaii-2027 page exists on the schedule "
     "index, so no in-window Honolulu turnaround could be verified. Not added (would be fabrication)."),
]

HEAD = ["id", "port", "ship", "date", "duration_nights", "lead_in_pp_usd", "cruise_total_2",
        "flight_route", "flight_2", "trip_total_2", "official_deep_link",
        "schedule_source", "independent_crosscheck_or_note", "result"]


def main():
    rows = [r for r in csv.DictReader(MASTER.open(newline=""))
            if "pass 3" in r["status"]]
    out = []
    for r in rows:
        ship = r["name"].split(" \u2014 ")[0].strip()
        pp = r["price_note"].split("$")[1].split("/")[0].replace(",", "")
        key = (r["port"], ship, r["date"])
        note = XCHECK.get(key, "Primary source read line by line: cruisetimetables day/month "
                               "from-port page (official fare feed) + official cruise-line deep link "
                               "on the same page; dedup-checked against master by (port, ship, date)")
        out.append([r["id"], r["port"], ship, r["date"], r["duration"].split()[0], pp,
                    r["price"], r["flight_route"], r["flight_cost_2"], r["trip_total_2"],
                    r["official"], r["source_url"], note, "VERIFIED"])
    for f in FLAGGED:
        out.append(list(f) + ["FLAGGED - NOT ADDED"])

    with LOG.open("w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(HEAD)
        w.writerows(out)
    print(f"wrote {LOG} ({len(rows)} verified + {len(FLAGGED)} flagged)")


if __name__ == "__main__":
    main()
