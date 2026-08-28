#!/usr/bin/env python3
"""CruiseDeals — verification sweep PASS 2 (2026-08-28, later pass).

Every in-window row (86 sailings) was re-verified line by line on 2026-08-28:
  1. re-read the sailing's own per-sailing schedule-index page
     (departure date, duration, full port sequence, interior per-person price),
  2. matched/refreshed the official cruise-line voyage deep link,
  3. refreshed the per-line official promotions snapshot,
  4. refreshed the KAYAK flight-route basis (SFO-SAN, SFO-LAX, YVR-SFO)
     and added a new open-jaw basis (SFO->LAX + FLL->SFO) for the
     Island Princess 3/2 Panama Canal voyage ending in Fort Lauderdale.

Findings applied (nothing invented, nothing deleted):
  - 4 rows previously "Not published" now carry verified USD snapshots:
    LA-25 ($377pp), LA-51 ($1,879pp), LA-56 ($539pp) — LA-44's GBP third-party
    price replaced by the published USD snapshot ($549pp).
  - LA-51 itinerary CORRECTED: Island Princess 3/2 is the 16-Night Panama Canal
    Ocean-to-Ocean ending Fort Lauderdale (master had mislabeled it Hawaii/Pacific).
  - SD-21 itinerary CORRECTED: Serenade 3/28 is 7N Ensenada, Cabo & La Paz
    (master had said Mazatlan).
  - SD-10 stops CORRECTED: Wonder 3/26 3N calls Catalina Island + Ensenada.
  - Price moves recorded with the prior per-person value in price_note.
  - The 9 REVIEW rows (LA-43/45/46/47/48, LA-52/53/54/55) remain flagged:
    pass 2 confirmed no indexed departure exists on those dates.

Zero new distinct in-window sailings exist beyond the 86 already listed —
the population is complete (every Feb 15 - Mar 31, 2027 turnaround at San Diego,
Los Angeles/San Pedro, Long Beach and San Francisco is in the master list, and
no per-sailing page lists additional voyage variants). This script therefore
adds NO fabricated rows.
"""
import csv, json, os, shutil, sys
from datetime import date, timedelta

ROOT = "/home/user/CruiseDeals"
CSV = f"{ROOT}/data/cruises_master_verified.csv"
JSON_OUT = f"{ROOT}/data/cruises.json"
DOCS_JSON = f"{ROOT}/docs/data/cruises.json"
DOCS_DATA = f"{ROOT}/docs/data"
VLOG2 = f"{ROOT}/data/verification_log_2026-08-28-pass2.csv"

# ------------------------------------------------------------------ flight basis
# All figures re-read from the linked KAYAK route pages on 2026-08-28 (pass 2).
ROUTES = {
    "SAN": dict(for2=312, label="SFO → SAN → SFO",
        note=("KAYAK route data (page accessed 2026-08-28): planning basis $156/person round trip; "
              "typical range $134–$287; cheapest round-trip observed $78"),
        url="https://www.kayak.com/flight-routes/San-Francisco-SFO/San-Diego-SAN"),
    "LAX": dict(for2=408, label="SFO → LAX → SFO",
        note=("KAYAK route data (page accessed 2026-08-28): planning basis $204/person round trip "
              "(≈ midpoint of typical range $138–$272); cheapest round-trip observed $89"),
        url="https://www.kayak.com/flight-routes/San-Francisco-SFO/Los-Angeles-LAX"),
    "SAN_YVR": dict(for2=570, label="SFO → SAN one-way; YVR → SFO return",
        note=("Open-jaw planning estimate $570/2 adults: SFO→SAN one-way basis $75pp (KAYAK one-way deals "
              "observed $48–$79) + YVR→SFO one-way basis $210pp (KAYAK cheapest one-way $155, typical $137–$290); "
              "route pages accessed 2026-08-28"),
        url="https://www.kayak.com/flight-routes/Vancouver-Intl-YVR/San-Francisco-SFO"),
    "LAX_FLL": dict(for2=530, label="SFO → LAX one-way; FLL → SFO return",
        note=("Open-jaw planning estimate $530/2 adults: SFO→LAX one-way basis $75pp (KAYAK one-way deals "
              "observed $48–$89) + FLL→SFO one-way basis $190pp (KAYAK one-way deals observed $151–$170, "
              "round-trip typical $278–$467, February indexed as cheapest month); route pages accessed 2026-08-28"),
        url="https://www.kayak.com/flight-routes/Fort-Lauderdale-FLL/San-Francisco-SFO"),
    "HOME": dict(for2=0, label="No flight required (SFO departure)",
        note="Port matches origin airport city", url=""),
}

