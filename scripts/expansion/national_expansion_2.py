#!/usr/bin/env python3
"""National expansion pass 2 (2026-08-30) — 50+ NEW verified in-window sailings.

Adds genuinely-new (non-duplicate) cruises departing U.S. ports in the
Feb 15 - Mar 31, 2027 window that were not already in the master list:
  * NEW PORTS: Baltimore, MD (BWI) and San Juan, PR (SJU, a U.S. territory port).
  * DEEPER DATES at Miami, Fort Lauderdale, Port Canaveral, Tampa (the prior pass
    only captured 2/20 & 2/27; March sailings were missing).

Every row read directly from cruisetimetables.com day pages (accessed 2026-08-30),
which republish the official cruise-line fare feed AND carry a per-sailing official
deep link. Each record: date, ship, cruise name, duration, itinerary stops, official
deep link, published Interior/Inside per-person USD price (MSC = lead-in 'From').

Flights: 2 adults, SFO round trip, arrive the day BEFORE embarkation / return the day
AFTER disembarkation, priced at the KAYAK route average x2 (planning estimate; live
quote required). One-way (open-jaw) sailings are flagged and NOT auto-priced.

A hard dedup guard rejects any (port, ship, date) already present in the master list.
Charter/theme & luxury rows with no bookable interior price are intentionally excluded
and recorded in the verification log as flagged irregularities.
"""
import csv, json, datetime, urllib.parse
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MASTER = ROOT / "data" / "cruises_master_verified.csv"
JSON = ROOT / "data" / "cruises.json"
DOCS_JSON = ROOT / "docs" / "data" / "cruises.json"
DOCS_CSV = ROOT / "docs" / "data" / "cruises_master_verified.csv"
PUB = "2026-08-30"

# port key -> (display port, airport, per-person RT planning $, kayak url, basis note)
PORTS = {
    "BWI":  ("Baltimore, MD",       "BWI", 485,
             "https://www.kayak.com/flight-routes/San-Francisco-SFO/Baltimore-Washington-BWI",
             "KAYAK SFO-BWI route average $485/person round trip (typical $374-$617); accessed 2026-08-30"),
    "SJU":  ("San Juan, PR",        "SJU", 532,
             "https://www.kayak.com/flight-routes/San-Francisco-SFO/San-Juan-Luis-Munoz-Marin-Intl-SJU",
             "KAYAK SFO-SJU route average $532/person round trip (typical $381-$661); accessed 2026-08-30"),
    "MIA":  ("Miami, FL",           "MIA", 422,
             "https://www.kayak.com/flight-routes/San-Francisco-SFO/Miami-MIA",
             "KAYAK SFO-MIA 12-month average $422/person round trip (typical $328-$545); accessed 2026-08-30"),
    "FLL":  ("Fort Lauderdale, FL", "FLL", 430,
             "https://www.kayak.com/flight-routes/San-Francisco-SFO/Fort-Lauderdale-FLL",
             "KAYAK SFO-FLL planning basis $430/person round trip (route avg ~$388; typical $278-$517); accessed 2026-08-30"),
    "PC":   ("Port Canaveral, FL",  "MCO", 430,
             "https://www.kayak.com/flight-routes/San-Francisco-SFO/Orlando-MCO",
             "KAYAK SFO-MCO (Orlando) planning basis $430/person round trip (Jan avg $376); accessed 2026-08-30"),
    "TPA":  ("Tampa, FL",           "TPA", 457,
             "https://www.kayak.com/flight-routes/San-Francisco-SFO/Tampa-TPA",
             "KAYAK SFO-TPA 12-month average $457/person round trip (typical $369-$578); accessed 2026-08-30"),
}

SRC = {
    "BWI":  "https://www.cruisetimetables.com/cruises-from-baltimore-maryland-2027.html",
    "SJU":  "https://www.cruisetimetables.com/cruises-from-san-juan-puerto-rico-2027.html",
    "MIA":  "https://www.cruisetimetables.com/cruises-from-miami-florida-2027.html",
    "FLL":  "https://www.cruisetimetables.com/cruises-from-fort-lauderdale-florida-2027.html",
    "PC":   "https://www.cruisetimetables.com/cruises-from-port-canaveral-florida-2027.html",
    "TPA":  "https://www.cruisetimetables.com/cruises-from-tampa-florida-2027.html",
}

