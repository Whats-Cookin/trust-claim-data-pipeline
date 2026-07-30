"""Mappings from Open Food Facts label tags and rating fields to LinkedTrust claim semantics."""

# Certification mappings: OFF label tag -> (certifier URL, display name, aspect)
CERTIFICATION_MAPPINGS = {
    "en:organic": {
        "subject": "https://www.usda.gov/topics/organic",
        "name": "USDA Organic",
        "aspect": "certification:organic",
    },
    "en:eu-organic": {
        "subject": "https://agriculture.ec.europa.eu/farming/organic-farming_en",
        "name": "EU Organic",
        "aspect": "certification:organic",
    },
    "en:fair-trade": {
        "subject": "https://www.fairtrade.net",
        "name": "Fair Trade",
        "aspect": "certification:fair-trade",
    },
    "en:rainforest-alliance": {
        "subject": "https://www.rainforest-alliance.org",
        "name": "Rainforest Alliance",
        "aspect": "certification:environment",
    },
}

# Rating mappings: OFF field name -> (system URL, display name, aspect, grade-to-stars mapping)
RATING_MAPPINGS = {
    "nutriscore_grade": {
        "subject": "https://world.openfoodfacts.org/nutriscore",
        "name": "Nutri-Score",
        "aspect": "nutrition",
        "stars": {"a": 5, "b": 4, "c": 3, "d": 2, "e": 1},
    },
    "ecoscore_grade": {
        "subject": "https://world.openfoodfacts.org/ecoscore",
        "name": "Eco-Score",
        "aspect": "environment",
        "stars": {"a": 5, "b": 4, "c": 3, "d": 2, "e": 1},
    },
    "nova_group": {
        "subject": "https://world.openfoodfacts.org/nova",
        "name": "NOVA",
        "aspect": "nutrition:processing",
        "stars": {1: 5, 2: 4, 3: 2, 4: 1},
    },
}
