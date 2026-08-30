#!/usr/bin/env python3
"""National expansion pass 3 (2026-08-30) — 51 NEW verified in-window sailings.

Fills the two remaining real gaps in the master list:

  * TWO BRAND-NEW U.S. DEPARTURE PORTS
      - Jacksonville, FL (fly JAX)  — Carnival Elation + Norwegian Dawn, 4N/5N Bahamas
      - Mobile, AL      (fly MOB)  — Carnival Spirit, 6N/8N/9N Bahamas & W. Caribbean
    Neither port appeared anywhere in the prior 189-row master list.

  * LATE-MARCH DATES (Mar 20 / Mar 27) at Miami, Tampa and mid/late-March at
    New Orleans, which passes 1-2 had stopped short of (they ended ~Mar 13).

Every row below was read LINE BY LINE from the cruisetimetables.com day / month
"from port" schedule pages (accessed 2026-08-30, site-dated 29 August 2026), which
republish the official cruise-line fare feed AND carry a per-sailing official deep
link. Each record carries: sail date, ship, official cruise name, nights, the full
published port sequence, the official cruise-line deep link, and the published
per-person USD Interior/Inside price (MSC = lead-in "From").

NOT ADDED (flagged irregularities, see verification log):
  * Carnival Spirit Mobile 2027-03-29 16N Panama Canal — OPEN JAW (Mobile -> Seattle).
    Kept out of the priced list; a single round-trip airfare cannot honestly be applied.
  * Norwegian Dawn Jacksonville 2027-04-04 15N Transatlantic — out of window (April).
  * Charleston, SC — cruisetimetables publishes NO 2027 departures (Carnival exited the
    port); zero in-window sailings, so nothing to add.

Flights: 2 adults, SFO round trip, arrive the day BEFORE embarkation / return the day
AFTER disembarkation, priced at the route's published average x 2 (planning estimate;
live quote required). A hard dedup guard rejects any (port, ship, date) already present.
"""
import csv, json, datetime, urllib.parse
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MASTER = ROOT / "data" / "cruises_master_verified.csv"
JSON = ROOT / "data" / "cruises.json"
DOCS_JSON = ROOT / "docs" / "data" / "cruises.json"
DOCS_CSV = ROOT / "docs" / "data" / "cruises_master_verified.csv"
PUB = "2026-08-30"

# port key -> (display port, airport, per-person RT planning $, route url, basis note)
PORTS = {
    "JAX": ("Jacksonville, FL", "JAX", 478,
            "https://www.kayak.com/flight-routes/San-Francisco-SFO/Jacksonville-JAX",
            "KAYAK SFO-JAX route page: 12-month average $478/person round trip "
            "(typical $369-$625; cheapest RT seen $306); accessed 2026-08-30"),
    "MOB": ("Mobile, AL", "MOB", 457,
            "https://www.kayak.com/flight-routes/San-Francisco-SFO/Mobile-MOB",
            "SFO-MOB average $457/person round trip (FareCompare route average; typical "
            "$332-$617; KAYAK cheapest RT seen $359; no nonstop, 1 connection); accessed 2026-08-30"),
    "MIA": ("Miami, FL", "MIA", 422,
            "https://www.kayak.com/flight-routes/San-Francisco-SFO/Miami-MIA",
            "KAYAK SFO-MIA 12-month average $422/person round trip (typical $328-$545); accessed 2026-08-30"),
    "TPA": ("Tampa, FL", "TPA", 457,
            "https://www.kayak.com/flight-routes/San-Francisco-SFO/Tampa-TPA",
            "KAYAK SFO-TPA 12-month average $457/person round trip (typical $369-$578); accessed 2026-08-30"),
    "MSY": ("New Orleans, LA", "MSY", 420,
            "https://www.kayak.com/flight-routes/San-Francisco-SFO/New-Orleans-MSY",
            "KAYAK SFO-MSY planning basis $420/person round trip; accessed 2026-08-30"),
}

