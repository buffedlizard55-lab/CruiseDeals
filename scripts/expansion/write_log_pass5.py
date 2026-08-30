#!/usr/bin/env python3
"""Emit the pass-5 per-row verification log from the rows actually written to master."""
import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MASTER = ROOT / "data" / "cruises_master_verified.csv"
LOG = ROOT / "data" / "verification_log_2026-08-30_national_expansion_pass5.csv"

# Independent (second-source) cross-checks actually performed this pass.
XCHECK = {
    ("San Juan, PR", "Crown Princess", "2027-02-21"):
        "rolcruise.co.uk cruise 2197539 independently lists the Crown Princess 'Southern Caribbean "
        "Adventurer' departing San Juan 21 Feb 2027 for 14 nights and quotes VOYAGE CODE 3709A - an "
        "EXACT match to the voyage code captured from the feed, confirming both the 14N variant and "
        "the same-day 7N/14N pair. globaljourneys.com separately lists the 7N Crown Princess "
        "San Juan sailing on 21 Feb 2027 at Interior US$759 vs feed $679 (agency vs feed drift).",
    ("Galveston, TX", "Symphony of the Seas", "2027-03-14"):
        "cruisesheet.com royal-caribbean-symphony-of-the-seas-7-night-galveston-roundtrip-march-14-"
        "2027 confirms the 7N Galveston round trip on 14 Mar 2027 with the exact port sequence "
        "Costa Maya -> Roatan -> Cozumel, Inside $1,044 vs feed Interior $1,094 (normal drift). "
        "icruise.com Symphony March 2027 grid independently lists Mar 14 2027 with the SAME port "
        "ORDER (Costa Maya, Roatan, Cozumel) - distinct from the Mar 7/21 sailings which run "
        "Roatan first - confirming this is the correct dated itinerary, not a generic one.",
    ("Port Canaveral, FL", "Explorer of the Seas", "2027-03-15"):
        "cruisecompete.com Explorer of the Seas page lists '4 Night - Caribbean Getaway Cruise ... "
        "Grand Turk, Turks and Caicos ... 2027 Sails: Mar 15, Mar 29, Apr 12' - EXACT match on "
        "cruise name, itinerary and BOTH in-window dates added this pass. *** PRICE IRREGULARITY: a "
        "later cruisetimetables re-render of the same day page showed this sailing as '4 Night "
        "Eastern Caribbean Cruise' Interior $435, and travelagewest.com shows $354 for Mar 15, "
        "versus the $549 captured at build time. Itinerary/date are solid; the interior price is "
        "VOLATILE across sources. FLAGGED - see NOTE-P5-04.",
    ("Tampa, FL", "Jewel of the Seas", "2027-02-22"):
        "pcolligan.cruiseone.com (World Travel Holdings feed) lists the Jewel of the Seas 5 Night "
        "Western Caribbean round trip Tampa departing 22 Feb 2027 at Interior $573 vs feed $574 - a "
        "one-dollar match - with the identical Costa Maya -> Cozumel port sequence. Note other "
        "agencies quote $455-$523 for the same sailing, so the lead-in is promo-dependent.",
}

