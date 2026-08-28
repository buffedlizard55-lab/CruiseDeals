# CruiseDeals

A static GitHub Pages research table for cruises departing **U.S. West Coast ports** during **February 15 – March 31, 2027**, with 2-adult cruise price snapshots, SFO-based flight planning, trip totals, official source links and line-by-line verification.

## Final verified state (2026-08-28)

- **79 records** = **77 in-window sailings** (all verified, all with a published USD interior snapshot) + **2 out-of-window rows** retained for audit.

### Pass 2 — independent line-by-line re-verification (2026-08-28)

A second, independent pass re-read every published 2027 schedule for the four U.S. West Coast turnaround ports (San Diego, Los Angeles/San Pedro + Long Beach, San Francisco, Seattle) and then the **per-ship, per-sailing index pages** for all 77 in-window sailings. Every row was re-checked on **date, port, duration, port sequence and published Interior USD price**, and each row now links to a **sailing-specific official deep link** (Disney `DW2236–DW2247`; Royal Caribbean voyage IDs `SR/VY/OV…`; Holland America `k717/k717a/k717b/k718a/k718/k718b/x719`; Princess voyage codes `X709–X714`, `E705–E708`, `R705/R706`, `2705`; NCL `packageId=23338094–99`; carnival.com `sailDate` itinerary links).

What this pass changed (all traceable in `data/verification_log_2026-08-28_pass2.csv`):

- **28 rows refreshed** — published Interior prices had drifted from the first pass's snapshot (e.g. Disney Wonder 19 Feb $1,754→**$1,328** pp; Serenade 18 Feb $288→**$335** pp; Koningsdam 20 Mar 7N $1,044→**$999** pp; Norwegian Encore 21 Feb $699→**$669** pp; Carnival Radiance 28 Feb $394→**$300** pp; Ruby Princess 28 Feb $1,779→**$1,704** pp). All totals recomputed as 2 × snapshot (+ flight estimate where applicable).
- **2 row corrections (3 fields)** — SD-21: Serenade 28 Mar 2027 7-night is **"Ensenada, Cabo & La Paz"** (official RCI title), not Mazatlán; Interior $649 pp. SD-24: Koningsdam 18-night ends in **Vancouver** — port sequence corrected accordingly and its flight block corrected from roundtrip SFO–SAN to open-jaw `SFO → SAN one-way; YVR → SFO return` ($570 for 2; trip total $4,548).
- **Scope additions to the audit** — ship-specific sweeps for **Norwegian Star** (last San Diego departure 13 Feb 2027 = 16-night Panama Canal repositioning to Miami → no in-window sailing), **Zuiderdam** (last San Diego departure 30 Jan 2027; Feb/Mar from Miami → no in-window sailing) and **Coral Princess** (Los Angeles call 21 Jan only). The only in-window Seattle event is the Hapag-Lloyd Europa segment call (27–28 Mar) — treated as a port call, not a mainstream departure.
- **Flight basis re-verified** on KAYAK route pages (2026-08-28): SFO–SAN typical **$134–$287** RT (cheapest seen $78), SFO–LAX typical **$138–$272** RT (cheapest seen $89), YVR–SFO typical **$137–$290** one-way. The planning estimates already in the table stand.
- **Result: still 77 in-window sailings.** No new genuine sailing was found, so no entry was added and none was invented.
- Departure cities: **San Diego, Los Angeles (San Pedro), Long Beach, San Francisco**. Seattle was swept — no in-window mainstream departures (season opens Apr 14). Vancouver is out of scope (not a U.S. port; it appears only as the *end* port of two HAL voyage variants, flagged with an open-jaw flight estimate).
- Cruise lines represented (every mainstream West Coast operator in the window): **Carnival, Disney, Holland America, Norwegian, Princess, Royal Caribbean**. All other lines (Celebrity, MSC, Regent, Silversea, Seabourn, Oceania, Cunard, Azamara, Costa, Windstar, Viking, Hapag-Lloyd, Virgin) were swept and are accounted for in the scope audit.
- Each row: cruise name, total price for 2 (2 × published interior per-person snapshot; **never guessed**), duration, port stops, official source links, line-level promotions snapshot, review status.
- Flight plan per row: 2 adults, SFO ⇄ port, **arrive the day before / return the day after**; dated Google Flights search link + KAYAK route-average basis per row. San Francisco departures need no flight.

### Pass 3 — search for 50 new entries (2026-08-28, no additions)

Independent re-read of the 2027 **from-port** indexes (San Diego, Los Angeles, San Francisco, Seattle) plus line sweeps (Celebrity, Virgin, Viking, Oceania, MSC). Result: **0 new qualifying sailings**. The in-window mainstream universe is still **exactly 77**. Inventing 50 extra rows would be hallucination; none were added. Evidence: `data/verification_log_2026-08-28_pass3_search50.csv`. Near-misses (not added): Ruby Princess SF Feb 12 (before window); NCL Star SD Feb 6 / Feb 13; Encore LA Feb 14; Hapag Europa SF Mar 18 (luxury segment); Virgin Brilliant Lady Mar 26 **Miami→LA** (not a West Coast departure); Celebrity Summit next LA sailing May 3 2027; Seattle Alaska season Apr 14.

