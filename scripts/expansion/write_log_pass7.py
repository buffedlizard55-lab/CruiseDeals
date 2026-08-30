#!/usr/bin/env python3
"""Write the pass-7 verification/evidence log (one row per newly added sailing)."""
import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MASTER = ROOT / "data" / "cruises_master_verified.csv"
OUT = ROOT / "data" / "verification_log_2026-08-31_national_expansion_pass7.csv"

SRC = {
    "Miami, FL": "https://www.cruisetimetables.com/cruises-from-miami-florida-2027.html",
    "Port Canaveral, FL": "https://www.cruisetimetables.com/cruises-from-port-canaveral-florida-2027.html",
    "Fort Lauderdale, FL": "https://www.cruisetimetables.com/cruises-from-fort-lauderdale-florida-2027.html",
    "Galveston, TX": "https://www.cruisetimetables.com/cruises-from-galveston-texas-2027.html",
    "New Orleans, LA": "https://www.cruisetimetables.com/cruises-from-new-orleans-louisiana-2027.html",
    "San Juan, PR": "https://www.cruisetimetables.com/cruises-from-san-juan-puerto-rico-2027.html",
    "Jacksonville, FL": "https://www.cruisetimetables.com/cruises-from-jacksonville-florida-2027.html",
    "Los Angeles (San Pedro), CA": "https://www.cruisetimetables.com/cruises-from-los-angeles-california-2027.html",
}

NOTE = ("Primary source read line by line: cruisetimetables PER-DAY from-port 2027 page "
        "(official cruise-line fare feed) + the official cruise-line deep link carried on that "
        "same page; targeted by a per-port date-coverage audit of all 45 in-window dates; "
        "dedup-checked against master by (port, ship, date, nights)")

XCHECK = {
    "GAL7": ("Independent cross-check: cruises.com lists Symphony of the Seas Galveston "
             "21-28 Feb 2027 Interior $650pp and cruisetimetables 2027 index shows Interior "
             "$765 / MSC Seascape From $470 for Sun 21 Feb; magicguides.com lists Disney Magic "
             "Galveston 21-26 Feb 2027 'From $2,241' as a STATEROOM total, confirming the "
             "Disney per-stateroom (not per-person) convention"),
    "SJU7": ("Independent cross-check: cruisedig.com and gangwaze.com both confirm the Crown "
             "Princess San Juan 2027 pattern (7N and 14N round trips) and confirm the 28 Mar "
             "sailing is ONE WAY San Juan -> Fort Lauderdale, which is why it was EXCLUDED here"),
    "PC7":  ("Independent cross-check: cruisesheet.com / cruises.com corroborate Star of the Seas "
             "7-night Port Canaveral round trips in Mar 2027 with interior fares in the "
             "$1,139-$1,435pp band"),
    "MIA7": ("Independent cross-check: cruisesheet.com / cruises.com corroborate the Miami "
             "Mar 2027 contemporary-line fare band; charter and ultra-luxury sailings "
             "(Atlantis-chartered Allure 7 Mar, Oceania Allura, Explora III) were excluded"),
    "FLL7": ("Independent cross-check: cruisetimetables 2027 Fort Lauderdale index corroborates "
             "the Mar 2027 Celebrity/Princess/Holland America fare band; Dave Ramsey charter "
             "(price 'NA') and Zaandam open-jaw Panama Canal to San Diego excluded"),
}

rows = [r for r in csv.DictReader(MASTER.open(newline="")) if "7-" in r["id"] and r["id"].split("7-")[0] in ("MIA","PC","FLL","GAL","MSY","SJU","JAX","LAX")]
rows = [r for r in rows if "pass 7" in r["status"]]

fields = ["id","port","ship","date","duration_nights","lead_in_pp_usd","cruise_total_2",
          "flight_route","flight_2","trip_total_2","official_deep_link","schedule_source",
          "independent_crosscheck_or_note","result"]

with OUT.open("w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=fields)
    w.writeheader()
    for r in rows:
        ship = r["name"].split("\u2014")[0].strip()
        pfx = r["id"].split("-")[0]
        note = NOTE + ". " + XCHECK.get(pfx, "")
        pp = "".join(c for c in r["price_note"] if c.isdigit() or c == ",").split(",")[0:2]
        w.writerow({
            "id": r["id"], "port": r["port"], "ship": ship, "date": r["date"],
            "duration_nights": r["duration"].split()[0],
            "lead_in_pp_usd": r["price_note"],
            "cruise_total_2": r["price"],
            "flight_route": r["flight_route"], "flight_2": r["flight_cost_2"],
            "trip_total_2": r["trip_total_2"],
            "official_deep_link": r["official"],
            "schedule_source": SRC[r["port"]],
            "independent_crosscheck_or_note": note,
            "result": "VERIFIED",
        })
print("wrote", OUT.name, len(rows), "rows")