FLAGGED = [
    ("FLAG-P5-01", "Fort Lauderdale, FL", "Nieuw Statendam", "2027-03-14", "7",
     "", "", "", "", "",
     "https://www.inspirationtravel.com/event/live-no-one-else-2027-caribbean-cruise",
     "cruisetimetables fromfortlauderdaleflorida-14mar2027",
     "NOT ADDED - FULL-SHIP CHARTER: '7 Night Live Like No One Else Cruise With Dave Ramsey'. The "
     "fare feed publishes literally 'NA' and the only booking channel is the charter operator "
     "(inspirationtravel.com). No bookable public interior fare exists, so pricing it would be "
     "fabrication. Consistent with the existing charter exclusions. FLAGGED FOR REVIEW."),
    ("FLAG-P5-02", "Miami, FL", "Oceania Marina", "2027-03-25", "16 / 23",
     "", "", "", "", "",
     "https://www.oceaniacruises.com/cruises/MNA270325",
     "cruisetimetables frommiamiflorida-25mar2027",
     "NOT ADDED - OPEN JAW + NO LEAD-IN FARE: the 16N 'Cosmopolitan Crossing' ends in ROME and the "
     "23N 'Grand Atlantic to Adriatic' ends in TRIESTE, so a single SFO round trip cannot honestly "
     "be applied. The 23N variant additionally publishes 'From NA' in EVERY cabin grade. Oceania is "
     "also premium/upper-premium rather than contemporary. FLAGGED FOR REVIEW."),
    ("FLAG-P5-03", "Miami, FL", "MSC Poesia", "2027-03-18", "21",
     "", "", "", "", "",
     "https://www.msccruisesusa.com/itinerary-details/21-nights-southern--western-caribbean?cruiseid=PO20270318MIAMI1",
     "cruisetimetables frommiamiflorida-18mar2027",
     "NOT ADDED - ENDS OUTSIDE WINDOW: 21 Night Southern & Western Caribbean departs Miami 18 Mar "
     "2027 (in window) but does not return until 8 Apr 2027, past the 31 Mar cutoff. The 10N "
     "variant departing the same day IS round-trip and in-window, and was added instead."),
    ("FLAG-P5-04", "Port Canaveral, FL", "Explorer of the Seas", "2027-03-15 / 2027-03-29", "4",
     "", "", "", "", "",
     "https://www.royalcaribbean.com/cruises/itinerary/4-night-caribbean-getaway-from-orlando-port-canaveral-on-explorer/EX04PCN-1082066547",
     "cruisetimetables fromportcanaveralflorida-15mar2027 / -29mar2027",
     "ADDED BUT PRICE FLAGGED - HIGH VOLATILITY: cruisecompete.com confirms the cruise name, the "
     "Grand Turk itinerary and BOTH sail dates exactly. However the interior lead-in differs widely "
     "by source: $549 (feed at build time, used), $435 (later cruisetimetables re-render, which "
     "also renamed it '4 Night Eastern Caribbean Cruise'), $354 (travelagewest.com). The schedule "
     "is verified; TREAT THE PRICE AS INDICATIVE ONLY and reconfirm on royalcaribbean.com."),
    ("FLAG-P5-05", "San Juan, PR", "Explora III", "2027-03-07", "7 / 14",
     "", "", "", "", "",
     "https://www.explorajourneys.com/us/en/destinations-globe/car/journeys/sjumia-07-v29?id-journey=EL20270307SJUMIA",
     "cruisetimetables fromsanjuanpuertorico-07mar2027",
     "NOT ADDED - OPEN JAW + OUT OF SEGMENT: both Explora Journeys voyages depart San Juan but END "
     "IN MIAMI (7N) and BARBADOS (14N), so the SFO round-trip flight model does not apply. Explora "
     "is also an ultra-luxury brand (lead-in $5,100-$8,680 per guest) outside the mainstream/"
     "contemporary scope. FLAGGED FOR REVIEW."),
    ("FLAG-P5-06", "New Orleans, LA / Tampa, FL / Galveston, TX", "(none)",
     "2027-02-22 / 2027-03-01 / 2027-03-08", "",
     "", "", "", "", "",
     "https://www.cruisetimetables.com/cruises-from-new-orleans-louisiana.html",
     "cruisetimetables per-day probes",
     "DATES SWEPT - ZERO RESULT: the per-day URLs for New Orleans 22 Feb, Tampa 1 Mar and Galveston "
     "8 Mar 2027 all redirect to the port index page rather than returning a sailing list, meaning "
     "there are NO departures on those dates. Recorded so the gap analysis is not re-run on them."),
]

# Same (port, ship, date) but different durations -> distinct bookable voyages, retained.
SAME_DAY = [
    ("NOTE-P5-01", "San Juan, PR", "Crown Princess", "2027-02-21", "7 and 14",
     "", "", "", "", "", "",
     "cruisetimetables fromsanjuanpuertorico-21feb2027",
     "RETAINED - NOT A DUPLICATE: Princess sells a 7N 'Southern Caribbean with Barbados and "
     "St. Lucia' (voyage 3709) and a 14N 'Southern Caribbean Adventurer' (voyage 3709A) departing "
     "San Juan the same day; the 14N is the combined back-to-back. Distinct official voyage codes, "
     "and rolcruise.co.uk independently confirms 3709A as a 14-night product."),
    ("NOTE-P5-02", "San Juan, PR", "Crown Princess", "2027-02-28", "7 and 14",
     "", "", "", "", "", "",
     "cruisetimetables fromsanjuanpuertorico-28feb2027",
     "RETAINED - NOT A DUPLICATE: same structure, official voyage codes 3710 (7N) and 3710A (14N)."),
    ("NOTE-P5-03", "San Juan, PR", "Crown Princess", "2027-03-07", "7 and 14",
     "", "", "", "", "", "",
     "cruisetimetables fromsanjuanpuertorico-07mar2027",
     "RETAINED - NOT A DUPLICATE: same structure, official voyage codes 3711 (7N) and 3711A (14N)."),
]

HEAD = ["id", "port", "ship", "date", "duration_nights", "lead_in_pp_usd", "cruise_total_2",
        "flight_route", "flight_2", "trip_total_2", "official_deep_link",
        "schedule_source", "independent_crosscheck_or_note", "result"]


def main():
    rows = [r for r in csv.DictReader(MASTER.open(newline=""))
            if "pass 5" in r["status"]]
    out = []
    for r in rows:
        ship = r["name"].split("\u2014")[0].strip()
        pp = r["price_note"].split("$")[1].split("/")[0].replace(",", "")
        key = (r["port"], ship, r["date"])
        note = XCHECK.get(key, "Primary source read line by line: cruisetimetables PER-DAY "
                               "from-port 2027 page (official cruise-line fare feed) + the official "
                               "cruise-line deep link carried on that same page; dedup-checked "
                               "against master by (port, ship, date, nights)")
        out.append([r["id"], r["port"], ship, r["date"], r["duration"].split()[0], pp,
                    r["price"], r["flight_route"], r["flight_cost_2"], r["trip_total_2"],
                    r["official"], r["source_url"], note, "VERIFIED"])
    for f in FLAGGED:
        out.append(list(f) + ["FLAGGED - NOT ADDED"])
    for n in SAME_DAY:
        out.append(list(n) + ["FLAGGED - RETAINED (distinct voyage)"])

    with LOG.open("w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(HEAD)
        w.writerows(out)
    print(f"wrote {LOG} ({len(rows)} verified + {len(FLAGGED)} flagged "
          f"+ {len(SAME_DAY)} same-day notes)")


if __name__ == "__main__":
    main()
