import re
from difflib import SequenceMatcher
from geopy.geocoders import Nominatim

CHENNAI_AREAS = [
    # --- CENTRAL CHENNAI ---
    "T-Nagar", "Thyagaraya Nagar", "Anna Nagar", "Mylapore", "Alwarpet", "Teynampet",
    "Nungambakkam", "Egmore", "Royapettah", "Kilpauk", "Kodambakkam", "Vadapalani",
    "Ashok Nagar", "West Mambalam", "Saidapet", "Choolaimedu", "Chetpet", "Gopalapuram",
    "Triplicane", "Chepauk", "Chintadripet", "Purusawalkam", "Sowcarpet", "Broadway",
    "Parrys", "Central", "Royapuram", "Vepery", "Choolai", "Aminjikarai", "Arumbakkam",

    # --- SOUTH CHENNAI & IT CORRIDOR ---
    "Adyar", "Velachery", "Besant Nagar", "Thiruvanmiyur", "Kotturpuram", "Guindy",
    "Ekkattuthangal", "Nandanam", "Sholinganallur", "Thoraipakkam", "Perungudi",
    "Karapakkam", "Palavakkam", "Kottivakkam", "Neelankarai", "Injambakkam", "Madipakkam",
    "Ullagaram", "Puzhuthivakkam", "Pallikaranai", "Medavakkam", "Keelkattalai", 
    "Kovilambakkam", "Sithalapakkam", "Perumbakkam", "Taramani", "Kanagam",

    # --- SOUTH SUBURBS & EXTENSIONS ---
    "Tambaram", "East Tambaram", "West Tambaram", "Chromepet", "Pallavaram", "Alandur",
    "Nanganallur", "Adambakkam", "Chitlapakkam", "Selaiyur", "Sembakkam", "Rajakilpakkam",
    "Vandalur", "Perungalathur", "Mudichur", "Gowrivakkam", "Hasthinapuram",

    # --- WEST CHENNAI & INDUSTRIAL HUBS ---
    "Ambattur", "Avadi", "Koyambedu", "Maduravoyal", "Porur", "Valasaravakkam",
    "Virugambakkam", "Saligramam", "Ramapuram", "Mugalivakkam", "Manapakkam",
    "Nandambakkam", "Nerkundram", "Nolambur", "Mogappair", "Padi", "Korattur",
    "Villivakkam", "Ayanavaram", "Kolathur", "Thiru-Vi-Ka-Nagar", "Iyyappanthanthangal",
    "Poonamallee", "Kattupakkam", "Mangadu", "Vanagaram",

    # --- NORTH CHENNAI ---
    "Tondiarpet", "Washermanpet", "Old Washermanpet", "New Washermanpet", "Vyasarpadi",
    "Perambur", "Sembium", "Erukkanchery", "Kodungaiyur", "Madhavaram", "Mathur",
    "Puzhal", "Thiruvottiyur", "Ennore", "Ernavoor", "Manali", "Chinnasekkadu",
    "Kasimedu", "Korukkupet", "Basin Bridge", "Mint"
]

geolocator = Nominatim(user_agent="my_civic_pulse_app_v1")

def find_best_fuzzy_match(word):
    best_match = None
    highest_score = 0.0
    
    clean_word = word.strip().lower().replace("-", " ")
    
    for area in CHENNAI_AREAS:
        clean_area = area.lower().replace("-", " ")
        score = SequenceMatcher(None, clean_word, clean_area).ratio()
        
        if score > highest_score:
            highest_score = score
            best_match = area
            
    if highest_score >= 0.70:
        return best_match
    return None


def misaligned_location(text_phrase):
    found_area = "Unknown"
    lat = 13.0827
    lng = 80.2707

    # Directly check the clean phrase sent by main.py
    clean_candidate = text_phrase.strip(".,!?()")

    matched_zone = find_best_fuzzy_match(clean_candidate)
    if matched_zone:
        found_area = matched_zone
        
        try:
            location = geolocator.geocode(f"{found_area}, Chennai, India")
            if location:
                lat = location.latitude
                lng = location.longitude
        except Exception as e:
            print(f"Geocoding Error for '{found_area}': {e}")

    return {
        "location_name": found_area,
        "latitude": lat,
        "longitude": lng
    }


def landmark_to_location(text_phrase):
    search_query = f"{text_phrase}, Chennai, India"

    try:
        location = geolocator.geocode(search_query, addressdetails=True)
        
        if location:
            raw_address = location.raw.get("address", {})

            detected_zone = (
                raw_address.get("suburb") or
                raw_address.get("neighbourhood") or
                raw_address.get("city_district") or
                "Central Chennai"
            )
            
            return {
                "landmark_name": text_phrase,
                "assigned_zone": detected_zone,
                "latitude": location.latitude,
                "longitude": location.longitude
            }
        else:
            return None
            
    except Exception as e:
        print(f"An error occurred during lookup: {e}")
        return None