# CruiseDeals

A static GitHub Pages research table for cruises departing **U.S. West Coast ports** during **February 15 – March 31, 2027**, with 2-adult cruise price snapshots, SFO-based flight planning, trip totals, official source links and line-by-line verification.

## Final verified state (2026-08-28)

- **79 records** = **77 in-window sailings** (all verified, all with a published USD interior snapshot) + **2 out-of-window rows** retained for audit.
- Departure cities: **San Diego, Los Angeles (San Pedro), Long Beach, San Francisco**. Seattle was swept — no in-window mainstream departures (season opens Apr 14). Vancouver is out of scope (not a U.S. port; it appears only as the *end* port of two HAL voyage variants, flagged with an open-jaw flight estimate).
- Cruise lines represented (every mainstream West Coast operator in the window): **Carnival, Disney, Holland America, Norwegian, Princess, Royal Caribbean**. All other lines (Celebrity, MSC, Regent, Silversea, Seabourn, Oceania, Cunard, Azamara, Costa, Windstar, Viking, Hapag-Lloyd, Virgin) were swept and are accounted for in the scope audit.
- Each row: cruise name, total price for 2 (2 × published interior per-person snapshot; **never guessed**), duration, port stops, official source links, line-level promotions snapshot, review status.
- Flight plan per row: 2 adults, SFO ⇄ port, **arrive the day before / return the day after**; dated Google Flights search link + KAYAK route-average basis per row. San Francisco departures need no flight.

### The "50 new entries" request — answered honestly (no hallucination)

A full line-by-line sweep of the 2027 port turnaround schedules found that the prior work had already captured the **entire** universe of mainstream U.S. West Coast departures in the window. There are **not 50 additional genuinely-new sailings** — inventing 50 would require fabrication, which this project refuses to do. What this finalization pass actually produced:

- **1 genuinely new sailing added** — **Island Princess, 16-Night Panama Canal Ocean-to-Ocean** (departs LA Mar 2, 2027; ends Fort Lauderdale; interior $1,879/person → $3,758 for 2). It is one-way, so its flight is open-jaw and the trip total is honestly marked "live quote required" (no fabricated airfare).
- **4 rows finalized** from "REVIEW / SCHEDULE INDEX" limbo into fully verified records with USD prices: Voyager of the Seas 4-Night Ensenada (2/15), Emerald Princess 7-Night Classic California Coast (3/14 and 3/28), and the Island Princess Panama Canal above.
- **9 hallucinated rows removed** — dates that do not exist on the verified 2027 schedule index (see below).

### Irregularities resolved (removed, not kept)

Nine pre-existing rows were confirmed as **date hallucinations or duplicates** against the verified schedule index and were **removed** from the master list (previously they were only flagged):

- **LA-43, LA-45, LA-46, LA-47, LA-48** — Emerald Princess departures on Mar 10, 17, 19, 24, 31 that have no indexed sailing. The real Emerald LA 7N sailings in the window are **Mar 14 / 21 / 28** (E706/E707/E708).
- **LA-52** (Radiance "3/5") → real sailing is **Mar 4** (already LA-83).
- **LA-53** (Panorama "3/12") → real sailing is **Mar 13** (already LA-80).
- **LA-54** (Radiance "3/19") → ship is at sea on the verified **Mar 14** 14-Night Hawaii.
- **LA-55** (Panorama "3/26") → real sailing is **Mar 27** (already LA-82).

No in-window row remains in "REVIEW" or "SCHEDULE INDEX" state. The only rows with a non-computable trip total are the two **out-of-window** rows and the **open-jaw Panama Canal** row (flight live quote required) — all clearly labelled.

## Flight basis (refreshed 2026-08-28)

Uniform route averages from KAYAK route pages (accessed 2026-08-28; date-specific live quotes still required): SFO–SAN **$156 pp RT** (typical $134–$287) · SFO–LAX **$204 pp RT** (12-mo avg; typical $138–$272; February historically peaks) · open-jaw SFO→SAN + YVR→SFO **$285 pp** for the two HAL variants ending in Vancouver. The Island Princess Panama Canal row uses an open-jaw SFO→LAX / FLL→SFO with **no published route average** — it is marked "live quote required" rather than guessed.

## Verification policy

Snapshot ≠ live quote; availability, cabin category, taxes/fees and promotions must be reconfirmed on the official page. Prices are read only from a trusted schedule-index source that publishes a USD interior per-person figure; where none exists the row says so (or the row is excluded). This project is not a booking engine and makes no guarantee of availability.

## Build & site

- `scripts/finalize_cleanup.py` — this pass: removes the 9 hallucinated rows, finalizes the 4 remaining rows into verified records, and syncs `data/` + `docs/data/`.
- `scripts/build_update.py` — earlier pass (Aug 28): added 36 verified sailings and applied the uniform flight basis.
- `scripts/flight_search.py` — prints dated flight-search links (Google Flights + KAYAK) per sailing for manual price tracking.
- GitHub Pages: the zero-build app lives in [`docs/`](docs/) (with `.nojekyll` and its own `data/` snapshot). A root [`index.html`](index.html) forwards to `docs/`.

## Key data files

- [`data/cruises_master_verified.csv`](data/cruises_master_verified.csv) — the master table
- [`data/cruises.json`](data/cruises.json) — feeds the site (`docs/data/cruises.json` is the site-local snapshot)
- [`data/verification_log_2026-08-28.csv`](data/verification_log_2026-08-28.csv) — every check, per row (including the 9 removals and 4 finalizations)
- [`data/cruise_line_scope_audit.csv`](data/cruise_line_scope_audit.csv) — every cruise line swept, with result and evidence (also shown in the page's Coverage audit table)
- [`data/scope_audit.json`](data/scope_audit.json) — browser-readable copy used by GitHub Pages

## Validation

Run `python scripts/validate_data.py` before publishing. It checks the 2027 date window, duplicate IDs, required HTTPS source/search links, USD labeling, audit-row count, and that the browser data copy matches the master JSON. The site deliberately labels route-average airfare and cruise fare snapshots as planning estimates—not live quotes—and keeps the honest result when an open-jaw fare cannot be computed.

