import pandas as pd
import random
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CSV_PATH = os.path.join(BASE_DIR, "data", "real_complaints.csv")

# Synthetic templates for conversational complaints
TEMPLATES = {
    "Noise & Pollution": [
        ("My neighbors have been blasting loud music all night and I cannot sleep.", "LOW"),
        ("There is constant construction noise coming from the site next door at 3 AM.", "MEDIUM"),
        ("Someone is running a noisy generator outside my window, it is unbearable.", "LOW"),
        ("The factory down the road is emitting thick black smoke and smells like chemicals.", "HIGH"),
        ("A group of people are partying in the street and yelling very loudly.", "LOW"),
        ("Air quality is terrible today, smog everywhere and it is hard to breathe.", "HIGH"),
        ("Car alarms have been going off for 3 hours straight on my block.", "LOW")
    ],
    "Roads & Traffic": [
        ("There is a massive pothole on Main Street that just ruined my tire.", "MEDIUM"),
        ("Traffic is completely gridlocked at the intersection because the lights are out.", "HIGH"),
        ("A delivery truck is double parked and blocking the entire lane.", "LOW"),
        ("The street signs are completely faded and causing accidents.", "MEDIUM"),
        ("Someone left a broken down car in the middle of the road.", "MEDIUM"),
        ("There is a severe traffic jam stretching for miles due to an accident.", "HIGH"),
        ("A commercial van is parked overnight in a residential zone.", "LOW"),
        ("The sidewalk is completely blocked by construction debris.", "LOW")
    ],
    "Public Infrastructure": [
        ("The water pipes burst on our street and it is flooding the entire road.", "HIGH"),
        ("We haven't had electricity for 12 hours, the entire neighborhood is pitch black.", "HIGH"),
        ("The public park equipment is broken and dangerous for children.", "MEDIUM"),
        ("There is a massive water leak coming from the main line.", "HIGH"),
        ("The streetlights are all broken and it feels very unsafe at night.", "MEDIUM"),
        ("The garbage hasn't been collected in weeks and the smell is awful.", "MEDIUM"),
        ("Someone dumped a huge pile of trash in the alleyway.", "LOW"),
        ("The bus shelter glass was shattered and there is glass everywhere.", "MEDIUM")
    ]
}

# Complex templates with overlapping terminology, sarcasm, ambiguity, and misspellings
COMPLEX_TEMPLATES = {
    "Noise & Pollution": [
        ("The traffic from the new park construction is so loud I can't think. It's a disaster.", "MEDIUM"), # 'traffic', 'park' usually in other categories
        ("Great job fixing the road, now the trucks rattle my house and make an ungodly racket.", "MEDIUM"),
        ("There is literal garbage burning in the alley, it smells toxic.", "HIGH"), # 'garbage' usually public infrastructure
        ("Smog from the highway is completely unbarable today. Very bad.", "HIGH"), # misspelling
        ("i cnt sleep bcoz of the water pump noise from the broken pipes!!", "MEDIUM") # abbreviations, 'water pipes' overlap
    ],
    "Roads & Traffic": [
        ("The park entrance is completely blocked by a collapsed wall, forcing cars into the wrong lane.", "HIGH"), # 'park', 'wall'
        ("So much noise from the cars stuck in the pothole. Please fix.", "LOW"), # 'noise'
        ("The heavy rain completely flooded the intersection and now no one can move.", "HIGH"), # 'flooded' usually public infrastructure
        ("ther is a huge bump on th road dat just borke my car", "MEDIUM"), # misspellings
        ("Amazing infrastructure you have here, it took me 3 hours to move 2 miles.", "LOW") # sarcasm, 'infrastructure'
    ],
    "Public Infrastructure": [
        ("The noise from the broken power transformer is sparking and driving us crazy.", "HIGH"), # 'noise' overlap
        ("Cars keep crashing into the broken street light pole that fell over.", "HIGH"), # 'cars', 'crashing' overlap
        ("The overflowing trash is spilling into the road and stopping traffic.", "MEDIUM"), # 'road', 'traffic'
        ("we hav no watr for 3 days plz help", "HIGH"), # heavy misspellings
        ("The park looks like a warzone, shattered glass everywhere.", "MEDIUM")
    ]
}

def generate_synthetic_data(num_samples=3000):
    new_rows = []
    for _ in range(num_samples):
        # 50% chance to use simple template, 50% chance to use complex template
        if random.random() > 0.5:
            source = TEMPLATES
        else:
            source = COMPLEX_TEMPLATES
            
        category = random.choice(list(source.keys()))
        text, urgency = random.choice(source[category])
        
        # Add slight variations to make text messy
        if random.random() > 0.5:
            text = text.lower()
        if random.random() > 0.8:
            text = text + " Please fix it ASAP!!!"
        if random.random() > 0.8:
            text = "Hey! " + text
            
        new_rows.append({"text": text, "category": category, "urgency": urgency})
        
    return pd.DataFrame(new_rows)

if __name__ == "__main__":
    print("Generating 3000 synthetic conversational and complex complaints...")
    new_df = generate_synthetic_data(3000)
    
    if os.path.exists(CSV_PATH):
        old_df = pd.read_csv(CSV_PATH)
        combined_df = pd.concat([old_df, new_df], ignore_index=True)
        # Shuffle
        combined_df = combined_df.sample(frac=1).reset_index(drop=True)
        combined_df.to_csv(CSV_PATH, index=False)
        print(f"Augmented dataset saved to {CSV_PATH}. Total rows: {len(combined_df)}")
    else:
        print(f"Could not find {CSV_PATH}!")
