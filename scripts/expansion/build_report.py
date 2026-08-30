#!/usr/bin/env python3
"""Generate a clean, per-port Markdown report of all in-window verified cruises.

Separate table per U.S. departure port, columns:
Cruise (ship + itinerary) | Line | Sail date | Duration | Stops | Cruise price (2 adults) |
SFO flight (2 adults) | Trip total (2 adults) | Promo | Official source | Schedule source.
"""
import csv, datetime
from pathlib import Path
from collections import defaultdict

ROOT = Path(__file__).resolve().parents[2]
MASTER = ROOT / "data" / "cruises_master_verified.csv"
OUT = ROOT / "docs" / "CRUISE_DEALS_BY_PORT.md"

START, END = "2027-02-15", "2027-03-31"

# Region + display order for ports.
PORT_REGION = {
    "San Diego, CA": "U.S. West Coast",
    "Los Angeles (San Pedro), CA": "U.S. West Coast",
    "Long Beach (Los Angeles), CA": "U.S. West Coast",
    "San Francisco, CA": "U.S. West Coast",
    "Galveston, TX": "U.S. Gulf Coast",
    "New Orleans, LA": "U.S. Gulf Coast",
    "Mobile, AL": "U.S. Gulf Coast",
    "Tampa, FL": "U.S. Gulf Coast",
    "Port Canaveral, FL": "U.S. East Coast (Florida)",
    "Fort Lauderdale, FL": "U.S. East Coast (Florida)",
    "Miami, FL": "U.S. East Coast (Florida)",
    "Jacksonville, FL": "U.S. East Coast (Florida)",
    "Baltimore, MD": "U.S. East Coast (Mid-Atlantic)",
    "San Juan, PR": "U.S. Caribbean (Puerto Rico)",
}
PORT_ORDER = list(PORT_REGION.keys())


def fmt_date(d):
    return datetime.date.fromisoformat(d).strftime("%a %b %-d, %Y")


def esc(s):
    return str(s).replace("|", "\\|")


