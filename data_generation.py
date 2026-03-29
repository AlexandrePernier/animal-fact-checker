import requests
import json
import os
import re
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("API_KEY")

# ─────────────────────────────────────────
# Configuration
# ─────────────────────────────────────────

USEFUL_FIELDS = ['lifespan', 'weight', 'diet', 'top_speed', 'length', 'height']
MIN_USEFUL_FIELDS = 3  # Nombre minimum de champs utiles pour garder un animal

ANIMALS = [
    "Lion", "Tiger", "Elephant", "Giraffe", "Zebra",
    "Cheetah", "Leopard", "Jaguar", "Hyena", "Wolf",
    "Fox", "Bear", "Polar Bear", "Grizzly Bear", "Panda",
    "Red Panda", "Koala", "Kangaroo", "Wallaby", "Sloth",
    "Chimpanzee", "Gorilla", "Orangutan", "Baboon", "Mandrill",
    "Raccoon", "Otter", "Weasel", "Badger", "Skunk",
    "Moose", "Deer", "Elk", "Bison", "Buffalo",
    "Horse", "Donkey", "Camel", "Llama", "Alpaca",
    "Hippopotamus", "Rhinoceros", "Warthog", "Boar", "Pig",
    "Dog", "Cat", "Rabbit", "Hare", "Squirrel",
    "Beaver", "Porcupine", "Mouse", "Rat", "Hamster",
    "Bat", "Hedgehog", "Mole", "Armadillo", "Anteater",
    "Dolphin", "Whale", "Orca", "Seal", "Sea Lion",
    "Walrus", "Shark", "Octopus", "Squid", "Jellyfish",
    "Crab", "Lobster", "Shrimp", "Starfish", "Sea Urchin",
    "Eagle", "Falcon", "Hawk", "Owl", "Parrot",
    "Penguin", "Flamingo", "Peacock", "Swan", "Duck",
    "Chicken", "Goose", "Crow", "Raven",
    "Snake", "Cobra", "Python", "Lizard", "Gecko",
    "Iguana", "Chameleon", "Crocodile", "Alligator", "Turtle"
]

# ─────────────────────────────────────────
# Normalisation des valeurs
# ─────────────────────────────────────────

def extract_max_number(raw_value):
    """Extrait le nombre maximum d'une chaîne."""
    if not raw_value:
        return None
    clean = re.sub(r'\(.*?\)', '', str(raw_value))
    numbers = [float(n.replace(',', '')) for n in re.findall(r'[\d,]+\.?\d*', clean)]
    return max(numbers) if numbers else None


def normalize_weight_kg(raw):
    """Convertit le poids en kg (int)."""
    if not raw:
        return None
    raw = str(raw).lower()

    # Cherche les kg en priorité
    kg_matches = re.findall(r'([\d,\.]+)\s*kg', raw)
    if kg_matches:
        numbers = [float(n.replace(',', '')) for n in kg_matches]
        return int(max(numbers))

    # Convertit les lbs en kg
    lbs_matches = re.findall(r'([\d,\.]+)\s*(?:lbs?|pounds?)', raw)
    if lbs_matches:
        numbers = [float(n.replace(',', '')) for n in lbs_matches]
        return int(max(numbers) * 0.453592)

    # Convertit les tonnes en kg
    tonne_matches = re.findall(r'([\d,\.]+)\s*tonne', raw)
    if tonne_matches:
        numbers = [float(n.replace(',', '')) for n in tonne_matches]
        return int(max(numbers) * 1000)

    return None


def normalize_lifespan_years(raw):
    """Extrait la durée de vie max en années (int)."""
    if not raw:
        return None
    raw = str(raw).lower()
    # Exclut les valeurs en captivité si deux valeurs présentes
    clean = re.sub(r'\(.*?\)', '', raw)
    numbers = [float(n) for n in re.findall(r'[\d\.]+', clean)]
    return int(max(numbers)) if numbers else None


def normalize_speed_mph(raw):
    """Extrait la vitesse max en mph (int)."""
    if not raw:
        return None
    raw = str(raw).lower()
    mph_matches = re.findall(r'([\d\.]+)\s*mph', raw)
    if mph_matches:
        return int(max(float(n) for n in mph_matches))
    kph_matches = re.findall(r'([\d\.]+)\s*(?:kph|km/h)', raw)
    if kph_matches:
        return int(max(float(n) for n in kph_matches) * 0.621371)
    numbers = [float(n) for n in re.findall(r'[\d\.]+', str(raw))]
    return int(max(numbers)) if numbers else None


def normalize_length_cm(raw):
    """Extrait la longueur max en cm (int)."""
    if not raw:
        return None
    raw = str(raw).lower()
    m_matches = re.findall(r'([\d\.]+)\s*m(?:eters?|ètres?)?\b', raw)
    if m_matches:
        return int(max(float(n) for n in m_matches) * 100)
    cm_matches = re.findall(r'([\d\.]+)\s*cm', raw)
    if cm_matches:
        return int(max(float(n) for n in cm_matches))
    ft_matches = re.findall(r'([\d\.]+)\s*(?:ft|feet)', raw)
    if ft_matches:
        return int(max(float(n) for n in ft_matches) * 30.48)
    in_matches = re.findall(r'([\d\.]+)\s*in(?:ches?)?', raw)
    if in_matches:
        return int(max(float(n) for n in in_matches) * 2.54)
    return None


