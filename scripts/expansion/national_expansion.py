#!/usr/bin/env python3
"""National expansion pass (2026-08-30) — add verified cruises departing from ANY
U.S. port city (not just the West Coast) in the Feb 15 - Mar 31, 2027 window.

The prior project scope was limited to U.S. WEST COAST ports (San Diego, Los Angeles,
Long Beach, San Francisco). The user's requirement is *any port city in the USA*, which
opens the far larger Gulf Coast + East Coast market (Galveston, New Orleans, Port
Canaveral, Tampa, Fort Lauderdale, Miami, ...). This pass adds 60 genuinely-new,
line-by-line-verified in-window sailings from those ports.

Every row below was read directly from cruisetimetables.com day/month/from-port pages
(accessed 2026-08-29/30), which publish the official fare feed AND a per-sailing official
cruise-line deep link. Each record carries: date, ship, cruise name, duration, itinerary
stops, official deep link, and a published INTERIOR/INSIDE (or MSC lead-in "From")
per-person USD price. Nothing is invented; a couple of MSC "From" fares and Disney
"Inside" fares are labelled as such. Charter/theme sailings with no published fare
(Star Trek, The 80s Cruise, JoCo, Rock Legends, Jam Cruise) were intentionally excluded.

Flights: 2 adults, SFO round trip, arrive the day BEFORE embarkation and fly home the day
AFTER disembarkation. Cost is a KAYAK route-average planning basis per person x2 (live
quote still required), matching the existing project's flight methodology.
"""
import csv, json, datetime, urllib.parse
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MASTER = ROOT / "data" / "cruises_master_verified.csv"
JSON = ROOT / "data" / "cruises.json"
DOCS_JSON = ROOT / "docs" / "data" / "cruises.json"
DOCS_CSV = ROOT / "docs" / "data" / "cruises_master_verified.csv"
PUB = "2026-08-30"

# Per-port flight basis: airport code, per-person round-trip planning $, KAYAK route page,
# and a short human note about the route average / typical range.
PORTS = {
    "GAL":  ("Galveston, TX",       "HOU", 300,
             "https://www.kayak.com/flight-routes/San-Francisco-SFO/Houston-Hobby-other-airports-HOU",
             "KAYAK SFO->Houston planning basis ~$300/person round trip (seasonal range ~$163-$485); accessed 2026-08-30"),
    "NOLA": ("New Orleans, LA",     "MSY", 420,
             "https://www.kayak.com/flight-routes/San-Francisco-SFO/New-Orleans-Louis-Armstrong-MSY",
             "KAYAK SFO-MSY planning basis $420/person round trip (typical ~$339-$481); accessed 2026-08-30"),
    "PC":   ("Port Canaveral, FL",  "MCO", 430,
             "https://www.kayak.com/flight-routes/San-Francisco-SFO/Orlando-MCO",
             "KAYAK SFO-MCO (Orlando) planning basis $430/person round trip (Jan avg $376; Southwest avg ~$449); accessed 2026-08-30"),
    "TPA":  ("Tampa, FL",           "TPA", 457,
             "https://www.kayak.com/flight-routes/San-Francisco-SFO/Tampa-TPA",
             "KAYAK SFO-TPA 12-month average $457/person round trip (typical $369-$578); accessed 2026-08-30"),
    "FLL":  ("Fort Lauderdale, FL", "FLL", 430,
             "https://www.kayak.com/flight-routes/San-Francisco-SFO/Fort-Lauderdale-FLL",
             "KAYAK SFO-FLL planning basis $430/person round trip (route avg ~$388; typical $278-$517); accessed 2026-08-30"),
    "MIA":  ("Miami, FL",           "MIA", 422,
             "https://www.kayak.com/flight-routes/San-Francisco-SFO/Miami-MIA",
             "KAYAK SFO-MIA 12-month average $422/person round trip (typical $328-$545); accessed 2026-08-30"),
}

SRC = {
    "GAL":  "https://www.cruisetimetables.com/cruises-from-galveston-texas-2027.html",
    "NOLA": "https://www.cruisetimetables.com/cruises-from-new-orleans-louisiana-2027.html",
    "PC":   "https://www.cruisetimetables.com/cruises-from-port-canaveral-florida-2027.html",
    "TPA":  "https://www.cruisetimetables.com/cruises-from-tampa-florida-2027.html",
    "FLL":  "https://www.cruisetimetables.com/cruises-from-fort-lauderdale-florida-2027.html",
    "MIA":  "https://www.cruisetimetables.com/cruises-from-miami-florida-2027.html",
}