# (portkey, ship, cruise_name, line, embark ISO, nights, stops, kind, pp, official, end_port_override)
# end_port_override = None for round-trip; else the disembark airport code for an open-jaw flag.
R = [
    # ---------- BALTIMORE, MD (fly BWI) — Carnival Pride 7N Bahamas ----------
    ("BWI","Carnival Pride","7 Night The Bahamas","Carnival Cruise Line","2027-02-21",7,"Nassau; Half Moon Cay; Celebration Key","Interior",718,"https://www.carnival.com/itinerary/7-day-the-bahamas-cruise/baltimore/pride/7-days/bak/?sailDate=02212027",None),
    ("BWI","Carnival Pride","7 Night The Bahamas","Carnival Cruise Line","2027-02-28",7,"Nassau; Half Moon Cay; Celebration Key","Interior",732,"https://www.carnival.com/itinerary/7-day-the-bahamas-cruise/baltimore/pride/7-days/bak/?sailDate=02282027",None),
    ("BWI","Carnival Pride","7 Night The Bahamas","Carnival Cruise Line","2027-03-07",7,"Nassau; Half Moon Cay; Celebration Key","Interior",1001,"https://www.carnival.com/itinerary/7-day-the-bahamas-cruise/baltimore/pride/7-days/bak/?sailDate=03072027",None),
    ("BWI","Carnival Pride","7 Night The Bahamas","Carnival Cruise Line","2027-03-14",7,"Nassau; Half Moon Cay; Celebration Key","Interior",869,"https://www.carnival.com/itinerary/7-day-the-bahamas-cruise/baltimore/pride/7-days/bak/?sailDate=03142027",None),
    ("BWI","Carnival Pride","7 Night The Bahamas","Carnival Cruise Line","2027-03-21",7,"Nassau; Half Moon Cay; Celebration Key","Interior",989,"https://www.carnival.com/itinerary/7-day-the-bahamas-cruise/baltimore/pride/7-days/bak/?sailDate=03212027",None),
    ("BWI","Carnival Pride","7 Night The Bahamas","Carnival Cruise Line","2027-03-28",7,"Nassau; Half Moon Cay; Celebration Key","Interior",979,"https://www.carnival.com/itinerary/7-day-the-bahamas-cruise/baltimore/pride/7-days/bak/?sailDate=03282027",None),

    # ---------- SAN JUAN, PR (fly SJU) ----------
    ("SJU","Celebrity Constellation","7 Night Southern Caribbean","Celebrity Cruises","2027-02-20",7,"St Thomas; Philipsburg (St. Maarten); St Johns (Antigua); Castries (St Lucia); Bridgetown (Barbados)","Interior",815,"https://www.celebritycruises.com/itinerary/7-night-southern-caribbean-cruise-from-san-juan-on-constellation-CS07D443?sailDate=2027-02-20&packageCode=CS07D450",None),
    ("SJU","Rhapsody of the Seas","7 Night Southern Caribbean","Royal Caribbean","2027-02-20",7,"Tortola; Philipsburg (St. Maarten); St Johns (Antigua); Basseterre (St. Kitts); St Croix","Interior",512,"https://www.royalcaribbean.com/cruises/itinerary/7-night-southern-caribbean-from-san-juan-on-rhapsody/RH07SJU-1851833253?sail-date=2027-02-20&currency=USD",None),
    ("SJU","Celebrity Constellation","7 Night Southern Caribbean","Celebrity Cruises","2027-02-27",7,"Tortola; Basseterre (St. Kitts); Roseau (Dominica); Castries (St Lucia); Bridgetown (Barbados)","Interior",716,"https://www.celebritycruises.com/itinerary/7-night-southern-caribbean-cruise-from-san-juan-on-constellation-CS07D449?sailDate=2027-02-27&packageCode=CS07D449",None),
    ("SJU","Rhapsody of the Seas","7 Night Southern Caribbean","Royal Caribbean","2027-02-27",7,"St Thomas; St Croix; Philipsburg (St. Maarten); St Johns (Antigua); Roseau (Dominica)","Interior",609,"https://www.royalcaribbean.com/cruises/itinerary/7-night-southern-caribbean-from-san-juan-on-rhapsody/RH07SJU-1321850013?sail-date=2027-02-27&currency=USD",None),
    ("SJU","Celebrity Constellation","7 Night Southern Caribbean","Celebrity Cruises","2027-03-06",7,"St Thomas; Philipsburg (St. Maarten); St Johns (Antigua); Castries (St Lucia); Bridgetown (Barbados)","Interior",658,"https://www.celebritycruises.com/itinerary/7-night-southern-caribbean-cruise-from-san-juan-on-constellation-CS07D443?sailDate=2027-03-06&packageCode=CS07D450",None),
    ("SJU","Celebrity Constellation","7 Night Southern Caribbean","Celebrity Cruises","2027-03-13",7,"St Thomas; Basseterre (St. Kitts); Roseau (Dominica); Castries (St Lucia); Bridgetown (Barbados)","Interior",863,"https://www.celebritycruises.com/itinerary/7-night-southern-caribbean-cruise-from-san-juan-on-constellation-CS07D447?sailDate=2027-03-13&packageCode=CS07D447",None),
    ("SJU","Valiant Lady","7 Night Southern Caribbean","Virgin Voyages","2027-02-20",7,"Tortola; Castries (St Lucia); Bridgetown (Barbados); Roseau (Dominica); Philipsburg (St. Maarten)","From",1043,"https://www.virginvoyages.com/book/voyage-planner/pre-checkout?currencyCode=USD&packageCode=7NSJR2&voyageId=VL2702207NSJR2",None),
    ("SJU","Valiant Lady","7 Night Southern Caribbean & Aruban Nights","Virgin Voyages","2027-02-27",7,"Oranjestad (Aruba); Willemstad (Curacao); Fort de France (Martinique); Basseterre (St. Kitts)","From",1043,"https://www.virginvoyages.com/book/voyage-planner/pre-checkout?currencyCode=USD&packageCode=7NSE&voyageId=VL2702277NSE",None),
    ("SJU","Valiant Lady","7 Night Southern Caribbean","Virgin Voyages","2027-03-06",7,"Philipsburg (St. Maarten); Bridgetown (Barbados); Castries (St Lucia); St Johns (Antigua); Tortola","From",1043,"https://www.virginvoyages.com/book/voyage-planner/pre-checkout?currencyCode=USD&packageCode=7NRT3&voyageId=VL2703067NRT3",None),
    ("SJU","Valiant Lady","6 Night Southern Caribbean","Virgin Voyages","2027-03-13",6,"Tortola; Basseterre (St. Kitts); St Johns (Antigua); Castries (St Lucia)","From",894,"https://www.virginvoyages.com/book/voyage-planner/pre-checkout?currencyCode=USD&packageCode=6NSJB&voyageId=VL2703136NSJB",None),
    # open-jaw: Rhapsody 10N ends in Miami
    ("SJU","Rhapsody of the Seas","10 Night Southern Caribbean (ends Miami)","Royal Caribbean","2027-03-06",10,"Tortola; Philipsburg (St. Maarten); St Johns (Antigua); Bridgetown (Barbados); Castries (St Lucia); Roseau (Dominica); St Croix; ends Miami, FL","Interior",1487,"https://www.royalcaribbean.com/cruises/itinerary/10-night-southern-caribbean-from-san-juan-on-rhapsody/RH10SJU-3860668643?sail-date=2027-03-06&currency=USD","MIA"),

    # ---------- MIAMI, FL (fly MIA) — March dates (new) ----------
    ("MIA","Carnival Magic","8 Night Eastern Caribbean","Carnival Cruise Line","2027-03-06",8,"Half Moon Cay; San Juan; Philipsburg (St. Maarten); St Thomas","Interior",659,"https://www.carnival.com/itinerary/8-day-eastern-caribbean-cruise/miami/magic/8-days/ceh/?sailDate=03062027",None),
    ("MIA","Carnival Sunrise","5 Night The Bahamas","Carnival Cruise Line","2027-03-06",5,"Nassau; Half Moon Cay; Celebration Key","Interior",327,"https://www.carnival.com/itinerary/5-day-the-bahamas-cruise/miami/sunrise/5-days/bhl/?sailDate=03062027",None),
    ("MIA","Freedom of the Seas","5 Night Perfect Day CocoCay & Bahamas","Royal Caribbean","2027-03-06",5,"Nassau; Perfect Day at CocoCay","Interior",678,"https://www.royalcaribbean.com/cruises/itinerary/5-night-perfect-day-cococay-bahamas-from-miami-on-freedom/FR05MIA-3040554279?sail-date=2027-03-06&currency=USD",None),
    ("MIA","Icon of the Seas","7 Night Western Caribbean & Perfect Day","Royal Caribbean","2027-03-06",7,"Costa Maya; Roatan; Cozumel; Perfect Day at CocoCay","Interior",1305,"https://www.royalcaribbean.com/cruises/itinerary/7-night-western-caribbean-perfect-day-from-miami-on-icon/IC07MIA-1694717396?sail-date=2027-03-06&currency=USD",None),
    ("MIA","Margaritaville at Sea Beachcomber","5 Night Bahamas & Eastern Caribbean","Margaritaville at Sea","2027-03-06",5,"Freeport; Puerto Plata/Amber Cove","Inside",349,"https://margaritavilleatsea.com/",None),
    ("MIA","Carnival Celebration","7 Night Eastern Caribbean","Carnival Cruise Line","2027-03-07",7,"Nassau; Puerto Plata/Amber Cove; Half Moon Cay; Celebration Key","Interior",670,"https://www.carnival.com/itinerary/7-day-eastern-caribbean-cruise/miami/celebration/7-days/cbw/?sailDate=03072027",None),
    ("MIA","Carnival Horizon","6 Night Western Caribbean","Carnival Cruise Line","2027-03-07",6,"Celebration Key; Montego Bay; George Town","Interior",523,"https://www.carnival.com/itinerary/6-day-western-caribbean-cruise/miami/horizon/6-days/cwm/?sailDate=03072027",None),
    ("MIA","Celebrity Xcel","7 Night Bahamas, Mexico & Cayman","Celebrity Cruises","2027-03-07",7,"Nassau; George Town; Cozumel; Costa Maya","Interior",775,"https://www.celebritycruises.com/itinerary/7-night-bahamas-mexico-cayman-from-miami-on-xcel-XC07E474?sailDate=2027-03-07&packageCode=XC07E474",None),
    ("MIA","Independence of the Seas","7 Night Eastern Caribbean & Perfect Day","Royal Caribbean","2027-03-07",7,"Perfect Day at CocoCay; San Juan; St Thomas","Interior",711,"https://www.royalcaribbean.com/cruises/itinerary/7-night-eastern-caribbean-perfect-day-from-miami-on-independence/ID07MIA-2916342427?sail-date=2027-03-07&currency=USD",None),
    ("MIA","Carnival Horizon","8 Night Southern Caribbean","Carnival Cruise Line","2027-03-13",8,"Oranjestad (Aruba); Willemstad (Curacao); Puerto Plata/Amber Cove","Interior",662,"https://www.carnival.com/itinerary/8-day-southern-caribbean-cruise/miami/horizon/8-days/css/?sailDate=03132027",None),
    ("MIA","Icon of the Seas","7 Night Eastern Caribbean & Perfect Day","Royal Caribbean","2027-03-13",7,"Philipsburg (St. Maarten); St Thomas; Perfect Day at CocoCay","Interior",1384,"https://www.royalcaribbean.com/cruises/itinerary/7-night-eastern-caribbean-perfect-day-from-miami-on-icon/IC07MIA-2623281014?sail-date=2027-03-13&currency=USD",None),
    ("MIA","MSC Meraviglia","8 Night Caribbean & Bahamas","MSC Cruises","2027-03-13",8,"Philipsburg (St. Maarten); St Johns (Antigua); St Thomas; Nassau","From",688,"https://www.msccruisesusa.com/itinerary-details/8-nights-caribbean--bahamas?cruiseid=MR20270313MIAMIA",None),

    # ---------- FORT LAUDERDALE, FL (fly FLL) — March dates (new) ----------
    ("FLL","Legend of the Seas","8 Night Perfect Day CocoCay & Caribbean","Royal Caribbean","2027-03-06",8,"Willemstad (Curacao); Oranjestad (Aruba); Cabo Rojo; Perfect Day at CocoCay","Interior",1767,"https://www.royalcaribbean.com/cruises/itinerary/8-night-perfect-day-cococay-caribbean-from-fort-lauderdale-on-legend/LE08FLL-1526021002?sail-date=2027-03-06&currency=USD",None),
    ("FLL","Regal Princess","8 Night Southern Caribbean with Aruba","Princess Cruises","2027-03-06",8,"Puerto Plata/Amber Cove; Willemstad (Curacao); Oranjestad (Aruba)","Interior",1799,"https://www.princess.com/itinerary-details/?voyageCode=G711",None),
    ("FLL","Rotterdam","10 Night Western Caribbean: Greater Antilles, Belize & Mexico","Holland America Line","2027-03-06",10,"Half Moon Cay; Falmouth (Jamaica); George Town; Roatan; Belize City; Cozumel","Inside",1299,"https://www.hollandamerica.com/en/us/find-a-cruise/c7w10d/y722",None),
    ("FLL","Adventure of the Seas","8 Night Southern Caribbean","Royal Caribbean","2027-03-13",8,"Nassau; Cabo Rojo; Oranjestad (Aruba); Willemstad (Curacao)","Interior",979,"https://www.royalcaribbean.com/cruises/itinerary/8-night-southern-caribbean-from-fort-lauderdale-on-adventure/AD08FLL-2966378858?sail-date=2027-03-13&currency=USD",None),
    ("FLL","Star Princess","7 Night Western Caribbean with Mexico","Princess Cruises","2027-03-13",7,"Roatan; Belize City; Cozumel","Interior",849,"https://www.princess.com/itinerary-details/?voyageCode=4712",None),
    ("FLL","Disney Destiny","5 Night Western Caribbean","Disney Cruise Line","2027-03-13",5,"Cozumel; Castaway Cay","Inside",3983,"https://disneycruise.disney.go.com/cruises-destinations/list/WD0102/5-Night-Western-Caribbean-Cruise-from-Fort-Lauderdale/2027-03-13-Disney-Destiny/",None),

    # ---------- PORT CANAVERAL, FL (fly MCO) — March dates (new) ----------
    ("PC","Carnival Vista","8 Night Southern Caribbean","Carnival Cruise Line","2027-03-06",8,"Willemstad (Curacao); Oranjestad (Aruba); Celebration Key","Interior",877,"https://www.carnival.com/itinerary/8-day-southern-caribbean-cruise/pt-canaveral/vista/8-days/cs9/?sailDate=03062027",None),
    ("PC","Celebrity Apex","7 Night Key West, Grand Cayman & Mexico","Celebrity Cruises","2027-03-06",7,"Key West; George Town; Cozumel","Interior",1038,"https://www.celebritycruises.com/itinerary/7-night-key-west-mexico-cayman-from-orlando-port-canaveral-on-apex-AX07W681?sailDate=2027-03-06&packageCode=AX07W681",None),
    ("PC","Disney Treasure","7 Night Western Caribbean","Disney Cruise Line","2027-03-06",7,"Cozumel; George Town; Falmouth (Jamaica); Castaway Cay","Inside",5628,"https://disneycruise.disney.go.com/cruises-destinations/list/WT0116/7-Night-Western-Caribbean-Cruise-from-Port-Canaveral/2027-03-06-Disney-Treasure/",None),
    ("PC","Harmony of the Seas","7 Night Eastern Caribbean & Perfect Day","Royal Caribbean","2027-03-06",7,"St Thomas; Puerto Plata/Amber Cove; Perfect Day at CocoCay","Interior",989,"https://www.royalcaribbean.com/cruises/itinerary/7-night-eastern-caribbean-perfect-day-from-orlando-port-canaveral-on-harmony/HM07PCN-1410170128?sail-date=2027-03-06&currency=USD",None),
    ("PC","Mardi Gras","7 Night Western Caribbean","Carnival Cruise Line","2027-03-06",7,"Roatan; Cozumel; Celebration Key","Interior",824,"https://www.carnival.com/itinerary/7-day-western-caribbean-cruise/pt-canaveral/mardi-gras/7-days/ws9/?sailDate=03062027",None),
    ("PC","Carnival Freedom","5 Night The Bahamas","Carnival Cruise Line","2027-03-13",5,"Nassau; Half Moon Cay; Celebration Key","Interior",533,"https://www.carnival.com/itinerary/5-day-the-bahamas-cruise/pt-canaveral/freedom/5-days/bmg/?sailDate=03132027",None),
    ("PC","Celebrity Apex","7 Night St. Thomas, St. Kitts & Puerto Plata","Celebrity Cruises","2027-03-13",7,"Puerto Plata/Amber Cove; St Thomas; Basseterre (St. Kitts)","Interior",1303,"https://www.celebritycruises.com/itinerary/7-night-st-thomas-st-kitts-cruise-from-orlando-port-canaveral-on-apex-AX07E469?sailDate=2027-03-13&packageCode=AX07E469",None),
    ("PC","Disney Treasure","7 Night Eastern Caribbean","Disney Cruise Line","2027-03-13",7,"St Thomas; Tortola; Castaway Cay","Inside",6159,"https://disneycruise.disney.go.com/cruises-destinations/list/WT0117/7-Night-Eastern-Caribbean-Cruise-from-Port-Canaveral/2027-03-13-Disney-Treasure/",None),
    ("PC","Harmony of the Seas","7 Night Eastern Caribbean & Perfect Day","Royal Caribbean","2027-03-13",7,"San Juan; Samana; Perfect Day at CocoCay","Interior",1066,"https://www.royalcaribbean.com/cruises/itinerary/7-night-eastern-caribbean-perfect-day-from-orlando-port-canaveral-on-harmony/HM07PCN-2764364175?sail-date=2027-03-13&currency=USD",None),
    ("PC","Mardi Gras","7 Night Eastern Caribbean","Carnival Cruise Line","2027-03-13",7,"Nassau; Half Moon Cay; Puerto Plata/Amber Cove; Celebration Key","Interior",822,"https://www.carnival.com/itinerary/7-day-eastern-caribbean-cruise/pt-canaveral/mardi-gras/7-days/eab/?sailDate=03132027",None),

    # ---------- TAMPA, FL (fly TPA) — March dates (new) ----------
    ("TPA","Carnival Paradise","5 Night Western Caribbean","Carnival Cruise Line","2027-03-06",5,"Roatan; Cozumel","Interior",465,"https://www.carnival.com/itinerary/5-day-western-caribbean-cruise/tampa/paradise/5-days/wcm/?sailDate=03062027",None),
    ("TPA","Radiance of the Seas","8 Night Western Caribbean","Royal Caribbean","2027-03-06",8,"Roatan; Costa Maya; Belize City; George Town","Interior",709,"https://www.royalcaribbean.com/cruises/itinerary/8-night-western-caribbean-from-tampa-on-radiance/RD08TPA-50893580?sail-date=2027-03-06&currency=USD",None),
    ("TPA","Carnival Legend","8 Night Caribbean & Panama","Carnival Cruise Line","2027-03-13",8,"Puerto Limon; Colon (Panama); George Town","Interior",1225,"https://www.carnival.com/itinerary/8-day-caribbean-and-panama-cruise/tampa/legend/8-days/wco/?sailDate=03132027",None),
    ("TPA","Jewel of the Seas","5 Night Western Caribbean","Royal Caribbean","2027-03-13",5,"Costa Maya; Cozumel","Interior",579,"https://www.royalcaribbean.com/cruises/itinerary/5-night-western-caribbean-from-tampa-on-jewel/JW05TPA-1176431029?sail-date=2027-03-13&currency=USD",None),
    ("TPA","Margaritaville at Sea Islander","5 Night Mexico Duo","Margaritaville at Sea","2027-03-13",5,"Cozumel; Progreso","Inside",399,"https://margaritavilleatsea.com/",None),
]


