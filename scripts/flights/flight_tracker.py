#!/usr/bin/env python3
"""
Flight price tracker for the CruiseDeals trip totals.
=====================================================

WHY THIS EXISTS
---------------
Until now every `flight_cost_2` in the master table was a KAYAK *route average* --
a planning estimate, not a bookable fare. The brief asks for real prices for
2 adults from SFO, arriving the day BEFORE embarkation and departing the cruise
city the day AFTER disembarkation, folded into the trip total.

This module turns that into a real, repeatable, auditable pipeline:

    1.  `itineraries()`   - derive the exact (airport, out_date, return_date)
                            searches implied by the master table. No guessing:
                            the dates come from `flight_out_date` /
                            `flight_return_date`, which are themselves derived
                            from the sail date and duration.
    2.  `search_url()`    - build the canonical Google Flights URL for a search,
                            pinned to 2 adults and USD.
    3.  `parse_quote()`   - parse the *fetched* Google Flights page text into
                            structured offers (price, airline, stops, times).
    4.  `record()`        - append an observation to the quote store, so repeated
                            runs build a PRICE HISTORY per itinerary over time.
    5.  `latest()`        - the most recent observation per itinerary.

VERIFICATION POLICY (no hallucinations)
---------------------------------------
This module NEVER invents a price. It only parses text that was actually
fetched from Google Flights, and every stored quote carries:
    * the exact source URL,
    * the observation timestamp,
    * the raw price string as it appeared on the page,
    * `passengers: 2` only when the page itself said "for 2 adults".
A quote that cannot be parsed is stored as a MISS, not as a number. Sailings
with no real quote keep their estimate and are clearly labelled as such.

NETWORK NOTE
------------
Outbound `curl`/`requests` are blocked in this sandbox (every host returns
HTTP 000). Pages are therefore fetched by the agent's own fetch tool and passed
to `parse_quote()` as text. `python3 flight_tracker.py plan` emits the exact
work list so the fetching is reproducible and reviewable.
"""
from __future__ import annotations

import csv
import json
import re
import sys
import urllib.parse
from dataclasses import dataclass, asdict, field
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MASTER = ROOT / "data" / "cruises_master_verified.csv"
STORE = ROOT / "data" / "flight_quotes.jsonl"

ORIGIN = "SFO"
ADULTS = 2
CURRENCY = "USD"


# --------------------------------------------------------------------------
# 1. Itineraries implied by the master table
# --------------------------------------------------------------------------
@dataclass(frozen=True)
class Itinerary:
    airport: str
    out_date: str
    return_date: str

    @property
    def key(self) -> str:
        return f"{ORIGIN}-{self.airport}-{self.out_date}-{self.return_date}"


def _airport_of(route: str) -> str | None:
    """'SFO -> MIA -> SFO' => 'MIA'. Returns None for rows with no simple round trip."""
    if "\u2192" not in route:
        return None                      # e.g. "No flight required (SFO departure)"
    mid = route.split("\u2192")[1].strip()
    if not re.fullmatch(r"[A-Z]{3}", mid):
        return None                      # open-jaw / multi-airport oddity: handle manually
    return mid


def sailings() -> list[dict]:
    with MASTER.open(newline="") as f:
        return [r for r in csv.DictReader(f) if not r["status"].startswith("AUDIT")]


def itineraries() -> dict[Itinerary, list[str]]:
    """Map each distinct flight search -> the sailing ids that need it."""
    out: dict[Itinerary, list[str]] = {}
    for r in sailings():
        apt = _airport_of(r["flight_route"])
        if apt is None:
            continue
        it = Itinerary(apt, r["flight_out_date"], r["flight_return_date"])
        out.setdefault(it, []).append(r["id"])
    return out


def search_url(it: Itinerary) -> str:
    q = (f"Flights from {ORIGIN} to {it.airport} on {it.out_date} "
         f"returning {it.return_date} for {ADULTS} adults")
    return ("https://www.google.com/travel/flights?q="
            + urllib.parse.quote(q) + f"&curr={CURRENCY}")


# --------------------------------------------------------------------------
# 2. Parsing a fetched Google Flights page
# --------------------------------------------------------------------------
@dataclass
class Offer:
    price_2_adults: int
    airline: str
    stops: str
    raw_price: str


@dataclass
class Quote:
    key: str
    airport: str
    out_date: str
    return_date: str
    observed_utc: str
    source_url: str
    passengers: int
    currency: str
    cheapest_2_adults: int | None
    offers: list[dict] = field(default_factory=list)
    status: str = "OK"
    note: str = ""


PRICE_RE = re.compile(r"\$([0-9][0-9,]*)")
# "1 stop in DEN1 stop7 hr 45 min\n\nUnited" / "NonstopNonstop5 hr 47 min\n\nUnited"
SUMMARY_RE = re.compile(
    r"(Nonstop|\d+ stop(?:s)?)(?:[^\n]*?)(\d+ hr(?: \d+ min)?)\n+([A-Z][^\n]{0,60})")