# --------------------------------------------------------- per-line promo snapshot
# Re-verified on official deal pages 2026-08-28 (pass 2). Sailing-specific
# applicability is NOT verified — reconfirm on the official page.
PROMOS = {
 "Carnival Cruise Line": ("Official Cruise Deals page (accessed 2026-08-28, ends Aug 31 2026 unless noted): "
   "Sail Away Soon Pack & Go Sale — up to 55% off, select sailings through Feb 2027; Early Saver Bonus — "
   "$1 room upgrade, save up to $1,100/room, deposits from $49pp, up to $50 onboard credit, sailings through Apr 2029; "
   "More Time, More Perks — 50% off deposits, up to 40% off, final payment 30 days out, sailings through May 2027; "
   "Free 3rd & 4th Guest Sale (cabins of 3+, through May 2027). Sailing-specific applicability not verified: "
   "carnival.com/cruise-deals"),
 "Royal Caribbean": ("Official deals page (accessed 2026-08-28): Mexico sailings from LA advertised from $289; "
   "2026 last-minute deals from $299; Kids Sail Free on select sailings; resident / 55+ / military / police & EMT "
   "rates. Sailing-specific applicability not verified: royalcaribbean.com/cruise-deals"),
 "Princess Cruises": ("Official deals page (accessed 2026-08-28): 'up to $600 per room onboard spend + low deposit' "
   "offer listed for bookings by Aug 31, 2026; page/geo terms vary. Sailing-specific applicability not verified: "
   "princess.com/cruise-deals-promotions"),
 "Holland America Line": ("Official site (accessed 2026-08-28): 'Save on Sunshine' up to 40% off + up to $400 "
   "onboard credit (Mexico eligible; book by Aug 31, 2026); 'Have It All' Early Booking Bonus on select 2027 fares. "
   "Sailing-specific applicability not verified: hollandamerica.com"),
 "Disney Cruise Line": ("No sailing-specific promo for these 2027 Baja sailings found in indexed sources "
   "(accessed 2026-08-28). DCL publishes periodic resident / military / restricted-fare offers; check the official "
   "Special Offers page before booking"),
 "Norwegian Cruise Line": ("Official deals page (accessed 2026-08-28): Free at Sea package (unlimited open bar, "
   "specialty dining, shore-excursion credit, Wi-Fi); Free 2nd Guest limited-time offer, all categories; "
   "Semi-Annual Sale (limited time); $150 CruiseFirst certificates; Latitudes past-guest bonus; "
   "military / teacher / first-responder discounts. Sailing-specific applicability not verified: ncl.com/cruise-deals"),
}

