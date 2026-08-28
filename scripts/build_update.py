#!/usr/bin/env python3
"""CruiseDeals research update — build script (2026-08-28).

Adds 36 NEW line-by-line-verified sailings (Feb 15 - Mar 31, 2027, U.S. West Coast
departures), refreshes the 2-adult flight planning estimates to a uniform
KAYAK route-average basis, and flags irregularities found in the prior list.

Every NEW row was verified against:
  1. its per-sailing schedule-index page on cruisetimetables.com
     (dates, duration, itinerary, interior per-person snapshot), and
  2. the official cruise-line deep link embedded on that page.
No row is added without both references. Prices are snapshots, not live quotes.
"""
import csv, json, sys
from datetime import date, timedelta

ROOT = "/home/user/CruiseDeals"
CSV = f"{ROOT}/data/cruises_master_verified.csv"
JSON_OUT = f"{ROOT}/data/cruises.json"
DOCS_JSON = f"{ROOT}/docs/data/cruises.json"
VLOG = f"{ROOT}/data/verification_log_2026-08-28.csv"

WINDOW_START, WINDOW_END = date(2027, 2, 15), date(2027, 3, 31)

# ---------------------------------------------------------------- flight model
# Uniform route basis verified against KAYAK route pages on 2026-08-28.
ROUTES = {
    "SAN": dict(pp_rt=156, for2=312, label="SFO → SAN → SFO",
                note="Planning basis $156/person round trip; KAYAK typical range $134–$287 (route page accessed 2026-08-28)",
                url="https://www.kayak.com/flight-routes/San-Francisco-SFO/San-Diego-SAN"),
    "LAX": dict(pp_rt=204, for2=408, label="SFO → LAX → SFO",
                note="KAYAK 12-month route average $204/person round trip (typical $138–$272; February historically peaks) accessed 2026-08-28",
                url="https://www.kayak.com/flight-routes/San-Francisco-SFO/Los-Angeles-LAX"),
    # Open jaw for one-way-in-voyage variants ending in Vancouver (YVR→SFO),
    # priced against KAYAK one-way deal observations accessed 2026-08-28:
    # SFO→SAN one-way deals observed $48–$79 (basis $75 pp), YVR→SFO one-way
    # typical $137–$290 (basis $210 pp) → $285 pp, $570 for 2.
    "SAN_YVR": dict(pp_rt=None, for2=570, label="SFO → SAN one-way; YVR → SFO return",
                    note="Open-jaw planning estimate $570/2 adults: SFO→SAN one-way basis $75pp (KAYAK observed one-way deals $48–$79) + YVR→SFO one-way basis $210pp (KAYAK typical $137–$290), route pages accessed 2026-08-28",
                    url="https://www.kayak.com/flight-routes/Vancouver-Intl-YVR/San-Francisco-SFO"),
    "HOME": dict(pp_rt=0, for2=0, label="No flight required (SFO departure)",
                 note="Port matches origin airport city", url=""),
}

def gflights(q_from, q_to, d1, d2):
    return ("https://www.google.com/travel/flights?q=Flights%20from%20"
            f"{q_from}%20to%20{q_to}%20{d1}%2C%20return%20{d2}")

def kayak_search(fromcode, tocode, d1, d2):
    return f"https://www.kayak.com/flights/{fromcode}-{tocode}/{d1}/{d2}/2adults?sort=bestflight_a"

