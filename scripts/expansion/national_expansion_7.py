#!/usr/bin/env python3
"""National expansion pass 7 (2026-08-31) — 50 NEW verified in-window sailings.

TARGETING
---------
A per-port date-coverage audit (all 45 in-window dates checked against the master)
drove this pass toward the ports whose calendars were still thinnest, deliberately
moving OUTSIDE the Florida mega-ports that dominated passes 4-6:

    port                 rows before  dates held  dates MISSING (of 45)
    San Juan, PR              21           7            38
    New Orleans, LA           17          11            34
    Galveston, TX             32          14            31
    Jacksonville, FL          20          20            25
    Los Angeles (San Pedro)   34          24            21

plus the highest-yield remaining uncovered Miami / Fort Lauderdale / Port Canaveral days.

Every row was read LINE BY LINE from the cruisetimetables.com per-day "from port" pages
(accessed 2026-08-31, site-dated 29 August 2026), which republish the official cruise-line
fare feed AND carry a per-sailing official deep link.

NOT ADDED (flagged -> see verification log):
  * Crown Princess SJU 2027-03-28 7N "Southern Caribbean with Aruba" — the published
    itinerary ENDS AT FORT LAUDERDALE, not San Juan. OPEN JAW, excluded.
  * Oceania Allura MIA 2027-03-21 10N — Veranda From $5,199, Suite "NA"; no interior/
    inside grade is sold. Ultra-luxury, outside the contemporary band.
  * Explora III MIA 2027-03-14 7N -> Bridgetown (Barbados). OPEN JAW, excluded.
  * Explora III MIA 2027-03-14 15N round trip — From $10,185 per guest, ultra-luxury.
  * Nieuw Amsterdam FLL 2027-03-21 21N and 12N — already held from an earlier pass.
  * Baltimore 2027-02-20, Miami 2027-03-17, Port Canaveral 2027-02-23 — zero-sailing days.

Flights: 2 adults, SFO round trip, arrive the day BEFORE embarkation / return the day
AFTER disembarkation, at the route average x 2 (planning estimate; live quote required).
Hard asserts: dedup on (port, ship, date, nights), in-window, nights >= 2.
"""
import csv, json, datetime, urllib.parse
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MASTER = ROOT / "data" / "cruises_master_verified.csv"
JSON = ROOT / "data" / "cruises.json"
DOCS_JSON = ROOT / "docs" / "data" / "cruises.json"
DOCS_CSV = ROOT / "docs" / "data" / "cruises_master_verified.csv"
PUB = "2026-08-31"

PORTS = {
    "MIA": ("Miami, FL", "MIA", 422,
            "https://www.kayak.com/flight-routes/San-Francisco-SFO/Miami-MIA",
            "KAYAK SFO-MIA 12-month average $422/person round trip (typical $328-$545); accessed 2026-08-30"),
    "PC":  ("Port Canaveral, FL", "MCO", 430,
            "https://www.kayak.com/flight-routes/San-Francisco-SFO/Orlando-MCO",
            "KAYAK SFO-MCO (Orlando) planning basis $430/person round trip (Jan avg $376); accessed 2026-08-30"),
    "FLL": ("Fort Lauderdale, FL", "FLL", 430,
            "https://www.kayak.com/flight-routes/San-Francisco-SFO/Fort-Lauderdale-FLL",
            "KAYAK SFO-FLL planning basis $430/person round trip (route avg ~$388; typical $278-$517); accessed 2026-08-30"),
    "GAL": ("Galveston, TX", "HOU", 300,
            "https://www.kayak.com/flight-routes/San-Francisco-SFO/Houston-HOU",
            "KAYAK SFO-HOU planning basis $300/person round trip (Galveston is served via Houston); accessed 2026-08-30"),
    "MSY": ("New Orleans, LA", "MSY", 420,
            "https://www.kayak.com/flight-routes/San-Francisco-SFO/New-Orleans-MSY",
            "KAYAK SFO-MSY planning basis $420/person round trip; accessed 2026-08-30"),
    "SJU": ("San Juan, PR", "SJU", 532,
            "https://www.kayak.com/flight-routes/San-Francisco-SFO/San-Juan-SJU",
            "KAYAK SFO-SJU planning basis $532/person round trip; accessed 2026-08-30"),
    "JAX": ("Jacksonville, FL", "JAX", 478,
            "https://www.kayak.com/flight-routes/San-Francisco-SFO/Jacksonville-JAX",
            "KAYAK SFO-JAX planning basis $478/person round trip; accessed 2026-08-30"),
    "LAX": ("Los Angeles (San Pedro), CA", "LAX", 204,
            "https://www.kayak.com/flight-routes/San-Francisco-SFO/Los-Angeles-LAX",
            "KAYAK SFO-LAX planning basis $204/person round trip; accessed 2026-08-28"),
}