SRC = {
    "JAX": "https://www.cruisetimetables.com/cruises-from-jacksonville-florida-2027.html",
    "MOB": "https://www.cruisetimetables.com/cruises-from-mobile-alabama-2027.html",
    "MIA": "https://www.cruisetimetables.com/cruises-from-miami-florida-2027.html",
    "TPA": "https://www.cruisetimetables.com/cruises-from-tampa-florida-2027.html",
    "MSY": "https://www.cruisetimetables.com/cruises-from-new-orleans-louisiana-2027.html",
}

# (portkey, ship, cruise_name, line, embark ISO, nights, stops, kind, pp, official)
R = [
    # ================= JACKSONVILLE, FL (NEW PORT, fly JAX) =================
    # Carnival Elation (Carnival) + Norwegian Dawn (NCL). Read from
    # fromjacksonvilleflorida-feb2027 / -mar2027 and the per-day pages.
    ("JAX", "Carnival Elation", "5 Night The Bahamas", "Carnival Cruise Line", "2027-02-15", 5,
     "Celebration Key; Half Moon Cay; Jacksonville", "Interior", 406,
     "https://www.carnival.com/itinerary/5-day-the-bahamas-cruise/jacksonville/elation/5-days/bmv/?sailDate=02152027"),
    ("JAX", "Norwegian Dawn", "5 Night Bahamas Round-Trip Jacksonville: Great Stirrup Cay & Nassau",
     "Norwegian Cruise Line", "2027-02-16", 5,
     "Freeport; Nassau; Great Stirrup Cay; Jacksonville", "Inside", 629,
     "https://www.ncl.com/vacation-builder?itineraryCode=DAWN5JAXFPONASNPIJAX&packageId=25382941&stateroomTypeCode=INSIDE&"),
    ("JAX", "Carnival Elation", "5 Night The Bahamas", "Carnival Cruise Line", "2027-02-20", 5,
     "Princess Cays; Celebration Key; Jacksonville", "Interior", 339,
     "https://www.carnival.com/itinerary/5-day-the-bahamas-cruise/jacksonville/elation/5-days/bmu/?sailDate=02202027"),
    ("JAX", "Norwegian Dawn", "5 Night Bahamas Round-Trip Jacksonville", "Norwegian Cruise Line",
     "2027-02-21", 5, "Freeport; Great Stirrup Cay; Nassau; Jacksonville", "Inside", 609,
     "https://www.ncl.com/vacation-builder?itineraryCode=DAWN5JAXFPONPINASJAX-NIC-DAWN5JAXFPONASNPIJAX&packageId=25382942&stateroomTypeCode=INSIDE&"),
    ("JAX", "Carnival Elation", "4 Night The Bahamas", "Carnival Cruise Line", "2027-02-25", 4,
     "Celebration Key; Nassau; Jacksonville", "Interior", 395,
     "https://www.carnival.com/itinerary/4-day-the-bahamas-cruise/jacksonville/elation/4-days/bme/?sailDate=02252027"),
    ("JAX", "Norwegian Dawn", "4 Night Bahamas Round-Trip Jacksonville: Great Stirrup Cay & Grand Bahama Island",
     "Norwegian Cruise Line", "2027-02-26", 4,
     "Freeport; Great Stirrup Cay; Jacksonville", "Inside", 559,
     "https://www.ncl.com/vacation-builder?itineraryCode=DAWN4JAXFPONPIJAX&packageId=25382928&stateroomTypeCode=INSIDE&"),
    ("JAX", "Carnival Elation", "5 Night The Bahamas", "Carnival Cruise Line", "2027-03-01", 5,
     "Celebration Key; Half Moon Cay; Jacksonville", "Interior", 466,
     "https://www.carnival.com/itinerary/5-day-the-bahamas-cruise/jacksonville/elation/5-days/bmv/?sailDate=03012027"),
    ("JAX", "Norwegian Dawn", "5 Night Bahamas Round-trip Jacksonville: Great Stirrup Cay & Key West",
     "Norwegian Cruise Line", "2027-03-02", 5,
     "Key West; Great Stirrup Cay; Jacksonville", "Inside", 659,
     "https://www.ncl.com/vacation-builder?itineraryCode=DAWN5JAXEYWNPIJAX&packageId=25382922&stateroomTypeCode=INSIDE&"),
    ("JAX", "Carnival Elation", "5 Night The Bahamas", "Carnival Cruise Line", "2027-03-06", 5,
     "Half Moon Cay; Celebration Key; Jacksonville", "Interior", 526,
     "https://www.carnival.com/itinerary/5-day-the-bahamas-cruise/jacksonville/elation/5-days/bmx/?sailDate=03062027"),
    ("JAX", "Norwegian Dawn", "5 Night Bahamas Round-trip Jacksonville: Great Stirrup Cay & Grand Bahama Island",
     "Norwegian Cruise Line", "2027-03-07", 5,
     "Great Stirrup Cay; Freeport; Jacksonville", "Inside", 659,
     "https://www.ncl.com/vacation-builder?itineraryCode=DAWN5JAXNPIFPOJAX-NIC-DAWN5JAXFPONPIJAX&packageId=25382943&stateroomTypeCode=INSIDE&"),
    ("JAX", "Carnival Elation", "4 Night The Bahamas", "Carnival Cruise Line", "2027-03-11", 4,
     "Celebration Key; Nassau; Jacksonville", "Interior", 485,
     "https://www.carnival.com/itinerary/4-day-the-bahamas-cruise/jacksonville/elation/4-days/bme/?sailDate=03112027"),
    ("JAX", "Norwegian Dawn", "4 Night Bahamas Round-Trip Jacksonville: Great Stirrup Cay & Grand Bahama Island",
     "Norwegian Cruise Line", "2027-03-12", 4,
     "Freeport; Great Stirrup Cay; Jacksonville", "Inside", 589,
     "https://www.ncl.com/vacation-builder?itineraryCode=DAWN4JAXFPONPIJAX&packageId=25382929&stateroomTypeCode=INSIDE&"),
    ("JAX", "Carnival Elation", "5 Night The Bahamas", "Carnival Cruise Line", "2027-03-15", 5,
     "Celebration Key; Half Moon Cay; Jacksonville", "Interior", 516,
     "https://www.carnival.com/itinerary/5-day-the-bahamas-cruise/jacksonville/elation/5-days/bmv/?sailDate=03152027"),
    ("JAX", "Norwegian Dawn", "5 Night Bahamas Round-Trip Jacksonville", "Norwegian Cruise Line",
     "2027-03-16", 5, "Freeport; Great Stirrup Cay; Nassau; Jacksonville", "Inside", 679,
     "https://www.ncl.com/vacation-builder?itineraryCode=DAWN5JAXFPONPINASJAX-NIC-DAWN5JAXFPONASNPIJAX&packageId=25382944&stateroomTypeCode=INSIDE&"),
    ("JAX", "Carnival Elation", "5 Night The Bahamas", "Carnival Cruise Line", "2027-03-20", 5,
     "Princess Cays; Celebration Key; Jacksonville", "Interior", 569,
     "https://www.carnival.com/itinerary/5-day-the-bahamas-cruise/jacksonville/elation/5-days/bmu/?sailDate=03202027"),
    ("JAX", "Norwegian Dawn", "5 Night Bahamas Round-trip Jacksonville", "Norwegian Cruise Line",
     "2027-03-21", 5, "Freeport; Great Stirrup Cay; Jacksonville", "Inside", 539,
     "https://www.ncl.com/vacation-builder?itineraryCode=DAWN5JAXFPONPIJAX&packageId=25382945&stateroomTypeCode=INSIDE&"),
    ("JAX", "Carnival Elation", "4 Night The Bahamas", "Carnival Cruise Line", "2027-03-25", 4,
     "Celebration Key; Nassau; Jacksonville", "Interior", 515,
     "https://www.carnival.com/itinerary/4-day-the-bahamas-cruise/jacksonville/elation/4-days/bme/?sailDate=03252027"),
    ("JAX", "Norwegian Dawn", "4 Night Bahamas Round-Trip Jacksonville: Great Stirrup Cay & Grand Bahama Island",
     "Norwegian Cruise Line", "2027-03-26", 4,
     "Freeport; Great Stirrup Cay; Jacksonville", "Inside", 609,
     "https://www.ncl.com/vacation-builder?itineraryCode=DAWN4JAXFPONPIJAX&packageId=25382930&stateroomTypeCode=INSIDE&"),
    ("JAX", "Carnival Elation", "5 Night The Bahamas", "Carnival Cruise Line", "2027-03-29", 5,
     "Celebration Key; Half Moon Cay; Jacksonville", "Interior", 576,
     "https://www.carnival.com/itinerary/5-day-the-bahamas-cruise/jacksonville/elation/5-days/bmv/?sailDate=03292027"),
    ("JAX", "Norwegian Dawn", "5 Night Bahamas Round-trip Jacksonville: Great Stirrup Cay & Key West",
     "Norwegian Cruise Line", "2027-03-30", 5,
     "Key West; Great Stirrup Cay; Jacksonville", "Inside", 709,
     "https://www.ncl.com/vacation-builder?itineraryCode=DAWN5JAXEYWNPIJAX&packageId=25382923&stateroomTypeCode=INSIDE&"),

    # ================= MOBILE, AL (NEW PORT, fly MOB) =================
    # Carnival Spirit is the only 2027 in-window operator. Read from
    # frommobilealabama-feb2027 / -mar2027.
    ("MOB", "Carnival Spirit", "8 Night The Bahamas", "Carnival Cruise Line", "2027-02-20", 8,
     "Key West; Celebration Key; Princess Cays; Nassau; Mobile", "Interior", 682,
     "https://www.carnival.com/itinerary/8-day-the-bahamas-cruise/mobile/spirit/8-days/ec6/?sailDate=02202027"),
    ("MOB", "Carnival Spirit", "6 Night The Bahamas", "Carnival Cruise Line", "2027-02-28", 6,
     "Celebration Key; Nassau; Mobile", "Interior", 482,
     "https://www.carnival.com/itinerary/6-day-the-bahamas-cruise/mobile/spirit/6-days/baa/?sailDate=02282027"),
    ("MOB", "Carnival Spirit", "8 Night The Bahamas", "Carnival Cruise Line", "2027-03-06", 8,
     "Key West; Celebration Key; Nassau; Half Moon Cay; Mobile", "Interior", 949,
     "https://www.carnival.com/itinerary/8-day-the-bahamas-cruise/mobile/spirit/8-days/ec5/?sailDate=03062027"),
    ("MOB", "Carnival Spirit", "6 Night The Bahamas", "Carnival Cruise Line", "2027-03-14", 6,
     "Celebration Key; Princess Cays; Mobile", "Interior", 700,
     "https://www.carnival.com/itinerary/6-day-the-bahamas-cruise/mobile/spirit/6-days/ba9/?sailDate=03142027"),
    ("MOB", "Carnival Spirit", "9 Night Western Caribbean", "Carnival Cruise Line", "2027-03-20", 9,
     "Cozumel; Roatan; George Town; Montego Bay; Mobile", "Interior", 1024,
     "https://www.carnival.com/itinerary/9-day-western-caribbean-cruise/mobile/spirit/9-days/jw1/?sailDate=03202027"),

    # ================= NEW ORLEANS, LA (deeper Feb/March dates) =================
    ("MSY", "Mariner of the Seas", "7 Night Western Caribbean Cruise", "Royal Caribbean",
     "2027-02-20", 7, "Cozumel; George Town; Falmouth (Jamaica); New Orleans", "Interior", 768,
     "https://www.royalcaribbean.com/cruises/itinerary/7-night-western-caribbean-from-new-orleans-on-mariner/MA07MSY-1227888471?sail-date=2027-02-20&currency=USD"),
    ("MSY", "Carnival Liberty", "7 Night Western Caribbean", "Carnival Cruise Line", "2027-02-21", 7,
     "Montego Bay; George Town; Cozumel; New Orleans", "Interior", 685,
     "https://www.carnival.com/itinerary/7-day-western-caribbean-cruise/new-orleans/liberty/7-days/wek/?sailDate=02212027"),
    ("MSY", "Norwegian Breakaway",
     "7 Night Caribbean Round-trip New Orleans: Harvest Caye, Cozumel & Roatan",
     "Norwegian Cruise Line", "2027-02-21", 7,
     "Cozumel; Roatan; Harvest Caye; Costa Maya; New Orleans", "Inside", 809,
     "https://www.ncl.com/vacation-builder?itineraryCode=BREAKAWAY7MSYCZMRTBBPICMAMSY-NIC-BREAKAWAY7MSYBPICMACZMRTBMSY&packageId=24870152&stateroomTypeCode=INSIDE&"),
    ("MSY", "Carnival Valor", "5 Night Western Caribbean", "Carnival Cruise Line", "2027-03-01", 5,
     "Cozumel; Progreso; New Orleans", "Interior", 419,
     "https://www.carnival.com/itinerary/5-day-western-caribbean-cruise/new-orleans/valor/5-days/cw6/?sailDate=03012027"),
    ("MSY", "Carnival Liberty", "7 Night Western Caribbean", "Carnival Cruise Line", "2027-03-07", 7,
     "Roatan; Belize City; Cozumel; New Orleans", "Interior", 609,
     "https://www.carnival.com/itinerary/7-day-western-caribbean-cruise/new-orleans/liberty/7-days/cwb/?sailDate=03072027"),
    ("MSY", "Norwegian Breakaway",
     "7 Night Caribbean Round-trip New Orleans: Harvest Caye, Cozumel & Roatan",
     "Norwegian Cruise Line", "2027-03-07", 7,
     "Cozumel; Roatan; Harvest Caye; Costa Maya; New Orleans", "Inside", 809,
     "https://www.ncl.com/vacation-builder?itineraryCode=BREAKAWAY7MSYCZMRTBBPICMAMSY-NIC-BREAKAWAY7MSYBPICMACZMRTBMSY&packageId=24870154&stateroomTypeCode=INSIDE&"),
    ("MSY", "Carnival Valor", "4 Night Western Caribbean", "Carnival Cruise Line", "2027-03-11", 4,
     "Cozumel; New Orleans", "Interior", 501,
     "https://www.carnival.com/itinerary/4-day-western-caribbean-cruise/new-orleans/valor/4-days/wcd/?sailDate=03112027"),
    ("MSY", "Mariner of the Seas", "7 Night Western Caribbean Cruise", "Royal Caribbean",
     "2027-03-13", 7, "Cozumel; George Town; Falmouth (Jamaica); New Orleans", "Interior", 843,
     "https://www.royalcaribbean.com/cruises/itinerary/7-night-western-caribbean-from-new-orleans-on-mariner/MA07MSY-1227888471?sail-date=2027-03-13&currency=USD"),
    ("MSY", "Carnival Liberty", "7 Night The Bahamas", "Carnival Cruise Line", "2027-03-14", 7,
     "Key West; Celebration Key; Nassau; New Orleans", "Interior", 725,
     "https://www.carnival.com/itinerary/7-day-the-bahamas-cruise/new-orleans/liberty/7-days/ecn/?sailDate=03142027"),
    ("MSY", "Norwegian Breakaway",
     "7 Night Caribbean Round-trip New Orleans: Harvest Caye, Cozumel & Roatan",
     "Norwegian Cruise Line", "2027-03-14", 7,
     "Cozumel; Roatan; Harvest Caye; Costa Maya; New Orleans", "Inside", 809,
     "https://www.ncl.com/vacation-builder?itineraryCode=BREAKAWAY7MSYCZMRTBBPICMAMSY-NIC-BREAKAWAY7MSYBPICMACZMRTBMSY&packageId=24870155&stateroomTypeCode=INSIDE&"),
    ("MSY", "Carnival Valor", "5 Night Western Caribbean", "Carnival Cruise Line", "2027-03-15", 5,
     "Cozumel; Progreso; New Orleans", "Interior", 614,
     "https://www.carnival.com/itinerary/5-day-western-caribbean-cruise/new-orleans/valor/5-days/cw6/?sailDate=03152027"),

    # ================= MIAMI, FL (late-March dates: Mar 1, Mar 20, Mar 27) =================
    ("MIA", "Carnival Conquest", "4 Night The Bahamas", "Carnival Cruise Line", "2027-03-01", 4,
     "Half Moon Cay; Celebration Key; Miami", "Interior", 305,
     "https://www.carnival.com/itinerary/4-day-the-bahamas-cruise/miami/conquest/4-days/bhp/?sailDate=03012027"),
    ("MIA", "MSC Seaside", "4 Night The Bahamas & Ocean Cay", "MSC Cruises", "2027-03-01", 4,
     "Nassau; Ocean Cay; Miami", "From", 241,
     "https://www.msccruisesusa.com/itinerary-details/4-nights-the-bahamas--ocean-cay?cruiseid=SE20270301MIAMIA"),
    ("MIA", "Norwegian Joy", "4 Night Bahamas Round-Trip Miami: Great Stirrup Cay",
     "Norwegian Cruise Line", "2027-03-01", 4, "Great Stirrup Cay; Miami", "Inside", 449,
     "https://www.ncl.com/vacation-builder?itineraryCode=JOY4MIANPIMIA&packageId=23379750&stateroomTypeCode=INSIDE&"),
    ("MIA", "Carnival Magic", "8 Night Southern Caribbean", "Carnival Cruise Line", "2027-03-20", 8,
     "Celebration Key; Oranjestad (Aruba); Willemstad (Curacao); Miami", "Interior", 773,
     "https://www.carnival.com/itinerary/8-day-southern-caribbean-cruise/miami/magic/8-days/czr/?sailDate=03202027"),
    ("MIA", "Carnival Sunrise", "5 Night The Bahamas", "Carnival Cruise Line", "2027-03-20", 5,
     "Nassau; Half Moon Cay; Celebration Key; Miami", "Interior", 452,
     "https://www.carnival.com/itinerary/5-day-the-bahamas-cruise/miami/sunrise/5-days/bhf/?sailDate=03202027"),
    ("MIA", "Freedom of the Seas", "5 Night Western Caribbean Cruise", "Royal Caribbean",
     "2027-03-20", 5, "Nassau; Puerto Plata/Amber Cove; Miami", "Interior", 528,
     "https://www.royalcaribbean.com/cruises/itinerary/5-night-western-caribbean-from-miami-on-freedom/FR05MIA-1172079608?sail-date=2027-03-20&currency=USD"),
    ("MIA", "Icon of the Seas", "7 Night Western Caribbean & Perfect Day", "Royal Caribbean",
     "2027-03-20", 7, "Costa Maya; Roatan; Cozumel; Perfect Day at CocoCay; Miami", "Interior", 1649,
     "https://www.royalcaribbean.com/cruises/itinerary/7-night-western-caribbean-perfect-day-from-miami-on-icon/IC07MIA-1694717396?sail-date=2027-03-20&currency=USD"),
    ("MIA", "Margaritaville at Sea Beachcomber", "7 Night Eastern Caribbean",
     "Margaritaville at Sea", "2027-03-20", 7,
     "St Thomas; San Juan; Puerto Plata/Amber Cove; Miami", "Inside", 669,
     "https://margaritavilleatsea.com/"),
    ("MIA", "Carnival Horizon", "8 Night Southern Caribbean", "Carnival Cruise Line", "2027-03-27", 8,
     "Oranjestad (Aruba); Willemstad (Curacao); Puerto Plata/Amber Cove; Miami", "Interior", 712,
     "https://www.carnival.com/itinerary/8-day-southern-caribbean-cruise/miami/horizon/8-days/css/?sailDate=03272027"),
    ("MIA", "Icon of the Seas", "7 Night Eastern Caribbean & Perfect Day", "Royal Caribbean",
     "2027-03-27", 7, "Philipsburg (St. Maarten); St Thomas; Perfect Day at CocoCay; Miami",
     "Interior", 1403,
     "https://www.royalcaribbean.com/cruises/itinerary/7-night-eastern-caribbean-perfect-day-from-miami-on-icon/IC07MIA-2623281014?sail-date=2027-03-27&currency=USD"),
    ("MIA", "Margaritaville at Sea Beachcomber", "7 Night Key West, Bahamas & Western Caribbean",
     "Margaritaville at Sea", "2027-03-27", 7,
     "Key West; George Town; Montego Bay; Nassau; Miami", "Inside", 599,
     "https://margaritavilleatsea.com/"),
    ("MIA", "MSC Meraviglia", "8 Night Eastern Caribbean", "MSC Cruises", "2027-03-27", 8,
     "Philipsburg (St. Maarten); Basseterre (St. Kitts); St Thomas; Puerto Plata/Amber Cove; Miami",
     "From", 708,
     "https://www.msccruisesusa.com/itinerary-details/8-nights-eastern-caribbean?cruiseid=MR20270327MIAMIA"),

    # ================= TAMPA, FL (late-March dates) =================
    ("TPA", "Carnival Paradise", "5 Night The Bahamas", "Carnival Cruise Line", "2027-03-20", 5,
     "Celebration Key; Nassau; Tampa", "Interior", 528,
     "https://www.carnival.com/itinerary/5-day-the-bahamas-cruise/tampa/paradise/5-days/bad/?sailDate=03202027"),
    ("TPA", "Norwegian Gem", "7 Night Caribbean Round-trip Tampa: Harvest Caye, Cozumel & Roatan",
     "Norwegian Cruise Line", "2027-03-20", 7,
     "Harvest Caye; Roatan; Cozumel; Tampa", "Inside", 889,
     "https://www.ncl.com/vacation-builder?itineraryCode=GEM7TPABPIRTBCZMTPA-NIC-GEM7TPABPICZMRTBTPA&packageId=25382904&stateroomTypeCode=INSIDE&"),
    ("TPA", "Radiance of the Seas", "6 Night Western Caribbean Cruise", "Royal Caribbean",
     "2027-03-20", 6, "Cozumel; Belize City; Costa Maya; Tampa", "Interior", 599,
     "https://www.royalcaribbean.com/cruises/itinerary/6-night-western-caribbean-from-tampa-on-radiance/RD06TPA-86128255?sail-date=2027-03-20&currency=USD"),
]