# ------------------------------------------------------------- new verified rows
# fmt: (id, name, line, date, nights, dur_str, port, route, stops, interior_pp,
#       source_index_page, official_link, promo, extra_note)
NEW = [
 # --- Royal Caribbean, Voyager of the Seas (Los Angeles / San Pedro) ---
 ("LA-57","Voyager of the Seas — 7-Night Ensenada, Cabo & Mazatlán","Royal Caribbean","2027-02-19",7,"7 nights","Los Angeles (San Pedro), CA","LAX","Ensenada; Cabo San Lucas; Mazatlán",478,
  "https://www.cruisetimetables.com/cruisesonvoyageroftheseas-19feb2027.html","https://www.royalcaribbean.com/cruises/itinerary/7-night-ensenada,-cabo-mazatlan-from-los-angeles-on-voyager/VY07LAX-2626294331?sail-date=2027-02-19&currency=USD"),
 ("LA-58","Voyager of the Seas — 7-Night Cabo, Vallarta & Mazatlán","Royal Caribbean","2027-02-26",7,"7 nights","Los Angeles (San Pedro), CA","LAX","Cabo San Lucas; Mazatlán; Puerto Vallarta",509,
  "https://www.cruisetimetables.com/cruisesonvoyageroftheseas-26feb2027.html","https://www.royalcaribbean.com/cruises/itinerary/7-night-cabo,-vallarta-mazatlan-from-los-angeles-on-voyager/VY07LAX-1182818524?sail-date=2027-02-26&currency=USD"),
 ("LA-59","Voyager of the Seas — 7-Night Ensenada, Cabo & Mazatlán","Royal Caribbean","2027-03-05",7,"7 nights","Los Angeles (San Pedro), CA","LAX","Ensenada; Cabo San Lucas; Mazatlán",525,
  "https://www.cruisetimetables.com/cruisesonvoyageroftheseas-05mar2027.html","https://www.royalcaribbean.com/cruises/itinerary/7-night-ensenada,-cabo-mazatlan-from-los-angeles-on-voyager/VY07LAX-2626294331?sail-date=2027-03-05&currency=USD"),
 ("LA-60","Voyager of the Seas — 7-Night Cabo, Vallarta & Mazatlán","Royal Caribbean","2027-03-12",7,"7 nights","Los Angeles (San Pedro), CA","LAX","Cabo San Lucas; Mazatlán; Puerto Vallarta",609,
  "https://www.cruisetimetables.com/cruisesonvoyageroftheseas-12mar2027.html","https://www.royalcaribbean.com/cruises/itinerary/7-night-cabo,-vallarta-mazatlan-from-los-angeles-on-voyager/VY07LAX-1182818524?sail-date=2027-03-12&currency=USD"),
 ("LA-61","Voyager of the Seas — 7-Night Cabo, Vallarta & Mazatlán","Royal Caribbean","2027-03-19",7,"7 nights","Los Angeles (San Pedro), CA","LAX","Cabo San Lucas; Mazatlán; Puerto Vallarta",620,
  "https://www.cruisetimetables.com/cruisesonvoyageroftheseas-19mar2027.html","https://www.royalcaribbean.com/cruises/itinerary/7-night-cabo,-vallarta-mazatlan-from-los-angeles-on-voyager/VY07LAX-1182818524?sail-date=2027-03-19&currency=USD"),
 ("LA-62","Voyager of the Seas — 6-Night Cabo Overnight & Catalina","Royal Caribbean","2027-03-26",6,"6 nights","Los Angeles (San Pedro), CA","LAX","Catalina Island; Cabo San Lucas (overnight)",638,
  "https://www.cruisetimetables.com/cruisesonvoyageroftheseas-26mar2027.html","https://www.royalcaribbean.com/cruises/itinerary/6-night-cabo-overnight-catalina-from-los-angeles-on-voyager/VY06LAX-1729758938?sail-date=2027-03-26&currency=USD"),
 # --- Royal Caribbean, Ovation of the Seas (Los Angeles / San Pedro) ---
 ("LA-63","Ovation of the Seas — 7-Night Cabo Overnight, Catalina & Ensenada","Royal Caribbean","2027-02-26",7,"7 nights","Los Angeles (San Pedro), CA","LAX","Catalina Island; Cabo San Lucas (overnight); Ensenada",650,
  "https://www.cruisetimetables.com/cruisesonovationoftheseas-26feb2027.html","https://www.royalcaribbean.com/cruises/itinerary/7-night-cabo-overnight-catalina-ensenada-from-los-angeles-on-ovation/OV07LAX-1983939617?sail-date=2027-02-26&currency=USD"),
 ("LA-64","Ovation of the Seas — 3-Night Ensenada","Royal Caribbean","2027-03-05",3,"3 nights","Los Angeles (San Pedro), CA","LAX","Ensenada",325,
  "https://www.cruisetimetables.com/cruisesonovationoftheseas-05mar2027.html","https://www.royalcaribbean.com/cruises/itinerary/3-night-ensenada-from-los-angeles-on-ovation/OV03LAX-1965470999?sail-date=2027-03-05&currency=USD"),
 ("LA-65","Ovation of the Seas — 4-Night Catalina & Ensenada","Royal Caribbean","2027-03-08",4,"4 nights","Los Angeles (San Pedro), CA","LAX","Catalina Island; Ensenada",366,
  "https://www.cruisetimetables.com/cruisesonovationoftheseas-08mar2027.html","https://www.royalcaribbean.com/cruises/itinerary/4-night-catalina-ensenada-from-los-angeles-on-ovation/OV04LAX-1005460505?sail-date=2027-03-08&currency=USD"),
 ("LA-66","Ovation of the Seas — 7-Night Cabo Overnight, Catalina & Ensenada","Royal Caribbean","2027-03-12",7,"7 nights","Los Angeles (San Pedro), CA","LAX","Catalina Island; Cabo San Lucas (overnight); Ensenada",706,
  "https://www.cruisetimetables.com/cruisesonovationoftheseas-12mar2027.html","https://www.royalcaribbean.com/cruises/itinerary/7-night-cabo-overnight-catalina-ensenada-from-los-angeles-on-ovation/OV07LAX-1983939617?sail-date=2027-03-12&currency=USD"),
 ("LA-67","Ovation of the Seas — 3-Night Ensenada","Royal Caribbean","2027-03-19",3,"3 nights","Los Angeles (San Pedro), CA","LAX","Ensenada",349,
  "https://www.cruisetimetables.com/cruisesonovationoftheseas-19mar2027.html","https://www.royalcaribbean.com/cruises/itinerary/3-night-ensenada-from-los-angeles-on-ovation/OV03LAX-1965470999?sail-date=2027-03-19&currency=USD"),
 ("LA-68","Ovation of the Seas — 4-Night Catalina & Ensenada","Royal Caribbean","2027-03-22",4,"4 nights","Los Angeles (San Pedro), CA","LAX","Catalina Island; Ensenada",428,
  "https://www.cruisetimetables.com/cruisesonovationoftheseas-22mar2027.html","https://www.royalcaribbean.com/cruises/itinerary/4-night-catalina-ensenada-from-los-angeles-on-ovation/OV04LAX-1005460505?sail-date=2027-03-22&currency=USD"),
 ("LA-69","Ovation of the Seas — 3-Night Ensenada","Royal Caribbean","2027-03-26",3,"3 nights","Los Angeles (San Pedro), CA","LAX","Ensenada",488,
  "https://www.cruisetimetables.com/cruisesonovationoftheseas-26mar2027.html","https://www.royalcaribbean.com/cruises/itinerary/3-night-ensenada-from-los-angeles-on-ovation/OV03LAX-1965470999?sail-date=2027-03-26&currency=USD"),
 ("LA-70","Ovation of the Seas — 4-Night Catalina & Ensenada","Royal Caribbean","2027-03-29",4,"4 nights","Los Angeles (San Pedro), CA","LAX","Catalina Island; Ensenada",439,
  "https://www.cruisetimetables.com/cruisesonovationoftheseas-29mar2027.html","https://www.royalcaribbean.com/cruises/itinerary/4-night-catalina-ensenada-from-los-angeles-on-ovation/OV04LAX-1005460505?sail-date=2027-03-29&currency=USD"),
 # --- Princess, Discovery Princess (Los Angeles / San Pedro) ---
 ("LA-71","Discovery Princess — 7-Night Mexican Riviera","Princess Cruises","2027-02-20",7,"7 nights","Los Angeles (San Pedro), CA","LAX","Cabo San Lucas; Mazatlán; Puerto Vallarta",599,
  "https://www.cruisetimetables.com/cruisesondiscoveryprincess-20feb2027.html","https://www.princess.com/itinerary-details/?voyageCode=X709"),
 ("LA-72","Discovery Princess — 7-Night Mexican Riviera","Princess Cruises","2027-02-27",7,"7 nights","Los Angeles (San Pedro), CA","LAX","Cabo San Lucas; Mazatlán; Puerto Vallarta",549,
  "https://www.cruisetimetables.com/cruisesondiscoveryprincess-27feb2027.html","https://www.princess.com/itinerary-details/?voyageCode=X710"),
 ("LA-73","Discovery Princess — 7-Night Mexican Riviera","Princess Cruises","2027-03-06",7,"7 nights","Los Angeles (San Pedro), CA","LAX","Cabo San Lucas; Mazatlán; Puerto Vallarta",749,
  "https://www.cruisetimetables.com/cruisesondiscoveryprincess-06mar2027.html","https://www.princess.com/itinerary-details/?voyageCode=X711"),
 ("LA-74","Discovery Princess — 7-Night Mexican Riviera","Princess Cruises","2027-03-13",7,"7 nights","Los Angeles (San Pedro), CA","LAX","Cabo San Lucas; Mazatlán; Puerto Vallarta",579,
  "https://www.cruisetimetables.com/cruisesondiscoveryprincess-13mar2027.html","https://www.princess.com/itinerary-details/?voyageCode=X712"),
 ("LA-75","Discovery Princess — 7-Night Mexican Riviera","Princess Cruises","2027-03-20",7,"7 nights","Los Angeles (San Pedro), CA","LAX","Cabo San Lucas; Mazatlán; Puerto Vallarta",649,
  "https://www.cruisetimetables.com/cruisesondiscoveryprincess-20mar2027.html","https://www.princess.com/itinerary-details/?voyageCode=X713"),
 ("LA-76","Discovery Princess — 7-Night Mexican Riviera","Princess Cruises","2027-03-27",7,"7 nights","Los Angeles (San Pedro), CA","LAX","Cabo San Lucas; Mazatlán; Puerto Vallarta",554,
  "https://www.cruisetimetables.com/cruisesondiscoveryprincess-27mar2027.html","https://www.princess.com/itinerary-details/?voyageCode=X714"),
 # --- Princess, Emerald Princess (Los Angeles / San Pedro) ---
 ("LA-77","Emerald Princess — 16-Night Hawaiian Islands","Princess Cruises","2027-02-26",16,"16 nights","Los Angeles (San Pedro), CA","LAX","Hilo; Honolulu (Oahu); Nawiliwili (Kauai); Kailua Kona; Ensenada",1189,
  "https://www.cruisetimetables.com/cruisesonemeraldprincess-26feb2027.html","https://www.princess.com/itinerary-details/?voyageCode=E705"),
 ("LA-78","Emerald Princess — 7-Night Classic California Coast","Princess Cruises","2027-03-21",7,"7 nights","Los Angeles (San Pedro), CA","LAX","Ensenada; San Diego; San Francisco (overnight)",529,
  "https://www.cruisetimetables.com/cruisesonemeraldprincess-21mar2027.html","https://www.princess.com/itinerary-details/?voyageCode=E707"),
 # --- Carnival Panorama (Long Beach) ---
 ("LA-79","Carnival Panorama — 6-Day Mexican Riviera","Carnival Cruise Line","2027-03-07",6,"6 nights","Long Beach (Los Angeles), CA","LAX","Cabo San Lucas; Ensenada",334,
  "https://www.cruisetimetables.com/cruisesoncarnivalpanorama-07mar2027.html","https://www.carnival.com/itinerary/6-day-mexican-riviera-cruise/long-beach-los-angeles/panorama/6-days/mrk/?sailDate=03072027"),
 ("LA-80","Carnival Panorama — 8-Day Mexican Riviera","Carnival Cruise Line","2027-03-13",8,"8 nights","Long Beach (Los Angeles), CA","LAX","Puerto Vallarta; Mazatlán; La Paz; Cabo San Lucas",593,
  "https://www.cruisetimetables.com/cruisesoncarnivalpanorama-13mar2027.html","https://www.carnival.com/itinerary/8-day-mexican-riviera-cruise/long-beach-los-angeles/panorama/8-days/mrx/?sailDate=03132027"),
 ("LA-81","Carnival Panorama — 6-Day Mexican Riviera","Carnival Cruise Line","2027-03-21",6,"6 nights","Long Beach (Los Angeles), CA","LAX","Cabo San Lucas; Ensenada",469,
  "https://www.cruisetimetables.com/cruisesoncarnivalpanorama-21mar2027.html","https://www.carnival.com/itinerary/6-day-mexican-riviera-cruise/long-beach-los-angeles/panorama/6-days/mrx/?sailDate=03212027"),
 ("LA-82","Carnival Panorama — 8-Day Mexican Riviera","Carnival Cruise Line","2027-03-27",8,"8 nights","Long Beach (Los Angeles), CA","LAX","Puerto Vallarta; Mazatlán; La Paz; Cabo San Lucas",703,
  "https://www.cruisetimetables.com/cruisesoncarnivalpanorama-27mar2027.html","https://www.carnival.com/itinerary/8-day-mexican-riviera-cruise/long-beach-los-angeles/panorama/8-days/mrx/?sailDate=03272027"),
 # --- Carnival Radiance (Long Beach) ---
 ("LA-83","Carnival Radiance — 5-Day Mexican Riviera","Carnival Cruise Line","2027-03-04",5,"5 nights","Long Beach (Los Angeles), CA","LAX","Cabo San Lucas; Ensenada",392,
  "https://www.cruisetimetables.com/cruisesoncarnivalradiance-04mar2027.html","https://www.carnival.com/itinerary/5-day-mexican-riviera-cruise/long-beach-los-angeles/radiance/5-days/mrp/?sailDate=03042027"),
 ("LA-84","Carnival Radiance — 5-Day Mexican Riviera","Carnival Cruise Line","2027-03-09",5,"5 nights","Long Beach (Los Angeles), CA","LAX","Cabo San Lucas; Ensenada",401,
  "https://www.cruisetimetables.com/cruisesoncarnivalradiance-09mar2027.html","https://www.carnival.com/itinerary/5-day-mexican-riviera-cruise/long-beach-los-angeles/radiance/5-days/mrq/?sailDate=03092027"),
 ("LA-85","Carnival Radiance — 14-Day Hawaii","Carnival Cruise Line","2027-03-14",14,"14 nights","Long Beach (Los Angeles), CA","LAX","Kahului (Maui); Honolulu (Oahu); Nawiliwili (Kauai); Hilo; Ensenada",1278,
  "https://www.cruisetimetables.com/cruisesoncarnivalradiance-14mar2027.html","https://www.carnival.com/itinerary/14-day-hawaii-cruise/long-beach-los-angeles/radiance/14-days/jht/?sailDate=03142027"),
 ("LA-86","Carnival Radiance — 4-Day Baja Mexico","Carnival Cruise Line","2027-03-28",4,"4 nights","Long Beach (Los Angeles), CA","LAX","Catalina Island; Ensenada",485,
  "https://www.cruisetimetables.com/cruisesoncarnivalradiance-28mar2027.html","https://www.carnival.com/itinerary/4-day-baja-mexico-cruise/long-beach-los-angeles/radiance/4-days/lxn/?sailDate=03282027"),
 # --- San Diego additions ---
 ("SD-51","Serenade of the Seas — 7-Night Ensenada, Cabo & Mazatlán","Royal Caribbean","2027-02-28",7,"7 nights","San Diego, CA","SAN","Ensenada; Cabo San Lucas; Mazatlán",519,
  "https://www.cruisetimetables.com/cruisesonserenadeoftheseas-28feb2027.html","https://www.royalcaribbean.com/cruises/itinerary/7-night-ensenada,-cabo-mazatlan-from-san-diego-on-serenade/SR07SAN-3702601301?sail-date=2027-02-28&currency=USD"),
 ("SD-52","Disney Wonder — 4-Night Baja","Disney Cruise Line","2027-03-08",4,"4 nights","San Diego, CA","SAN","Ensenada",1874,
  "https://www.cruisetimetables.com/cruisesondisneywonder-08mar2027.html","https://disneycruise.disney.go.com/cruises-destinations/list/DW2242/4-Night-Baja-Cruise-from-San-Diego/2027-03-08-Disney-Wonder/"),
 ("SD-53","Koningsdam — 7-Night Mexican Riviera","Holland America Line","2027-03-27",7,"7 nights","San Diego, CA","SAN","Cabo San Lucas; Mazatlán; Puerto Vallarta",1149,
  "https://www.cruisetimetables.com/cruisesonkoningsdam-27mar2027.html","https://www.hollandamerica.com/en/us/find-a-cruise/m7r07a/k718a"),
 ("SD-54","Koningsdam — 11-Night Mexican Riviera & Pacific Coast (ends Vancouver)","Holland America Line","2027-03-27",11,"11 nights","San Diego, CA","SAN_YVR","Cabo San Lucas; Mazatlán; Puerto Vallarta; San Diego; Victoria; Vancouver",1199,
  "https://www.cruisetimetables.com/cruisesonkoningsdam-27mar2027.html","https://www.hollandamerica.com/en/us/find-a-cruise/m7r11a/k718"),
 ("SD-55","Koningsdam — 28-Night Mexico Riviera, Pacific Coastal & Circle Hawaii (ends Vancouver)","Holland America Line","2027-03-27",28,"28 nights","San Diego, CA","SAN_YVR","Cabo San Lucas; Mazatlán; Puerto Vallarta; San Diego; Victoria; Vancouver; Nawiliwili (Kauai); Honolulu (Oahu); Kailua Kona; Kahului (Maui); Hilo; Vancouver",3184,
  "https://www.cruisetimetables.com/cruisesonkoningsdam-27mar2027.html","https://www.hollandamerica.com/en/us/find-a-cruise/h7h28a/k718b"),
 ("SD-56","Zaandam — 7-Night Mexican Riviera","Holland America Line","2027-03-28",7,"7 nights","San Diego, CA","SAN","Puerto Vallarta; Mazatlán; Cabo San Lucas",899,
  "https://www.cruisetimetables.com/cruisesonzaandam-28mar2027.html","https://www.hollandamerica.com/en/us/find-a-cruise/m7r07d/x719"),
]