SRC = {
    "MIA": "https://www.cruisetimetables.com/cruises-from-miami-florida-2027.html",
    "PC":  "https://www.cruisetimetables.com/cruises-from-port-canaveral-florida-2027.html",
    "FLL": "https://www.cruisetimetables.com/cruises-from-fort-lauderdale-florida-2027.html",
    "GAL": "https://www.cruisetimetables.com/cruises-from-galveston-texas-2027.html",
    "MSY": "https://www.cruisetimetables.com/cruises-from-new-orleans-louisiana-2027.html",
    "SJU": "https://www.cruisetimetables.com/cruises-from-san-juan-puerto-rico-2027.html",
    "JAX": "https://www.cruisetimetables.com/cruises-from-jacksonville-florida-2027.html",
    "LAX": "https://www.cruisetimetables.com/cruises-from-los-angeles-california-2027.html",
}

# (portkey, ship, cruise_name, line, embark ISO, nights, stops, kind, pp, official)
R = [
    # ======================= NEW ORLEANS, LA =======================
    # --- Sun 21 Feb 2027 (fromneworleanslouisiana-21feb2027) ---
    # --- Sun 7 Mar 2027 (fromneworleanslouisiana-07mar2027) ---
    # ======================= SAN JUAN, PR =======================
    # --- Sun 14 Mar 2027 (fromsanjuanpuertorico-14mar2027) ---
    ("SJU", "Crown Princess", "14 Night Southern Caribbean Adventurer", "Princess Cruises",
     "2027-03-14", 14,
     "St Thomas; Basseterre (St. Kitts); Roseau (Dominica); St Georges (Grenada); "
     "Bridgetown (Barbados); San Juan; St Thomas; Philipsburg (St. Maarten); "
     "St Johns (Antigua); Castries (St Lucia); Bridgetown (Barbados); San Juan",
     "Interior", 1541,
     "https://www.princess.com/itinerary-details/?voyageCode=3712A"),
    ("SJU", "Crown Princess", "7 Night Southern Caribbean with Barbados and St. Kitts",
     "Princess Cruises", "2027-03-14", 7,
     "St Thomas; Basseterre (St. Kitts); Roseau (Dominica); St Georges (Grenada); "
     "Bridgetown (Barbados); San Juan", "Interior", 849,
     "https://www.princess.com/itinerary-details/?voyageCode=3712"),
    ("SJU", "Norwegian Prima", "7 Night Caribbean Round-Trip San Juan: Curacao & Aruba",
     "Norwegian Cruise Line", "2027-03-14", 7,
     "Tortola; St Thomas; Willemstad (Curacao); Oranjestad (Aruba); San Juan", "Inside", 1409,
     "https://www.ncl.com/vacation-builder?itineraryCode=PRIMA7SJUTOVSTTWILORJSJU-NIC-PRIMA7SJUORJSTTTOVWILSJU&packageId=24929595&stateroomTypeCode=INSIDE&"),
    ("SJU", "Vision of the Seas", "7 Night Southern Caribbean Cruise", "Royal Caribbean",
     "2027-03-14", 7,
     "Tortola; St Johns (Antigua); Roseau (Dominica); St Croix; Basseterre (St. Kitts); San Juan",
     "Interior", 749,
     "https://www.royalcaribbean.com/cruises/itinerary/7-night-southern-caribbean-from-san-juan-on-vision/VI07SJU-2553535272?sail-date=2027-03-14&currency=USD"),
    # --- Sun 21 Mar 2027 (fromsanjuanpuertorico-21mar2027) ---
    ("SJU", "Crown Princess", "7 Night Southern Caribbean with Barbados and St. Lucia",
     "Princess Cruises", "2027-03-21", 7,
     "St Thomas; Philipsburg (St. Maarten); St Johns (Antigua); Castries (St Lucia); "
     "Bridgetown (Barbados); San Juan", "Interior", 749,
     "https://www.princess.com/itinerary-details/?voyageCode=3713"),
    ("SJU", "Norwegian Prima", "7 Night Caribbean Round-trip San Juan: St. Thomas & Tortola",
     "Norwegian Cruise Line", "2027-03-21", 7,
     "Tortola; Basseterre (St. Kitts); Bridgetown (Barbados); Philipsburg (St. Maarten); "
     "St Thomas; San Juan", "Inside", 1749,
     "https://www.ncl.com/vacation-builder?itineraryCode=PRIMA7SJUTOVBASBGIPHISTTSJU-NIC-PRIMA7SJUBASBGIPHISTTTOVSJU&packageId=24929586&stateroomTypeCode=INSIDE&"),
    ("SJU", "Vision of the Seas", "7 Night Southern Caribbean Cruise", "Royal Caribbean",
     "2027-03-21", 7,
     "St Thomas; St Croix; Philipsburg (St. Maarten); St Johns (Antigua); Roseau (Dominica); "
     "San Juan", "Interior", 759,
     "https://www.royalcaribbean.com/cruises/itinerary/7-night-southern-caribbean-from-san-juan-on-vision/VI07SJU-1321850104?sail-date=2027-03-21&currency=USD"),
    # --- Sun 28 Mar 2027 (fromsanjuanpuertorico-28mar2027) ---
    ("SJU", "Norwegian Prima", "7 Night Caribbean Round-trip San Juan: St. Thomas & Tortola",
     "Norwegian Cruise Line", "2027-03-28", 7,
     "Tortola; St Thomas; Castries (St Lucia); Oranjestad (Aruba); San Juan", "Inside", 1389,
     "https://www.ncl.com/vacation-builder?itineraryCode=PRIMA7SJUTOVSTTSLUORJSJU-NIC-PRIMA7SJUORJSLUSTTTOVSJU&packageId=24929596&stateroomTypeCode=INSIDE&"),
    ("SJU", "Vision of the Seas", "7 Night Southern Caribbean Cruise", "Royal Caribbean",
     "2027-03-28", 7,
     "St Thomas; St Johns (Antigua); Philipsburg (St. Maarten); St Croix; "
     "Basseterre (St. Kitts); San Juan", "Interior", 734,
     "https://www.royalcaribbean.com/cruises/itinerary/7-night-southern-caribbean-from-san-juan-on-vision/VI07SJU-3297807724?sail-date=2027-03-28&currency=USD"),

    # ======================= GALVESTON, TX =======================
    # --- Thu 18 Feb 2027 (fromgalvestontexas-18feb2027) ---
    # --- Thu 25 Feb 2027 (fromgalvestontexas-25feb2027) ---
    ("GAL", "Carnival Miracle", "4 Night Western Caribbean", "Carnival Cruise Line",
     "2027-02-25", 4, "Cozumel; Galveston", "Interior", 448,
     "https://www.carnival.com/itinerary/4-day-western-caribbean-cruise/galveston/miracle/4-days/glb/?sailDate=02252027"),
    ("GAL", "Liberty of the Seas", "4 Night Western Caribbean Cruise", "Royal Caribbean",
     "2027-02-25", 4, "Cozumel; Galveston", "Interior", 554,
     "https://www.royalcaribbean.com/cruises/itinerary/4-night-western-caribbean-from-galveston-on-liberty/LB04GAL-597171099?sail-date=2027-02-25&currency=USD"),
    # --- Thu 11 Mar 2027 (fromgalvestontexas-11mar2027) ---
    ("GAL", "Liberty of the Seas", "4 Night Western Caribbean Cruise", "Royal Caribbean",
     "2027-03-11", 4, "Cozumel; Galveston", "Interior", 575,
     "https://www.royalcaribbean.com/cruises/itinerary/4-night-western-caribbean-from-galveston-on-liberty/LB04GAL-597171099?sail-date=2027-03-11&currency=USD"),

    # ======================= JACKSONVILLE, FL =======================
    # --- Sat 20 Mar 2027 (fromjacksonvilleflorida-20mar2027) ---
    # --- Sun 21 Mar 2027 (fromjacksonvilleflorida-21mar2027) ---
    # ======================= LOS ANGELES (SAN PEDRO), CA =======================
    # --- Sat 20 Feb 2027 (fromlosangelescalifornia-20feb2027) ---
    # ======================= PORT CANAVERAL, FL =======================
    # --- Thu 18 Mar 2027 (fromportcanaveralflorida-18mar2027) ---
    ("PC", "Carnival Freedom", "4 Night The Bahamas", "Carnival Cruise Line",
     "2027-03-18", 4, "Half Moon Cay; Celebration Key; Port Canaveral", "Interior", 430,
     "https://www.carnival.com/itinerary/4-day-the-bahamas-cruise/pt-canaveral/freedom/4-days/bm6/?sailDate=03182027"),
    ("PC", "MSC Seashore", "3 Night The Bahamas & Ocean Cay", "MSC Cruises", "2027-03-18", 3,
     "Nassau; Ocean Cay; Port Canaveral", "From", 315,
     "https://www.msccruisesusa.com/itinerary-details/3-nights-the-bahamas--ocean-cay?cruiseid=SH20270318CPVCPV"),

    # ======================= FORT LAUDERDALE, FL =======================
    # --- Sun 21 Mar 2027 (fromfortlauderdaleflorida-21mar2027) ---
    ("FLL", "Nieuw Statendam", "14 Night Eastern Caribbean: Bahamas & San Juan",
     "Holland America Line", "2027-03-21", 14,
     "Nassau; Puerto Plata/Amber Cove; Grand Turk; Half Moon Cay; Fort Lauderdale; Grand Turk; "
     "San Juan; St Thomas; Half Moon Cay; Fort Lauderdale", "Inside", 1669,
     "https://www.hollandamerica.com/en/us/find-a-cruise/c7e14d/j731a"),
    ("FLL", "Nieuw Statendam", "7 Night Eastern Caribbean: Amber Cove & Bahamas",
     "Holland America Line", "2027-03-21", 7,
     "Nassau; Puerto Plata/Amber Cove; Grand Turk; Half Moon Cay; Fort Lauderdale",
     "Inside", 899,
     "https://www.hollandamerica.com/en/us/find-a-cruise/c7e07g/j731"),
    ("FLL", "Sun Princess", "7 Night Western Caribbean with Mexico", "Princess Cruises",
     "2027-03-21", 7, "Cozumel; Belize City; Roatan; Fort Lauderdale", "Interior", 669,
     "https://www.princess.com/itinerary-details/?voyageCode=U713"),

    # ======================= MIAMI, FL =======================
    # --- Sun 14 Mar 2027 (frommiamiflorida-14mar2027) ---
    ("MIA", "Allure of the Seas", "7 Night Eastern Caribbean & Perfect Day",
     "Royal Caribbean", "2027-03-14", 7,
     "Perfect Day at CocoCay; San Juan; Philipsburg (St. Maarten); Miami", "Interior", 1173,
     "https://www.royalcaribbean.com/cruises/itinerary/7-night-eastern-caribbean-perfect-day-from-miami-on-allure/AL07MIA-3946942606?sail-date=2027-03-14&currency=USD"),
    ("MIA", "Carnival Celebration", "7 Night Eastern Caribbean", "Carnival Cruise Line",
     "2027-03-14", 7,
     "St Thomas; Puerto Plata/Amber Cove; Celebration Key; Miami", "Interior", 660,
     "https://www.carnival.com/itinerary/7-day-eastern-caribbean-cruise/miami/celebration/7-days/ccb/?sailDate=03142027"),
    ("MIA", "Carnival Magic", "6 Night Eastern Caribbean", "Carnival Cruise Line",
     "2027-03-14", 6,
     "Celebration Key; Puerto Plata/Amber Cove; Grand Turk; Miami", "Interior", 489,
     "https://www.carnival.com/itinerary/6-day-eastern-caribbean-cruise/miami/magic/6-days/ce9/?sailDate=03142027"),
    ("MIA", "Celebrity Xcel", "7 Night Puerto Plata & St. Maarten", "Celebrity Cruises",
     "2027-03-14", 7,
     "Philipsburg (St. Maarten); St Thomas; Puerto Plata/Amber Cove; Miami", "Interior", 900,
     "https://www.celebritycruises.com/itinerary/7-night-puerto-plata-st-maarten-from-miami-on-xcel-XC07E472?sailDate=2027-03-14&packageCode=XC07E472"),
    ("MIA", "Independence of the Seas", "7 Night Western Caribbean Cruise", "Royal Caribbean",
     "2027-03-14", 7,
     "Nassau; Puerto Plata/Amber Cove; George Town (Grand Cayman); Miami", "Interior", 680,
     "https://www.royalcaribbean.com/cruises/itinerary/7-night-western-caribbean-from-miami-on-independence/ID07MIA-442897693?sail-date=2027-03-14&currency=USD"),
    ("MIA", "Norwegian Aqua",
     "7 Night Caribbean Round-trip Miami: Great Stirrup Cay & Dominican Republic",
     "Norwegian Cruise Line", "2027-03-14", 7,
     "Puerto Plata/Amber Cove; St Thomas; Tortola; Great Stirrup Cay; Miami", "Inside", 1239,
     "https://www.ncl.com/vacation-builder?itineraryCode=AQUA7MIAPOPSTTTOVNPIMIA-NIC-AQUA7MIANPIPOPSTTTOVMIA&packageId=23353058&stateroomTypeCode=INSIDE&"),
    # --- Sun 21 Mar 2027 (frommiamiflorida-21mar2027) ---
    ("MIA", "Allure of the Seas", "7 Night Caribbean & Perfect Day", "Royal Caribbean",
     "2027-03-21", 7,
     "Nassau; Perfect Day at CocoCay; San Juan; Samana; Miami", "Interior", 994,
     "https://www.royalcaribbean.com/cruises/itinerary/7-night-caribbean-perfect-day-from-miami-on-allure/AL07MIA-3531491794?sail-date=2027-03-21&currency=USD"),
    ("MIA", "Carnival Celebration", "7 Night Western Caribbean", "Carnival Cruise Line",
     "2027-03-21", 7, "Roatan; Cozumel; Celebration Key; Miami", "Interior", 702,
     "https://www.carnival.com/itinerary/7-day-western-caribbean-cruise/miami/celebration/7-days/wsi/?sailDate=03212027"),
    ("MIA", "Carnival Horizon", "6 Night Western Caribbean", "Carnival Cruise Line",
     "2027-03-21", 6,
     "Celebration Key; Ocho Rios; George Town (Grand Cayman); Miami", "Interior", 612,
     "https://www.carnival.com/itinerary/6-day-western-caribbean-cruise/miami/horizon/6-days/cwn/?sailDate=03212027"),
    ("MIA", "Celebrity Xcel", "7 Night St. Thomas & Antigua", "Celebrity Cruises",
     "2027-03-21", 7, "Nassau; St Thomas; St Johns (Antigua); Miami", "Interior", 1141,
     "https://www.celebritycruises.com/itinerary/7-night-st-thomas-antigua-cruise-from-miami-on-xcel-XC07E473?sailDate=2027-03-21&packageCode=XC07E473"),
    ("MIA", "Independence of the Seas", "7 Night Eastern Caribbean Cruise", "Royal Caribbean",
     "2027-03-21", 7,
     "San Juan; St Thomas; Puerto Plata/Amber Cove; Miami", "Interior", 822,
     "https://www.royalcaribbean.com/cruises/itinerary/7-night-eastern-caribbean-from-miami-on-independence/ID07MIA-3300717572?sail-date=2027-03-21&currency=USD"),
    ("MIA", "MSC Meraviglia", "6 Night Eastern Caribbean & Bahamas", "MSC Cruises",
     "2027-03-21", 6, "Grand Turk; Ocean Cay; Nassau; Miami", "From", 415,
     "https://www.msccruisesusa.com/itinerary-details/6-nights-eastern-caribbean--bahamas?cruiseid=MR20270321MIAMIA"),
    ("MIA", "MSC Meraviglia", "14 Night Caribbean & Bahamas", "MSC Cruises",
     "2027-03-21", 14,
     "Grand Turk; Ocean Cay; Nassau; Miami; Philipsburg (St. Maarten); Basseterre (St. Kitts); "
     "St Thomas; Puerto Plata/Amber Cove; Miami", "From", 1301,
     "https://www.msccruisesusa.com/itinerary-details/14-nights-caribbean--bahamas?cruiseid=MR20270321MIAMI1"),
    ("MIA", "Norwegian Aqua",
     "7 Night Caribbean Round-trip Miami: Great Stirrup Cay & Dominican Republic",
     "Norwegian Cruise Line", "2027-03-21", 7,
     "Puerto Plata/Amber Cove; St Thomas; Tortola; Great Stirrup Cay; Miami", "Inside", 1239,
     "https://www.ncl.com/vacation-builder?itineraryCode=AQUA7MIAPOPSTTTOVNPIMIA-NIC-AQUA7MIANPIPOPSTTTOVMIA&packageId=23353059&stateroomTypeCode=INSIDE&"),
    ("MIA", "Resilient Lady", "6 Night Eastern Caribbean Cruise", "Virgin Voyages",
     "2027-03-21", 6, "Grand Turk; Samana; Puerto Plata/Amber Cove; Miami", "From", 894,
     "https://www.virginvoyages.com/book/voyage-planner/pre-checkout?currencyCode=USD&packageCode=6NGSP&voyageId=RS2703216NGSP"),
    # --- Sun 7 Mar 2027 (frommiamiflorida-07mar2027) ---
    # Allure of the Seas 7N "Atlantis Epic" charter, Cruise Prices "NA" -> EXCLUDED (full-ship charter).
    ("MIA", "MSC Meraviglia", "6 Night Eastern Caribbean & Bahamas", "MSC Cruises",
     "2027-03-07", 6, "Grand Turk; Ocean Cay; Nassau; Miami", "From", 355,
     "https://www.msccruisesusa.com/itinerary-details/6-nights-eastern-caribbean--bahamas?cruiseid=MR20270307MIAMIA"),
    ("MIA", "MSC Meraviglia", "14 Night Caribbean & Bahamas", "MSC Cruises",
     "2027-03-07", 14,
     "Grand Turk; Ocean Cay; Nassau; Miami; Philipsburg (St. Maarten); St Johns (Antigua); "
     "St Thomas; Nassau; Miami", "From", 1151,
     "https://www.msccruisesusa.com/itinerary-details/14-nights-caribbean--bahamas?cruiseid=MR20270307MIAMI1"),
    ("MIA", "MSC Poesia", "11 Night Southern & Western Caribbean", "MSC Cruises",
     "2027-03-07", 11,
     "Ocho Rios; Cartagena; Colon (Panama); Puerto Limon; Roatan; Belize City; Miami",
     "From", 1851,
     "https://www.msccruisesusa.com/itinerary-details/11-nights-southern--western-caribbean?cruiseid=PO20270307MIAMIA"),
    ("MIA", "MSC Poesia", "21 Night Southern & Western Caribbean", "MSC Cruises",
     "2027-03-07", 21,
     "Ocho Rios; Cartagena; Colon (Panama); Puerto Limon; Roatan; Belize City; Miami; "
     "Willemstad (Curacao); Kralendijk (Bonaire); Oranjestad (Aruba); Cabo Rojo; Ocho Rios; Miami",
     "From", 2909,
     "https://www.msccruisesusa.com/itinerary-details/21-nights-southern--western-caribbean?cruiseid=PO20270307MIAMI1"),
    ("MIA", "Norwegian Aqua",
     "7 Night Caribbean Round-trip Miami: Great Stirrup Cay & Dominican Republic",
     "Norwegian Cruise Line", "2027-03-07", 7,
     "Puerto Plata/Amber Cove; St Thomas; Tortola; Great Stirrup Cay; Miami", "Inside", 1089,
     "https://www.ncl.com/vacation-builder?itineraryCode=AQUA7MIAPOPSTTTOVNPIMIA-NIC-AQUA7MIANPIPOPSTTTOVMIA&packageId=23353057&stateroomTypeCode=INSIDE&"),

    # --- Fort Lauderdale, Sun 14 Mar 2027 (fromfortlauderdaleflorida-14mar2027) ---
    # Nieuw Statendam 7N "Live Like No One Else With Dave Ramsey": Cruise Prices "NA" -> EXCLUDED (charter).
    # Zaandam 14N Panama Canal ENDS AT SAN DIEGO -> OPEN JAW, excluded.
    ("FLL", "Sun Princess", "7 Night Eastern Caribbean with Puerto Rico", "Princess Cruises",
     "2027-03-14", 7,
     "Grand Turk; San Juan; Puerto Plata/Amber Cove; Fort Lauderdale", "Interior", 1019,
     "https://www.princess.com/itinerary-details/?voyageCode=U712"),

    # --- Port Canaveral, Sun 14 Mar 2027 (fromportcanaveralflorida-14mar2027) ---
    ("PC", "Carnival Venezia", "7 Night Western Caribbean", "Carnival Cruise Line",
     "2027-03-14", 7, "Celebration Key; Cozumel; Roatan; Port Canaveral", "Interior", 712,
     "https://www.carnival.com/itinerary/7-day-western-caribbean-cruise/pt-canaveral/venezia/7-days/wsa/?sailDate=03142027"),
    ("PC", "Carnival Vista", "6 Night Eastern Caribbean", "Carnival Cruise Line",
     "2027-03-14", 6,
     "Puerto Plata/Amber Cove; Half Moon Cay; Celebration Key; Port Canaveral", "Interior", 522,
     "https://www.carnival.com/itinerary/6-day-eastern-caribbean-cruise/pt-canaveral/vista/6-days/cef/?sailDate=03142027"),
    ("PC", "MSC Seashore", "4 Night The Bahamas & Ocean Cay", "MSC Cruises", "2027-03-14", 4,
     "Nassau; Ocean Cay; Port Canaveral", "From", 327,
     "https://www.msccruisesusa.com/itinerary-details/4-nights-the-bahamas--ocean-cay?cruiseid=SH20270314CPVCPV"),
    ("PC", "Norwegian Epic",
     "7 Night Western Caribbean: Great Stirrup Cay, Cozumel & Grand Cayman",
     "Norwegian Cruise Line", "2027-03-14", 7,
     "Great Stirrup Cay; Falmouth (Jamaica); George Town (Grand Cayman); Cozumel; Port Canaveral",
     "Inside", 859,
     "https://www.ncl.com/vacation-builder?itineraryCode=EPIC7PCVNPIBZECMACZMPCV-NIC-EPIC7PCVCZMFMHGECNPIPCV&packageId=23361674&stateroomTypeCode=INSIDE&"),
    ("PC", "Star of the Seas", "7 Night Perfect Day At CocoCay & Caribbean",
     "Royal Caribbean", "2027-03-14", 7,
     "Costa Maya; Roatan; Cozumel; Perfect Day at CocoCay; Port Canaveral", "Interior", 1435,
     "https://www.royalcaribbean.com/cruises/itinerary/7-night-perfect-day-at-cococay-caribbean-from-orlando-port-canaveral-on-star/ST07PCN-2334033785?sail-date=2027-03-14&currency=USD"),

    # --- San Juan, Sun 7 Mar 2027 (fromsanjuanpuertorico-07mar2027) ---
    # Explora III 7N -> ends MIAMI and 14N -> ends BRIDGETOWN: OPEN JAW + ultra-luxury, both excluded.
    # --- Galveston, Sun 21 Feb 2027 (fromgalvestontexas-21feb2027) ---
    ("GAL", "Disney Magic",
     "5 Night Western Caribbean Cruise From Galveston With Marvel Days At Sea",
     "Disney Cruise Line", "2027-02-21", 5, "Cozumel; Progreso; Galveston",
     "Disney-stateroom", 2321,
     "https://disneycruise.disney.go.com/cruises-destinations/list/DM1779/5-Night-Western-Caribbean-Cruise-from-Galveston-with-Marvel-Days-at-Sea/2027-02-21-Disney-Magic/"),
    ("GAL", "MSC Seascape", "7 Night Western Caribbean", "MSC Cruises", "2027-02-21", 7,
     "Costa Maya; Roatan; Cozumel; Galveston", "From", 470,
     "https://www.msccruisesusa.com/itinerary-details/7-nights-western-caribbean?cruiseid=SC20270221GLSGLS"),
    ("GAL", "Symphony of the Seas", "7 Night Western Caribbean Cruise", "Royal Caribbean",
     "2027-02-21", 7, "Roatan; Costa Maya; Cozumel; Galveston", "Interior", 765,
     "https://www.royalcaribbean.com/cruises/itinerary/7-night-western-caribbean-from-galveston-on-symphony/SY07GAL-3851841824?sail-date=2027-02-21&currency=USD"),

    # --- New Orleans, Sun 14 Mar 2027 (fromneworleanslouisiana-14mar2027) ---
    # --- Galveston, Sun 28 Feb 2027 (fromgalvestontexas-28feb2027) ---
    # --- Jacksonville, Sat 6 Mar 2027 (fromjacksonvilleflorida-06mar2027) ---
    # --- Miami, Sun 28 Mar 2027 (frommiamiflorida-28mar2027) ---
    ("MIA", "Allure of the Seas", "7 Night Eastern Caribbean Cruise", "Royal Caribbean",
     "2027-03-28", 7,
     "Philipsburg (St. Maarten); St Thomas; Puerto Plata/Amber Cove; Miami", "Interior", 1021,
     "https://www.royalcaribbean.com/cruises/itinerary/7-night-eastern-caribbean-from-miami-on-allure/AL07MIA-2574420622?sail-date=2027-03-28&currency=USD"),
    ("MIA", "Carnival Celebration", "8 Night Eastern Caribbean", "Carnival Cruise Line",
     "2027-03-28", 8,
     "Grand Turk; St Thomas; San Juan; Puerto Plata/Amber Cove; Miami", "Interior", 816,
     "https://www.carnival.com/itinerary/8-day-eastern-caribbean-cruise/miami/celebration/8-days/cer/?sailDate=03282027"),
    ("MIA", "Carnival Magic", "6 Night Eastern Caribbean", "Carnival Cruise Line",
     "2027-03-28", 6,
     "Celebration Key; Puerto Plata/Amber Cove; Grand Turk; Miami", "Interior", 529,
     "https://www.carnival.com/itinerary/6-day-eastern-caribbean-cruise/miami/magic/6-days/ce9/?sailDate=03282027"),
    ("MIA", "Celebrity Xcel", "7 Night Bahamas, Mexico & Cayman", "Celebrity Cruises",
     "2027-03-28", 7,
     "Nassau; George Town (Grand Cayman); Cozumel; Costa Maya; Miami", "Interior", 1003,
     "https://www.celebritycruises.com/itinerary/7-night-bahamas-mexico-cayman-from-miami-on-xcel-XC07E474?sailDate=2027-03-28&packageCode=XC07E474"),
]

