# what type of incident
CATEGORIES = {

    "EMERGENCY": [
        "fire",
        "collapse",
        "collapsed",
        "explosion",
        "accident",
        "injury",
        "injured",
        "death",
        "died",
        "fatal",
        "unsafe",
        "hazard"
    ],

    "SANITATION": [
        "garbage",
        "trash",
        "waste",
        "dumpyard",
        "sewage",
        "drainage",
        "open drain",
        "blocked drain",
        "overflowing drain",
        "stagnant water",
        "waterlogging",
        "flooding",
        "mosquito",
        "public toilet",
        "dirty toilet",
        "bad smell",
        "stink"
    ],

    "INFRASTRUCTURE": [
        "pothole",
        "bad road",
        "damaged road",
        "broken road",
        "bridge",
        "flyover",
        "footpath",
        "pavement",
        "subway",
        "street light",
        "streetlight",
        "electric pole",
        "transformer",
        "encroachment",
        "illegal construction"
    ],

    "UTILITIES": [
        "power cut",
        "power outage",
        "electricity",
        "eb",
        "tangedco",
        "water supply",
        "water shortage",
        "metro water",
        "water leakage",
        "pipe burst",
        "contaminated water",
        "dirty water"
    ],

    "TRANSPORT": [
        "traffic",
        "traffic jam",
        "signal",
        "traffic signal",
        "bus delay",
        "metro delay",
        "parking issue",
        "illegal parking",
        "road block",
        "road closed"
    ],

    "PUBLIC_HEALTH": [
        "dengue",
        "malaria",
        "dog bite",
        "stray dogs",
        "dog menace",
        "cattle on road",
        "dead animal",
        "pollution",
        "air pollution",
        "smoke",
        "toxic"
    ]
}

# criticality level
INTENT_LEVELS = {

    "LEVEL_1": [
        "noticed",
        "saw",
        "observed",
        "reported",
        "sharing",
        "informing",
        "there is",
        "happened",
        "update"
    ],

    "LEVEL_2": [
        "issue",
        "problem",
        "bad",
        "worst",
        "poor",
        "unsafe",
        "annoying",
        "risk",
        "concern",
        "affected",
        "suffering",
        "delay",
        "unresolved",
        "broken",
        "damaged",
        "overflowing",
        "blocked",
        "leaking"
    ],

    "LEVEL_3": [
        "urgent",
        "emergency",
        "critical",
        "danger",
        "dangerous",
        "help",
        "immediate",
        "sos",
        "distress",
        "crisis",
        "accident",
        "injury",
        "death",
        "fire",
        "collapse",
        "burst",
        "flooded",
        "stuck"
    ]
}

# is it a grievance at all
COMPLAINT_TERMS = [

    "issue",
    "problem",
    "not working",
    "broken",
    "frequent",
    "blocked",
    "overflow",
    "bad",
    "worst",
    "unsafe",
    "delay",
    "power cut",
    "waterlogging",
    "traffic jam"
]

# are they asking a question?
QUESTION_TERMS = [

    "how",
    "what",
    "why",
    "when",
    "where",
    "can i",
    "does anyone",
    "anybody",
    "help regarding",
    "clarification",
    "feedback"
]