def money(n):
    return "$" + format(int(round(n)), ",")


def gflights(apt, out, back):
    q = f"Flights from SFO to {apt} {out}, return {back}"
    return "https://www.google.com/travel/flights?q=" + urllib.parse.quote(q)


def build_rows(existing_keys):
    counters = {}
    rows = []
    for (pk, ship, cname, line, embark, nights, stops, kind, pp, official) in R:
        port_name, apt, base_pp, kayak, kayak_note = PORTS[pk]
        key = (port_name, ship, embark)
        assert key not in existing_keys, f"DUPLICATE against master: {key}"
        existing_keys.add(key)
        assert "2027-02-15" <= embark <= "2027-03-31", f"OUT OF WINDOW: {key}"
        assert nights >= 2, f"too short: {key}"
        counters[pk] = counters.get(pk, 0) + 1
        rid = f"{pk}3-{counters[pk]:02d}"
        d_embark = datetime.date.fromisoformat(embark)
        d_disembark = d_embark + datetime.timedelta(days=nights)
        d_out = d_embark - datetime.timedelta(days=1)
        d_back = d_disembark + datetime.timedelta(days=1)
        cruise_2 = 2 * pp
        flight_2 = 2 * base_pp
        kind_label = {"Interior": "Interior", "Inside": "Inside",
                      "From": "MSC lead-in 'From'"}[kind]
        if kind == "From":
            pnote = (f"Lead-in 'From' fare ${pp:,}/person (cheapest cabin); "
                     f"total is 2 x snapshot (pub. {PUB})")
        else:
            pnote = f"{kind_label} snapshot ${pp:,}/person; total is 2 x snapshot (pub. {PUB})"

        rows.append({
            "id": rid,
            "name": f"{ship} \u2014 {cname}",
            "line": line,
            "date": embark,
            "duration": f"{nights} nights",
            "port": port_name,
            "stops": stops,
            "price": money(cruise_2),
            "price_note": pnote,
            "source": "CruiseTimetables (official fare feed) + official cruise-line deep link",
            "official": official,
            "promo": "No sailing-specific promo verified (confirm current line offers on the official page)",
            "status": f"NEW {PUB} pass 3 \u2014 new ports (Jacksonville, Mobile) + late-March dates, line-by-line verified",
            "source_url": SRC[pk],
            "flight_out_date": d_out.isoformat(),
            "flight_return_date": d_back.isoformat(),
            "flight_route": f"SFO \u2192 {apt} \u2192 SFO",
            "flight_cost_2": f"{money(flight_2)} planning estimate",
            "flight_source": kayak_note,
            "flight_source_url": kayak,
            "trip_total_2": money(cruise_2 + flight_2),
            "trip_total_note": ("Cruise snapshot (2 x lead-in cabin) + 2-adult SFO round-trip flight "
                                "planning estimate (arrive 1 day early / return 1 day late); live quote required."),
            "price_currency": "USD",
            "verification_note": (
                f"National-expansion pass 3 ({PUB}): sail date, ship, duration, full port sequence and the "
                f"published per-person USD {kind_label} price were read line by line from the cruisetimetables "
                f"day / from-port 2027 schedule pages (official cruise-line fare feed), and the official "
                f"cruise-line deep link was taken from the same page. Dedup-checked against the existing master "
                f"list by (port, ship, date); in-window assertion 2027-02-15..2027-03-31 enforced in code. "
                f"Snapshot \u2260 live quote; cabin class, taxes/fees and availability must be reconfirmed."
            ),
            "flight_search_url": gflights(apt, d_out.isoformat(), d_back.isoformat()),
        })
    return rows


def main():
    with MASTER.open(newline="") as f:
        reader = csv.DictReader(f)
        fields = reader.fieldnames
        existing = list(reader)
    existing_keys = set((r["port"], r["name"].split(" \u2014 ")[0].strip(), r["date"]) for r in existing)
    existing_ids = {r["id"] for r in existing}
    new = build_rows(existing_keys)
    for r in new:
        assert r["id"] not in existing_ids, f"dup id {r['id']}"
    combined = existing + new
    with MASTER.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(combined)
    with JSON.open("w") as f:
        json.dump(combined, f, indent=1, ensure_ascii=False)
    DOCS_JSON.write_text(JSON.read_text())
    DOCS_CSV.write_text(MASTER.read_text())
    inwin = sum(1 for r in combined if "2027-02-15" <= r["date"] <= "2027-03-31")
    print(f"added {len(new)} new rows; total {len(combined)}; in-window {inwin}")
    from collections import Counter
    for p, n in Counter(r["port"] for r in new).most_common():
        print(f"  {n:2d}  {p}")


if __name__ == "__main__":
    main()