### Pass 4 — independent re-verification + 50-entry search (2026-08-28, this pass)

A fresh, independent pass re-read the authoritative 2027 **from-port** indexes and monthly pages (all dated **2026-08-28**) and independently re-confirmed the results. Full record of every check: [`data/verification_log_2026-08-28_pass4_independent.csv`](data/verification_log_2026-08-28_pass4_independent.csv) (also mirrored to `docs/data/`).

What the independent pass confirmed:

- **Scope boundaries.** Only **4 U.S. West Coast ports** have in-window ocean cruises: **San Diego, Los Angeles/San Pedro, Long Beach, San Francisco**. **Seattle** — first 2027 departure is Carnival Spirit **Apr 14**, so **0 in-window**. **Oregon** (Astoria/Portland) — river/port-call only, **0 in-window**. Vancouver is out of scope (not a U.S. port; appears only as an *end* port of two HAL variants).
- **Source authority.** Every row's price is read from a published USD **Interior/Inside per-person** figure on the trusted schedule index (which quotes the official fare feed and links a per-sailing official deep link), then **doubled** for 2 adults. Snapshot ≠ live quote; taxes/cabin/availability require reconfirmation.
- **Line-by-line cross-check sample (12 rows, all 6 lines, all MATCH).** Disney Wonder SD 3/1 ($1,911pp→$3,822) · Serenade SD 3/7 ($349pp→$698) · Koningsdam SD 3/20 7N ($999pp→$1,998) · Island Princess LA 3/2 16N ($1,879pp→$3,758) · Voyager LA 3/5 7N ($525pp→$1,050) · Ovation LA 3/8 4N ($366pp→$732) · Discovery Princess LA 3/6 7N ($749pp→$1,498) · Carnival Panorama LA 3/7 6N ($334pp→$668) · Carnival Radiance LA 3/9 5N ($401pp→$802) · Norwegian Encore LA 3/7 7N ($689pp→$1,378) · Ruby Princess SF 2/28 16N ($1,704pp→$3,408) · Ruby Princess SF 3/16 16N ($1,264pp→$2,528).
- **Flight basis re-confirmed.** KAYAK SFO→SAN: typical round-trip **$134–$287**, average **~$156**, lowest ~$77 → matches the table's $156/pp planning basis. SFO→LAX typical **$138–$272**. Estimates remain labelled *planning estimate, live quote required*.
- **Data integrity.** `python scripts/validate_data.py` → **OK: 77 in-window sailings, 2 audit-only rows, 24 scope checks**; `data/` and `docs/data/` snapshots byte-identical.
- **Search for 50 new entries → 0 new.** The in-window mainstream universe is still **exactly 77**. No genuinely new qualifying sailing exists in the indexed data; fabricating 50 rows would be hallucination, so none were added. Near-misses (all out-of-window or out-of-scope, not added): Ruby Princess SF Feb 12 · Norwegian Star SD Feb 6/Feb 13 (Panama Canal reposition) · Encore LA Feb 14 · Radiance LA Feb 14 Hawaii · Panorama LA Feb 13 · Hapag-Lloyd Europa SF Mar 18 (EUR luxury) and Seattle 27–28 Mar (port call) · Virgin Brilliant Lady Mar 26 Miami→LA (not a West Coast departure) · Celebrity Summit next LA turnaround May 3 2027 · Seattle Alaska season opens Apr 14.

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
- [`data/verification_log_2026-08-28_pass2.csv`](data/verification_log_2026-08-28_pass2.csv) — independent pass-2 line-by-line results for all 79 rows (29 price refreshes, 1 itinerary correction, 1 flight-block correction, 77/77 in-window schedule-index matches)
- [`data/verification_log_2026-08-28_pass3_search50.csv`](data/verification_log_2026-08-28_pass3_search50.csv) — prior 50-entry search evidence
- [`data/verification_log_2026-08-28_pass4_independent.csv`](data/verification_log_2026-08-28_pass4_independent.csv) — this pass's independent re-verification (scope boundaries, 12-row cross-check across all 6 lines, flight basis, integrity, 0-new 50-entry search)
- [`data/cruise_line_scope_audit.csv`](data/cruise_line_scope_audit.csv) — every cruise line + ship-specific sweep, with result and evidence (24 rows; also shown in the page's Coverage audit table)
- [`data/scope_audit.json`](data/scope_audit.json) — browser-readable copy used by GitHub Pages

## Validation

Run `python scripts/validate_data.py` before publishing. It checks the 2027 date window, duplicate IDs, required HTTPS source/search links, USD labeling, audit-row count, and that the browser data copy matches the master JSON. The site deliberately labels route-average airfare and cruise fare snapshots as planning estimates—not live quotes—and keeps the honest result when an open-jaw fare cannot be computed.