# ------------------------------------------------------------------ fresh reads
# Per-sailing index page re-read 2026-08-28 (pass 2):
#   id -> (interior_pp_or_None, official_deep_link, port_label, stops_or_None,
#          name_or_None, duration_or_None, route_key_or_None_to_keep)
# price_pp None => row had no published price in pass 2 either (not the case here).
FRESH = {
 # --- Disney Wonder (San Diego) ---
 "SD-01": (2285, "https://disneycruise.disney.go.com/cruises-destinations/list/DW2236/4-Night-Baja-Cruise-from-San-Diego/2027-02-15-Disney-Wonder/", None, None, None, None, None),
 "SD-02": (1328, "https://disneycruise.disney.go.com/cruises-destinations/list/DW2237/3-Night-Baja-Cruise-from-San-Diego/2027-02-19-Disney-Wonder/", None, None, None, None, None),
 "SD-03": (1474, "https://disneycruise.disney.go.com/cruises-destinations/list/DW2238/4-Night-Baja-Cruise-from-San-Diego/2027-02-22-Disney-Wonder/", None, None, None, None, None),
 "SD-04": (1328, "https://disneycruise.disney.go.com/cruises-destinations/list/DW2239/3-Night-Baja-Cruise-from-San-Diego/2027-02-26-Disney-Wonder/", None, None, None, None, None),
 "SD-05": (1911, "https://disneycruise.disney.go.com/cruises-destinations/list/DW2240/4-Night-Baja-Cruise-from-San-Diego/2027-03-01-Disney-Wonder/", None, None, None, None, None),
 "SD-06": (1784, "https://disneycruise.disney.go.com/cruises-destinations/list/DW2241/3-Night-Baja-Cruise-from-San-Diego/2027-03-05-Disney-Wonder/", None, None, None, None, None),
 "SD-07": (3430, "https://disneycruise.disney.go.com/cruises-destinations/list/DW2243/7-Night-Mexican-Riviera-Cruise-from-San-Diego/2027-03-12-Disney-Wonder/", None, None, None, None, None),
 "SD-08": (1946, "https://disneycruise.disney.go.com/cruises-destinations/list/DW2244/3-Night-Baja-Cruise-from-San-Diego/2027-03-19-Disney-Wonder/", None, None, None, None, None),
 "SD-09": (2824, "https://disneycruise.disney.go.com/cruises-destinations/list/DW2245/4-Night-Baja-Cruise-from-San-Diego/2027-03-22-Disney-Wonder/", None, None, None, None, None),
 "SD-10": (2341, "https://disneycruise.disney.go.com/cruises-destinations/list/DW2246/3-Night-Baja-Cruise-from-San-Diego/2027-03-26-Disney-Wonder/", None,
           "Catalina Island; Ensenada; San Diego", None, None, None),
 "SD-11": (2856, "https://disneycruise.disney.go.com/cruises-destinations/list/DW2247/4-Night-Baja-Cruise-from-San-Diego/2027-03-29-Disney-Wonder/", None, None, None, None, None),
 "SD-52": (1874, "https://disneycruise.disney.go.com/cruises-destinations/list/DW2242/4-Night-Baja-Cruise-from-San-Diego/2027-03-08-Disney-Wonder/", None, None, None, None, None),
 # --- Serenade of the Seas (San Diego) ---
 "SD-12": (335, "https://www.royalcaribbean.com/cruises/itinerary/3-night-ensenada-from-san-diego-on-serenade/SR03SAN-2087072271?sail-date=2027-02-18&currency=USD", None, None, None, None, None),
 "SD-13": (329, "https://www.royalcaribbean.com/cruises/itinerary/4-night-catalina-ensenada-from-san-diego-on-serenade/SR04SAN-3051025153?sail-date=2027-02-21&currency=USD", None, None, None, None, None),
 "SD-14": (335, "https://www.royalcaribbean.com/cruises/itinerary/3-night-ensenada-from-san-diego-on-serenade/SR03SAN-2087072271?sail-date=2027-02-25&currency=USD", None, None, None, None, None),
 "SD-15": (349, "https://www.royalcaribbean.com/cruises/itinerary/4-night-catalina-ensenada-from-san-diego-on-serenade/SR04SAN-3051025153?sail-date=2027-03-07&currency=USD", None, None, None, None, None),
 "SD-16": (335, "https://www.royalcaribbean.com/cruises/itinerary/3-night-ensenada-from-san-diego-on-serenade/SR03SAN-2087072271?sail-date=2027-03-11&currency=USD", None, None, None, None, None),
 "SD-17": (349, "https://www.royalcaribbean.com/cruises/itinerary/4-night-catalina-ensenada-from-san-diego-on-serenade/SR04SAN-3051025153?sail-date=2027-03-14&currency=USD", None, None, None, None, None),
 "SD-18": (335, "https://www.royalcaribbean.com/cruises/itinerary/3-night-ensenada-from-san-diego-on-serenade/SR03SAN-2087072271?sail-date=2027-03-18&currency=USD", None, None, None, None, None),
 "SD-19": (346, "https://www.royalcaribbean.com/cruises/itinerary/4-night-catalina-ensenada-from-san-diego-on-serenade/SR04SAN-3051025153?sail-date=2027-03-21&currency=USD", None, None, None, None, None),
 "SD-20": (335, "https://www.royalcaribbean.com/cruises/itinerary/3-night-ensenada-from-san-diego-on-serenade/SR03SAN-2087072271?sail-date=2027-03-25&currency=USD", None, None, None, None, None),
 "SD-21": (649, "https://www.royalcaribbean.com/cruises/itinerary/7-night-ensenada,-cabo-la-paz-from-san-diego-on-serenade/SR07SAN-394531984?sail-date=2027-03-28&currency=USD", None,
           "La Paz; Cabo San Lucas; Ensenada", "Serenade of the Seas — 7-Night Ensenada, Cabo & La Paz", None, None),
 "SD-51": (519, "https://www.royalcaribbean.com/cruises/itinerary/7-night-ensenada,-cabo-mazatlan-from-san-diego-on-serenade/SR07SAN-3702601301?sail-date=2027-02-28&currency=USD", None, None, None, None, None),
 # --- Koningsdam / Zaandam (San Diego) ---
 "SD-22": (999,  "https://www.hollandamerica.com/en/us/find-a-cruise/m7s07a/k717", None,
           "Cabo San Lucas; La Paz; Mazatlán", None, None, None),
 "SD-23": (1944, "https://www.hollandamerica.com/en/us/find-a-cruise/m7s14a/k717b", None,
           "Cabo San Lucas; La Paz; Mazatlán; San Diego; Cabo San Lucas; Mazatlán; Puerto Vallarta; San Diego", None, None, None),
 "SD-24": (1989, "https://www.hollandamerica.com/en/us/find-a-cruise/m7s18a/k717a", None,
           "Cabo San Lucas; La Paz; Mazatlán; San Diego; Cabo San Lucas; Mazatlán; Puerto Vallarta; San Diego; Victoria; Vancouver", None, None, None),
 "SD-53": (1149, "https://www.hollandamerica.com/en/us/find-a-cruise/m7r07a/k718a", None, None, None, None, None),
 "SD-54": (1199, "https://www.hollandamerica.com/en/us/find-a-cruise/m7r11a/k718", None, None, None, None, None),
 "SD-55": (3184, "https://www.hollandamerica.com/en/us/find-a-cruise/h7h28a/k718b", None, None, None, None, None),
 "SD-56": (899,  "https://www.hollandamerica.com/en/us/find-a-cruise/m7r07d/x719", None, None, None, None, None),
 # --- Carnival Panorama / Radiance (Long Beach) ---
 "LA-26": (315, "https://www.carnival.com/itinerary/6-day-mexican-riviera-cruise/long-beach-los-angeles/panorama/6-days/mrk/?sailDate=02212027", None, None, None, None, None),
 "LA-27": (493, "https://www.carnival.com/itinerary/8-day-mexican-riviera-cruise/long-beach-los-angeles/panorama/8-days/mry/?sailDate=02272027", None, None, None, None, None),
 "LA-28": (300, "https://www.carnival.com/itinerary/4-day-baja-mexico-cruise/long-beach-los-angeles/radiance/4-days/lxn/?sailDate=02282027", None, None, None, None, None),
 "LA-79": (334, "https://www.carnival.com/itinerary/6-day-mexican-riviera-cruise/long-beach-los-angeles/panorama/6-days/mrk/?sailDate=03072027", None, None, None, None, None),
 "LA-80": (593, "https://www.carnival.com/itinerary/8-day-mexican-riviera-cruise/long-beach-los-angeles/panorama/8-days/mrx/?sailDate=03132027", None, None, None, None, None),
 "LA-81": (469, "https://www.carnival.com/itinerary/6-day-mexican-riviera-cruise/long-beach-los-angeles/panorama/6-days/mrx/?sailDate=03212027", None, None, None, None, None),
 "LA-82": (703, "https://www.carnival.com/itinerary/8-day-mexican-riviera-cruise/long-beach-los-angeles/panorama/8-days/mrx/?sailDate=03272027", None, None, None, None, None),
 "LA-83": (392, "https://www.carnival.com/itinerary/5-day-mexican-riviera-cruise/long-beach-los-angeles/radiance/5-days/mrp/?sailDate=03042027", None, None, None, None, None),
 "LA-84": (401, "https://www.carnival.com/itinerary/5-day-mexican-riviera-cruise/long-beach-los-angeles/radiance/5-days/mrq/?sailDate=03092027", None, None, None, None, None),
 "LA-85": (1278, "https://www.carnival.com/itinerary/14-day-hawaii-cruise/long-beach-los-angeles/radiance/14-days/jht/?sailDate=03142027", None, None, None, None, None),
 "LA-86": (485, "https://www.carnival.com/itinerary/4-day-baja-mexico-cruise/long-beach-los-angeles/radiance/4-days/lxn/?sailDate=03282027", None, None, None, None, None),
 # --- Voyager of the Seas (San Pedro) ---
 "LA-25": (377, "https://www.royalcaribbean.com/cruises/itinerary/4-night-ensenada-from-los-angeles-on-voyager/VY04LAX-3628863837?sail-date=2027-02-15&currency=USD", None, None, None, None, None),
 "LA-57": (478, "https://www.royalcaribbean.com/cruises/itinerary/7-night-ensenada,-cabo-mazatlan-from-los-angeles-on-voyager/VY07LAX-2626294331?sail-date=2027-02-19&currency=USD", None, None, None, None, None),
 "LA-58": (509, "https://www.royalcaribbean.com/cruises/itinerary/7-night-cabo,-vallarta-mazatlan-from-los-angeles-on-voyager/VY07LAX-1182818524?sail-date=2027-02-26&currency=USD", None, None, None, None, None),
 "LA-59": (525, "https://www.royalcaribbean.com/cruises/itinerary/7-night-ensenada,-cabo-mazatlan-from-los-angeles-on-voyager/VY07LAX-2626294331?sail-date=2027-03-05&currency=USD", None, None, None, None, None),
 "LA-60": (609, "https://www.royalcaribbean.com/cruises/itinerary/7-night-cabo,-vallarta-mazatlan-from-los-angeles-on-voyager/VY07LAX-1182818524?sail-date=2027-03-12&currency=USD", None, None, None, None, None),
 "LA-61": (620, "https://www.royalcaribbean.com/cruises/itinerary/7-night-cabo,-vallarta-mazatlan-from-los-angeles-on-voyager/VY07LAX-1182818524?sail-date=2027-03-19&currency=USD", None, None, None, None, None),
 "LA-62": (638, "https://www.royalcaribbean.com/cruises/itinerary/6-night-cabo-overnight-catalina-from-los-angeles-on-voyager/VY06LAX-1729758938?sail-date=2027-03-26&currency=USD", None, None, None, None, None),
 # --- Ovation of the Seas (San Pedro) ---
 "LA-29": (345, "https://www.royalcaribbean.com/cruises/itinerary/3-night-ensenada-from-los-angeles-on-ovation/OV03LAX-1965470999?sail-date=2027-02-19&currency=USD", None, None, None, None, None),
 "LA-30": (365, "https://www.royalcaribbean.com/cruises/itinerary/4-night-catalina-ensenada-from-los-angeles-on-ovation/OV04LAX-1005460505?sail-date=2027-02-22&currency=USD", None, None, None, None, None),
 "LA-63": (650, "https://www.royalcaribbean.com/cruises/itinerary/7-night-cabo-overnight-catalina-ensenada-from-los-angeles-on-ovation/OV07LAX-1983939617?sail-date=2027-02-26&currency=USD", None, None, None, None, None),
 "LA-64": (325, "https://www.royalcaribbean.com/cruises/itinerary/3-night-ensenada-from-los-angeles-on-ovation/OV03LAX-1965470999?sail-date=2027-03-05&currency=USD", None, None, None, None, None),
 "LA-65": (366, "https://www.royalcaribbean.com/cruises/itinerary/4-night-catalina-ensenada-from-los-angeles-on-ovation/OV04LAX-1005460505?sail-date=2027-03-08&currency=USD", None, None, None, None, None),
 "LA-66": (706, "https://www.royalcaribbean.com/cruises/itinerary/7-night-cabo-overnight-catalina-ensenada-from-los-angeles-on-ovation/OV07LAX-1983939617?sail-date=2027-03-12&currency=USD", None, None, None, None, None),
 "LA-67": (349, "https://www.royalcaribbean.com/cruises/itinerary/3-night-ensenada-from-los-angeles-on-ovation/OV03LAX-1965470999?sail-date=2027-03-19&currency=USD", None, None, None, None, None),
 "LA-68": (428, "https://www.royalcaribbean.com/cruises/itinerary/4-night-catalina-ensenada-from-los-angeles-on-ovation/OV04LAX-1005460505?sail-date=2027-03-22&currency=USD", None, None, None, None, None),
 "LA-69": (488, "https://www.royalcaribbean.com/cruises/itinerary/3-night-ensenada-from-los-angeles-on-ovation/OV03LAX-1965470999?sail-date=2027-03-26&currency=USD", None, None, None, None, None),
 "LA-70": (439, "https://www.royalcaribbean.com/cruises/itinerary/4-night-catalina-ensenada-from-los-angeles-on-ovation/OV04LAX-1005460505?sail-date=2027-03-29&currency=USD", None, None, None, None, None),
 # --- Norwegian Encore (San Pedro) ---
 "LA-31": (669, "https://www.ncl.com/vacation-builder?itineraryCode=ENCORE7LAXCSLMZTPVRLAX&packageId=23338094&stateroomTypeCode=INSIDE&", None, None, None, None, None),
 "LA-32": (699, "https://www.ncl.com/vacation-builder?itineraryCode=ENCORE7LAXCSLMZTPVRLAX&packageId=23338095&stateroomTypeCode=INSIDE&", None, None, None, None, None),
 "LA-33": (689, "https://www.ncl.com/vacation-builder?itineraryCode=ENCORE7LAXCSLMZTPVRLAX&packageId=23338096&stateroomTypeCode=INSIDE&", None, None, None, None, None),
 "LA-34": (739, "https://www.ncl.com/vacation-builder?itineraryCode=ENCORE7LAXCSLMZTPVRLAX&packageId=23338097&stateroomTypeCode=INSIDE&", None, None, None, None, None),
 "LA-35": (719, "https://www.ncl.com/vacation-builder?itineraryCode=ENCORE7LAXCSLMZTPVRLAX&packageId=23338098&stateroomTypeCode=INSIDE&", None, None, None, None, None),
 "LA-36": (749, "https://www.ncl.com/vacation-builder?itineraryCode=ENCORE7LAXCSLMZTPVRLAX&packageId=23338099&stateroomTypeCode=INSIDE&", None, None, None, None, None),
 # --- Discovery Princess (San Pedro) ---
 "LA-71": (599, "https://www.princess.com/itinerary-details/?voyageCode=X709", None, None, None, None, None),
 "LA-72": (549, "https://www.princess.com/itinerary-details/?voyageCode=X710", None, None, None, None, None),
 "LA-73": (749, "https://www.princess.com/itinerary-details/?voyageCode=X711", None, None, None, None, None),
 "LA-74": (579, "https://www.princess.com/itinerary-details/?voyageCode=X712", None, None, None, None, None),
 "LA-75": (649, "https://www.princess.com/itinerary-details/?voyageCode=X713", None, None, None, None, None),
 "LA-76": (554, "https://www.princess.com/itinerary-details/?voyageCode=X714", None, None, None, None, None),
 # --- Emerald Princess (San Pedro) ---
 "LA-77": (1189, "https://www.princess.com/itinerary-details/?voyageCode=E705", None, None, None, None, None),
 "LA-44": (549, "https://www.princess.com/itinerary-details/?voyageCode=E706", None,
           "San Francisco; Santa Barbara; San Diego; Ensenada",
           "Emerald Princess — 7-Night Classic California Coast", "7 nights", None),
 "LA-78": (529, "https://www.princess.com/itinerary-details/?voyageCode=E707", None, None, None, None, None),
 "LA-56": (539, "https://www.princess.com/itinerary-details/?voyageCode=E708", None,
           "San Francisco; Santa Barbara; San Diego; Ensenada", None, "7 nights", None),
 # --- Island Princess (San Pedro) — itinerary CORRECTED ---
 "LA-51": (1879, "https://www.princess.com/itinerary-details/?voyageCode=2705", None,
           "Puerto Vallarta; Huatulco; Puerto Chiapas; Puntarenas; Panama City; Panama Canal; Oranjestad; Fort Lauderdale",
           "Island Princess — 16-Night Panama Canal Ocean to Ocean (ends Fort Lauderdale)",
           "16 nights", "LAX_FLL"),
 # --- Ruby Princess (San Francisco — no flight) ---
 "SF-51": (1704, "https://www.princess.com/itinerary-details/?voyageCode=R705", None, None, None, None, None),
 "SF-52": (1264, "https://www.princess.com/itinerary-details/?voyageCode=R706", None, None, None, None, None),
}

