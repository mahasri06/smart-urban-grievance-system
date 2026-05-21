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


# --- THE MAIN GATEWAY ---
if __name__ == "__main__":
    print("🚀 Civic Pulse Location Engine Activated!")
    
    # Test Case A: Should trip Approach 1 instantly using your fuzzy match rules
    post_a = "Massive traffic gridlock over near velacheryy junction!"
    result_a = pipeline_runner(post_a)
    print("📦 FINAL PACKET SAVED TO DATABASE:")
    print(result_a)
    
    print("-" * 60)
    time.sleep(1) # Safety gap
    
    # Test Case B: Will fail Approach 1, but succeed on Approach 2 with the landmark lookup
    post_b = "Water pipe leakage flooding roads right near Phoenix Mall"
    result_b = pipeline_runner(post_b)
    print("📦 FINAL PACKET SAVED TO DATABASE:")
    print(result_b)