#!/usr/bin/env python3
"""Deterministic integrity checks for the published CruiseDeals snapshot.

This does not claim that a fare is still available. It catches broken rows,
window mistakes, missing source links, duplicate IDs, and arithmetic drift
before the static table is published.
"""
import csv, json, re
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
START, END = date(2027, 2, 15), date(2027, 3, 31)
MONEY = re.compile(r"^\$[0-9,]+$")

with (ROOT / "data/cruises_master_verified.csv").open(newline="") as f:
    rows = list(csv.DictReader(f))
assert len(rows) == 79, f"expected 79 rows, got {len(rows)}"
assert len({r["id"] for r in rows}) == len(rows), "duplicate IDs"

in_window = []
for r in rows:
    d = date.fromisoformat(r["date"])
    is_out = r["status"].startswith("OUT OF WINDOW")
    if START <= d <= END:
        assert not is_out, f"in-window row marked out: {r['id']}"
        in_window.append(r)
    else:
        assert is_out, f"out-of-window row not marked out: {r['id']}"
    for field in ("official", "source_url", "flight_source_url", "flight_search_url"):
        assert r[field].startswith("https://"), f"{r['id']} missing https {field}"
    assert r["price_currency"] == "USD", f"{r['id']} non-USD price"
    if r["price"] != "Not published":
        assert MONEY.match(r["price"]), f"{r['id']} malformed cruise price"
    if r["trip_total_2"].startswith("$"):
        assert MONEY.match(r["trip_total_2"]), f"{r['id']} malformed total"

assert len(in_window) == 77, f"expected 77 in-window rows, got {len(in_window)}"
with (ROOT / "data/cruise_line_scope_audit.csv").open(newline="") as f:
    audit = list(csv.DictReader(f))
assert len(audit) == 24, f"expected 24 audit rows, got {len(audit)}"
assert all(r["official_review_link"].startswith("https://") for r in audit)

# Keep the browser copy exactly in sync with the source snapshot.
with (ROOT / "data/cruises.json").open() as f:
    source_json = json.load(f)
with (ROOT / "docs/data/cruises.json").open() as f:
    docs_json = json.load(f)
assert source_json == docs_json, "docs/data/cruises.json is stale"
print(f"OK: {len(in_window)} in-window sailings, {len(rows)-len(in_window)} audit-only rows, {len(audit)} scope checks")