def parse_quote(it: Itinerary, url: str, page_text: str) -> Quote:
    """Parse fetched Google Flights text. Never fabricates: on failure -> status MISS."""
    now = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    q = Quote(key=it.key, airport=it.airport, out_date=it.out_date,
              return_date=it.return_date, observed_utc=now, source_url=url,
              passengers=ADULTS, currency=CURRENCY, cheapest_2_adults=None)

    # Hard gate: only trust the page if it states the passenger basis we asked for.
    if f"for {ADULTS} adults" not in page_text:
        q.status = "MISS"
        q.note = ("page did not state 'for 2 adults' - refusing to record a price "
                  "that may be per-person")
        return q

    # Structured offers. In Google's layout the fare is rendered immediately
    # BEFORE its "1 stop in DEN1 stop7 hr 45 min\n\nUnited" summary line, so we
    # look backwards from the summary and take the nearest preceding price.
    seen: set[tuple[str, str, int]] = set()
    for m in SUMMARY_RE.finditer(page_text):
        stops, _dur, airline = m.group(1), m.group(2), m.group(3).strip()
        head = page_text[max(0, m.start() - 400): m.start()]
        pms = PRICE_RE.findall(head)
        if not pms:
            continue
        price = int(pms[-1].replace(",", ""))
        airline = airline.split("Operated by")[0].strip()
        sig = (airline, stops, price)
        if sig in seen:
            continue
        seen.add(sig)
        q.offers.append(asdict(Offer(price, airline, stops, f"${pms[-1]}")))

    prices = [o["price_2_adults"] for o in q.offers]

    # Google's own "Cheapest from $N" banner is the authoritative floor when present.
    banner = re.search(r"Cheapest\s*\nfrom[\s\S]{0,80}?\$([0-9][0-9,]*)", page_text)
    if banner:
        prices.append(int(banner.group(1).replace(",", "")))

    if not prices:
        q.status = "MISS"
        q.note = "no parseable priced itinerary on page"
        return q

    q.cheapest_2_adults = min(prices)
    q.offers.sort(key=lambda o: o["price_2_adults"])
    return q


# --------------------------------------------------------------------------
# 3. Quote store = append-only price history
# --------------------------------------------------------------------------
def record(q: Quote) -> None:
    with STORE.open("a") as f:
        f.write(json.dumps(asdict(q), ensure_ascii=False) + "\n")


def all_quotes() -> list[dict]:
    if not STORE.exists():
        return []
    return [json.loads(l) for l in STORE.read_text().splitlines() if l.strip()]


def latest() -> dict[str, dict]:
    """Most recent OK observation per itinerary key."""
    best: dict[str, dict] = {}
    for q in all_quotes():
        if q["status"] != "OK":
            continue
        cur = best.get(q["key"])
        if cur is None or q["observed_utc"] >= cur["observed_utc"]:
            best[q["key"]] = q
    return best


def history(key: str) -> list[dict]:
    return sorted((q for q in all_quotes() if q["key"] == key),
                  key=lambda q: q["observed_utc"])


# --------------------------------------------------------------------------
# CLI
# --------------------------------------------------------------------------
def _cmd_plan(argv: list[str]) -> None:
    """Emit the work list: which searches are needed, most-impactful first."""
    limit = int(argv[0]) if argv else 0
    its = itineraries()
    have = latest()
    todo = [(len(ids), it, ids) for it, ids in its.items() if it.key not in have]
    todo.sort(key=lambda t: (-t[0], t[1].airport, t[1].out_date))
    if limit:
        todo = todo[:limit]
    for n, it, _ids in todo:
        print(f"{n}\t{it.airport}\t{it.out_date}\t{it.return_date}\t{search_url(it)}")


def _cmd_status(_argv: list[str]) -> None:
    its = itineraries()
    have = latest()
    covered_sailings = sum(len(ids) for it, ids in its.items() if it.key in have)
    total_sailings = sum(len(ids) for ids in its.values())
    print(f"itineraries needed : {len(its)}")
    print(f"itineraries quoted : {len(have)}")
    print(f"sailings covered   : {covered_sailings} / {total_sailings}")
    print(f"observations stored: {len(all_quotes())}")


def _cmd_history(argv: list[str]) -> None:
    for q in history(argv[0]):
        print(f"{q['observed_utc']}  {q['status']:4}  "
              f"${q['cheapest_2_adults'] or '-'}  {q['key']}")


if __name__ == "__main__":
    cmds = {"plan": _cmd_plan, "status": _cmd_status, "history": _cmd_history}
    if len(sys.argv) < 2 or sys.argv[1] not in cmds:
        print(f"usage: {Path(__file__).name} [{'|'.join(cmds)}] ...")
        raise SystemExit(2)
    cmds[sys.argv[1]](sys.argv[2:])
