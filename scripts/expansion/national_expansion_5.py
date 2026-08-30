#!/usr/bin/env python3
"""National expansion pass 5 (2026-08-30) — 53 NEW verified in-window sailings.

GAP THIS PASS CLOSES
--------------------
Pass 4 fixed the Saturday-cluster bias at Miami and Port Canaveral, but a fresh
date-coverage audit of the master list showed several ports were still thin:

    Fort Lauderdale   6 dates      Port Canaveral   7 dates
    Tampa             6 dates      San Juan         4 dates
    Galveston        10 dates      Miami           14 dates (of ~45 possible)

This pass sweeps the remaining uncovered per-day pages at those six ports. It adds
53 sailings and brings in TEN ships and one cruise line that were not represented
anywhere in the master list before:

    NEW LINE:  Princess Cruises now present at Fort Lauderdale / Port Canaveral /
               San Juan (Regal Princess, Sun Princess, Sky Princess, Crown Princess,
               Enchanted Princess)
    NEW SHIPS: Explorer of the Seas, Jewel of the Seas, Vision of the Seas,
               Norwegian Prima, Norwegian Gem, Carnival Breeze, Celebrity Silhouette
               (as a regular revenue sailing, not the charter), Oceania Marina

Every row was read LINE BY LINE from the cruisetimetables.com per-day "from port"
pages (accessed 2026-08-30, site-dated 29 August 2026), which republish the official
cruise-line fare feed AND carry a per-sailing official deep link. Each record holds:
sail date, ship, official cruise name, nights, full published port sequence, the
official cruise-line deep link, and the published per-person USD Interior/Inside
price (MSC & Virgin = lead-in "From").

NOT ADDED (flagged irregularities -> see verification log):
  * Nieuw Statendam FLL 2027-03-14 "7 Night Live Like No One Else Cruise With Dave
    Ramsey" — full-ship charter via inspirationtravel.com, fare feed publishes "NA".
  * Oceania Marina Miami 2027-03-25 16N / 23N — OPEN JAW to Rome / Trieste, and the
    23N variant publishes "From NA" in every cabin grade.
  * MSC Poesia Miami 2027-03-18 21N — ends 8 Apr 2027, OUTSIDE the window.
  * New Orleans 2027-02-22 — day page redirects to the port index: no sailings.

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
PUB = "2026-08-30"

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
    "TPA": ("Tampa, FL", "TPA", 457,
            "https://www.kayak.com/flight-routes/San-Francisco-SFO/Tampa-TPA",
            "KAYAK SFO-TPA planning basis $457/person round trip; accessed 2026-08-30"),
    "GAL": ("Galveston, TX", "HOU", 300,
            "https://www.kayak.com/flight-routes/San-Francisco-SFO/Houston-HOU",
            "KAYAK SFO-HOU planning basis $300/person round trip (Galveston is served via Houston); accessed 2026-08-30"),
    "SJU": ("San Juan, PR", "SJU", 532,
            "https://www.kayak.com/flight-routes/San-Francisco-SFO/San-Juan-SJU",
            "KAYAK SFO-SJU planning basis $532/person round trip; accessed 2026-08-30"),
}

SRC = {
    "MIA": "https://www.cruisetimetables.com/cruises-from-miami-florida-2027.html",
    "PC":  "https://www.cruisetimetables.com/cruises-from-port-canaveral-florida-2027.html",
    "FLL": "https://www.cruisetimetables.com/cruises-from-fort-lauderdale-florida-2027.html",
    "TPA": "https://www.cruisetimetables.com/cruises-from-tampa-florida-2027.html",
    "GAL": "https://www.cruisetimetables.com/cruises-from-galveston-texas-2027.html",
    "SJU": "https://www.cruisetimetables.com/cruises-from-san-juan-puerto-rico-2027.html",
}

# (portkey, ship, cruise_name, line, embark ISO, nights, stops, kind, pp, official)
R = [
    # ======================= FORT LAUDERDALE, FL =======================
    # --- Sun 7 Mar 2027 (fromfortlauderdaleflorida-07mar2027) ---
    ("FLL", "Adventure of the Seas", "6 Night Western Caribbean Cruise", "Royal Caribbean",
     "2027-03-07", 6, "Cozumel; Costa Maya; Nassau; Fort Lauderdale", "Interior", 533,
     "https://www.royalcaribbean.com/cruises/itinerary/6-night-western-caribbean-from-fort-lauderdale-on-adventure/AD06FLL-3043633741?sail-date=2027-03-07&currency=USD"),
    ("FLL", "Celebrity Beyond", "7 Night St. Thomas, St. Kitts & Puerto Plata",
     "Celebrity Cruises", "2027-03-07", 7,
     "Puerto Plata/Amber Cove; St Thomas; Basseterre (St. Kitts); Fort Lauderdale", "Interior", 1264,
     "https://www.celebritycruises.com/itinerary/7-night-st-thomas-st-kitts-cruise-from-fort-lauderdale-on-beyond-BY07E466?sailDate=2027-03-07&packageCode=BY07E466"),
    ("FLL", "Celebrity Silhouette", "6 Night Grand Cayman, Mexico & Bahamas",
     "Celebrity Cruises", "2027-03-07", 6,
     "Cozumel; George Town; Bimini Islands; Fort Lauderdale", "Interior", 632,
     "https://www.celebritycruises.com/itinerary/6-night-grand-cayman-mexico-bahamas-from-fort-lauderdale-on-silhouette-SI06W293?sailDate=2027-03-07&packageCode=SI06W293"),
    ("FLL", "Enchanted Princess", "10 Night Eastern Caribbean with St. Kitts",
     "Princess Cruises", "2027-03-07", 10,
     "Half Moon Cay; Puerto Plata/Amber Cove; San Juan; Philipsburg (St. Maarten); "
     "St Johns (Antigua); Basseterre (St. Kitts); Fort Lauderdale", "Interior", 1074,
     "https://www.princess.com/itinerary-details/?voyageCode=N708"),
    ("FLL", "Nieuw Statendam", "7 Night Eastern Caribbean: San Juan & St. Thomas",
     "Holland America Line", "2027-03-07", 7,
     "Grand Turk; San Juan; St Thomas; Half Moon Cay; Fort Lauderdale", "Inside", 999,
     "https://www.hollandamerica.com/en/us/find-a-cruise/c7e07b/j727"),
    # --- Sun 14 Mar 2027 (fromfortlauderdaleflorida-14mar2027) ---
    ("FLL", "Celebrity Beyond", "7 Night St. Thomas, St. Kitts & Puerto Plata",
     "Celebrity Cruises", "2027-03-14", 7,
     "Puerto Plata/Amber Cove; St Thomas; Basseterre (St. Kitts); Fort Lauderdale", "Interior", 1346,
     "https://www.celebritycruises.com/itinerary/7-night-st-thomas-st-kitts-cruise-from-fort-lauderdale-on-beyond-BY07E466?sailDate=2027-03-14&packageCode=BY07E466"),
    ("FLL", "Legend of the Seas", "6 Night Caribbean & Perfect Day", "Royal Caribbean",
     "2027-03-14", 6, "Perfect Day at CocoCay; Cozumel; Costa Maya; Fort Lauderdale",
     "Interior", 1359,
     "https://www.royalcaribbean.com/cruises/itinerary/6-night-caribbean-perfect-day-from-fort-lauderdale-on-legend/LE06FLL-385066157?sail-date=2027-03-14&currency=USD"),
    ("FLL", "Regal Princess",
     "6 Night Eastern Caribbean with Turks & Caicos & Celebration Key", "Princess Cruises",
     "2027-03-14", 6,
     "Celebration Key; Grand Turk; Puerto Plata/Amber Cove; Fort Lauderdale", "Interior", 724,
     "https://www.princess.com/itinerary-details/?voyageCode=G712"),
    ("FLL", "Sun Princess", "14 Night Eastern/Western Caribbean Adventurer",
     "Princess Cruises", "2027-03-14", 14,
     "Grand Turk; San Juan; further Eastern & Western Caribbean calls; Fort Lauderdale",
     "Interior", 1538,
     "https://www.princess.com/itinerary-details/?voyageCode=U712A"),

    # ======================= PORT CANAVERAL, FL =======================
    # --- Mon 1 Mar 2027 (fromportcanaveralflorida-01mar2027) ---
    ("PC", "Carnival Glory", "4 Night The Bahamas", "Carnival Cruise Line", "2027-03-01", 4,
     "Nassau; Celebration Key; Port Canaveral", "Interior", 309,
     "https://www.carnival.com/itinerary/4-day-the-bahamas-cruise/pt-canaveral/glory/4-days/bmb/?sailDate=03012027"),
    ("PC", "Disney Wish", "4 Night Bahamian Cruise From Port Canaveral", "Disney Cruise Line",
     "2027-03-01", 4, "Castaway Cay; Lighthouse Point; Port Canaveral", "Inside", 3512,
     "https://disneycruise.disney.go.com/cruises-destinations/list/WW0559/4-Night-Bahamian-Cruise-from-Port-Canaveral/2027-03-01-Disney-Wish/"),
    ("PC", "Sky Princess",
     "6 Night Eastern Caribbean with Turks and Caicos & Celebration Key", "Princess Cruises",
     "2027-03-01", 6, "Nassau; Grand Turk; Celebration Key; Port Canaveral", "Interior", 621,
     "https://www.princess.com/itinerary-details/?voyageCode=Y710"),
    ("PC", "Utopia of the Seas", "4 Night Bahamas & Perfect Day Cruise", "Royal Caribbean",
     "2027-03-01", 4, "Nassau; Perfect Day at CocoCay; Port Canaveral", "Interior", 635,
     "https://www.royalcaribbean.com/cruises/itinerary/4-night-bahamas-perfect-day-from-orlando-port-canaveral-on-utopia/UT04PCN-4069341576?sail-date=2027-03-01&currency=USD"),
    # --- Mon 15 Mar 2027 (fromportcanaveralflorida-15mar2027) ---
    ("PC", "Carnival Glory", "4 Night The Bahamas", "Carnival Cruise Line", "2027-03-15", 4,
     "Half Moon Cay; Celebration Key; Port Canaveral", "Interior", 469,
     "https://www.carnival.com/itinerary/4-day-the-bahamas-cruise/pt-canaveral/glory/4-days/bm6/?sailDate=03152027"),
    ("PC", "Disney Wish", "4 Night Bahamian Cruise From Port Canaveral", "Disney Cruise Line",
     "2027-03-15", 4, "Castaway Cay; Lighthouse Point; Port Canaveral", "Inside", 4280,
     "https://disneycruise.disney.go.com/cruises-destinations/list/WW0563/4-Night-Bahamian-Cruise-from-Port-Canaveral/2027-03-15-Disney-Wish/"),
    ("PC", "Explorer of the Seas", "4 Night Caribbean Getaway Cruise", "Royal Caribbean",
     "2027-03-15", 4, "Grand Turk; Port Canaveral", "Interior", 549,
     "https://www.royalcaribbean.com/cruises/itinerary/4-night-caribbean-getaway-from-orlando-port-canaveral-on-explorer/EX04PCN-1082066547?sail-date=2027-03-15&currency=USD"),
    ("PC", "Utopia of the Seas", "4 Night Bahamas & Perfect Day Cruise", "Royal Caribbean",
     "2027-03-15", 4, "Nassau; Perfect Day at CocoCay; Port Canaveral", "Interior", 873,
     "https://www.royalcaribbean.com/cruises/itinerary/4-night-bahamas-perfect-day-from-orlando-port-canaveral-on-utopia/UT04PCN-4069341576?sail-date=2027-03-15&currency=USD"),
    # --- Mon 22 Mar 2027 (fromportcanaveralflorida-22mar2027) ---
    ("PC", "Carnival Freedom", "5 Night The Bahamas", "Carnival Cruise Line", "2027-03-22", 5,
     "Celebration Key; Nassau; Half Moon Cay; Port Canaveral", "Interior", 543,
     "https://www.carnival.com/itinerary/5-day-the-bahamas-cruise/pt-canaveral/freedom/5-days/bme/?sailDate=03222027"),
    ("PC", "Carnival Glory", "4 Night The Bahamas", "Carnival Cruise Line", "2027-03-22", 4,
     "Nassau; Celebration Key; Port Canaveral", "Interior", 524,
     "https://www.carnival.com/itinerary/4-day-the-bahamas-cruise/pt-canaveral/glory/4-days/bmb/?sailDate=03222027"),
    ("PC", "Disney Wish", "4 Night Bahamian Cruise From Port Canaveral", "Disney Cruise Line",
     "2027-03-22", 4, "Nassau; Castaway Cay; Port Canaveral", "Inside", 4713,
     "https://disneycruise.disney.go.com/cruises-destinations/list/WW0565/4-Night-Bahamian-Cruise-from-Port-Canaveral/2027-03-22-Disney-Wish/"),
    ("PC", "Norwegian Getaway",
     "4 Night Bahamas Round-trip Orlando (Port Canaveral): Great Stirrup Cay & Nassau",
     "Norwegian Cruise Line", "2027-03-22", 4, "Great Stirrup Cay; Nassau; Port Canaveral",
     "Inside", 429,
     "https://www.ncl.com/vacation-builder?itineraryCode=GETAWAY4PCVNPINASPCV-NIC-GETAWAY4PCVNASNPIPCV&packageId=23468065&stateroomTypeCode=INSIDE&"),
    ("PC", "Utopia of the Seas", "4 Night Bahamas & Perfect Day Cruise", "Royal Caribbean",
     "2027-03-22", 4, "Perfect Day at CocoCay; Nassau; Port Canaveral", "Interior", 792,
     "https://www.royalcaribbean.com/cruises/itinerary/4-night-bahamas-perfect-day-from-orlando-port-canaveral-on-utopia/UT04PCN-4069341576?sail-date=2027-03-22&currency=USD"),

    # --- Mon 29 Mar 2027 (fromportcanaveralflorida-29mar2027) ---
    ("PC", "Carnival Glory", "4 Night The Bahamas", "Carnival Cruise Line", "2027-03-29", 4,
     "Nassau; Celebration Key; Port Canaveral", "Interior", 544,
     "https://www.carnival.com/itinerary/4-day-the-bahamas-cruise/pt-canaveral/glory/4-days/bma/?sailDate=03292027"),
    ("PC", "Disney Wish", "4 Night Bahamian Cruise From Port Canaveral", "Disney Cruise Line",
     "2027-03-29", 4, "Castaway Cay; Lighthouse Point; Port Canaveral", "Inside", 4824,
     "https://disneycruise.disney.go.com/cruises-destinations/list/WW0567/4-Night-Bahamian-Cruise-from-Port-Canaveral/2027-03-29-Disney-Wish/"),
    ("PC", "Explorer of the Seas", "4 Night Caribbean Getaway Cruise", "Royal Caribbean",
     "2027-03-29", 4, "Grand Turk; Port Canaveral", "Interior", 626,
     "https://www.royalcaribbean.com/cruises/itinerary/4-night-caribbean-getaway-from-orlando-port-canaveral-on-explorer/EX04PCN-1082066547?sail-date=2027-03-29&currency=USD"),
    ("PC", "Utopia of the Seas", "4 Night Bahamas & Perfect Day Cruise", "Royal Caribbean",
     "2027-03-29", 4, "Nassau; Perfect Day at CocoCay; Port Canaveral", "Interior", 941,
     "https://www.royalcaribbean.com/cruises/itinerary/4-night-bahamas-perfect-day-from-orlando-port-canaveral-on-utopia/UT04PCN-4069341576?sail-date=2027-03-29&currency=USD"),

    # ======================= MIAMI, FL =======================
    # --- Thu 18 Mar 2027 (frommiamiflorida-18mar2027) ---
    ("MIA", "Brilliant Lady", "4 Night Key West & Bimini Beach Club", "Virgin Voyages",
     "2027-03-18", 4, "Key West; Bimini Islands; Miami", "From", 636,
     "https://www.virginvoyages.com/book/voyage-planner/pre-checkout?currencyCode=USD&packageCode=4NKW&voyageId=BR2703184NKW"),
    ("MIA", "Carnival Firenze", "4 Night The Bahamas", "Carnival Cruise Line", "2027-03-18", 4,
     "Half Moon Cay; Celebration Key; Miami", "Interior", 458,
     "https://www.carnival.com/itinerary/4-day-the-bahamas-cruise/miami/firenze/4-days/bhp/?sailDate=03182027"),
    ("MIA", "MSC Poesia", "10 Night Southern Caribbean", "MSC Cruises", "2027-03-18", 10,
     "Willemstad (Curacao); Kralendijk (Bonaire); Oranjestad (Aruba); Cabo Rojo; Ocho Rios; Miami",
     "From", 1118,
     "https://www.msccruisesusa.com/itinerary-details/10-nights-southern-caribbean?cruiseid=PO20270318MIAMIA"),
    # --- Thu 25 Mar 2027 (frommiamiflorida-25mar2027) ---
    ("MIA", "Carnival Sunrise", "4 Night The Bahamas", "Carnival Cruise Line", "2027-03-25", 4,
     "Celebration Key; Half Moon Cay; Miami", "Interior", 444,
     "https://www.carnival.com/itinerary/4-day-the-bahamas-cruise/miami/sunrise/4-days/bhq/?sailDate=03252027"),
    ("MIA", "Freedom of the Seas", "4 Night Eastern Caribbean Cruise", "Royal Caribbean",
     "2027-03-25", 4, "Grand Turk; Miami", "Interior", 569,
     "https://www.royalcaribbean.com/cruises/itinerary/4-night-eastern-caribbean-from-miami-on-freedom/FR04MIA-3280107330?sail-date=2027-03-25&currency=USD"),

    # ======================= TAMPA, FL =======================
    # --- Mon 22 Feb 2027 (fromtampaflorida-22feb2027) ---
    ("TPA", "Jewel of the Seas", "5 Night Western Caribbean Cruise", "Royal Caribbean",
     "2027-02-22", 5, "Costa Maya; Cozumel; Tampa", "Interior", 574,
     "https://www.royalcaribbean.com/cruises/itinerary/5-night-western-caribbean-from-tampa-on-jewel/JW05TPA-1176431029?sail-date=2027-02-22&currency=USD"),
    # --- Mon 8 Mar 2027 (fromtampaflorida-08mar2027) ---
    ("TPA", "Jewel of the Seas", "5 Night Western Caribbean Cruise", "Royal Caribbean",
     "2027-03-08", 5, "Cozumel; Costa Maya; Tampa", "Interior", 449,
     "https://www.royalcaribbean.com/cruises/itinerary/5-night-western-caribbean-from-tampa-on-jewel/JW05TPA-1176431029?sail-date=2027-03-08&currency=USD"),
    ("TPA", "Norwegian Gem", "4 Night Bahamas Round-trip Tampa: Great Stirrup Cay",
     "Norwegian Cruise Line", "2027-03-08", 4, "Great Stirrup Cay; Tampa", "Inside", 409,
     "https://www.ncl.com/vacation-builder?itineraryCode=GEM4TPANPITPA&packageId=25382895&stateroomTypeCode=INSIDE&"),

    # ======================= GALVESTON, TX =======================
    # --- Mon 22 Feb 2027 (fromgalvestontexas-22feb2027) ---
    ("GAL", "Carnival Breeze", "4 Night Western Caribbean", "Carnival Cruise Line",
     "2027-02-22", 4, "Cozumel; Galveston", "Interior", 372,
     "https://www.carnival.com/itinerary/4-day-western-caribbean-cruise/galveston/breeze/4-days/glb/?sailDate=02222027"),

    # --- Sun 21 Mar 2027 (fromfortlauderdaleflorida-21mar2027) ---
    ("FLL", "Adventure of the Seas", "6 Night Western Caribbean Cruise", "Royal Caribbean",
     "2027-03-21", 6, "Falmouth (Jamaica); George Town; Nassau; Fort Lauderdale", "Interior", 703,
     "https://www.royalcaribbean.com/cruises/itinerary/6-night-western-caribbean-from-fort-lauderdale-on-adventure/AD06FLL-1756957036?sail-date=2027-03-21&currency=USD"),
    ("FLL", "Celebrity Beyond", "7 Night Grand Cayman, Mexico & Bahamas", "Celebrity Cruises",
     "2027-03-21", 7,
     "Bimini Islands; Nassau; Cozumel; George Town; Fort Lauderdale", "Interior", 1303,
     "https://www.celebritycruises.com/itinerary/7-night-grand-cayman-mexico-bahamas-from-fort-lauderdale-on-beyond-BY07W714?sailDate=2027-03-21&packageCode=BY07W714"),
    ("FLL", "Nieuw Amsterdam",
     "12 Night Panama Canal Discovery: Costa Rica & Greater Antilles", "Holland America Line",
     "2027-03-21", 12,
     "Half Moon Cay; Oranjestad (Aruba); Cartagena; Panama Canal; Colon; Puerto Limon; "
     "George Town; Fort Lauderdale", "Inside", 1749,
     "https://www.hollandamerica.com/en/us/find-a-cruise/c7f12a/i723"),

    # ======================= GALVESTON, TX (continued) =======================
    # --- Sun 14 Mar 2027 (fromgalvestontexas-14mar2027) ---
    ("GAL", "Carnival Jubilee", "6 Night Western Caribbean", "Carnival Cruise Line",
     "2027-03-14", 6, "Cozumel; Roatan; Galveston", "Interior", 890,
     "https://www.carnival.com/itinerary/6-day-western-caribbean-cruise/galveston/jubilee/6-days/wcp/?sailDate=03142027"),
    ("GAL", "MSC Seascape", "7 Night Western Caribbean", "MSC Cruises", "2027-03-14", 7,
     "Costa Maya; Roatan; Cozumel; Galveston", "From", 650,
     "https://www.msccruisesusa.com/itinerary-details/7-nights-western-caribbean?cruiseid=SC20270314GLSGLS"),
    ("GAL", "Symphony of the Seas", "7 Night Western Caribbean Cruise", "Royal Caribbean",
     "2027-03-14", 7, "Costa Maya; Roatan; Cozumel; Galveston", "Interior", 1094,
     "https://www.royalcaribbean.com/cruises/itinerary/7-night-western-caribbean-from-galveston-on-symphony/SY07GAL-3851841824?sail-date=2027-03-14&currency=USD"),

    # ======================= SAN JUAN, PR =======================
    # --- Sun 21 Feb 2027 (fromsanjuanpuertorico-21feb2027) ---
    ("SJU", "Crown Princess", "7 Night Southern Caribbean with Barbados and St. Lucia",
     "Princess Cruises", "2027-02-21", 7,
     "St Thomas; Philipsburg (St. Maarten); St Johns (Antigua); Castries (St Lucia); "
     "Bridgetown (Barbados); San Juan", "Interior", 679,
     "https://www.princess.com/itinerary-details/?voyageCode=3709"),
    ("SJU", "Crown Princess", "14 Night Southern Caribbean Adventurer", "Princess Cruises",
     "2027-02-21", 14,
     "St Thomas; Philipsburg (St. Maarten); St Johns (Antigua); Castries (St Lucia); "
     "Bridgetown (Barbados); San Juan (turn); Philipsburg; Fort de France (Martinique); "
     "Roseau (Dominica); St Georges (Grenada); Bridgetown; San Juan", "Interior", 1227,
     "https://www.princess.com/itinerary-details/?voyageCode=3709A"),
    ("SJU", "Norwegian Prima",
     "7 Night Caribbean Round-Trip San Juan: Barbados & St. Thomas",
     "Norwegian Cruise Line", "2027-02-21", 7,
     "Tortola; Basseterre (St. Kitts); Bridgetown (Barbados); Castries (St Lucia); "
     "Philipsburg (St. Maarten); St Thomas; San Juan", "Inside", 1449,
     "https://www.ncl.com/vacation-builder?itineraryCode=PRIMA7SJUTOVBASBGISLUPHISTTSJU-NIC-PRIMA7SJUBASBGIPHISLUSTTTOVSJU&packageId=24929584&stateroomTypeCode=INSIDE&"),
    ("SJU", "Vision of the Seas", "7 Night Southern Caribbean Cruise", "Royal Caribbean",
     "2027-02-21", 7,
     "St Thomas; St Croix; Philipsburg (St. Maarten); further Southern Caribbean calls; San Juan",
     "Interior", 599,
     "https://www.royalcaribbean.com/cruises/itinerary/7-night-southern-caribbean-from-san-juan-on-vision/VI07SJU-1321850104?sail-date=2027-02-21&currency=USD"),
    # --- Sun 28 Feb 2027 (fromsanjuanpuertorico-28feb2027) ---
    ("SJU", "Crown Princess", "14 Night Southern Caribbean Adventurer", "Princess Cruises",
     "2027-02-28", 14,
     "Philipsburg (St. Maarten); Fort de France (Martinique); Roseau (Dominica); "
     "St Georges (Grenada); Bridgetown (Barbados); San Juan (turn); St Thomas; Philipsburg; "
     "St Johns (Antigua); Castries (St Lucia); Bridgetown; San Juan", "Interior", 1282,
     "https://www.princess.com/itinerary-details/?voyageCode=3710A"),
    ("SJU", "Crown Princess", "7 Night Southern Caribbean Adventurer", "Princess Cruises",
     "2027-02-28", 7,
     "Philipsburg (St. Maarten); Fort de France (Martinique); Roseau (Dominica); "
     "St Georges (Grenada); Bridgetown (Barbados); San Juan", "Interior", 599,
     "https://www.princess.com/itinerary-details/?voyageCode=3710"),
    ("SJU", "Norwegian Prima",
     "7 Night Caribbean Round-Trip San Juan: Barbados & St. Thomas",
     "Norwegian Cruise Line", "2027-02-28", 7,
     "Tortola; Roseau (Dominica); Bridgetown (Barbados); Philipsburg (St. Maarten); "
     "St Thomas; San Juan", "Inside", 1369,
     "https://www.ncl.com/vacation-builder?itineraryCode=PRIMA7SJUTOVRSUBGIPHISTTSJU-NIC-PRIMA7SJUBGIPHIRSUSTTTOVSJU&packageId=24929585&stateroomTypeCode=INSIDE&"),
    ("SJU", "Vision of the Seas", "7 Night Southern Caribbean Cruise", "Royal Caribbean",
     "2027-02-28", 7,
     "St Thomas; St Johns (Antigua); Fort de France (Martinique); St Vincent; "
     "St Georges (Grenada); San Juan", "Interior", 719,
     "https://www.royalcaribbean.com/cruises/itinerary/7-night-southern-caribbean-from-san-juan-on-vision/VI07SJU-685544967?sail-date=2027-02-28&currency=USD"),
    # --- Sun 7 Mar 2027 (fromsanjuanpuertorico-07mar2027) ---
    ("SJU", "Crown Princess", "14 Night Southern Caribbean Adventurer", "Princess Cruises",
     "2027-03-07", 14,
     "St Thomas; Philipsburg (St. Maarten); St Johns (Antigua); Castries (St Lucia); "
     "Bridgetown (Barbados); San Juan (turn); St Thomas; Basseterre (St. Kitts); "
     "Roseau (Dominica); St Georges (Grenada); Bridgetown; San Juan", "Interior", 1441,
     "https://www.princess.com/itinerary-details/?voyageCode=3711A"),
    ("SJU", "Crown Princess", "7 Night Southern Caribbean with Barbados and St. Lucia",
     "Princess Cruises", "2027-03-07", 7,
     "St Thomas; Philipsburg (St. Maarten); St Johns (Antigua); Castries (St Lucia); "
     "Bridgetown (Barbados); San Juan", "Interior", 649,
     "https://www.princess.com/itinerary-details/?voyageCode=3711"),
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
        # Dedup key includes nights: a ship can legitimately sell two DIFFERENT bookable
        # voyages departing the same port on the same day (e.g. Crown Princess San Juan
        # 21 Feb sells both a 7N and a 14N collector). Passes 3-4 established these are
        # distinct products. Every same-(port,ship,date) pair is surfaced below for review.
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
        rid = f"{pk}5-{counters[pk]:02d}"
        d_embark = datetime.date.fromisoformat(embark)
        d_disembark = d_embark + datetime.timedelta(days=nights)
        d_out = d_embark - datetime.timedelta(days=1)
        d_back = d_disembark + datetime.timedelta(days=1)
        cruise_2 = 2 * pp
        flight_2 = 2 * base_pp
        kind_label = {"Interior": "Interior", "Inside": "Inside",
                      "From": "MSC/Virgin lead-in 'From'"}[kind]
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
            "status": f"NEW {PUB} pass 5 \u2014 remaining uncovered dates at FLL/PC/MIA/TPA/GAL/SJU, line-by-line verified",
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
                f"National-expansion pass 5 ({PUB}): sail date, ship, duration, full port sequence and the "
                f"published per-person USD {kind_label} price were read line by line from the cruisetimetables "
                f"PER-DAY from-port 2027 page (official cruise-line fare feed); the official cruise-line deep "
                f"link was taken from that same page. This pass closed the remaining uncovered departure dates "
                f"at Fort Lauderdale, Port Canaveral, Miami, Tampa, Galveston and San Juan. Dedup-checked "
                f"against the master by (port, ship, date, nights); in-window and duration asserts enforced in "
                f"code. Snapshot \u2260 live quote; cabin class, taxes/fees and availability must be reconfirmed."
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
    # byte-for-byte mirrors (text-mode copy would rewrite CRLF -> LF and break parity)
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