# (port, ship, cruise_name, line, embark ISO, nights, stops, price_kind, price_pp, official_url)
R = [
    # ---------------- GALVESTON, TX (fly HOU) ----------------
    ("GAL","Carnival Breeze","4 Night Western Caribbean","Carnival Cruise Line","2027-02-18",4,"Cozumel","Interior",417,"https://www.carnival.com/itinerary/4-day-western-caribbean-cruise/galveston/breeze/4-days/glb/?sailDate=02182027"),
    ("GAL","Carnival Dream","7 Night The Bahamas","Carnival Cruise Line","2027-02-27",7,"Key West; Celebration Key; Nassau","Interior",648,"https://www.carnival.com/itinerary/7-day-the-bahamas-cruise/galveston/dream/7-days/ec8/?sailDate=02272027"),
    ("GAL","Norwegian Viva","7 Night Caribbean: Harvest Caye, Cozumel & Roatan","Norwegian Cruise Line","2027-02-27",7,"Cozumel; Roatan; Harvest Caye; Costa Maya","Inside",859,"https://www.ncl.com/vacation-builder?itineraryCode=VIVA7GALCZMRTBBPICMAGAL-NIC-VIVA7GALBPICMACZMRTBGAL&packageId=23369093&stateroomTypeCode=INSIDE&"),
    ("GAL","Carnival Jubilee","6 Night Western Caribbean","Carnival Cruise Line","2027-02-28",6,"Cozumel; Roatan","Interior",530,"https://www.carnival.com/itinerary/6-day-western-caribbean-cruise/galveston/jubilee/6-days/wcp/?sailDate=02282027"),
    ("GAL","MSC Seascape","7 Night Western Caribbean","MSC Cruises","2027-02-28",7,"Costa Maya; Roatan; Cozumel","From",470,"https://www.msccruisesusa.com/itinerary-details/7-nights-western-caribbean?cruiseid=SC20270228GLSGLS"),
    ("GAL","Symphony of the Seas","7 Night Western Caribbean","Royal Caribbean","2027-02-28",7,"Costa Maya; Roatan; Cozumel","Interior",862,"https://www.royalcaribbean.com/cruises/itinerary/7-night-western-caribbean-from-galveston-on-symphony/SY07GAL-3851841824?sail-date=2027-02-28&currency=USD"),
    ("GAL","Carnival Miracle","4 Night Western Caribbean","Carnival Cruise Line","2027-03-01",4,"Cozumel","Interior",467,"https://www.carnival.com/itinerary/4-day-western-caribbean-cruise/galveston/miracle/4-days/glb/?sailDate=03012027"),
    ("GAL","Liberty of the Seas","5 Night Western Caribbean","Royal Caribbean","2027-03-01",5,"Cozumel; Costa Maya","Interior",573,"https://www.royalcaribbean.com/cruises/itinerary/5-night-western-caribbean-from-galveston-on-liberty/LB05GAL-2956042566?sail-date=2027-03-01&currency=USD"),
    ("GAL","Disney Magic","4 Night Western Caribbean (Marvel Days at Sea)","Disney Cruise Line","2027-03-03",4,"Progreso","Inside",2020,"https://disneycruise.disney.go.com/cruises-destinations/list/DM1781/4-Night-Western-Caribbean-Cruise-from-Galveston-with-Marvel-Days-at-Sea/2027-03-03-Disney-Magic/"),
    ("GAL","Carnival Miracle","10 Night Caribbean & Panama","Carnival Cruise Line","2027-03-05",10,"Cozumel; Puerto Limon; Colon; Roatan","Interior",1137,"https://www.carnival.com/itinerary/10-day-caribbean-and-panama-cruise/galveston/miracle/10-days/wc8/?sailDate=03052027"),
    ("GAL","Carnival Dream","7 Night Western Caribbean","Carnival Cruise Line","2027-03-06",7,"Roatan; Belize City; Cozumel","Interior",738,"https://www.carnival.com/itinerary/7-day-western-caribbean-cruise/galveston/dream/7-days/wec/?sailDate=03062027"),
    ("GAL","Carnival Jubilee","8 Night The Bahamas","Carnival Cruise Line","2027-03-06",8,"Nassau; Half Moon Cay; Celebration Key","Interior",1224,"https://www.carnival.com/itinerary/8-day-the-bahamas-cruise/galveston/jubilee/8-days/ba7/?sailDate=03062027"),
    ("GAL","Liberty of the Seas","5 Night Western Caribbean","Royal Caribbean","2027-03-06",5,"Costa Maya; Cozumel","Interior",815,"https://www.royalcaribbean.com/cruises/itinerary/5-night-western-caribbean-from-galveston-on-liberty/LB05GAL-2956042566?sail-date=2027-03-06&currency=USD"),
    ("GAL","Norwegian Viva","7 Night Caribbean: Harvest Caye, Cozumel & Roatan","Norwegian Cruise Line","2027-03-06",7,"Cozumel; Roatan; Harvest Caye; Costa Maya","Inside",1039,"https://www.ncl.com/vacation-builder?itineraryCode=VIVA7GALCZMRTBBPICMAGAL-NIC-VIVA7GALBPICMACZMRTBGAL&packageId=23369094&stateroomTypeCode=INSIDE&"),
    ("GAL","Disney Magic","5 Night Western Caribbean (Marvel Days at Sea)","Disney Cruise Line","2027-03-07",5,"Cozumel; Progreso","Inside",3561,"https://disneycruise.disney.go.com/cruises-destinations/list/DM1782/5-Night-Western-Caribbean-Cruise-from-Galveston-with-Marvel-Days-at-Sea/2027-03-07-Disney-Magic/"),
    ("GAL","MSC Seascape","7 Night Western Caribbean","MSC Cruises","2027-03-07",7,"Costa Maya; Roatan; Cozumel","From",620,"https://www.msccruisesusa.com/itinerary-details/7-nights-western-caribbean?cruiseid=SC20270307GLSGLS"),
    ("GAL","Carnival Dream","7 Night Western Caribbean","Carnival Cruise Line","2027-03-20",7,"Montego Bay; George Town; Cozumel","Interior",779,"https://www.carnival.com/itinerary/7-day-western-caribbean-cruise/galveston/dream/7-days/cwc/?sailDate=03202027"),
    ("GAL","Carnival Jubilee","8 Night The Bahamas","Carnival Cruise Line","2027-03-20",8,"Nassau; Half Moon Cay; Celebration Key","Interior",914,"https://www.carnival.com/itinerary/8-day-the-bahamas-cruise/galveston/jubilee/8-days/ba9/?sailDate=03202027"),
    ("GAL","Liberty of the Seas","5 Night Western Caribbean","Royal Caribbean","2027-03-20",5,"Costa Maya; Cozumel","Interior",603,"https://www.royalcaribbean.com/cruises/itinerary/5-night-western-caribbean-from-galveston-on-liberty/LB05GAL-2956042566?sail-date=2027-03-20&currency=USD"),
    ("GAL","Norwegian Viva","7 Night Caribbean: Harvest Caye, Cozumel & Roatan","Norwegian Cruise Line","2027-03-20",7,"Cozumel; Roatan; Harvest Caye; Costa Maya","Inside",1109,"https://www.ncl.com/vacation-builder?itineraryCode=VIVA7GALCZMRTBBPICMAGAL-NIC-VIVA7GALBPICMACZMRTBGAL&packageId=23369096&stateroomTypeCode=INSIDE&"),

    # ---------------- NEW ORLEANS, LA (fly MSY) ----------------
    ("NOLA","Carnival Valor","5 Night Western Caribbean","Carnival Cruise Line","2027-02-15",5,"Cozumel; Progreso","Interior",394,"https://www.carnival.com/itinerary/5-day-western-caribbean-cruise/new-orleans/valor/5-days/cw6/?sailDate=02152027"),
    ("NOLA","Carnival Valor","5 Night Western Caribbean","Carnival Cruise Line","2027-02-20",5,"Cozumel; Progreso","Interior",370,"https://www.carnival.com/itinerary/5-day-western-caribbean-cruise/new-orleans/valor/5-days/cw6/?sailDate=02202027"),
    ("NOLA","Carnival Valor","5 Night Western Caribbean","Carnival Cruise Line","2027-03-06",5,"Cozumel; Progreso","Interior",514,"https://www.carnival.com/itinerary/5-day-western-caribbean-cruise/new-orleans/valor/5-days/cw6/?sailDate=03062027"),
    ("NOLA","Mariner of the Seas","7 Night Western Caribbean","Royal Caribbean","2027-03-06",7,"Cozumel; George Town; Falmouth","Interior",646,"https://www.royalcaribbean.com/cruises/itinerary/7-night-western-caribbean-from-new-orleans-on-mariner/MA07MSY-1227888471?sail-date=2027-03-06&currency=USD"),
    ("NOLA","Carnival Valor","5 Night Western Caribbean","Carnival Cruise Line","2027-03-20",5,"Cozumel; Progreso","Interior",679,"https://www.carnival.com/itinerary/5-day-western-caribbean-cruise/new-orleans/valor/5-days/cw6/?sailDate=03202027"),
    ("NOLA","Mariner of the Seas","7 Night Western Caribbean","Royal Caribbean","2027-03-20",7,"Cozumel; George Town; Falmouth","Interior",635,"https://www.royalcaribbean.com/cruises/itinerary/7-night-western-caribbean-from-new-orleans-on-mariner/MA07MSY-1227888471?sail-date=2027-03-20&currency=USD"),

    # ---------------- PORT CANAVERAL, FL (fly MCO) ----------------
    ("PC","Carnival Vista","8 Night Southern Caribbean","Carnival Cruise Line","2027-02-20",8,"Willemstad (Curacao); Oranjestad (Aruba); Celebration Key","Interior",701,"https://www.carnival.com/itinerary/8-day-southern-caribbean-cruise/pt-canaveral/vista/8-days/csa/?sailDate=02202027"),
    ("PC","Celebrity Apex","7 Night Key West, Mexico & Cayman","Celebrity Cruises","2027-02-20",7,"Key West; Bimini; George Town; Cozumel","Interior",977,"https://www.celebritycruises.com/itinerary/7-night-key-west-mexico-cayman-from-orlando-port-canaveral-on-apex-AX07W681?sailDate=2027-02-20&packageCode=AX07W681"),
    ("PC","Disney Treasure","7 Night Western Caribbean","Disney Cruise Line","2027-02-20",7,"Cozumel; George Town; Falmouth; Castaway Cay","Inside",4732,"https://disneycruise.disney.go.com/cruises-destinations/list/WT0114/7-Night-Western-Caribbean-Cruise-from-Port-Canaveral/2027-02-20-Disney-Treasure/"),
    ("PC","Harmony of the Seas","5 Night Bahamas & Perfect Day","Royal Caribbean","2027-02-20",5,"Perfect Day at CocoCay; Nassau","Interior",639,"https://www.royalcaribbean.com/cruises/itinerary/5-night-bahamas-perfect-day-from-orlando-port-canaveral-on-harmony/HM05PCN-3790280278?sail-date=2027-02-20&currency=USD"),
    ("PC","Mardi Gras","7 Night Eastern Caribbean","Carnival Cruise Line","2027-02-20",7,"Nassau; Half Moon Cay; Puerto Plata; Celebration Key","Interior",571,"https://www.carnival.com/itinerary/7-day-eastern-caribbean-cruise/pt-canaveral/mardi-gras/7-days/eab/?sailDate=02202027"),
    ("PC","MSC Grandiosa","7 Night Western Caribbean & Bahamas","MSC Cruises","2027-02-20",7,"Nassau; Ocean Cay; Cozumel; Costa Maya","From",433,"https://www.msccruisesusa.com/itinerary-details/7-nights-western-caribbean--bahamas?cruiseid=GR20270220CPVCPV"),
    ("PC","MSC Grandiosa","14 Night Caribbean & Bahamas","MSC Cruises","2027-02-20",14,"Nassau; Ocean Cay; Cozumel; Costa Maya; Nassau; Ocean Cay; Puerto Plata","From",776,"https://www.msccruisesusa.com/itinerary-details/14-nights-caribbean--bahamas?cruiseid=GR20270220CPVCP1"),
    ("PC","Carnival Freedom","5 Night The Bahamas","Carnival Cruise Line","2027-02-27",5,"Nassau; Half Moon Cay; Celebration Key","Interior",323,"https://www.carnival.com/itinerary/5-day-the-bahamas-cruise/pt-canaveral/freedom/5-days/bmg/?sailDate=02272027"),
    ("PC","Celebrity Apex","7 Night St. Thomas, St. Kitts & Puerto Plata","Celebrity Cruises","2027-02-27",7,"Puerto Plata; St Thomas; Basseterre (St. Kitts)","Interior",1224,"https://www.celebritycruises.com/itinerary/7-night-st-thomas-st-kitts-cruise-from-orlando-port-canaveral-on-apex-AX07E469?sailDate=2027-02-27&packageCode=AX07E469"),
    ("PC","Disney Treasure","7 Night Eastern Caribbean","Disney Cruise Line","2027-02-27",7,"Tortola; San Juan; Castaway Cay","Inside",5174,"https://disneycruise.disney.go.com/cruises-destinations/list/WT0115/7-Night-Eastern-Caribbean-Cruise-from-Port-Canaveral/2027-02-27-Disney-Treasure/"),
    ("PC","Mardi Gras","7 Night Eastern Caribbean","Carnival Cruise Line","2027-02-27",7,"Nassau; Half Moon Cay; Puerto Plata; Celebration Key","Interior",577,"https://www.carnival.com/itinerary/7-day-eastern-caribbean-cruise/pt-canaveral/mardi-gras/7-days/eab/?sailDate=02272027"),
    ("PC","MSC Grandiosa","7 Night Eastern Caribbean & Bahamas","MSC Cruises","2027-02-27",7,"Nassau; Ocean Cay; Puerto Plata/Amber Cove","From",343,"https://www.msccruisesusa.com/itinerary-details/7-nights-eastern-caribbean--bahamas?cruiseid=GR20270227CPVCPV"),

    # ---------------- TAMPA, FL (fly TPA) ----------------
    ("TPA","Margaritaville at Sea Islander","7 Night Key West & Mexico","Margaritaville at Sea","2027-02-20",7,"Cozumel; Progreso; Key West","Inside",499,"https://margaritavilleatsea.com/"),
    ("TPA","Radiance of the Seas","7 Night Western Caribbean","Royal Caribbean","2027-02-20",7,"Costa Maya; Roatan; Belize City; Cozumel","Interior",618,"https://www.royalcaribbean.com/cruises/itinerary/7-night-western-caribbean-from-tampa-on-radiance/RD07TPA-511769733?sail-date=2027-02-20&currency=USD"),
    ("TPA","Jewel of the Seas","5 Night Western Caribbean","Royal Caribbean","2027-02-27",5,"Costa Maya; Cozumel","Interior",560,"https://www.royalcaribbean.com/cruises/itinerary/5-night-western-caribbean-from-tampa-on-jewel/JW05TPA-1176431029?sail-date=2027-02-27&currency=USD"),
    ("TPA","Margaritaville at Sea Islander","5 Night Key West and Progreso","Margaritaville at Sea","2027-02-27",5,"Key West; Progreso","Inside",399,"https://margaritavilleatsea.com/"),
    ("TPA","Radiance of the Seas","7 Night Western Caribbean","Royal Caribbean","2027-02-27",7,"Cozumel; Costa Maya; Roatan","Interior",565,"https://www.royalcaribbean.com/cruises/itinerary/7-night-western-caribbean-from-tampa-on-radiance/RD07TPA-2072238172?sail-date=2027-02-27&currency=USD"),

    # ---------------- FORT LAUDERDALE, FL (fly FLL) ----------------
    ("FLL","Legend of the Seas","8 Night Perfect Day CocoCay & Caribbean","Royal Caribbean","2027-02-20",8,"Oranjestad (Aruba); Willemstad (Curacao); Cabo Rojo; Perfect Day at CocoCay","Interior",1674,"https://www.royalcaribbean.com/cruises/itinerary/8-night-perfect-day-cococay-caribbean-from-fort-lauderdale-on-legend/LE08FLL-1526021002?sail-date=2027-02-20&currency=USD"),
    ("FLL","Regal Princess","8 Night Eastern Caribbean with Puerto Rico","Princess Cruises","2027-02-20",8,"Philipsburg (St. Maarten); San Juan; Puerto Plata; Grand Turk","Interior",984,"https://www.princess.com/itinerary-details/?voyageCode=G709"),
    ("FLL","Regal Princess","14 Night Eastern Caribbean Adventurer with Celebration Key","Princess Cruises","2027-02-20",14,"Philipsburg; San Juan; Puerto Plata; Grand Turk; Celebration Key; Grand Turk; Nassau","Interior",1199,"https://www.princess.com/itinerary-details/?voyageCode=G709A"),
    ("FLL","Adventure of the Seas","8 Night Southern Caribbean","Royal Caribbean","2027-02-27",8,"Grand Turk; Oranjestad (Aruba); Willemstad (Curacao)","Interior",1121,"https://www.royalcaribbean.com/cruises/itinerary/8-night-southern-caribbean-from-fort-lauderdale-on-adventure/AD08FLL-4180568102?sail-date=2027-02-27&currency=USD"),
    ("FLL","Caribbean Princess","6 Night Eastern Caribbean with Turks & Caicos & Celebration Key","Princess Cruises","2027-02-27",6,"Grand Turk; Puerto Plata; Celebration Key","Interior",449,"https://www.princess.com/itinerary-details/?voyageCode=B706"),
    ("FLL","Disney Destiny","5 Night Western Caribbean","Disney Cruise Line","2027-02-27",5,"Cozumel; Castaway Cay","Inside",3313,"https://disneycruise.disney.go.com/cruises-destinations/list/WD0099/5-Night-Western-Caribbean-Cruise-from-Fort-Lauderdale/2027-02-27-Disney-Destiny/"),
    ("FLL","Eurodam","10 Night Eastern Caribbean: St. Maarten, Antigua & Bahamas","Holland America Line","2027-02-27",10,"Half Moon Cay; San Juan; Tortola; Philipsburg; St Johns (Antigua); Basseterre (St. Kitts)","Inside",1199,"https://www.hollandamerica.com/en/us/find-a-cruise/c7e10b/d724"),
    ("FLL","Star Princess","14 Night Eastern/Western Caribbean Adventurer with Celebration Key","Princess Cruises","2027-02-27",14,"Cozumel; Celebration Key; +others (see official itinerary)","Interior",2053,"https://www.princess.com/itinerary-details/?voyageCode=4710A"),

    # ---------------- MIAMI, FL (fly MIA) ----------------
    ("MIA","Carnival Magic","8 Night Eastern Caribbean","Carnival Cruise Line","2027-02-20",8,"Half Moon Cay; San Juan; Philipsburg (St. Maarten); St Thomas","Interior",559,"https://www.carnival.com/itinerary/8-day-eastern-caribbean-cruise/miami/magic/8-days/ceh/?sailDate=02202027"),
    ("MIA","Carnival Sunrise","5 Night The Bahamas","Carnival Cruise Line","2027-02-20",5,"Nassau; Half Moon Cay; Celebration Key","Interior",297,"https://www.carnival.com/itinerary/5-day-the-bahamas-cruise/miami/sunrise/5-days/bhf/?sailDate=02202027"),
    ("MIA","Freedom of the Seas","5 Night Western Caribbean","Royal Caribbean","2027-02-20",5,"Nassau; Cozumel","Interior",486,"https://www.royalcaribbean.com/cruises/itinerary/5-night-western-caribbean-from-miami-on-freedom/FR05MIA-2694211651?sail-date=2027-02-20&currency=USD"),
    ("MIA","Icon of the Seas","7 Night Western Caribbean & Perfect Day","Royal Caribbean","2027-02-20",7,"Costa Maya; Roatan; Cozumel; Perfect Day at CocoCay","Interior",1191,"https://www.royalcaribbean.com/cruises/itinerary/7-night-western-caribbean-perfect-day-from-miami-on-icon/IC07MIA-1694717396?sail-date=2027-02-20&currency=USD"),
    ("MIA","MSC World America","14 Night Eastern & Western Caribbean","MSC Cruises","2027-02-20",14,"Puerto Plata; San Juan; Ocean Cay; Roatan; Costa Maya; Cozumel","From",1436,"https://www.msccruisesusa.com/itinerary-details/14-nights-eastern--western-caribbean?cruiseid=AM20270220MIAMI1"),
    ("MIA","Allure of the Seas","7 Night Western Caribbean & Perfect Day","Royal Caribbean","2027-02-21",7,"Nassau; Perfect Day at CocoCay; Cozumel; Costa Maya","Interior",1035,"https://www.royalcaribbean.com/cruises/itinerary/7-night-western-caribbean-perfect-day-from-miami-on-allure/AL07MIA-778812363?sail-date=2027-02-21&currency=USD"),
    ("MIA","Carnival Celebration","7 Night Western Caribbean","Carnival Cruise Line","2027-02-21",7,"Celebration Key; Cozumel; Roatan","Interior",547,"https://www.carnival.com/itinerary/7-day-western-caribbean-cruise/miami/celebration/7-days/cc7/?sailDate=02212027"),
    ("MIA","Carnival Horizon","6 Night Western Caribbean","Carnival Cruise Line","2027-02-21",6,"Celebration Key; Montego Bay; George Town","Interior",452,"https://www.carnival.com/itinerary/6-day-western-caribbean-cruise/miami/horizon/6-days/cwm/?sailDate=02212027"),
    ("MIA","Celebrity Xcel","7 Night Puerto Plata & St. Maarten","Celebrity Cruises","2027-02-21",7,"Philipsburg (St. Maarten); Tortola; Puerto Plata","Interior",851,"https://www.celebritycruises.com/itinerary/7-night-puerto-plata-st-maarten-from-miami-on-xcel-XC07E472?sailDate=2027-02-21&packageCode=XC07E472"),
]