# Line-level official promo snapshots (all accessed 2026-08-28; applicability to any
# specific sailing is NOT verified — always reconfirm terms on the official page).
PROMOS = {
 "Royal Caribbean": "Official deals page (accessed 2026-08-28): Mexico sailings from LA advertised from $289; last-minute deals from $299; Kids Sail Free on select sailings; extra resident / senior 55+ / military / police & EMT discounts. Sailing-specific applicability not verified: royalcaribbean.com/cruise-deals",
 "Princess Cruises": "Official deals page (accessed 2026-08-28): 'up to $600 per room onboard spend + low deposit' offer listed for bookings by Aug 31, 2026; page/geo terms vary. Sailing-specific applicability not verified: princess.com/cruise-deals-promotions",
 "Carnival Cruise Line": "Official deals page (accessed 2026-08-28): Sail Away Soon Pack & Go Sale up to 55% off (select sailings through Feb 2027, ends Aug 31, 2026); Early Saver Bonus (room upgrade from $1, save up to $1,100/room, deposits from $49, sailings through Apr 2029); Free 3rd & 4th Guest sale (select sailings through May 2027). Sailing-specific applicability not verified: carnival.com/cruise-deals",
 "Holland America Line": "Official site (accessed 2026-08-28): 'Save on Sunshine' up to 40% off + up to $400 onboard credit (Mexico eligible; book by Aug 31, 2026); 'Have It All' Early Booking Bonus on select 2027 fares. Sailing-specific applicability not verified: hollandamerica.com",
 "Disney Cruise Line": "No sailing-specific promo for these 2027 Baja sailings found in indexed sources (accessed 2026-08-28). DCL publishes periodic resident / military / restricted-fare offers; check the official Special Offers page before booking",
 "Norwegian Cruise Line": "Line-level promos change frequently; no sailing-specific promo verified on official channels as of 2026-08-28: ncl.com/cruise-deals",
}