def normalize_height_cm(raw):
    """Extrait la hauteur max en cm (int)."""
    return normalize_length_cm(raw)


def normalize_diet(raw):
    """Normalise le régime alimentaire."""
    if not raw:
        return None
    valid = ["Carnivore", "Herbivore", "Omnivore", "Insectivore"]
    for v in valid:
        if v.lower() in str(raw).lower():
            return v
    return None


# ─────────────────────────────────────────
# Image Wikipedia
# ─────────────────────────────────────────

HEADERS = {"User-Agent": "AnimalFactApp/1.0 (educational project)"}

def get_thumbnail_from_title(page_title):
    """Récupère le thumbnail Wikipedia d'un article par son titre."""
    try:
        url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{page_title.replace(' ', '_')}"
        res = requests.get(url, headers=HEADERS, timeout=5)
        if res.status_code == 200:
            data = res.json()
            if "thumbnail" in data:
                return data["thumbnail"]["source"]
    except Exception:
        pass
    return None


def get_image(animal_name):
    """
    Récupère l'image Wikipedia de l'animal.
    Stratégie :
      1. Cherche directement par nom exact
      2. Si pas de thumbnail, cherche via l'API de recherche Wikipedia
      3. Si toujours rien, retourne None (pas de fallback aléatoire)
    """
    # Étape 1 — recherche directe par nom exact
    image = get_thumbnail_from_title(animal_name)
    if image:
        return image

    # Étape 2 — recherche Wikipedia pour trouver le bon titre d'article
    try:
        search_url = "https://en.wikipedia.org/w/api.php"
        params = {
            "action": "query",
            "list": "search",
            "srsearch": f"{animal_name} animal",
            "format": "json",
            "srlimit": 3  # On prend les 3 premiers résultats
        }
        res = requests.get(search_url, params=params, headers=HEADERS, timeout=5)
        results = res.json().get("query", {}).get("search", [])

        for result in results:
            title = result["title"]
            image = get_thumbnail_from_title(title)
            if image:
                print(f"    🔍 '{animal_name}' → found via search: '{title}'")
                return image

    except Exception:
        pass

    # Étape 3 — aucune image trouvée
    print(f"    ⚠️  No image found for '{animal_name}'")
    return None


# ─────────────────────────────────────────
# Validation
# ─────────────────────────────────────────

def is_useful(normalized):
    """Vérifie que l'animal a assez de champs utiles."""
    fields = ['lifespan_years', 'weight_kg', 'diet', 'top_speed_mph', 'length_cm', 'height_cm']
    count = sum(1 for f in fields if normalized.get(f) is not None)
    return count >= MIN_USEFUL_FIELDS


# ─────────────────────────────────────────
# Pipeline principal
# ─────────────────────────────────────────

def process_animal(name):
    """Appelle l'API, normalise et valide un animal."""
    res = requests.get(
        f'https://api.api-ninjas.com/v1/animals?name={name}',
        headers={'X-Api-Key': API_KEY},
        timeout=10
    )

    if res.status_code != 200 or not res.json():
        print(f"  ❌ API error for {name}")
        return None

    animal = res.json()[0]
    charac = animal.get("characteristics", {})

    normalized = {
        "name": animal["name"],
        "diet": normalize_diet(charac.get("diet")),
        "lifespan_years": normalize_lifespan_years(charac.get("lifespan")),
        "weight_kg": normalize_weight_kg(charac.get("weight")),
        "top_speed_mph": normalize_speed_mph(charac.get("top_speed")),
        "length_cm": normalize_length_cm(charac.get("length")),
        "height_cm": normalize_height_cm(charac.get("height")),
        "image": get_image(animal["name"])
    }

    if not is_useful(normalized):
        print(f"  ⚠️  Skipped {name} (not enough data)")
        return None

    print(f"  ✅ {name} — {sum(1 for f in ['diet','lifespan_years','weight_kg','top_speed_mph','length_cm','height_cm'] if normalized.get(f))} fields")
    return normalized


def main():
    animals_data = []
    skipped = []

    for name in ANIMALS:
        result = process_animal(name)
        if result:
            animals_data.append(result)
        else:
            skipped.append(name)

    with open("animals.json", "w", encoding="utf-8") as f:
        json.dump(animals_data, f, indent=2, ensure_ascii=False)

    print(f"\n✅ Done — {len(animals_data)} animals saved, {len(skipped)} skipped")
    if skipped:
        print(f"⚠️  Skipped: {', '.join(skipped)}")

    no_image = [a["name"] for a in animals_data if not a.get("image")]
    if no_image:
        print(f"🖼️  No image found for: {', '.join(no_image)}")

if __name__ == "__main__":
    main()