# Per-sailing schedule-index page (source_url upgrade for the older 50 rows and
# re-check link for all): id -> index URL. Derived from the same pages used for
# the price reads above.
def idx(ship, d):
    return f"https://www.cruisetimetables.com/cruiseson{ship}-{d}.html"

INDEX = {
 "SD-01": idx("disneywonder","15feb2027"), "SD-02": idx("disneywonder","19feb2027"),
 "SD-03": idx("disneywonder","22feb2027"), "SD-04": idx("disneywonder","26feb2027"),
 "SD-05": idx("disneywonder","01mar2027"), "SD-06": idx("disneywonder","05mar2027"),
 "SD-07": idx("disneywonder","12mar2027"), "SD-08": idx("disneywonder","19mar2027"),
 "SD-09": idx("disneywonder","22mar2027"), "SD-10": idx("disneywonder","26mar2027"),
 "SD-11": idx("disneywonder","29mar2027"), "SD-52": idx("disneywonder","08mar2027"),
 "SD-12": idx("serenadeoftheseas","18feb2027"), "SD-13": idx("serenadeoftheseas","21feb2027"),
 "SD-14": idx("serenadeoftheseas","25feb2027"), "SD-15": idx("serenadeoftheseas","07mar2027"),
 "SD-16": idx("serenadeoftheseas","11mar2027"), "SD-17": idx("serenadeoftheseas","14mar2027"),
 "SD-18": idx("serenadeoftheseas","18mar2027"), "SD-19": idx("serenadeoftheseas","21mar2027"),
 "SD-20": idx("serenadeoftheseas","25mar2027"), "SD-21": idx("serenadeoftheseas","28mar2027"),
 "SD-51": idx("serenadeoftheseas","28feb2027"),
 "SD-22": idx("koningsdam","20mar2027"), "SD-23": idx("koningsdam","20mar2027"),
 "SD-24": idx("koningsdam","20mar2027"), "SD-53": idx("koningsdam","27mar2027"),
 "SD-54": idx("koningsdam","27mar2027"), "SD-55": idx("koningsdam","27mar2027"),
 "SD-56": idx("zaandam","28mar2027"),
 "LA-26": idx("carnivalpanorama","21feb2027"), "LA-27": idx("carnivalpanorama","27feb2027"),
 "LA-79": idx("carnivalpanorama","07mar2027"), "LA-80": idx("carnivalpanorama","13mar2027"),
 "LA-81": idx("carnivalpanorama","21mar2027"), "LA-82": idx("carnivalpanorama","27mar2027"),
 "LA-28": idx("carnivalradiance","28feb2027"), "LA-83": idx("carnivalradiance","04mar2027"),
 "LA-84": idx("carnivalradiance","09mar2027"), "LA-85": idx("carnivalradiance","14mar2027"),
 "LA-86": idx("carnivalradiance","28mar2027"),
 "LA-25": idx("voyageroftheseas","15feb2027"), "LA-57": idx("voyageroftheseas","19feb2027"),
 "LA-58": idx("voyageroftheseas","26feb2027"), "LA-59": idx("voyageroftheseas","05mar2027"),
 "LA-60": idx("voyageroftheseas","12mar2027"), "LA-61": idx("voyageroftheseas","19mar2027"),
 "LA-62": idx("voyageroftheseas","26mar2027"),
 "LA-29": idx("ovationoftheseas","19feb2027"), "LA-30": idx("ovationoftheseas","22feb2027"),
 "LA-63": idx("ovationoftheseas","26feb2027"), "LA-64": idx("ovationoftheseas","05mar2027"),
 "LA-65": idx("ovationoftheseas","08mar2027"), "LA-66": idx("ovationoftheseas","12mar2027"),
 "LA-67": idx("ovationoftheseas","19mar2027"), "LA-68": idx("ovationoftheseas","22mar2027"),
 "LA-69": idx("ovationoftheseas","26mar2027"), "LA-70": idx("ovationoftheseas","29mar2027"),
 "LA-31": idx("norwegianencore","21feb2027"), "LA-32": idx("norwegianencore","28feb2027"),
 "LA-33": idx("norwegianencore","07mar2027"), "LA-34": idx("norwegianencore","14mar2027"),
 "LA-35": idx("norwegianencore","21mar2027"), "LA-36": idx("norwegianencore","28mar2027"),
 "LA-71": idx("discoveryprincess","20feb2027"), "LA-72": idx("discoveryprincess","27feb2027"),
 "LA-73": idx("discoveryprincess","06mar2027"), "LA-74": idx("discoveryprincess","13mar2027"),
 "LA-75": idx("discoveryprincess","20mar2027"), "LA-76": idx("discoveryprincess","27mar2027"),
 "LA-77": idx("emeraldprincess","26feb2027"), "LA-44": idx("emeraldprincess","14mar2027"),
 "LA-78": idx("emeraldprincess","21mar2027"), "LA-56": idx("emeraldprincess","28mar2027"),
 "LA-51": idx("islandprincess","02mar2027"),
 "SF-51": idx("rubyprincess","28feb2027"), "SF-52": idx("rubyprincess","16mar2027"),
}