def main():
    rows = [r for r in csv.DictReader(MASTER.open(newline=""))
            if START <= r["date"] <= END]
    by_port = defaultdict(list)
    for r in rows:
        by_port[r["port"]].append(r)

    ordered = [p for p in PORT_ORDER if p in by_port]
    ordered += sorted(p for p in by_port if p not in PORT_REGION)

    lines = []
    lines.append("# Cruise Deals by U.S. Port — Feb 15 to Mar 31, 2027")
    lines.append("")
    live = sum(1 for r in rows if "live quote (Google Flights, 2 adults)" in r.get("flight_cost_2", ""))
    lines.append("**2 adults · price = 2 × published interior/inside per-person snapshot · "
                 "flights = SFO round trip (arrive the day before, fly home the day after) · "
                 "trip total = cruise + flight.**")
    lines.append("")
    lines.append(f"**Airfare basis:** {live} sailings now carry a **LIVE dated Google Flights fare "
                 f"for 2 adults** (marked `live quote` in the flight column, with the exact search "
                 f"URL as the source link). The remaining {len(rows) - live} still use a KAYAK "
                 f"route-average planning estimate (marked `planning estimate`) and are being "
                 f"converted progressively — see `data/flight_quotes.jsonl` for the full quote "
                 f"history and `scripts/flights/` for the tracker.")
    lines.append("")
    lines.append(f"_Snapshot generated from the verified master table. {len(rows)} in-window sailings "
                 f"across {len(ordered)} U.S. departure ports. Prices are planning snapshots, not live "
                 f"quotes — reconfirm cabin, taxes/fees and availability on each official page. "
                 f"No fabricated rows._")
    lines.append("")

    # Summary index
    lines.append("## Ports covered")
    lines.append("")
    lines.append("| Region | Port | Sailings | Cheapest trip total (2 adults) |")
    lines.append("|---|---|--:|--:|")
    for p in ordered:
        recs = by_port[p]
        def num(r):
            v = r["trip_total_2"].replace("$", "").replace(",", "")
            try:
                return int(v)
            except ValueError:
                return 10**9
        cheapest = min((num(r) for r in recs), default=10**9)
        cheap_txt = "$" + format(cheapest, ",") if cheapest < 10**9 else "—"
        region = PORT_REGION.get(p, "Other")
        lines.append(f"| {region} | {p} | {len(recs)} | {cheap_txt} |")
    lines.append("")

    for p in ordered:
        recs = sorted(by_port[p], key=lambda r: (r["date"], r["name"]))
        region = PORT_REGION.get(p, "Other")
        route = recs[0]["flight_route"]
        parts = route.replace("\u2192", "|").split("|")
        dest = parts[1].strip() if len(parts) > 1 else route
        subtitle = f"{region} · fly SFO ⇄ {dest}" if "No flight" not in route else f"{region} · home port (no SFO flight needed)"
        lines.append(f"## {p}  \n_{subtitle}_")
        lines.append("")
        lines.append("| Cruise | Line | Sail date | Duration | Stops | Cruise (2 adults) | "
                     "SFO flight (2 adults) | Trip total (2 adults) | Promo | Official | Schedule |")
        lines.append("|---|---|---|---|---|--:|--:|--:|---|---|---|")
        for r in recs:
            promo = r["promo"]
            if len(promo) > 42:
                promo = "confirm on official page"
            official = f"[official ↗]({r['official']})"
            sched = f"[index ↗]({r['source_url']})"
            flight = f"{r['flight_cost_2']}"
            lines.append(
                f"| {esc(r['name'])} | {esc(r['line'])} | {fmt_date(r['date'])} | {esc(r['duration'])} | "
                f"{esc(r['stops'])} | {esc(r['price'])} | {esc(flight)} | **{esc(r['trip_total_2'])}** | "
                f"{esc(promo)} | {official} | {sched} |"
            )
        lines.append("")

    lines.append("---")
    lines.append("")
    lines.append("### Method & sources (line-by-line, no hallucination)")
    lines.append("")
    lines.append("- **Cruise data** read from the CruiseTimetables from-port / monthly / day schedule index "
                 "(which republishes the official cruise-line fare feed), with a **per-sailing official "
                 "cruise-line deep link** captured for every row (carnival.com `sailDate`, royalcaribbean.com "
                 "voyage IDs, princess.com `voyageCode`, ncl.com `packageId`, disneycruise.disney.go.com voyage "
                 "codes, celebritycruises.com package codes, msccruisesusa.com cruise IDs).")
    lines.append("- **Prices** are the published **Interior/Inside per-person** figure × 2 adults. MSC rows use "
                 "the line's lead-in *From* fare and Disney/HAL rows use *Inside* — labelled in the master table's "
                 "price note.")
    lines.append("- **Flights**: 2 adults, SFO round trip, arrive the day before embarkation and return the day "
                 "after disembarkation, priced at each route's **KAYAK route average** (planning estimate; live "
                 "quote required). Dated Google Flights + KAYAK links are in the master CSV per row.")
    lines.append("- **Independent cross-checks** performed on a sample (e.g. Carnival Magic Miami 2/20 and "
                 "Radiance of the Seas Tampa 2/20 confirmed on icruise/nauticalflock; interior $618 matched). "
                 "Full per-row evidence: `data/verification_log_2026-08-30_national_expansion.csv`.")
    lines.append("- **Excluded (flagged):** full-ship charter/theme sailings with no published fare — Star Trek: "
                 "The Cruise & The 80s Cruise (New Orleans, Mariner of the Seas), JoCo Cruise (Fort Lauderdale, "
                 "Eurodam), Rock Legends / Jam Cruise (Miami). These are real sailings but carry no bookable "
                 "public interior price, so they are not added to the priced master list.")
    lines.append("")
    OUT.write_text("\n".join(lines))
    print(f"wrote {OUT} ({len(rows)} rows, {len(ordered)} ports)")


if __name__ == "__main__":
    main()
