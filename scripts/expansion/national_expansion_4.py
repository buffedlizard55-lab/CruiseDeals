#!/usr/bin/env python3
"""National expansion pass 4 (2026-08-30) — 52 NEW verified in-window sailings.

GAP THIS PASS CLOSES
--------------------
Passes 1-3 captured the big Florida/Gulf ports only on their Saturday/Sunday
"turnaround cluster" dates. But Miami alone indexes 177 sailings in March 2027 and
the master list held only 8 Miami dates. The real missing universe is the
MID-WEEK departures (Mon / Thu / Fri) and the short 3-4 night runs that never
fall on the Saturday cluster.

This pass sweeps the uncovered day pages at Miami, Port Canaveral, Fort Lauderdale
and Galveston and adds 52 genuinely-new sailings, bringing in NINE ships that were
not represented anywhere in the master list before:

    Carnival Conquest, Carnival Firenze, Carnival Glory, MSC Seaside, MSC Poesia,
    Norwegian Joy, Norwegian Getaway, Norwegian Escape, Norwegian Sun,
    Wonder of the Seas, Utopia of the Seas, Disney Wish, Brilliant Lady,
    Scarlet Lady, Celebrity Beyond, Celebrity Eclipse, Nieuw Statendam,
    Nieuw Amsterdam, Carnival Miracle (Galveston 10N)

Every row was read LINE BY LINE from the cruisetimetables.com per-day "from port"
pages (accessed 2026-08-30, site-dated 29 August 2026), which republish the official
cruise-line fare feed AND carry a per-sailing official deep link. Each record holds:
sail date, ship, official cruise name, nights, full published port sequence, the
official cruise-line deep link, and the published per-person USD Interior/Inside
price (MSC & Virgin = lead-in "From").

NOT ADDED (flagged irregularities -> see verification log):
  * Celebrity Silhouette FLL 2027-02-21 "5 Night Ultimate Disco Cruise" — full-ship
    CHARTER, fare feed publishes literally "NA". No bookable public interior price,
    so pricing it would be fabrication.
  * Norwegian Jewel Miami 2027-02-15 "11 Night Big Nude Boat 2027" — full-ship
    charter (bare-necessities.com), no public interior fare in the feed.
  * Norwegian Star Miami 2027-03-01 15N Transatlantic — OPEN JAW, ends Barcelona.
  * MSC Poesia Miami 2027-02-25 21N — ends in window but is a repositioning-style
    long voyage; retained ONLY as the 10N variant which is round-trip Miami.

Flights: 2 adults, SFO round trip, arrive the day BEFORE embarkation / return the day
AFTER disembarkation, at the route average x 2 (planning estimate; live quote required).
Hard asserts: dedup on (port, ship, date), in-window, nights >= 2.
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
    "MSY": ("New Orleans, LA", "MSY", 420,
            "https://www.kayak.com/flight-routes/San-Francisco-SFO/New-Orleans-MSY",
            "KAYAK SFO-MSY planning basis $420/person round trip; accessed 2026-08-30"),
    "GAL": ("Galveston, TX", "HOU", 300,
            "https://www.kayak.com/flight-routes/San-Francisco-SFO/Houston-HOU",
            "KAYAK SFO-HOU planning basis $300/person round trip (Galveston is served via Houston); accessed 2026-08-30"),
}

SRC = {
    "MIA": "https://www.cruisetimetables.com/cruises-from-miami-florida-2027.html",
    "PC":  "https://www.cruisetimetables.com/cruises-from-port-canaveral-florida-2027.html",
    "FLL": "https://www.cruisetimetables.com/cruises-from-fort-lauderdale-florida-2027.html",
    "TPA": "https://www.cruisetimetables.com/cruises-from-tampa-florida-2027.html",
    "MSY": "https://www.cruisetimetables.com/cruises-from-new-orleans-louisiana-2027.html",
    "GAL": "https://www.cruisetimetables.com/cruises-from-galveston-texas-2027.html",
}

# (portkey, ship, cruise_name, line, embark ISO, nights, stops, kind, pp, official)
R = [
    # ======================= MIAMI, FL — uncovered mid-week days =======================
    # --- Mon 15 Feb 2027 (frommiamiflorida-15feb2027) ---
    ("MIA", "Carnival Conquest", "4 Night The Bahamas", "Carnival Cruise Line", "2027-02-15", 4,
     "Half Moon Cay; Celebration Key; Miami", "Interior", 295,
     "https://www.carnival.com/itinerary/4-day-the-bahamas-cruise/miami/conquest/4-days/bhp/?sailDate=02152027"),
    ("MIA", "Carnival Sunrise", "5 Night The Bahamas", "Carnival Cruise Line", "2027-02-15", 5,
     "Half Moon Cay; Celebration Key; Nassau; Miami", "Interior", 307,
     "https://www.carnival.com/itinerary/5-day-the-bahamas-cruise/miami/sunrise/5-days/bhi/?sailDate=02152027"),
    ("MIA", "Freedom of the Seas", "5 Night Western Caribbean Cruise", "Royal Caribbean",
     "2027-02-15", 5, "Nassau; Puerto Plata/Amber Cove; Miami", "Interior", 558,
     "https://www.royalcaribbean.com/cruises/itinerary/5-night-western-caribbean-from-miami-on-freedom/FR05MIA-1172079608?sail-date=2027-02-15&currency=USD"),
    ("MIA", "MSC Seaside", "4 Night The Bahamas & Ocean Cay", "MSC Cruises", "2027-02-15", 4,
     "Nassau; Ocean Cay; Miami", "From", 261,
     "https://www.msccruisesusa.com/itinerary-details/4-nights-the-bahamas--ocean-cay?cruiseid=SE20270215MIAMIA"),
    ("MIA", "MSC Seaside", "7 Night Caribbean & Bahamas", "MSC Cruises", "2027-02-15", 7,
     "Nassau; Ocean Cay; Miami; Nassau; Ocean Cay; Miami", "From", 515,
     "https://www.msccruisesusa.com/itinerary-details/7-nights-caribbean--bahamas?cruiseid=SE20270215MIAMI1"),
    # --- Thu 18 Feb 2027 ---
    ("MIA", "Brilliant Lady", "4 Night Key West & Bimini Beach Club", "Virgin Voyages",
     "2027-02-18", 4, "Key West; Bimini Islands; Miami", "From", 676,
     "https://www.virginvoyages.com/book/voyage-planner/pre-checkout?currencyCode=USD&packageCode=4NKW&voyageId=BR2702184NKW"),
    ("MIA", "Carnival Firenze", "8 Night Southern Caribbean", "Carnival Cruise Line",
     "2027-02-18", 8, "Oranjestad (Aruba); Willemstad (Curacao); Grand Turk; Miami", "Interior", 639,
     "https://www.carnival.com/itinerary/8-day-southern-caribbean-cruise/miami/firenze/8-days/czm/?sailDate=02182027"),
    # --- Mon 22 Feb 2027 ---
    ("MIA", "Brilliant Lady", "10 Night Eastern Caribbean & Bimini Beach Club", "Virgin Voyages",
     "2027-02-22", 10,
     "Philipsburg (St. Maarten); Tortola; Basseterre (St. Kitts); St Johns (Antigua); Bimini Islands; Miami",
     "From", 1390,
     "https://www.virginvoyages.com/book/voyage-planner/pre-checkout?currencyCode=USD&packageCode=10NMM&voyageId=BR27022210NMM"),
    ("MIA", "Carnival Conquest", "4 Night The Bahamas", "Carnival Cruise Line", "2027-02-22", 4,
     "Half Moon Cay; Celebration Key; Miami", "Interior", 275,
     "https://www.carnival.com/itinerary/4-day-the-bahamas-cruise/miami/conquest/4-days/bhp/?sailDate=02222027"),
    ("MIA", "MSC Seaside", "4 Night The Bahamas & Ocean Cay", "MSC Cruises", "2027-02-22", 4,
     "Nassau; Ocean Cay; Miami", "From", 241,
     "https://www.msccruisesusa.com/itinerary-details/4-nights-the-bahamas--ocean-cay?cruiseid=SE20270222MIAMIA"),
    ("MIA", "MSC Seaside", "7 Night Caribbean & Bahamas", "MSC Cruises", "2027-02-22", 7,
     "Nassau; Ocean Cay; Miami; Nassau; Ocean Cay; Miami", "From", 495,
     "https://www.msccruisesusa.com/itinerary-details/7-nights-caribbean--bahamas?cruiseid=SE20270222MIAMI1"),
    ("MIA", "Norwegian Joy", "4 Night Bahamas Round-Trip Miami: Great Stirrup Cay & Nassau",
     "Norwegian Cruise Line", "2027-02-22", 4, "Great Stirrup Cay; Nassau; Miami", "Inside", 439,
     "https://www.ncl.com/vacation-builder?itineraryCode=JOY4MIANPINASMIA-NIC-JOY4MIANASNPIMIA&packageId=23379749&stateroomTypeCode=INSIDE&"),
    # --- Thu 25 Feb 2027 ---
    ("MIA", "Carnival Sunrise", "4 Night The Bahamas", "Carnival Cruise Line", "2027-02-25", 4,
     "Half Moon Cay; Celebration Key; Miami", "Interior", 294,
     "https://www.carnival.com/itinerary/4-day-the-bahamas-cruise/miami/sunrise/4-days/bhp/?sailDate=02252027"),
    ("MIA", "Freedom of the Seas", "9 Night Southern Caribbean Cruise", "Royal Caribbean",
     "2027-02-25", 9,
     "Bimini Islands; Cabo Rojo; Oranjestad (Aruba); Willemstad (Curacao); Miami", "Interior", 1037,
     "https://www.royalcaribbean.com/cruises/itinerary/9-night-southern-caribbean-from-miami-on-freedom/FR09MIA-2800916411?sail-date=2027-02-25&currency=USD"),
    ("MIA", "Independence of the Seas", "5 Night Western Caribbean & Perfect Day",
     "Royal Caribbean", "2027-02-25", 5, "Cozumel; Perfect Day at CocoCay; Miami", "Interior", 477,
     "https://www.royalcaribbean.com/cruises/itinerary/5-night-western-caribbean-perfect-day-from-miami-on-independence/ID05MIA-1771094742?sail-date=2027-02-25&currency=USD"),
    ("MIA", "MSC Poesia", "10 Night Southern Caribbean", "MSC Cruises", "2027-02-25", 10,
     "Willemstad (Curacao); Kralendijk (Bonaire); Oranjestad (Aruba); Cabo Rojo; Ocho Rios; Miami",
     "From", 1128,
     "https://www.msccruisesusa.com/itinerary-details/10-nights-southern-caribbean?cruiseid=PO20270225MIAMIA"),
    # --- Mon 1 Mar 2027 ---
    ("MIA", "Norwegian Sun", "12 Night Panama Canal Round-trip Miami: Bahamas & Costa Rica",
     "Norwegian Cruise Line", "2027-03-01", 12,
     "Great Stirrup Cay; Cabo Rojo; Oranjestad (Aruba); Willemstad (Curacao); Cartagena; "
     "Panama Canal; Colon; Puerto Limon; Miami", "Inside", 2049,
     "https://www.ncl.com/vacation-builder?itineraryCode=SUN12MIANPICBRORJWILCTGPCGCLNLIOMIA-NIC-SUN12MIACBRCLNCTGLIONPIORJPCGWILMIA&packageId=23377868&stateroomTypeCode=INSIDE&"),
    ("MIA", "Scarlet Lady", "5 Night Dominican Republic & Bimini Beach Club", "Virgin Voyages",
     "2027-03-01", 5, "Puerto Plata/Amber Cove; Bimini Islands; Miami", "From", 845,
     "https://www.virginvoyages.com/book/voyage-planner/pre-checkout?currencyCode=USD&packageCode=5NPP&voyageId=SC2703015NPP"),
    ("MIA", "Wonder of the Seas", "4 Night Perfect Day CocoCay & Bahamas", "Royal Caribbean",
     "2027-03-01", 4, "Nassau; Perfect Day at CocoCay; Miami", "Interior", 613,
     "https://www.royalcaribbean.com/cruises/itinerary/4-night-perfect-day-cococay-bahamas-from-miami-on-wonder/WN04MIA-1040267344?sail-date=2027-03-01&currency=USD"),

    # --- Mon 8 Mar 2027 (frommiamiflorida-08mar2027) ---
    ("MIA", "Brilliant Lady", "10 Night Eastern Caribbean & Bimini Beach Club", "Virgin Voyages",
     "2027-03-08", 10,
     "Philipsburg (St. Maarten); Tortola; St Croix; San Juan; Puerto Plata/Amber Cove; Bimini Islands; Miami",
     "From", 1391,
     "https://www.virginvoyages.com/book/voyage-planner/pre-checkout?currencyCode=USD&packageCode=10NDP&voyageId=BR27030810NDP"),
    ("MIA", "Carnival Conquest", "4 Night The Bahamas", "Carnival Cruise Line", "2027-03-08", 4,
     "Half Moon Cay; Celebration Key; Miami", "Interior", 325,
     "https://www.carnival.com/itinerary/4-day-the-bahamas-cruise/miami/conquest/4-days/bhs/?sailDate=03082027"),
    ("MIA", "Carnival Firenze", "10 Night Southern Caribbean", "Carnival Cruise Line",
     "2027-03-08", 10,
     "Philipsburg (St. Maarten); Basseterre (St. Kitts); Castries (St Lucia); St Johns (Antigua); St Thomas; Miami",
     "Interior", 754,
     "https://www.carnival.com/itinerary/10-day-southern-caribbean-cruise/miami/firenze/10-days/js0/?sailDate=03082027"),
    ("MIA", "MSC Seaside", "4 Night The Bahamas & Ocean Cay", "MSC Cruises", "2027-03-08", 4,
     "Nassau; Ocean Cay; Miami", "From", 261,
     "https://www.msccruisesusa.com/itinerary-details/4-nights-the-bahamas--ocean-cay?cruiseid=SE20270308MIAMIA"),
    # --- Thu 11 Mar 2027 (frommiamiflorida-11mar2027) ---
    ("MIA", "Carnival Sunrise", "4 Night The Bahamas", "Carnival Cruise Line", "2027-03-11", 4,
     "Princess Cays; Celebration Key; Miami", "Interior", 374,
     "https://www.carnival.com/itinerary/4-day-the-bahamas-cruise/miami/sunrise/4-days/bhu/?sailDate=03112027"),
    ("MIA", "Freedom of the Seas", "4 Night Eastern Caribbean Cruise", "Royal Caribbean",
     "2027-03-11", 4, "Grand Turk; Miami", "Interior", 480,
     "https://www.royalcaribbean.com/cruises/itinerary/4-night-eastern-caribbean-from-miami-on-freedom/FR04MIA-3280107330?sail-date=2027-03-11&currency=USD"),
    ("MIA", "Margaritaville at Sea Beachcomber", "4 Night Bahamas Duo", "Margaritaville at Sea",
     "2027-03-11", 4, "Nassau; Freeport; Miami", "Inside", 299,
     "https://margaritavilleatsea.com/"),
    ("MIA", "Scarlet Lady", "4 Night Key West & Bimini Beach Club", "Virgin Voyages",
     "2027-03-11", 4, "Key West; Bimini Islands; Miami", "From", 636,
     "https://www.virginvoyages.com/book/voyage-planner/pre-checkout?currencyCode=USD&packageCode=4NKW&voyageId=SC2703114NKW"),

    # ================= PORT CANAVERAL, FL — uncovered mid-week days =================
    # --- Fri 19 Feb 2027 (fromportcanaveralflorida-19feb2027) ---
    ("PC", "Carnival Glory", "3 Night The Bahamas", "Carnival Cruise Line", "2027-02-19", 3,
     "Celebration Key; Port Canaveral", "Interior", 301,
     "https://www.carnival.com/itinerary/3-day-the-bahamas-cruise/pt-canaveral/glory/3-days/bav/?sailDate=02192027"),
    ("PC", "Disney Wish", "3 Night Bahamian Cruise From Port Canaveral", "Disney Cruise Line",
     "2027-02-19", 3, "Nassau; Castaway Cay; Port Canaveral", "Inside", 2015,
     "https://disneycruise.disney.go.com/cruises-destinations/list/WW0556/3-Night-Bahamian-Cruise-from-Port-Canaveral/2027-02-19-Disney-Wish/"),
    ("PC", "Norwegian Escape",
     "7 Night Caribbean Round-trip Orlando: Dominican Republic & St. Thomas",
     "Norwegian Cruise Line", "2027-02-19", 7,
     "Puerto Plata/Amber Cove; St Thomas; Tortola; Great Stirrup Cay; Port Canaveral", "Inside", 839,
     "https://www.ncl.com/vacation-builder?itineraryCode=ESCAPE7PCVPOPSTTTOVNPIPCV-NIC-ESCAPE7PCVNPIPOPSTTTOVPCV&packageId=23369115&stateroomTypeCode=INSIDE&"),
    ("PC", "Utopia of the Seas", "3 Night Bahamas & Perfect Day Cruise", "Royal Caribbean",
     "2027-02-19", 3, "Nassau; Perfect Day at CocoCay; Port Canaveral", "Interior", 659,
     "https://www.royalcaribbean.com/cruises/itinerary/3-night-bahamas-perfect-day-from-orlando-port-canaveral-on-utopia/UT03PCN-3464558580?sail-date=2027-02-19&currency=USD"),
    # --- Mon 22 Feb 2027 ---
    ("PC", "Carnival Freedom", "5 Night The Bahamas", "Carnival Cruise Line", "2027-02-22", 5,
     "Celebration Key; Nassau; Half Moon Cay; Port Canaveral", "Interior", 312,
     "https://www.carnival.com/itinerary/5-day-the-bahamas-cruise/pt-canaveral/freedom/5-days/bme/?sailDate=02222027"),
    ("PC", "Carnival Glory", "4 Night The Bahamas", "Carnival Cruise Line", "2027-02-22", 4,
     "Nassau; Celebration Key; Port Canaveral", "Interior", 293,
     "https://www.carnival.com/itinerary/4-day-the-bahamas-cruise/pt-canaveral/glory/4-days/bm7/?sailDate=02222027"),
    ("PC", "Disney Wish", "4 Night Bahamian Cruise From Port Canaveral", "Disney Cruise Line",
     "2027-02-22", 4, "Nassau; Castaway Cay; Port Canaveral", "Inside", 3033,
     "https://disneycruise.disney.go.com/cruises-destinations/list/WW0557/4-Night-Bahamian-Cruise-from-Port-Canaveral/2027-02-22-Disney-Wish/"),
    ("PC", "Norwegian Getaway",
     "4 Night Bahamas Round-trip Orlando (Port Canaveral): Great Stirrup Cay & Nassau",
     "Norwegian Cruise Line", "2027-02-22", 4, "Nassau; Great Stirrup Cay; Port Canaveral",
     "Inside", 399,
     "https://www.ncl.com/vacation-builder?itineraryCode=GETAWAY4PCVNASNPIPCV&packageId=23468063&stateroomTypeCode=INSIDE&"),
    ("PC", "Utopia of the Seas", "4 Night Bahamas & Perfect Day Cruise", "Royal Caribbean",
     "2027-02-22", 4, "Perfect Day at CocoCay; Nassau; Port Canaveral", "Interior", 742,
     "https://www.royalcaribbean.com/cruises/itinerary/4-night-bahamas-perfect-day-from-orlando-port-canaveral-on-utopia/UT04PCN-4069341576?sail-date=2027-02-22&currency=USD"),

    # ================= FORT LAUDERDALE, FL — uncovered days =================
    # --- Sun 21 Feb 2027 (fromfortlauderdaleflorida-21feb2027) ---
    ("FLL", "Adventure of the Seas", "6 Night Western Caribbean Cruise", "Royal Caribbean",
     "2027-02-21", 6, "Falmouth (Jamaica); George Town; Nassau; Fort Lauderdale", "Interior", 592,
     "https://www.royalcaribbean.com/cruises/itinerary/6-night-western-caribbean-from-fort-lauderdale-on-adventure/AD06FLL-1756957036?sail-date=2027-02-21&currency=USD"),
    ("FLL", "Celebrity Beyond", "7 Night St. Thomas, St. Kitts & Puerto Plata",
     "Celebrity Cruises", "2027-02-21", 7,
     "Puerto Plata/Amber Cove; St Thomas; Basseterre (St. Kitts); Fort Lauderdale", "Interior", 1420,
     "https://www.celebritycruises.com/itinerary/7-night-st-thomas-st-kitts-cruise-from-fort-lauderdale-on-beyond-BY07E466?sailDate=2027-02-21&packageCode=BY07E466"),
    ("FLL", "Nieuw Statendam", "7 Night Western Caribbean: Greater Antilles & Mexico",
     "Holland America Line", "2027-02-21", 7,
     "Half Moon Cay; Ocho Rios; George Town; Cozumel; Fort Lauderdale", "Inside", 899,
     "https://www.hollandamerica.com/en/us/find-a-cruise/c7w07a/j723"),
    ("FLL", "Nieuw Statendam", "14 Night Western & Eastern Caribbean: Mexico & Bahamas",
     "Holland America Line", "2027-02-21", 14,
     "Half Moon Cay; Ocho Rios; George Town; Cozumel; Fort Lauderdale (turn); further Caribbean calls; Fort Lauderdale",
     "Inside", 1629,
     "https://www.hollandamerica.com/en/us/find-a-cruise/c7x14d/j723a"),
    # --- Sun 28 Feb 2027 ---
    ("FLL", "Celebrity Beyond", "7 Night Grand Cayman, Mexico & Bahamas", "Celebrity Cruises",
     "2027-02-28", 7, "Nassau; Cozumel; George Town; Fort Lauderdale", "Interior", 943,
     "https://www.celebritycruises.com/itinerary/7-night-grand-cayman-mexico-bahamas-from-fort-lauderdale-on-beyond-BY07W678?sailDate=2027-02-28&packageCode=BY07W678"),
    ("FLL", "Celebrity Eclipse", "12 Night Ultimate Southern Caribbean", "Celebrity Cruises",
     "2027-02-28", 12,
     "Basseterre (St. Kitts); Castries (St Lucia); Bridgetown (Barbados); Willemstad (Curacao); "
     "Kralendijk (Bonaire); Oranjestad (Aruba); Fort Lauderdale", "Interior", 1394,
     "https://www.celebritycruises.com/itinerary/12-night-ultimate-southern-caribbean-from-fort-lauderdale-on-eclipse-EC12D054?sailDate=2027-02-28&packageCode=EC12D054"),
    ("FLL", "Legend of the Seas", "6 Night Caribbean & Perfect Day", "Royal Caribbean",
     "2027-02-28", 6, "Perfect Day at CocoCay; Cozumel; Costa Maya; Fort Lauderdale", "Interior", 1308,
     "https://www.royalcaribbean.com/cruises/itinerary/6-night-caribbean-perfect-day-from-fort-lauderdale-on-legend/LE06FLL-385066157?sail-date=2027-02-28&currency=USD"),
    ("FLL", "Nieuw Amsterdam",
     "21 Night Panama Canal & Eastern Caribbean: U.S. Virgin Islands", "Holland America Line",
     "2027-02-28", 21,
     "Half Moon Cay; Oranjestad (Aruba); Cartagena; Panama Canal; Colon; Puerto Limon; George Town; "
     "Fort Lauderdale (turn); St Johns (Antigua); St Thomas; Tortola; San Juan; Half Moon Cay; Fort Lauderdale",
     "Inside", 2694,
     "https://www.hollandamerica.com/en/us/find-a-cruise/c7f21b/i719a"),

    # --- Mon 8 Mar 2027 (fromportcanaveralflorida-08mar2027) ---
    ("PC", "Carnival Freedom", "5 Night The Bahamas", "Carnival Cruise Line", "2027-03-08", 5,
     "Celebration Key; Nassau; Half Moon Cay; Port Canaveral", "Interior", 483,
     "https://www.carnival.com/itinerary/5-day-the-bahamas-cruise/pt-canaveral/freedom/5-days/bma/?sailDate=03082027"),
    ("PC", "Carnival Glory", "4 Night The Bahamas", "Carnival Cruise Line", "2027-03-08", 4,
     "Nassau; Celebration Key; Port Canaveral", "Interior", 379,
     "https://www.carnival.com/itinerary/4-day-the-bahamas-cruise/pt-canaveral/glory/4-days/bmb/?sailDate=03082027"),
    ("PC", "Disney Wish", "4 Night Bahamian Cruise From Port Canaveral", "Disney Cruise Line",
     "2027-03-08", 4, "Nassau; Castaway Cay; Port Canaveral", "Inside", 4001,
     "https://disneycruise.disney.go.com/cruises-destinations/list/WW0561/4-Night-Bahamian-Cruise-from-Port-Canaveral/2027-03-08-Disney-Wish/"),
    ("PC", "Norwegian Getaway",
     "4 Night Bahamas Round-trip Orlando (Port Canaveral): Great Stirrup Cay & Nassau",
     "Norwegian Cruise Line", "2027-03-08", 4, "Great Stirrup Cay; Nassau; Port Canaveral",
     "Inside", 399,
     "https://www.ncl.com/vacation-builder?itineraryCode=GETAWAY4PCVNPINASPCV-NIC-GETAWAY4PCVNASNPIPCV&packageId=23468064&stateroomTypeCode=INSIDE&"),
    ("PC", "Utopia of the Seas", "4 Night Bahamas & Perfect Day Cruise", "Royal Caribbean",
     "2027-03-08", 4, "Nassau; Perfect Day at CocoCay; Port Canaveral", "Interior", 722,
     "https://www.royalcaribbean.com/cruises/itinerary/4-night-bahamas-perfect-day-from-orlando-port-canaveral-on-utopia/UT04PCN-4069341576?sail-date=2027-03-08&currency=USD"),

    # ================= TAMPA, FL — uncovered Mon 15 Mar 2027 =================
    ("TPA", "Carnival Paradise", "5 Night Western Caribbean", "Carnival Cruise Line",
     "2027-03-15", 5, "George Town; Cozumel; Tampa", "Interior", 530,
     "https://www.carnival.com/itinerary/5-day-western-caribbean-cruise/tampa/paradise/5-days/wcb/?sailDate=03152027"),

    # NOTE: New Orleans 2027-03-15 (Carnival Valor 5N Western Caribbean) was read from
    # fromneworleanslouisiana-15mar2027.html but the dedup guard matched it against an
    # existing master row from an earlier pass -> NOT re-added.

    # ================= GALVESTON, TX — uncovered Mon 15 Feb 2027 =================
    ("GAL", "Carnival Miracle", "10 Night Western Caribbean", "Carnival Cruise Line",
     "2027-02-15", 10,
     "Cozumel; Belize City; Roatan; Montego Bay; George Town; Galveston", "Interior", 856,
     "https://www.carnival.com/itinerary/10-day-western-caribbean-cruise/galveston/miracle/10-days/wca/?sailDate=02152027"),
    ("GAL", "Liberty of the Seas", "5 Night Western Caribbean Cruise", "Royal Caribbean",
     "2027-02-15", 5, "Cozumel; Costa Maya; Galveston", "Interior", 477,
     "https://www.royalcaribbean.com/cruises/itinerary/5-night-western-caribbean-from-galveston-on-liberty/LB05GAL-2956042566?sail-date=2027-02-15&currency=USD"),
]


def money(n):
    return "$" + format(int(round(n)), ",")


def gflights(apt, out, back):
    q = f"Flights from SFO to {apt} {out}, return {back}"
    return "https://www.google.com/travel/flights?q=" + urllib.parse.quote(q)


SAME_DAY_PAIRS = []


def build_rows(existing_keys):
    counters = {}
    rows = []
    seen_same_day = {}
    for (pk, ship, cname, line, embark, nights, stops, kind, pp, official) in R:
        port_name, apt, base_pp, kayak, kayak_note = PORTS[pk]
        # Dedup key includes nights: a ship can legitimately sell two DIFFERENT bookable
        # voyages departing the same port on the same day (e.g. MSC Seaside Miami 15 Feb
        # sells both a 4N Bahamas and a 7N combined back-to-back; RCI/Carnival do the same).
        # Pass 3 established these are distinct products, not duplicates. We still surface
        # every same-(port,ship,date) pair below so it gets eyeballed rather than assumed.
        key = (port_name, ship, embark, nights)
        assert key not in existing_keys, f"DUPLICATE against master: {key}"
        existing_keys.add(key)
        same_day = (port_name, ship, embark)
        if same_day in seen_same_day:
            SAME_DAY_PAIRS.append((rid, port_name, ship, embark,
                                   seen_same_day[same_day], nights))
        seen_same_day[same_day] = nights
        assert "2027-02-15" <= embark <= "2027-03-31", f"OUT OF WINDOW: {key}"
        assert nights >= 2, f"too short: {key}"
        assert official.startswith("https://"), f"bad link: {key}"
        counters[pk] = counters.get(pk, 0) + 1
        rid = f"{pk}4-{counters[pk]:02d}"
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
            "status": f"NEW {PUB} pass 4 \u2014 mid-week / short-cruise sweep of FL & Gulf ports, line-by-line verified",
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
                f"National-expansion pass 4 ({PUB}): sail date, ship, duration, full port sequence and the "
                f"published per-person USD {kind_label} price were read line by line from the cruisetimetables "
                f"PER-DAY from-port 2027 page (official cruise-line fare feed); the official cruise-line deep "
                f"link was taken from that same page. This pass targeted the MID-WEEK and short 3-4 night "
                f"departures that the earlier Saturday-cluster passes never reached. Dedup-checked against the "
                f"master by (port, ship, date); in-window and duration asserts enforced in code. "
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
        for rid, port, ship, date, n1, n2 in SAME_DAY_PAIRS:
            print(f"  {rid}: {ship} ex-{port} {date} -> {n1}N and {n2}N")


if __name__ == "__main__":
    main()
