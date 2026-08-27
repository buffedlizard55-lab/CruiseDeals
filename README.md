# CruiseDeals

A static GitHub Pages research table for cruises departing U.S. West Coast ports during **February 15, 2027 through March 31, 2027**.

## Included

- 50 research records: **48 in-window sailings** plus **2 out-of-window records retained for audit**.
- Departure cities: San Diego, Los Angeles/Long Beach, and San Francisco.
- Cruise lines represented: Carnival, Disney, Holland America, Norwegian, Princess, and Royal Caribbean.
- Search and filter by ship, cruise line, departure port, price availability, and audit status.
- Total-for-two price snapshots where an indexed source published an interior rate; otherwise the table says **Not published** rather than guessing.
- Official cruise-line links are provided for manual confirmation. Linked timetable/aggregator sources are disclosed in the source-trail column.

## Verification policy

This repository intentionally separates a **schedule + price snapshot** from a live quote. Price snapshots can change, and may not include optional extras. Rows sourced from an index without a published price are flagged for review; the two departures outside the requested date window are explicitly excluded. Confirm cabin category, taxes, availability, and promotions on the official cruise-line page before booking.

The research snapshot is dated **2026-08-27 UTC**. It is not a booking engine and makes no guarantee of availability.

## GitHub Pages

The published page is in [`docs/`](docs/). The machine-readable files are:

- [`data/cruises_master_verified.csv`](data/cruises_master_verified.csv)
- [`data/cruises.json`](data/cruises.json)