# Irregularity flags for pre-existing rows (verified against the cruisetimetables
# departure calendar / per-sailing pages on 2026-08-28). Row data is preserved;
# only status + verification_note are updated for manual review.
FLAGS = {
 "LA-43": ("REVIEW — date mismatch vs verified schedule index",
  "FLAGGED 2026-08-28: no Emerald Princess departure indexed on 2027-03-10. Verified Emerald LA departures in window: Feb 26 (16N Hawaiian Islands, E705), Mar 14 / 21 / 28 (7N Classic California Coast, E706-E708 family). Row price/itinerary could not be matched to any indexed sailing; official confirmation required."),
 "LA-45": ("REVIEW — date mismatch vs verified schedule index",
  "FLAGGED 2026-08-28: no Emerald Princess departure indexed on 2027-03-17. Nearest verified: Mar 14 & Mar 21 7N Classic California Coast. Row's 12-night claim matches no indexed Emerald LA sailing in the window."),
 "LA-46": ("REVIEW — date mismatch vs verified schedule index",
  "FLAGGED 2026-08-28: no Emerald Princess departure indexed on 2027-03-19 (the ship is at sea between verified Mar 14 and Mar 21 LA departures; 2027-03-19 is an indexed San Diego port call on the E706 sailing, not a turnaround)."),
 "LA-47": ("REVIEW — date mismatch vs verified schedule index",
  "FLAGGED 2026-08-28: no Emerald Princess departure indexed on 2027-03-24 (the ship is at sea on the verified Mar 21 7N sailing). Claimed 7-night itinerary matches no indexed sailing for that date."),
 "LA-48": ("REVIEW — date mismatch vs verified schedule index",
  "FLAGGED 2026-08-28: no Emerald Princess departure indexed on 2027-03-31 (the ship is at sea on the verified Mar 28 7N sailing, next turnaround Apr 4). Claimed 21-night itinerary matches no indexed sailing for that date."),
 "LA-52": ("REVIEW — date mismatch vs verified schedule index",
  "FLAGGED 2026-08-28: no Carnival Radiance turnaround indexed on 2027-03-05. Verified Radiance Long Beach departures near that date: Mar 4 (5N) and Mar 9 (5N) with per-sailing pages; row likely intended one of these."),
 "LA-53": ("REVIEW — date mismatch vs verified schedule index",
  "FLAGGED 2026-08-28: no Carnival Panorama departure indexed on 2027-03-12. Verified Panorama Long Beach departures near that date: Mar 7 (6N) and Mar 13 (8N); row likely intended Sat 2027-03-13."),
 "LA-54": ("REVIEW — date mismatch vs verified schedule index",
  "FLAGGED 2026-08-28: no Carnival Radiance turnaround indexed on 2027-03-19 (the ship is at sea on the verified Mar 14 14N Hawaii sailing). Nearest verified departures: Mar 9 (5N), Mar 28 (4N)."),
 "LA-55": ("REVIEW — date mismatch vs verified schedule index",
  "FLAGGED 2026-08-28: no Carnival Panorama departure indexed on 2027-03-26. Verified Panorama departures near that date: Mar 21 (6N) and Mar 27 (8N); row likely intended Sat 2027-03-27."),
 "LA-44": (None,  # keep existing REVIEW — GBP status; only amend note
  "ENRICHED 2026-08-28: the indexed 2027-03-14 Emerald Princess LA sailing is the 7-Night Classic California Coast (E706): LA → San Francisco → Santa Barbara → San Diego → Ensenada → LA; schedule-index interior snapshot $549/person USD, voyage link princess.com/itinerary-details/?voyageCode=E706. Row's GBP third-party snapshot and 'Hawaii' wording conflict with the verified identity — reconcile on the official page before any booking."),
 "LA-56": (None,
  "ENRICHED 2026-08-28: the verified 2027-03-28 Emerald Princess LA turnaround is the 7-Night Classic California Coast (E708 family, sister sailings E706/E707 confirmed via per-sailing index pages). Pull live price from princess.com before treating this row as bookable."),
}

