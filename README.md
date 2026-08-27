# CruiseDeals

A static GitHub Pages research table for cruises departing U.S. West Coast ports during **February 15, 2027 through March 31, 2027**.

## Included

- 52 research records: **50 in-window sailings** plus **2 out-of-window records retained for audit**.
- Departure cities: San Diego, Los Angeles/Long Beach, and San Francisco.
- Cruise lines represented: Carnival, Disney, Holland America, Norwegian, Princess, and Royal Caribbean.
- Search and filter by ship, cruise line, departure port, price availability, and audit status.
- Total-for-two cruise price snapshots where an indexed source published an interior rate; otherwise the table says **Not published** rather than guessing.
- Flight planning dates and cost estimates for two adults flying from SFO one day before departure and returning one day after the cruise. These use linked route averages—not date-specific live quotes—and the UI links to route searches for live confirmation.
- Official cruise-line links are provided for manual confirmation. Linked timetable/aggregator sources are disclosed in the source-trail column.

## Verification policy

This repository intentionally separates a **schedule + price snapshot** from a live quote. Price snapshots can change, and may not include optional extras. Rows sourced from an index without a published price are flagged for review; the two departures outside the requested date window are explicitly excluded. Confirm cabin category, taxes, availability, and promotions on the official cruise-line page before booking.

The research snapshot is dated **2026-08-27 UTC**. Five Princess travel-seller snapshots are explicitly retained in GBP and flagged for review; they are not converted to USD or treated as official quotes. Schedule-index rows are also flagged where the exact official sailing record was not available. The project is not a booking engine and makes no guarantee of availability.

## GitHub Pages

The published page is in [`docs/`](docs/). The machine-readable files are:

- [`data/cruises_master_verified.csv`](data/cruises_master_verified.csv)
- [`data/cruises.json`](data/cruises.json)