def money(n):
    return "$" + format(int(round(n)), ",")


def gflights(apt, out, back, oneway_dest=None):
    if oneway_dest:
        q = f"Flights from SFO to {apt} on {out} oneway 2 adults"
    else:
        q = f"Flights from SFO to {apt} {out}, return {back}"
    return "https://www.google.com/travel/flights?q=" + urllib.parse.quote(q)


def build_rows(existing_keys):
    counters = {}
    rows = []
    for (pk, ship, cname, line, embark, nights, stops, kind, pp, official, endport) in R:
        port_name, apt, base_pp, kayak, kayak_note = PORTS[pk]
        key = (port_name, ship, embark)
        assert key not in existing_keys, f"DUPLICATE against master: {key}"
        # local id sequence continues after any existing id for that port key prefix
        counters[pk] = counters.get(pk, 0) + 1
        rid = f"{pk}2-{counters[pk]:02d}"
        d_embark = datetime.date.fromisoformat(embark)
        d_disembark = d_embark + datetime.timedelta(days=nights)
        d_out = d_embark - datetime.timedelta(days=1)
        d_back = d_disembark + datetime.timedelta(days=1)
        cruise_2 = 2 * pp
        kind_label = {"Interior": "Interior", "Inside": "Inside", "From": "MSC/Virgin lead-in 'From'"}[kind]
        if kind == "From":
            pnote = (f"Lead-in 'From' fare ${pp:,}/person (cheapest cabin); total is 2 x snapshot (pub. {PUB})")
        else:
            pnote = f"{kind_label} snapshot ${pp:,}/person; total is 2 x snapshot (pub. {PUB})"

        if endport:  # open-jaw: do not fabricate a route-average airfare
            flight_route = f"SFO \u2192 {apt} (one-way); {endport} \u2192 SFO (one-way)"
            flight_cost = "Open-jaw — live quote required"
            flight_note = ("One-way (open-jaw) sailing: outbound SFO->embark port + return from a DIFFERENT "
                           "disembark port. No single route average applies; price both legs live. FLAGGED.")
            trip_total = "Live quote required (open-jaw)"
            trip_note = "Open-jaw voyage — cruise snapshot only; airfare must be quoted live for two different legs."
            fs_url = gflights(apt, d_out.isoformat(), d_back.isoformat(), oneway_dest=endport)
        else:
            flight_2 = 2 * base_pp
            flight_route = f"SFO \u2192 {apt} \u2192 SFO"
            flight_cost = f"{money(flight_2)} planning estimate"
            flight_note = kayak_note
            trip_total = money(cruise_2 + flight_2)
            trip_note = "Cruise snapshot (2 x interior) + 2-adult SFO round-trip flight planning estimate; live quote required."
            fs_url = gflights(apt, d_out.isoformat(), d_back.isoformat())

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
            "status": f"NEW {PUB} pass 2 \u2014 new ports (Baltimore, San Juan) + deeper March dates, line-by-line verified",
            "source_url": SRC[pk],
            "flight_out_date": d_out.isoformat(),
            "flight_return_date": d_back.isoformat(),
            "flight_route": flight_route,
            "flight_cost_2": flight_cost,
            "flight_source": flight_note,
            "flight_source_url": kayak,
            "trip_total_2": trip_total,
            "trip_total_note": trip_note,
            "price_currency": "USD",
            "verification_note": (
                f"National-expansion pass 2 ({PUB}): date, ship, duration, port sequence and published per-person "
                f"USD {kind_label} price read directly from the cruisetimetables day/from-port schedule index "
                f"(official fare feed), with the official cruise-line deep link from the same page. Dedup-checked "
                f"against the existing master list by (port, ship, date). Snapshot \u2260 live quote; cabin class, "
                f"taxes/fees and availability must be confirmed on the official page."
            ),
            "flight_search_url": fs_url,
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