def money(n):
    return "$" + format(int(round(n)), ",")


def gflights(apt, out, back):
    q = f"Flights from SFO to {apt} {out}, return {back}"
    return "https://www.google.com/travel/flights?q=" + urllib.parse.quote(q)


def build_rows():
    counters = {}
    rows = []
    for (pk, ship, cname, line, embark, nights, stops, kind, pp, official) in R:
        counters[pk] = counters.get(pk, 0) + 1
        rid = f"{pk}-{counters[pk]:02d}"
        port_name, apt, base_pp, kayak, kayak_note = PORTS[pk]
        d_embark = datetime.date.fromisoformat(embark)
        d_disembark = d_embark + datetime.timedelta(days=nights)
        d_out = d_embark - datetime.timedelta(days=1)
        d_back = d_disembark + datetime.timedelta(days=1)
        cruise_2 = 2 * pp
        flight_2 = 2 * base_pp
        trip_2 = cruise_2 + flight_2
        kind_label = {"Interior": "Interior", "Inside": "Inside", "From": "MSC lead-in 'From'"}[kind]
        if kind == "From":
            pnote = (f"MSC lead-in 'From' fare ${pp:,}/person (cheapest cabin, Bella experience); "
                     f"total is 2 x snapshot (pub. {PUB})")
        else:
            pnote = f"{kind_label} snapshot ${pp:,}/person; total is 2 x snapshot (pub. {PUB})"
        row = {
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
            "status": f"NEW {PUB} \u2014 National expansion (any U.S. port), line-by-line verified",
            "source_url": SRC[pk],
            "flight_out_date": d_out.isoformat(),
            "flight_return_date": d_back.isoformat(),
            "flight_route": f"SFO \u2192 {apt} \u2192 SFO",
            "flight_cost_2": f"{money(flight_2)} planning estimate",
            "flight_source": kayak_note,
            "flight_source_url": kayak,
            "trip_total_2": money(trip_2),
            "trip_total_note": "Cruise snapshot (2 x interior) + 2-adult SFO round-trip flight planning estimate; live quote required.",
            "price_currency": "USD",
            "verification_note": (
                f"National-expansion pass ({PUB}): date, ship, duration, port sequence and published "
                f"per-person USD {kind_label} price read directly from the cruisetimetables day/month/from-port "
                f"schedule index (official fare feed), with the official cruise-line deep link from the same page. "
                f"Flight is SFO round trip, arrive day before / return day after, priced at the KAYAK route average x2. "
                f"Snapshot \u2260 live quote; cabin class, taxes/fees and availability must be confirmed on the official page."
            ),
            "flight_search_url": gflights(apt, d_out.isoformat(), d_back.isoformat()),
        }
        rows.append(row)
    return rows


def main():
    with MASTER.open(newline="") as f:
        reader = csv.DictReader(f)
        fields = reader.fieldnames
        existing = list(reader)
    new = build_rows()
    existing_ids = {r["id"] for r in existing}
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
    c = Counter(r["port"] for r in new)
    for p, n in c.most_common():
        print(f"  {n:2d}  {p}")


if __name__ == "__main__":
    main()
