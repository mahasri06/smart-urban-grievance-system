import time
from location_processor import misaligned_location, landmark_to_location

def pipeline_runner(tweet_text):
    
    local_match = misaligned_location(tweet_text)
    
    if local_match["location_name"] != "Unknown / General Chennai":
        return {
            "display_name": local_match["location_name"],
            "latitude": local_match["latitude"],
            "longitude": local_match["longitude"],
            "method": "Fuzzy Area List"
        }
        

    words = tweet_text.split()
    clean_words = [w.strip(".,!?()\"'") for w in words]

    candidates = []
    for i in range(len(clean_words) - 1):
        candidates.append(f"{clean_words[i]} {clean_words[i+1]}")
        
    for phrase in candidates:
        if len(phrase) < 5:
            continue
        
        landmark_data = landmark_to_location(phrase)
        
        if landmark_data:
            return {
                "display_name": f"{phrase} ({landmark_data['assigned_zone']})",
                "latitude": landmark_data["latitude"],
                "longitude": landmark_data["longitude"],
                "method": "Nominatim Landmark POI"
            }
            
        # nominatim: 1 request per second
        time.sleep(1)

    return {
        "display_name": "General Chennai",
        "latitude": 13.0827,
        "longitude": 80.2707,
        "method": "Default Fallback"
    }

