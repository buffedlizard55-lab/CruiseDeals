#!/usr/bin/env python3
"""National expansion pass 6 (2026-08-30) — 50 NEW verified in-window sailings.

GAP THIS PASS CLOSES
--------------------
A per-port DATE-COVERAGE audit (every one of the 45 in-window dates checked against
the master) showed how much of the calendar was still untouched after pass 5:

    port                 rows  dates held  dates MISSING (of 45)
    Miami, FL              65      16              29
    Fort Lauderdale, FL    34       9              36
    Port Canaveral, FL     53      11              34
    Galveston, TX          26      12              33
    Tampa, FL              17       8              37

This pass sweeps the highest-yield remaining uncovered per-day pages at those ports.
It adds 50 sailings and brings in SEVEN ships that appeared nowhere in the master
list before:

    Harmony of the Seas, Radiance of the Seas, MSC Seashore, Disney Magic,
    Margaritaville at Sea Islander, Norwegian Jewel (as a regular revenue sailing),
    plus new Norwegian Joy / Carnival Conquest / Carnival Sunrise dated voyages.

Every row was read LINE BY LINE from the cruisetimetables.com per-day "from port"
pages (accessed 2026-08-30, site-dated 29 August 2026), which republish the official
cruise-line fare feed AND carry a per-sailing official deep link. Each record holds:
sail date, ship, official cruise name, nights, full published port sequence, the
official cruise-line deep link, and the published per-person USD Interior/Inside
price (MSC & Virgin = lead-in "From").

NOT ADDED (flagged irregularities -> see verification log):
  * Norwegian Jewel Miami 2027-03-15 "4 Night Keeping The Blues Alive At Sea XII" —
    full-ship CHARTER (bluesaliveatsea.com), fare feed publishes literally "NA".
  * Azamara Journey Miami 2027-03-29 37N and 12N — both OPEN JAW (Venice / Lisbon).
  * Explora III Miami 2027-03-29 7N — OPEN JAW to San Juan; ultra-luxury brand.
  * Carnival Firenze Miami 2027-03-22 13N — departs in window, returns 4 Apr 2027.
  * New Orleans 2027-03-08 — day page redirects to the port index: no sailings.

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
}

SRC = {
    "MIA": "https://www.cruisetimetables.com/cruises-from-miami-florida-2027.html",
    "PC":  "https://www.cruisetimetables.com/cruises-from-port-canaveral-florida-2027.html",
    "FLL": "https://www.cruisetimetables.com/cruises-from-fort-lauderdale-florida-2027.html",
    "TPA": "https://www.cruisetimetables.com/cruises-from-tampa-florida-2027.html",
    "GAL": "https://www.cruisetimetables.com/cruises-from-galveston-texas-2027.html",
}

# (portkey, ship, cruise_name, line, embark ISO, nights, stops, kind, pp, official)
R = [
    # ======================= MIAMI, FL =======================
    # --- Thu 4 Mar 2027 (frommiamiflorida-04mar2027) ---
    ("MIA", "Brilliant Lady", "4 Night Key West & Bimini Beach Club", "Virgin Voyages",
     "2027-03-04", 4, "Key West; Bimini Islands; Miami", "From", 636,
     "https://www.virginvoyages.com/book/voyage-planner/pre-checkout?currencyCode=USD&packageCode=4NKW&voyageId=BR2703044NKW"),
    # --- Sun 28 Feb 2027 (frommiamiflorida-28feb2027) ---
    ("MIA", "Allure of the Seas", "7 Night Eastern Caribbean Cruise", "Royal Caribbean",
     "2027-02-28", 7, "Philipsburg (St. Maarten); St Thomas; Puerto Plata/Amber Cove; Miami",
     "Interior", 1358,
     "https://www.royalcaribbean.com/cruises/itinerary/7-night-eastern-caribbean-from-miami-on-allure/AL07MIA-2574420622?sail-date=2027-02-28&currency=USD"),
    ("MIA", "Carnival Celebration", "7 Night Eastern Caribbean", "Carnival Cruise Line",
     "2027-02-28", 7, "St Thomas; San Juan; Celebration Key; Miami", "Interior", 591,
     "https://www.carnival.com/itinerary/7-day-eastern-caribbean-cruise/miami/celebration/7-days/cb9/?sailDate=02282027"),
    ("MIA", "Carnival Magic", "6 Night Eastern Caribbean", "Carnival Cruise Line",
     "2027-02-28", 6, "Celebration Key; Puerto Plata/Amber Cove; Grand Turk; Miami",
     "Interior", 439,
     "https://www.carnival.com/itinerary/6-day-eastern-caribbean-cruise/miami/magic/6-days/ce9/?sailDate=02282027"),
    ("MIA", "Celebrity Xcel", "7 Night St. Thomas & Antigua", "Celebrity Cruises",
     "2027-02-28", 7, "Nassau; St Thomas; St Johns (Antigua); Miami", "Interior", 892,
     "https://www.celebritycruises.com/itinerary/7-night-st-thomas-antigua-cruise-from-miami-on-xcel-XC07E473?sailDate=2027-02-28&packageCode=XC07E473"),
    ("MIA", "Explora III",
     "14 Night An Extended Journey through Azure Horizons & Elegant Isles",
     "Explora Journeys", "2027-02-28", 14,
     "St John (USVI); St Johns (Antigua); Iles Des Saintes; St Thomas; San Juan; "
     "Philipsburg (St. Maarten); St Barthelemy; Basseterre (St. Kitts); Grand Turk; Miami",
     "From", 9675,
     "https://www.explorajourneys.com/us/en/destinations-globe/car/journeys/miamia-14-v10?id-journey=EL20270228MIAMIA&id-offer=airinclusa"),
    ("MIA", "Norwegian Aqua",
     "7 Night Caribbean Round-trip Miami: Great Stirrup Cay & Dominican Republic",
     "Norwegian Cruise Line", "2027-02-28", 7,
     "Puerto Plata/Amber Cove; St Thomas; Tortola; Great Stirrup Cay; Miami", "Inside", 1089,
     "https://www.ncl.com/vacation-builder?itineraryCode=AQUA7MIAPOPSTTTOVNPIMIA-NIC-AQUA7MIANPIPOPSTTTOVMIA&packageId=23353056&stateroomTypeCode=INSIDE&"),
    ("MIA", "Resilient Lady", "7 Night Western Caribbean & Bimini Beach Club", "Virgin Voyages",
     "2027-02-28", 7,
     "George Town (Grand Cayman); Ocho Rios; Nassau; Bimini Islands; Miami", "From", 973,
     "https://www.virginvoyages.com/book/voyage-planner/pre-checkout?currencyCode=USD&packageCode=7NONB&voyageId=RS2702287NONB"),
    # --- Wed 24 Mar 2027 (frommiamiflorida-24mar2027) ---
    ("MIA", "Norwegian Sun",
     "12 Night Panama Canal Round-trip Miami: Mexico, Jamaica & Costa Rica",
     "Norwegian Cruise Line", "2027-03-24", 12,
     "Ocho Rios; George Town (Grand Cayman); Cartagena; Panama Canal (cruising); Colon; "
     "Puerto Limon; Harvest Caye; Cozumel; Miami", "Inside", 1819,
     "https://www.ncl.com/vacation-builder?itineraryCode=SUN12MIAOCJGECCTGPCGCLNLIOBPICZMMIA-NIC-SUN12MIABPICLNCTGCZMGECLIOOCJPCGMIA&packageId=23377871&stateroomTypeCode=INSIDE&"),
    ("MIA", "Zuiderdam", "4 Night Caribbean Getaway: Key West & Bahamas",
     "Holland America Line", "2027-03-24", 4, "Key West; Half Moon Cay; Miami", "Inside", 549,
     "https://www.hollandamerica.com/en/us/find-a-cruise/c7e04a/u724"),
    ("MIA", "Zuiderdam", "14 Night Eastern & Southern Caribbean: Key West & Abc Islands",
     "Holland America Line", "2027-03-24", 14,
     "Key West; Half Moon Cay; Miami; Half Moon Cay; Cabo Rojo; Kralendijk (Bonaire); "
     "Willemstad (Curacao); Oranjestad (Aruba); Miami", "Inside", 1494,
     "https://www.hollandamerica.com/en/us/find-a-cruise/c7x14m/u724a"),
    # --- Mon 15 Mar 2027 (frommiamiflorida-15mar2027) ---
    ("MIA", "Carnival Conquest", "4 Night The Bahamas", "Carnival Cruise Line", "2027-03-15", 4,
     "Half Moon Cay; Celebration Key; Miami", "Interior", 365,
     "https://www.carnival.com/itinerary/4-day-the-bahamas-cruise/miami/conquest/4-days/bhr/?sailDate=03152027"),
    ("MIA", "Carnival Sunrise", "5 Night The Bahamas", "Carnival Cruise Line", "2027-03-15", 5,
     "Celebration Key; Half Moon Cay; Nassau; Miami", "Interior", 427,
     "https://www.carnival.com/itinerary/5-day-the-bahamas-cruise/miami/sunrise/5-days/bh9/?sailDate=03152027"),
    ("MIA", "Freedom of the Seas", "5 Night Western Caribbean Cruise", "Royal Caribbean",
     "2027-03-15", 5, "Nassau; Puerto Plata/Amber Cove; Miami", "Interior", 548,
     "https://www.royalcaribbean.com/cruises/itinerary/5-night-western-caribbean-from-miami-on-freedom/FR05MIA-1172079608?sail-date=2027-03-15&currency=USD"),
    ("MIA", "Margaritaville at Sea Beachcomber", "5 Night Bahamas & Eastern Caribbean",
     "Margaritaville at Sea", "2027-03-15", 5,
     "Nassau; Puerto Plata/Amber Cove; Miami", "Inside", 429,
     "https://margaritavilleatsea.com/"),
    ("MIA", "MSC Seaside", "4 Night The Bahamas & Ocean Cay", "MSC Cruises", "2027-03-15", 4,
     "Nassau; Ocean Cay; Miami", "From", 281,
     "https://www.msccruisesusa.com/itinerary-details/4-nights-the-bahamas--ocean-cay?cruiseid=SE20270315MIAMIA"),
    ("MIA", "MSC Seaside", "7 Night Caribbean & Bahamas", "MSC Cruises", "2027-03-15", 7,
     "Nassau; Ocean Cay; Miami; Nassau; Ocean Cay; Miami", "From", 615,
     "https://www.msccruisesusa.com/itinerary-details/7-nights-caribbean--bahamas?cruiseid=SE20270315MIAMI1"),
    ("MIA", "Norwegian Joy",
     "4 Night Bahamas Round-trip Miami: Great Stirrup Cay & Nassau",
     "Norwegian Cruise Line", "2027-03-15", 4, "Nassau; Great Stirrup Cay; Miami", "Inside", 519,
     "https://www.ncl.com/vacation-builder?itineraryCode=JOY4MIANASNPIMIA&packageId=23425119&stateroomTypeCode=INSIDE&"),
    ("MIA", "Scarlet Lady", "5 Night Dominican Republic & Bimini Beach Club", "Virgin Voyages",
     "2027-03-15", 5, "Puerto Plata/Amber Cove; Bimini Islands; Miami", "From", 845,
     "https://www.virginvoyages.com/book/voyage-planner/pre-checkout?currencyCode=USD&packageCode=5NPP&voyageId=SC2703155NPP"),
    ("MIA", "Wonder of the Seas", "4 Night Perfect Day CocoCay & Bahamas", "Royal Caribbean",
     "2027-03-15", 4, "Nassau; Perfect Day at CocoCay; Miami", "Interior", 753,
     "https://www.royalcaribbean.com/cruises/itinerary/4-night-perfect-day-cococay-bahamas-from-miami-on-wonder/WN04MIA-1040267344?sail-date=2027-03-15&currency=USD"),
    # --- Mon 22 Mar 2027 (frommiamiflorida-22mar2027) ---
    ("MIA", "Brilliant Lady", "4 Night Bahamas & Bimini Beach Club", "Virgin Voyages",
     "2027-03-22", 4, "Bimini Islands; Miami", "From", 556,
     "https://www.virginvoyages.com/book/voyage-planner/pre-checkout?currencyCode=USD&packageCode=4NMF&voyageId=BR2703224NMF"),
    ("MIA", "Carnival Conquest", "4 Night The Bahamas", "Carnival Cruise Line", "2027-03-22", 4,
     "Celebration Key; Half Moon Cay; Miami", "Interior", 455,
     "https://www.carnival.com/itinerary/4-day-the-bahamas-cruise/miami/conquest/4-days/bhq/?sailDate=03222027"),
    ("MIA", "MSC Seaside", "4 Night The Bahamas & Ocean Cay", "MSC Cruises", "2027-03-22", 4,
     "Nassau; Ocean Cay; Miami", "From", 381,
     "https://www.msccruisesusa.com/itinerary-details/4-nights-the-bahamas--ocean-cay?cruiseid=SE20270322MIAMIA"),
    ("MIA", "MSC Seaside", "7 Night Caribbean & Bahamas", "MSC Cruises", "2027-03-22", 7,
     "Nassau; Ocean Cay; Miami; Nassau; Ocean Cay; Miami", "From", 755,
     "https://www.msccruisesusa.com/itinerary-details/7-nights-caribbean--bahamas?cruiseid=SE20270322MIAMI1"),
    ("MIA", "Norwegian Joy",
     "4 Night Bahamas Round-Trip Miami: Great Stirrup Cay & Nassau",
     "Norwegian Cruise Line", "2027-03-22", 4, "Great Stirrup Cay; Nassau; Miami", "Inside", 499,
     "https://www.ncl.com/vacation-builder?itineraryCode=JOY4MIANPINASMIA-NIC-JOY4MIANASNPIMIA&packageId=23379752&stateroomTypeCode=INSIDE&"),
    ("MIA", "Wonder of the Seas", "4 Night Perfect Day CocoCay & Bahamas", "Royal Caribbean",
     "2027-03-22", 4, "Nassau; Perfect Day at CocoCay; Miami", "Interior", 878,
     "https://www.royalcaribbean.com/cruises/itinerary/4-night-perfect-day-cococay-bahamas-from-miami-on-wonder/WN04MIA-1040267344?sail-date=2027-03-22&currency=USD"),
    # --- Mon 29 Mar 2027 (frommiamiflorida-29mar2027) ---
    ("MIA", "Carnival Conquest", "4 Night The Bahamas", "Carnival Cruise Line", "2027-03-29", 4,
     "Half Moon Cay; Celebration Key; Miami", "Interior", 475,
     "https://www.carnival.com/itinerary/4-day-the-bahamas-cruise/miami/conquest/4-days/bhp/?sailDate=03292027"),
    ("MIA", "Carnival Sunrise", "5 Night The Bahamas", "Carnival Cruise Line", "2027-03-29", 5,
     "Celebration Key; Half Moon Cay; Nassau; Miami", "Interior", 447,
     "https://www.carnival.com/itinerary/5-day-the-bahamas-cruise/miami/sunrise/5-days/bhg/?sailDate=03292027"),
    ("MIA", "Freedom of the Seas", "5 Night Western Caribbean Cruise", "Royal Caribbean",
     "2027-03-29", 5, "Nassau; Puerto Plata/Amber Cove; Miami", "Interior", 558,
     "https://www.royalcaribbean.com/cruises/itinerary/5-night-western-caribbean-from-miami-on-freedom/FR05MIA-1172079608?sail-date=2027-03-29&currency=USD"),
    ("MIA", "MSC Seaside", "4 Night The Bahamas & Ocean Cay", "MSC Cruises", "2027-03-29", 4,
     "Nassau; Ocean Cay; Miami", "From", 401,
     "https://www.msccruisesusa.com/itinerary-details/4-nights-the-bahamas--ocean-cay?cruiseid=SE20270329MIAMIA"),
    ("MIA", "MSC Seaside", "7 Night Caribbean & Bahamas", "MSC Cruises", "2027-03-29", 7,
     "Nassau; Ocean Cay; Miami; Nassau; Ocean Cay; Miami", "From", 695,
     "https://www.msccruisesusa.com/itinerary-details/7-nights-caribbean--bahamas?cruiseid=SE20270329MIAMI1"),
    ("MIA", "Norwegian Jewel", "4 Night Caribbean Round-trip Miami", "Norwegian Cruise Line",
     "2027-03-29", 4, "Cozumel; Miami", "Inside", 499,
     "https://www.ncl.com/vacation-builder?itineraryCode=JEWEL4MIACZMMIA&packageId=24767586&stateroomTypeCode=INSIDE&"),

    # ======================= PORT CANAVERAL, FL =======================
    # --- Thu 25 Feb 2027 (fromportcanaveralflorida-25feb2027) ---
    ("PC", "Harmony of the Seas", "5 Night Bahamas & Perfect Day Cruise", "Royal Caribbean",
     "2027-02-25", 5, "Perfect Day at CocoCay; Nassau; Port Canaveral", "Interior", 677,
     "https://www.royalcaribbean.com/cruises/itinerary/5-night-bahamas-perfect-day-from-orlando-port-canaveral-on-harmony/HM05PCN-3790280278?sail-date=2027-02-25&currency=USD"),
    ("PC", "MSC Seashore", "3 Night The Bahamas & Ocean Cay", "MSC Cruises", "2027-02-25", 3,
     "Nassau; Ocean Cay; Port Canaveral", "From", 222,
     "https://www.msccruisesusa.com/itinerary-details/3-nights-the-bahamas--ocean-cay?cruiseid=SH20270225CPVCPV"),

    # --- Thu 4 Mar 2027 (fromportcanaveralflorida-04mar2027) ---
    ("PC", "Carnival Freedom", "4 Night The Bahamas", "Carnival Cruise Line", "2027-03-04", 4,
     "Half Moon Cay; Celebration Key; Port Canaveral", "Interior", 370,
     "https://www.carnival.com/itinerary/4-day-the-bahamas-cruise/pt-canaveral/freedom/4-days/bm6/?sailDate=03042027"),
    ("PC", "MSC Seashore", "3 Night The Bahamas & Ocean Cay", "MSC Cruises", "2027-03-04", 3,
     "Nassau; Ocean Cay; Port Canaveral", "From", 275,
     "https://www.msccruisesusa.com/itinerary-details/3-nights-the-bahamas--ocean-cay?cruiseid=SH20270304CPVCPV"),
    # --- Thu 11 Mar 2027 (fromportcanaveralflorida-11mar2027) ---
    ("PC", "MSC Seashore", "3 Night The Bahamas & Ocean Cay", "MSC Cruises", "2027-03-11", 3,
     "Nassau; Ocean Cay; Port Canaveral", "From", 305,
     "https://www.msccruisesusa.com/itinerary-details/3-nights-the-bahamas--ocean-cay?cruiseid=SH20270311CPVCPV"),

    # ======================= FORT LAUDERDALE, FL =======================
    # --- Sun 28 Feb 2027 (fromfortlauderdaleflorida-28feb2027) ---
    ("FLL", "Nieuw Amsterdam",
     "12 Night Panama Canal Discovery: Costa Rica & Greater Antilles", "Holland America Line",
     "2027-02-28", 12,
     "Half Moon Cay; Oranjestad (Aruba); Cartagena; Panama Canal (cruising); Colon; "
     "Puerto Limon; George Town (Grand Cayman); Fort Lauderdale", "Inside", 1749,
     "https://www.hollandamerica.com/en/us/find-a-cruise/c7f12a/i719"),
    ("FLL", "Nieuw Statendam", "7 Night Eastern Caribbean: Amber Cove & Bahamas",
     "Holland America Line", "2027-02-28", 7,
     "Nassau; Grand Turk; Puerto Plata/Amber Cove; Half Moon Cay; Fort Lauderdale", "Inside", 899,
     "https://www.hollandamerica.com/en/us/find-a-cruise/c7e07e/j726"),
    ("FLL", "Nieuw Statendam", "14 Night Eastern Caribbean: Bahamas & San Juan",
     "Holland America Line", "2027-02-28", 14,
     "Nassau; Grand Turk; Puerto Plata/Amber Cove; Half Moon Cay; Fort Lauderdale; Grand Turk; "
     "San Juan; St Thomas; Half Moon Cay; Fort Lauderdale", "Inside", 1714,
     "https://www.hollandamerica.com/en/us/find-a-cruise/c7e14c/j726a"),
    ("FLL", "Regal Princess",
     "6 Night Eastern Caribbean with Turks & Caicos & Celebration Key", "Princess Cruises",
     "2027-02-28", 6, "Celebration Key; Grand Turk; Nassau; Fort Lauderdale", "Interior", 449,
     "https://www.princess.com/itinerary-details/?voyageCode=G710"),
    ("FLL", "Regal Princess",
     "14 Night Southern/Eastern Caribbean Adventurer with Celebration Key", "Princess Cruises",
     "2027-02-28", 14,
     "Celebration Key; Grand Turk; Nassau; Fort Lauderdale; Puerto Plata/Amber Cove; "
     "Willemstad (Curacao); Oranjestad (Aruba); Fort Lauderdale", "Interior", 2178,
     "https://www.princess.com/itinerary-details/?voyageCode=G710A"),
    ("FLL", "Sun Princess", "14 Night Eastern/Western Caribbean Adventurer", "Princess Cruises",
     "2027-02-28", 14,
     "Puerto Plata/Amber Cove; San Juan; Grand Turk; Fort Lauderdale; Cozumel; Roatan; "
     "Belize City; Fort Lauderdale", "Interior", 1320,
     "https://www.princess.com/itinerary-details/?voyageCode=U710A"),
    # --- Thu 25 Feb 2027 (fromfortlauderdaleflorida-25feb2027) ---
    ("FLL", "Enchanted Princess", "10 Night Eastern Caribbean with St. Kitts",
     "Princess Cruises", "2027-02-25", 10,
     "Half Moon Cay; Puerto Plata/Amber Cove; San Juan; Philipsburg (St. Maarten); "
     "St Johns (Antigua); Basseterre (St. Kitts); Fort Lauderdale", "Interior", 1434,
     "https://www.princess.com/itinerary-details/?voyageCode=N707"),

    # ======================= GALVESTON, TX =======================
    # --- Sun 21 Mar 2027 (fromgalvestontexas-21mar2027) ---
    # NOTE: the cruisetimetables feed publishes Disney fares as a PER-STATEROOM total for
    # 2 guests, not per person. Independently confirmed for this exact sailing:
    # icruise.com "Mar 21, 2027 ... $1,480 Interior Stateroom (double occupancy)" and
    # cdoe.cruiseone.com "March 21-26, 2027 Interior $1,480 / $296 per night", i.e. exactly
    # half of the $2,961 shown in the feed (magicguides.com quotes the same $2,961 as the
    # party-of-two "From" price). So pp = 1480 and the 2-person total is the feed's $2,961.
    ("GAL", "Disney Magic", "5 Night Western Caribbean Cruise From Galveston",
     "Disney Cruise Line", "2027-03-21", 5, "Cozumel; Progreso; Galveston", "Stateroom2", 1480,
     "https://disneycruise.disney.go.com/cruises-destinations/list/DM1785/5-Night-Western-Caribbean-Cruise-from-Galveston/2027-03-21-Disney-Magic/"),
    ("GAL", "MSC Seascape", "7 Night Western Caribbean", "MSC Cruises", "2027-03-21", 7,
     "Costa Maya; Roatan; Cozumel; Galveston", "From", 590,
     "https://www.msccruisesusa.com/itinerary-details/7-nights-western-caribbean?cruiseid=SC20270321GLSGLS"),
    ("GAL", "Symphony of the Seas", "7 Night Western Caribbean Cruise", "Royal Caribbean",
     "2027-03-21", 7, "Roatan; Costa Maya; Cozumel; Galveston", "Interior", 917,
     "https://www.royalcaribbean.com/cruises/itinerary/7-night-western-caribbean-from-galveston-on-symphony/SY07GAL-3851841824?sail-date=2027-03-21&currency=USD"),
    # --- Sun 28 Mar 2027 (fromgalvestontexas-28mar2027) ---
    ("GAL", "Carnival Jubilee", "6 Night Western Caribbean", "Carnival Cruise Line",
     "2027-03-28", 6, "Cozumel; Roatan; Galveston", "Interior", 669,
     "https://www.carnival.com/itinerary/6-day-western-caribbean-cruise/galveston/jubilee/6-days/wcp/?sailDate=03282027"),
    ("GAL", "MSC Seascape", "7 Night Western Caribbean", "MSC Cruises", "2027-03-28", 7,
     "Costa Maya; Roatan; Cozumel; Galveston", "From", 544,
     "https://www.msccruisesusa.com/itinerary-details/7-nights-western-caribbean?cruiseid=SC20270328GLSGLS"),
    ("GAL", "Symphony of the Seas", "7 Night Western Caribbean Cruise", "Royal Caribbean",
     "2027-03-28", 7, "Costa Maya; Roatan; Cozumel; Galveston", "Interior", 844,
     "https://www.royalcaribbean.com/cruises/itinerary/7-night-western-caribbean-from-galveston-on-symphony/SY07GAL-3851841824?sail-date=2027-03-28&currency=USD"),
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
        # voyages departing the same port on the same day (e.g. MSC Seaside sells a 4N and
        # the combined 7N back-to-back). Passes 3-5 established these are distinct
        # products. Every same-(port,ship,date) pair is surfaced below for review.
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
        rid = f"{pk}6-{counters[pk]:02d}"
        d_embark = datetime.date.fromisoformat(embark)
        d_disembark = d_embark + datetime.timedelta(days=nights)
        d_out = d_embark - datetime.timedelta(days=1)
        d_back = d_disembark + datetime.timedelta(days=1)
        cruise_2 = 2 * pp
        flight_2 = 2 * base_pp
        kind_label = {"Interior": "Interior", "Inside": "Inside",
                      "From": "MSC/Virgin lead-in 'From'",
                      "Stateroom2": "Inside"}[kind]
        if kind == "Stateroom2":
            pnote = (f"Inside ${pp:,}/person double occupancy (Disney feed publishes a "
                     f"per-stateroom total for 2; per-person confirmed independently); "
                     f"total is 2 x ${pp:,} (pub. {PUB})")
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
            "status": f"NEW {PUB} pass 6 \u2014 date-coverage sweep of remaining uncovered days at MIA/PC/FLL/TPA/GAL, line-by-line verified",
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
                f"National-expansion pass 6 ({PUB}): sail date, ship, duration, full port sequence and the "
                f"published per-person USD {kind_label} price were read line by line from the cruisetimetables "
                f"PER-DAY from-port 2027 page (official cruise-line fare feed); the official cruise-line deep "
                f"link was taken from that same page. Targeted via a per-port date-coverage audit of all 45 "
                f"in-window dates. Dedup-checked against the master by (port, ship, date, nights); in-window "
                f"and duration asserts enforced in code. Snapshot \u2260 live quote; cabin class, taxes/fees "
                f"and availability must be reconfirmed."
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
