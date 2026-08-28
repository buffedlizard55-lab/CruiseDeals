# CruiseDeals

A static GitHub Pages research table for cruises departing U.S. West Coast ports during **February 15 – March 31, 2027**, with 2-adult cruise price snapshots, SFO-based flight planning, trip totals, official source links, promotions, and line-by-line verification — performed **twice** on Aug 28, 2026.

## What's inside

- **88 research records: 86 in-window sailings — the complete bookable population.** Pass 2 (Aug 28, 2026) re-swept every 2027 turnaround calendar ship by ship and confirmed **no indexed sailing or voyage variant is missing**; there are no further genuinely "new" entries that could be added without fabricating rows. Two out-of-window rows are retained for audit.
- Departure cities: San Diego, Los Angeles (San Pedro), Long Beach, San Francisco. Seattle was swept — no in-window mainstream departures (2027 season opens Apr 14). Vancouver is out of scope (not a U.S. port).
- Cruise lines represented: Carnival, Disney, Holland America, Norwegian, Princess, Royal Caribbean. Every other major line was swept and is accounted for in the [scope audit](data/cruise_line_scope_audit.csv). Shortest in-window duration is **3 nights** — no 1–2-night cruises operate from these ports in the window.
- Each row: cruise name, total price for 2 (2 × published interior per-person snapshot), duration, port stops, official voyage deep link, line-level promotions snapshot, review status.
- Flight plan per row: 2 adults, SFO ⇄ port, **arrive the day before / return the day after**; dated Google Flights search link + KAYAK route basis per row. San Francisco departures need no flight; open-jaw rows (voyages ending in Vancouver or Fort Lauderdale) use disclosed one-way bases.
- **Trip total** = cruise snapshot + 2-adult flight estimate. Not a live quote.

## Pass 2 — Aug 28, 2026 full re-verification (77 rows re-read + 9 flags re-checked)

Every in-window row was re-read from its own per-sailing schedule-index page and matched to the official voyage deep link:

- **45 prices confirmed unchanged · 18 price drops · 10 price increases** (each changed row shows the prior per-person value in `price_note` and is tagged PRICE MOVED ↕ on the site).
- **4 rows gained their first published USD price:** LA-25 Voyager 2/15 ($377pp), LA-44 Emerald 3/14 ($549pp — replacing a GBP third-party snapshot; the old "/ Hawaii" wording was wrong, voyage is E706 Classic California Coast), LA-56 Emerald 3/28 ($539pp, E708), LA-51 Island 3/2 ($1,879pp).
- **3 corrections (irregularities found and fixed):**
  - **LA-51** — Island Princess 3/2 is the **16-Night Panama Canal Ocean-to-Ocean ending in Fort Lauderdale** (voyage 2705); the earlier "Hawaii / Pacific" label was wrong. Open-jaw flight basis SFO→LAX + FLL→SFO applied.
  - **SD-21** — Serenade 3/28 calls **La Paz**, not Mazatlán (official link SR07SAN-394531984); price $649pp.
  - **SD-10** — Wonder 3/26 3-Night Baja calls **Catalina Island + Ensenada** (DW2246); stops corrected.
- **9 rows remain flagged REVIEW** (LA-43/45/46/47/48, LA-52/53/54/55): pass 2 re-confirmed no indexed departure exists on those dates. Data preserved, not deleted.
- Logs: [`data/verification_log_2026-08-28-pass2.csv`](data/verification_log_2026-08-28-pass2.csv) (one line per row) and the first-sweep log.

### Irregularities flagged in the earlier sweep (for manual review)

Emerald Princess rows LA-43/45/46/47/48 have dates with no indexed departure (verified Emerald LA departures in window: Feb 26; Mar 14, 21, 28). LA-52/53/54/55 (Radiance/Panorama) likewise mismatch the verified Long Beach calendar (actual: Radiance Mar 4, 9, 14, 28; Panorama Feb 21, 27, Mar 7, 13, 21, 27). Other verified scope findings: **Carnival Firenze** Feb–Mar 2027 sailings are roundtrip **Miami** (excluded, reconfirmed in pass 2); **Emerald Princess** San Francisco appearances Mar 16 / 25–26 / 30 are mid-cruise port calls, not SF departures.

## Flight basis (refreshed 2026-08-28, pass 2)

KAYAK route pages re-read Aug 28, 2026: SFO–SAN typical **$134–$287** RT (planning basis **$156/pp RT**; cheapest RT observed $78) · SFO–LAX typical **$138–$272** RT (basis **$204/pp ≈ midpoint**; cheapest RT $89) · YVR→SFO one-way typical **$137–$290**, cheapest $155 (open-jaw rows **$570 for 2**) · FLL→SFO one-way deals **$151–$170**, RT typical $278–$467, February indexed cheapest month (Island Princess open-jaw row **$530 for 2**). Every row links a dated Google Flights search for live checking; route-average bases are planning estimates, not quotes.

## Verification policy

Snapshot ≠ live quote; availability, cabin category, taxes/fees and promotions must be reconfirmed on the official page. Rows sourced from an index without a published price are explicitly marked. GBP third-party snapshots are never converted or summed into trip totals (the one such row, LA-44, was replaced by its published USD snapshot in pass 2). The two departures outside the requested window stay excluded. This project is not a booking engine and makes no guarantee of availability.

## Build & site

- `scripts/sweep_pass2.py` — applies the pass-2 verification results (fresh price reads, deep links, corrections, promo + flight-basis refresh), regenerates CSV/JSON, writes the pass-2 log and syncs `docs/data/`.
- `scripts/build_update.py` — first-sweep build (36 added rows, flight-basis normalization, flagging). Kept for provenance.
- `scripts/flight_search.py` — prints dated flight-search links (Google Flights + KAYAK) per sailing for manual price tracking.
- GitHub Pages: the zero-build app lives in [`docs/`](docs/) (with `.nojekyll` and its own `data/` snapshot). A root [`index.html`](index.html) forwards to `docs/`, so the existing GitHub Pages **root** source serves the app after merge; alternatively configure Pages to publish `/docs` directly.
