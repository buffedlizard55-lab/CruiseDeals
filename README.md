# CruiseDeals

A static GitHub Pages research table for cruises departing U.S. West Coast ports during **February 15 – March 31, 2027**, with 2-adult cruise price snapshots, SFO-based flight planning estimates, trip totals, official source links and line-by-line verification.

## What's inside

- **88 research records**: **86 in-window sailings** (50 from the Aug 27 sweep + **36 newly verified on Aug 28, 2026**) plus 2 out-of-window rows retained for audit.
- Departure cities: San Diego, Los Angeles (San Pedro), Long Beach, San Francisco. Seattle was swept — no in-window mainstream departures. Vancouver is out of scope (not a U.S. port).
- Cruise lines represented: Carnival, Disney, Holland America, Norwegian, Princess, Royal Caribbean. Every other major line was swept and is accounted for in the scope audit.
- Each row: cruise name, total price for 2 (2 × published interior per-person snapshot; **"Not published"** where no trusted index publishes a price — never guessed), duration, port stops, official source links, line-level promotions snapshot, review status.
- Flight plan per row: 2 adults, SFO ⇄ port, **arrive the day before / return the day after**; dated Google Flights search link + KAYAK route-average basis per row. San Francisco departures need no flight.
- **Trip total** = cruise snapshot + 2-adult flight estimate. Not a live quote.

## Aug 28, 2026 sweep — line by line

36 new rows were verified one sailing at a time: departure date, duration, full port sequence and the interior per-person snapshot were each read from the sailing's own schedule-index page and matched to the official cruise-line voyage deep link before inclusion. See:

- [`data/verification_log_2026-08-28.csv`](data/verification_log_2026-08-28.csv) — every check, per row
- [`data/cruises_master_verified.csv`](data/cruises_master_verified.csv) — the master table
- [`data/cruises.json`](data/cruises.json) — feeds the site (`docs/data/cruises.json` is the site-local snapshot)

### Irregularities flagged in the prior list (for manual review)

Nine pre-existing rows could not be matched to the verified 2027 schedule index and are now marked **REVIEW — date mismatch** (data preserved, not deleted): **LA-43, LA-45, LA-46, LA-47, LA-48** (Emerald Princess dates that have no indexed departure — verified Emerald LA departures in window are Feb 26; Mar 14, 21, 28), **LA-52** (Radiance 3/5 → likely Mar 4 or Mar 9), **LA-53** (Panorama 3/12 → likely Sat Mar 13), **LA-54** (Radiance 3/19 — ship is at sea on the verified Mar 14 14-Night Hawaii sailing), **LA-55** (Panorama 3/26 → likely Sat Mar 27). LA-44 keeps its GBP warning and gained a verified-identity note (Mar 14 = 7-Night Classic California Coast, E706).

Other verified scope findings: **Carnival Firenze** Feb–Mar 2027 sailings are all roundtrip **Miami** (excluded); **Emerald Princess** San Francisco appearances Mar 16 / 25–26 / 30 are mid-cruise port calls on LA roundtrips, not SF departures; **Seattle**'s 2027 season opens Apr 14 (Carnival Spirit).

## Flight basis (refreshed 2026-08-28)

Uniform route averages from KAYAK route pages (accessed 2026-08-28; date-specific live quotes still required): SFO–SAN **$156** pp RT (typical $134–$287) · SFO–LAX **$204** pp RT (12-mo avg; typical $138–$272; February historically peaks) · open-jaw SFO→SAN + YVR→SFO **$285** pp for the two HAL variants ending in Vancouver. Older rows previously referenced an Expedia $177/LAX basis; all rows now share the KAYAK basis, and every row links a dated Google Flights search for live checking.

## Verification policy

Snapshot ≠ live quote; availability, cabin category, taxes/fees and promotions must be reconfirmed on the official page. Rows sourced from an index without a published price are explicitly marked; the two departures outside the requested window stay excluded; GBP third-party snapshots are never converted or summed into trip totals. This project is not a booking engine and makes no guarantee of availability.

## Build & site

- `scripts/build_update.py` — regenerates the CSV/JSON corpus, applies the uniform flight basis, appends verified rows and syncs `docs/data/`.
- `scripts/flight_search.py` — prints dated flight-search links (Google Flights + KAYAK) per sailing for manual price tracking.
- GitHub Pages: publish from [`docs/`](docs/) (contains `.nojekyll`; the page is a zero-build static site that reads `docs/data/cruises.json`).
