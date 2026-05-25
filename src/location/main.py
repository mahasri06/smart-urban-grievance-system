import time
from location.location_processor import misaligned_location, landmark_to_location
from location.llm_parser import extract_locations_with_llm

def pipeline_runner(text):
    
    # phase 1: immediately found
    local_match = misaligned_location(text.lower())
    if local_match["location_name"] != "Unknown":
        return {
            "display_name": local_match["location_name"],
            "latitude": local_match["latitude"],
            "longitude": local_match["longitude"]
        }
        
    # phase 2: LLM extraction
    llm_locations = extract_locations_with_llm(text)

    for loc in llm_locations:
        if len(loc) < 3:
            continue

        if "chennai" in loc.lower():
            query_string = loc
        else:
            query_string = f"{loc}, Chennai"

        time.sleep(1)
        landmark_data = landmark_to_location(query_string)

        if landmark_data:
            osm_type = landmark_data.get("type", "").lower()
            
            if osm_type in ["shop", "amenity", "pub", "restaurant", "cafe", "beauty"]:
                continue

        return {
                "display_name": f"{loc.capitalize()} ({landmark_data.get('assigned_zone', 'Chennai Area')})",
                "latitude": landmark_data["latitude"],
                "longitude": landmark_data["longitude"],
                "method": "Gemini + Nominatim Verified POI"
            }
    
    return {
        "display_name": "General Chennai",
        "latitude": 13.0827,
        "longitude": 80.2707,
        "method": "Default Fallback"
    }