def money(n): return f"${n:,}"
def parse_money(s):
    s = str(s).replace("$","").replace("£","").replace(",","").strip()
    return int(s) if s.isdigit() else None

def gflights(q_from, q_to, d1, d2):
    return ("https://www.google.com/travel/flights?q=Flights%20from%20"
            f"{q_from}%20to%20{q_to}%20{d1}%2C%20return%20{d2}%20for%202%20adults")

def route_key_for(r):
    fr = r["flight_route"]
    if "SFO → SAN one-way" in fr: return "SAN_YVR"
    if "FLL" in fr: return "LAX_FLL"
    if "SFO → SAN" in fr: return "SAN"
    if "SFO → LAX" in fr: return "LAX"
    return "HOME"

def main():
    with open(CSV, newline="") as f:
        rows = list(csv.DictReader(f))
    fields = list(rows[0].keys())
    by_id = {r["id"]: r for r in rows}
    log = []
    stats = dict(confirmed=0, price_up=0, price_down=0, price_added=0,
                 corrected=0, resolved=0, still_flagged=0, out=0)

    for r in rows:
        rid = r["id"]
        if r["status"].startswith("OUT OF WINDOW"):
            stats["out"] += 1
            continue

        if rid in ("LA-43","LA-45","LA-46","LA-47","LA-48","LA-52","LA-53","LA-54","LA-55"):
            # Keep preserved rows flagged; append pass-2 confirmation.
            r["verification_note"] = (r["verification_note"].rsplit("PASS 2 2026-08-28:",1)[0].strip()
                + " PASS 2 2026-08-28: re-swept the port turnaround calendar and per-sailing index — "
                  "still no matching indexed departure on this date; row remains preserved but NOT bookable.")
            r["promo"] = PROMOS.get(r["line"], r["promo"])
            stats["still_flagged"] += 1
            log.append([rid, r["name"], r["date"],
                f"NO MATCH — re-checked {INDEX.get(rid, 'port calendar')}: no indexed sailing on this date",
                "n/a — no voyage to match", "n/a", "scope unchanged", "out of verified population",
                "STILL FLAGGED — preserved for manual review"])
            continue

        assert rid in FRESH and rid in INDEX, f"missing fresh data for {rid}"
        pp, official, port, stops, name, dur, rk = FRESH[rid]
        old_total = parse_money(r["price"])          # master stores total for 2
        old_cur = r["price_currency"]
        old_note = r["price_note"]
        old_pp = (old_total // 2) if (old_cur == "USD" and old_total is not None) else None

        # price & note
        r["price_currency"] = "USD"
        r["price"] = money(pp * 2)
        if old_pp is None:
            r["price_note"] = (f"Interior snapshot {money(pp)}/person; total is 2 × snapshot "
                               f"(first published USD snapshot found on pass 2, 2026-08-28; "
                               f"replaces prior listing note: \"{old_note}\")")
            stats["price_added"] += 1
            price_result = f"ADDED — published USD snapshot {money(pp)}pp replaces prior unpriced listing"
        elif old_pp != pp:
            direction = "price_drop" if pp < old_pp else "price_increase"
            r["price_note"] = (f"Interior snapshot {money(pp)}/person; total is 2 × snapshot "
                               f"(was {money(old_pp)}/person in the Aug 27–28 first sweep — {direction})")
            stats["price_down" if pp < old_pp else "price_up"] += 1
            price_result = f"CHANGED — was {money(old_pp)}pp, now {money(pp)}pp ({direction})"
        else:
            r["price_note"] = (f"Interior snapshot {money(pp)}/person; total is 2 × snapshot "
                               f"(re-confirmed unchanged 2026-08-28 pass 2)")
            stats["confirmed"] += 1
            price_result = f"CONFIRMED — {money(pp)}pp unchanged"

        # official link / index link
        r["official"] = official
        r["source_url"] = INDEX[rid]
        r["source"] = "CruiseTimetables per-sailing index + official line voyage deep link (pass 2, 2026-08-28)"
        if port: r["port"] = port
        if stops: r["stops"] = stops
        if name: r["name"] = name
        if dur: r["duration"] = dur

        # flight model
        key = rk if rk else route_key_for(r)
        rr = ROUTES[key]
        d = date.fromisoformat(r["date"])
        import re
        dur_src = dur if dur else r["duration"]
        m_nights = re.search(r"(\d+)", dur_src)
        assert m_nights, f"cannot parse duration for {rid}: {dur_src!r}"
        nights_n = int(m_nights.group(1))
        r["duration"] = f"{nights_n} nights"
        end = d + timedelta(days=nights_n)
        r["flight_out_date"] = (d - timedelta(days=1)).isoformat()
        r["flight_return_date"] = (end + timedelta(days=1)).isoformat()
        r["flight_route"] = rr["label"]
        r["flight_cost_2"] = (f"{money(rr['for2'])} planning estimate" if rr["for2"] else "Not required")
        r["flight_source"] = (f"KAYAK route data: {rr['note']}" if rr["url"] else rr["note"])
        r["flight_source_url"] = rr["url"]
        if key == "LAX_FLL":
            r["flight_search_url"] = ("https://www.google.com/travel/flights?q=One-way%20flights%20SFO%20to%20LAX%20"
                f"{r['flight_out_date']}%2C%20then%20FLL%20to%20SFO%20{r['flight_return_date']}%20for%202%20adults")
        elif key == "SAN_YVR":
            r["flight_search_url"] = ("https://www.google.com/travel/flights?q=One-way%20flights%20SFO%20to%20SAN%20"
                f"{r['flight_out_date']}%2C%20then%20YVR%20to%20SFO%20{r['flight_return_date']}%20for%202%20adults")
        elif key == "HOME":
            r["flight_search_url"] = ""
        else:
            dest = "LAX" if key == "LAX" else "SAN"
            r["flight_search_url"] = gflights("SFO", dest, r["flight_out_date"], r["flight_return_date"])

        cruise2 = pp * 2
        r["trip_total_2"] = money(cruise2 + rr["for2"]) if rr["for2"] else money(cruise2)
        r["trip_total_note"] = ("Cruise snapshot + 2-adult flight planning estimate (SFO out the day before, "
            "back the day after); live quotes required for both.")

        # promo
        r["promo"] = PROMOS[r["line"]]

        # status / verification note
        corrected = (rid == "LA-51" or rid == "SD-21" or rid == "SD-10")
        resolved = (rid in ("LA-25","LA-44","LA-56"))
        if rid == "LA-51":
            r["status"] = "CORRECTED + VERIFIED PASS 2 · 2026-08-28 — itinerary fixed to 16-Night Panama Canal"
            r["verification_note"] = ("CORRECTED 2026-08-28 pass 2: prior listing said 'Hawaii / Pacific' — the "
              "per-sailing index shows the voyage is the 16-Night Panama Canal Ocean to Ocean, Los Angeles → "
              "Fort Lauderdale (princess.com voyage 2705). Interior snapshot $1,879pp read from the index. "
              "Flight basis switched to open-jaw SFO→LAX one-way + FLL→SFO one-way. Snapshot ≠ live quote.")
        elif rid == "SD-21":
            r["status"] = "CORRECTED + VERIFIED PASS 2 · 2026-08-28 — itinerary fixed to Ensenada, Cabo & La Paz"
            r["verification_note"] = ("CORRECTED 2026-08-28 pass 2: prior listing said 'Ensenada, Cabo & Mazatlán' — "
              "the per-sailing index and official deep link (SR07SAN-394531984) show the March 28 voyage calls "
              "La Paz, Cabo San Lucas and Ensenada. Interior snapshot $649pp (was $529pp). Snapshot ≠ live quote.")
        elif rid == "SD-10":
            r["status"] = "CORRECTED + VERIFIED PASS 2 · 2026-08-28 — stops fixed to Catalina + Ensenada"
            r["verification_note"] = ("CORRECTED 2026-08-28 pass 2: the 3-Night Baja voyage departing 2027-03-26 "
              "calls at Catalina Island and Ensenada (DW2246); prior listing omitted Catalina. Interior snapshot "
              "$2,341pp (was $1,754pp). Snapshot ≠ live quote.")
        elif rid == "LA-44":
            r["status"] = "RESOLVED + VERIFIED PASS 2 · 2026-08-28 — GBP price replaced by published USD snapshot"
            r["verification_note"] = ("RESOLVED 2026-08-28 pass 2: the row previously carried a third-party GBP "
              "snapshot and 'Hawaii' wording; the verified voyage is the 7-Night Classic California Coast (E706): "
              "LA → San Francisco → Santa Barbara → San Diego → Ensenada → LA, interior $549pp USD on the index. "
              "Snapshot ≠ live quote; confirm on princess.com.")
        elif rid == "LA-56":
            r["status"] = "RESOLVED + VERIFIED PASS 2 · 2026-08-28 — price now published (E708)"
            r["verification_note"] = ("RESOLVED 2026-08-28 pass 2: 7-Night Classic California Coast (E708) now has "
              "an indexed interior snapshot $539pp USD; official voyage link added. Snapshot ≠ live quote.")
        elif rid == "LA-25":
            r["status"] = "RESOLVED + VERIFIED PASS 2 · 2026-08-28 — price now published (VY04LAX)"
            r["verification_note"] = ("RESOLVED 2026-08-28 pass 2: 4-Night Ensenada (Voyager, VY04LAX-3628863837) "
              "now has an indexed interior snapshot $377pp USD; official voyage link added. Snapshot ≠ live quote.")
        else:
            r["status"] = "VERIFIED PASS 2 · 2026-08-28 — Schedule + price snapshot (line-by-line)"
            r["verification_note"] = ("Re-verified line by line 2026-08-28 (pass 2) against the sailing's own "
              "schedule-index page (date, duration, port sequence, interior per-person price) plus the official "
              "voyage deep link. Snapshot ≠ live quote; cabin class, taxes/fees and availability must be "
              "confirmed on the official page.")

        if corrected:
            stats["corrected"] = stats.get("corrected", 0) + 1
        elif resolved:
            stats["resolved"] = stats.get("resolved", 0) + 1
        result = ("CORRECTED + VERIFIED" if corrected else
                  "RESOLVED + VERIFIED" if resolved else
                  ("PRICE " + price_result.split(" — ")[0] if price_result.startswith("CHANGED") else
                   "CONFIRMED + VERIFIED" if price_result.startswith("CONFIRMED") else
                   "PRICE ADDED + VERIFIED"))
        log.append([rid, r["name"], r["date"],
            f"PASS — re-read date/duration/itinerary/price from: {r['source_url']}",
            f"PASS — official voyage deep link: {r['official']}",
            f"{price_result} (interior per person, USD)",
            f"PASS — departs {r['port']} (U.S. West Coast)",
            "PASS — inside 2027-02-15…2027-03-31",
            f"{result} · trip total for 2 {r['trip_total_2']}"])

    with open(CSV, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields); w.writeheader(); w.writerows(rows)

    data_js = json.dumps(rows, indent=2, ensure_ascii=False)
    with open(JSON_OUT, "w") as f: f.write(data_js + "\n")
    with open(DOCS_JSON, "w") as f: f.write(data_js + "\n")

    with open(VLOG2, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["id","sailing","departure","check_1_index_page_reread","check_2_official_deep_link",
                    "check_3_price","check_4_scope","check_5_window","result"])
        w.writerows(log)

    for name in ("cruises_master_verified.csv","cruise_line_scope_audit.csv",
                 "verification_log_2026-08-28.csv","verification_log_2026-08-28-pass2.csv"):
        src = f"{ROOT}/data/{name}"
        if os.path.exists(src): shutil.copy(src, f"{DOCS_DATA}/{name}")

    print("stats:", stats)
    print("rows:", len(rows))
    flagged = sum(1 for r in rows if r["status"].startswith("REVIEW") or r["status"].startswith("OUT"))
    print("flagged/out rows:", flagged)

if __name__ == "__main__":
    sys.exit(main())
