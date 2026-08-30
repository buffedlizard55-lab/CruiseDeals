#!/usr/bin/env python3
"""Emit the pass-4 per-row verification log from the rows actually written to master."""
import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MASTER = ROOT / "data" / "cruises_master_verified.csv"
LOG = ROOT / "data" / "verification_log_2026-08-30_national_expansion_pass4.csv"

# Independent (second-source) cross-checks actually performed this pass.
XCHECK = {
    ("Port Canaveral, FL", "Utopia of the Seas", "2027-03-08"):
        "cruisedirect.com Utopia of the Seas ship page lists the Mar 8 2027 - Mar 12 2027 (Mon-Fri) "
        "4 Nights Bahamas sailing at Interior $722 / Oceanview $822 / Balcony $804 / Suite $1,244 - "
        "EXACT four-figure MATCH with the feed. royalcaribbean.com confirms the itinerary "
        "(Nassau; Perfect Day at CocoCay; cruising; Port Canaveral). Strongest check this pass.",
    ("Port Canaveral, FL", "Carnival Glory", "2027-02-19"):
        "cnunnery.dreamvacations.com (Carnival API reseller) publishes the Carnival Glory 3 Night "
        "Bahamas round trip Port Canaveral with a single call at Celebration Key, dep 3:30 PM, "
        "return 8:00 AM day 4 - MATCH on ship, duration, port sequence and departure time. "
        "Interior lead-in shown $299 vs feed $301 - normal feed drift, retained feed value.",
    ("Miami, FL", "Carnival Firenze", "2027-02-18"):
        "carnival.com/itinerary/8-day-southern-caribbean-cruise/miami/firenze/8-days/czm?sailDate="
        "02182027 resolves live and shows Start: Miami > Aruba > Curacao > Grand Turk > End: Miami. "
        "cruiseweb.com independently lists the 8-night Southern Caribbean ex-Miami on Carnival "
        "Firenze with a Feb 18 2027 sailing - MATCH. NOTE PRICE DRIFT: a later cruisetimetables "
        "render of the same day page showed Interior $616 vs the $639 captured at build time; both "
        "are feed snapshots, difference flagged rather than silently changed.",
    ("Fort Lauderdale, FL", "Nieuw Statendam", "2027-02-21"):
        "prnewswire.com Holland America 2026-2027 season release confirms the 7-Day 'Western "
        "Caribbean: Greater Antilles and Mexico' aboard Nieuw Statendam sails round trip Fort "
        "Lauderdale calling Half Moon Cay, Ocho Rios, Grand Cayman and Cozumel - MATCH on port "
        "sequence. cruisesheet.com/cruisebound.com show the identical itinerary operating on the "
        "same Feb-21 weekend slot in the prior season, confirming the deployment pattern.",
}