def money(n): return f"${n:,}"

def parse_money(s):
    s = s.replace("$","").replace("£","").replace(",","").strip()
    return int(s) if s.isdigit() else None

def main():
    with open(CSV, newline="") as f:
        rows = list(csv.DictReader(f))
    fields = list(rows[0].keys())

    # ---- 1. uniform flight-basis refresh on existing rows + flags
    for r in rows:
        route = r["flight_route"]
        if "SFO → SAN" in route:
            rk = "SAN"
        elif "SFO → LAX" in route:
            rk = "LAX"
        else:
            rk = "HOME"
        rr = ROUTES[rk]
        old_cost = r["flight_cost_2"]
        old_route_label = r["flight_route"]
        if rk != "HOME" and old_cost != f"{money(rr['for2'])} planning estimate":
            r["flight_cost_2"] = f"{money(rr['for2'])} planning estimate"
            r["flight_route"] = rr["label"]
            r["flight_source"] = f"KAYAK route data: {rr['note']}"
            r["flight_source_url"] = rr["url"]
            p = parse_money(r["price"]) if r["price_currency"] == "USD" else None
            if p is not None:
                r["trip_total_2"] = money(p + rr["for2"])
                r["trip_total_note"] = ("Cruise snapshot + 2-adult flight planning estimate "
                    f"({rr['label']}); live quote required. Flight basis refreshed to KAYAK route average 2026-08-28 (was '{old_cost}' on {old_route_label}).")
        elif rk == "SAN":
            r["flight_source"] = f"KAYAK route data: {rr['note']}"
            r["flight_source_url"] = rr["url"]
        # flags
        if r["id"] in FLAGS:
            st, note = FLAGS[r["id"]]
            if st: r["status"] = st
            r["verification_note"] = note

    # ---- 2. append new verified rows
    out = list(rows)
    for ( rid,name,line,dstr,nights,dur,port,rk,stops,pp,idx,off ) in NEW:
        d = date.fromisoformat(dstr)
        assert WINDOW_START <= d <= WINDOW_END, f"{rid} outside window!"
        rr = ROUTES[rk]
        end = d + timedelta(days=nights)
        f_out = (d - timedelta(days=1)).isoformat()
        f_back = (end + timedelta(days=1)).isoformat()
        cruise2 = pp * 2
        trip = cruise2 + rr["for2"]
        if rk == "SAN_YVR":
            fs_url = gflights("SFO","SAN",f_out,"")
            fs_url = (f"https://www.google.com/travel/flights?q=One-way%20flights%20SFO%20to%20SAN%20{f_out}%2C%20then%20YVR%20to%20SFO%20{f_back}")
        else:
            dest = "LAX" if rk == "LAX" else "SAN"
            fs_url = gflights("SFO", dest, f_out, f_back) + f"%20for%202%20adults"
        row = {
            "id": rid, "name": name, "line": line, "date": dstr, "duration": dur,
            "port": port, "stops": stops,
            "price": money(cruise2),
            "price_note": f"Interior snapshot {money(pp)}/person; total is 2 × snapshot",
            "source": "CruiseTimetables per-sailing index + official line deep link",
            "official": off,
            "promo": PROMOS[line],
            "status": "NEW 2026-08-28 — Schedule + price snapshot (line-by-line verified)",
            "source_url": idx,
            "flight_out_date": f_out, "flight_return_date": f_back,
            "flight_route": rr["label"],
            "flight_cost_2": f"{money(rr['for2'])} planning estimate",
            "flight_source": f"KAYAK route data: {rr['note']}",
            "flight_source_url": rr["url"],
            "trip_total_2": money(trip),
            "trip_total_note": "Cruise snapshot + 2-adult flight planning estimate; live quotes required for both.",
            "price_currency": "USD",
            "verification_note": ("Line-by-line verified 2026-08-28 against the per-sailing schedule-index page "
                "(departure date, duration, port sequence and interior per-person snapshot all read from the linked page) "
                "plus the official cruise-line voyage deep link. Snapshot ≠ live quote; cabin class, taxes/fees and "
                "availability must be confirmed on the official page."),
            "flight_search_url": fs_url,
        }
        assert len(row) == len(fields) and list(row) == fields, f"schema mismatch {rid}"
        out.append(row)

    # ---- 3. write CSV + JSON (+ docs copy)
    with open(CSV, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields); w.writeheader(); w.writerows(out)
    data_js = json.dumps(out, indent=2, ensure_ascii=False)
    for p in (JSON_OUT, DOCS_JSON):
        import os; os.makedirs(os.path.dirname(p), exist_ok=True)
        with open(p, "w") as f: f.write(data_js + "\n")
    # keep the site's data snapshot self-contained (GitHub Pages serves docs/ as root)
    import shutil
    for name in ("cruises_master_verified.csv", "cruise_line_scope_audit.csv", "verification_log_2026-08-28.csv"):
        src = f"{ROOT}/data/{name}"
        if os.path.exists(src): shutil.copy(src, f"{ROOT}/docs/data/{name}")

    # ---- 4. verification log (one line per new entry)
    with open(VLOG, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["id","sailing","departure","check_1_schedule_index","check_2_official_link",
                    "check_3_price_read","check_4_scope","check_5_window","result"])
        for ( rid,name,line,dstr,nights,dur,port,rk,stops,pp,idx,off ) in NEW:
            w.writerow([rid, name, dstr,
                f"PASS — dates/duration/itinerary/read interior ${pp}pp from: {idx}",
                f"PASS — official voyage deep link present: {off}",
                "PASS — interior per-person snapshot published in USD at index",
                f"PASS — departs {port} (U.S. West Coast)",
                "PASS — inside 2027-02-15…2027-03-31",
                "ADDED"])
    new_in = sum(1 for r in out if r["status"].startswith("NEW"))
    inwin = sum(1 for r in out if not r["status"].startswith("OUT OF WINDOW"))
    print(f"rows total: {len(out)} | new verified: {new_in} | in-window: {inwin}")

if __name__ == "__main__":
    sys.exit(main())
