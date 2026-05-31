from scraper.processors.filter import is_relevant_cached, detect_categories_cached

tests = [
    'Multiple potholes on roads and streets',
    'There is sewage and stagnant water',
    'Power outage in my area; no electricity',
    'Just a generic post about weather',
]

for t in tests:
    print('TEXT:', t)
    print('  relevant ->', is_relevant_cached(t))
    print('  categories ->', detect_categories_cached(t))
    print()