FLAGGED = [
    ("FLAG-P4-01", "Fort Lauderdale, FL", "Celebrity Silhouette", "2027-02-21", "5",
     "", "", "", "", "",
     "https://ultimatediscocruise.com/",
     "cruisetimetables fromfortlauderdaleflorida-21feb2027",
     "NOT ADDED - FULL-SHIP CHARTER: '5 Night Ultimate Disco Cruise And Beyond'. The fare feed "
     "publishes literally 'NA' - there is no bookable public interior fare, and the only booking "
     "channel is the charter operator. Pricing it would be fabrication. Consistent with the "
     "existing exclusion of Star Trek: The Cruise, The 80s Cruise, JoCo Cruise, Rock Legends and "
     "Jam Cruise. FLAGGED FOR REVIEW."),
    ("FLAG-P4-02", "Miami, FL", "Norwegian Jewel", "2027-02-15", "11",
     "", "", "", "", "",
     "https://www.cruisetimetables.com/frommiamiflorida-15feb2027.html",
     "cruisetimetables frommiamiflorida-15feb2027",
     "NOT ADDED - FULL-SHIP CHARTER: 11 Night 'Big Nude Boat 2027', sold only via "
     "cruisebare.com / Bare Necessities. No public interior fare in the feed. FLAGGED FOR REVIEW."),
    ("FLAG-P4-03", "Miami, FL", "Norwegian Star", "2027-03-01", "15",
     "", "", "", "", "",
     "https://www.cruisetimetables.com/frommiamiflorida-01mar2027.html",
     "cruisetimetables frommiamiflorida-01mar2027",
     "NOT ADDED - OPEN JAW: 15 Night Transatlantic departs Miami 1 Mar 2027 but ENDS IN BARCELONA. "
     "A single SFO round-trip airfare cannot honestly be applied to a one-way voyage. Same rule "
     "already applied to Carnival Spirit ex-Mobile 29 Mar. FLAGGED FOR REVIEW."),
    ("FLAG-P4-04", "Miami, FL", "Explora I", "2027-03-08", "16",
     "", "", "", "", "",
     "https://www.explorajourneys.com/us/en/destinations-globe/tra/journeys/miabcn-16-v5?id-journey=EX20270308MIABCN",
     "cruisetimetables frommiamiflorida-08mar2027",
     "NOT ADDED - OPEN JAW + OUT OF SEGMENT: Explora Journeys 16 Night Miami -> Barcelona, ends "
     "outside the U.S. Also an ultra-luxury brand (lead-in $8,315pp) outside the mainstream/"
     "contemporary scope the list targets. FLAGGED FOR REVIEW."),
    ("FLAG-P4-05", "Miami, FL", "Oceania Allura", "2027-03-11", "10",
     "", "", "", "", "",
     "https://www.oceaniacruises.com/cruises/ALU270311",
     "cruisetimetables frommiamiflorida-11mar2027",
     "NOT ADDED - NO LEAD-IN CABIN PRICE: 10 Night Tropical Island Havens, round trip Miami and "
     "genuinely in window, but the feed publishes 'Veranda From NA' with only a Suite price "
     "($6,899pp). There is no interior/lead-in fare to price two adults against without guessing. "
     "Oceania is also a premium/upper-premium brand rather than contemporary. FLAGGED FOR REVIEW."),
    ("FLAG-P4-06", "New Orleans, LA", "Carnival Valor", "2027-03-15", "5",
     "", "", "", "", "",
     "https://www.carnival.com/itinerary/5-day-western-caribbean-cruise/new-orleans/valor/5-days/cw6/?sailDate=03152027",
     "cruisetimetables fromneworleanslouisiana-15mar2027",
     "NOT ADDED - ALREADY IN MASTER: read from the day page during this sweep, but the automated "
     "(port, ship, date, nights) dedup guard matched an existing row from an earlier pass. "
     "Correctly rejected as a duplicate rather than double-counted."),
]

# Same (port, ship, date) but different durations -> distinct bookable voyages, retained.
SAME_DAY = [
    ("NOTE-P4-01", "Miami, FL", "MSC Seaside", "2027-02-15", "4 and 7",
     "", "", "", "", "", "",
     "cruisetimetables frommiamiflorida-15feb2027",
     "RETAINED - NOT A DUPLICATE: MSC Seaside sells both a 4N Bahamas & Ocean Cay and a 7N "
     "Caribbean & Bahamas departing Miami the same day (the 7N is the combined back-to-back). "
     "Separate cruise IDs SE20270215MIAMIA and SE20270215MIAMI1 on msccruisesusa.com. Same "
     "precedent as the pass-3 Koningsdam/Grandiosa/Regal Princess pairs."),
    ("NOTE-P4-02", "Miami, FL", "MSC Seaside", "2027-02-22", "4 and 7",
     "", "", "", "", "", "",
     "cruisetimetables frommiamiflorida-22feb2027",
     "RETAINED - NOT A DUPLICATE: same 4N / 7N back-to-back structure, cruise IDs "
     "SE20270222MIAMIA and SE20270222MIAMI1."),
    ("NOTE-P4-03", "Fort Lauderdale, FL", "Nieuw Statendam", "2027-02-21", "7 and 14",
     "", "", "", "", "", "",
     "cruisetimetables fromfortlauderdaleflorida-21feb2027",
     "RETAINED - NOT A DUPLICATE: Holland America sells the 7N Western Caribbean and a 14N "
     "Western & Eastern Caribbean collector departing the same day; distinct voyage codes "
     "c7w07a/j723 and c7x14d/j723a on hollandamerica.com."),
]

HEAD = ["id", "port", "ship", "date", "duration_nights", "lead_in_pp_usd", "cruise_total_2",
        "flight_route", "flight_2", "trip_total_2", "official_deep_link",
        "schedule_source", "independent_crosscheck_or_note", "result"]


def main():
    rows = [r for r in csv.DictReader(MASTER.open(newline=""))
            if "pass 4" in r["status"]]
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