SAME_DAY_PAIRS = []


def money(n):
    return "$" + format(int(round(n)), ",")


def gflights(apt, out, back):
    q = f"Flights from SFO to {apt} {out}, return {back}"
    return "https://www.google.com/travel/flights?q=" + urllib.parse.quote(q)


def build_rows(existing_keys):
    counters = {}
    rows = []
    seen_same_day = {}
    for (pk, ship, cname, line, embark, nights, stops, kind, pp, official) in R:
        port_name, apt, base_pp, kayak, kayak_note = PORTS[pk]
        key = (port_name, ship, embark, nights)
        assert key not in existing_keys, f"DUPLICATE against master: {key}"
        existing_keys.add(key)
        same_day = (port_name, ship, embark)
        if same_day in seen_same_day:
            SAME_DAY_PAIRS.append((port_name, ship, embark, seen_same_day[same_day], nights))
        seen_same_day[same_day] = nights
        assert "2027-02-15" <= embark <= "2027-03-31", f"OUT OF WINDOW: {key}"
        assert nights >= 2, f"too short: {key}"
        assert official.startswith("https://"), f"bad link: {key}"
        counters[pk] = counters.get(pk, 0) + 1
        rid = f"{pk}7-{counters[pk]:02d}"
        d_embark = datetime.date.fromisoformat(embark)
        d_disembark = d_embark + datetime.timedelta(days=nights)
        d_out = d_embark - datetime.timedelta(days=1)
        d_back = d_disembark + datetime.timedelta(days=1)
        # Disney publishes its "from" fares as a PER-STATEROOM total for 2 guests
        # (confirmed pass 7 against Costco Travel / AffordableTours / iCruise).
        # NEVER double a Disney figure.
        cruise_2 = pp if kind == "Disney-stateroom" else 2 * pp
        flight_2 = 2 * base_pp
        kind_label = {"Interior": "Interior", "Inside": "Inside",
                      "From": "MSC/Virgin lead-in 'From'",
                      "Disney-stateroom": "Disney Inside (per stateroom, 2 guests)"}[kind]
        if kind == "Disney-stateroom":
            pnote = (f"Disney Inside from-fare ${pp:,} is a PER-STATEROOM total for 2 guests, "
                     f"NOT per person; used as-is, not doubled (pub. {PUB})")
        elif kind == "From":
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
            "status": f"NEW {PUB} pass 7 \u2014 date-coverage sweep beyond the Florida mega-ports (SJU/MSY/GAL/JAX/LAX + remaining MIA/FLL/PC days), line-by-line verified",
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
                f"National-expansion pass 7 ({PUB}): sail date, ship, duration, full port sequence and the "
                f"published per-person USD {kind_label} price were read line by line from the cruisetimetables "
                f"PER-DAY from-port 2027 page (official cruise-line fare feed); the official cruise-line deep "
                f"link was taken from that same page. Targeted via a per-port date-coverage audit of all 45 "
                f"in-window dates, prioritising ports outside the Florida mega-ports. Dedup-checked against "
                f"the master by (port, ship, date, nights); in-window and duration asserts enforced in code. "
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
    existing_keys = set(
        (r["port"], r["name"].split("\u2014")[0].strip(), r["date"],
         int(r["duration"].split()[0]))
        for r in existing)
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
    DOCS_JSON.write_bytes(JSON.read_bytes())
    DOCS_CSV.write_bytes(MASTER.read_bytes())
    inwin = sum(1 for r in combined if "2027-02-15" <= r["date"] <= "2027-03-31")
    print(f"added {len(new)} new rows; total {len(combined)}; in-window {inwin}")
    from collections import Counter
    for p, n in Counter(r["port"] for r in new).most_common():
        print(f"  {n:2d}  {p}")
    if SAME_DAY_PAIRS:
        print("\nSame (port, ship, date) but DIFFERENT durations "
              "-> distinct bookable voyages, retained (flagged for review):")
        for port, ship, date, n1, n2 in SAME_DAY_PAIRS:
            print(f"  {ship} ex-{port} {date} -> {n1}N and {n2}N")


if __name__ == "__main__":
    main()
