import random
import requests
import json
import os
from dotenv import load_dotenv  

load_dotenv()  

def get_image(animal_name):
    try:
        formatted_name = animal_name.replace(" ", "_")

        url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{formatted_name}"

        headers = {
            "User-Agent": "AnimalFactApp/1.0"
        }

        res = requests.get(url, headers=headers)
        print(res)
        if res.status_code == 200:
            data = res.json()
            print(data)
            if "thumbnail" in data:
                return data["thumbnail"]["source"]

        # fallback image
        return f"https://picsum.photos/400/300?random={random.randint(1,1000)}"

    except:
        return f"https://picsum.photos/400/300?random={random.randint(1,1000)}"
    
animals_data = []
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

for name in ANIMALS:
    res = requests.get(
        f'https://api.api-ninjas.com/v1/animals?name={name}',
        headers={'X-Api-Key': os.getenv("API_KEY")}
    )

    if res.status_code != 200:
        continue

    data = res.json()
    if not data:
        continue

    animal = data[0]

    animals_data.append({
        "name": animal["name"],
        "characteristics": animal.get("characteristics", {}),
        "image": get_image(animal["name"])  # 🔥 AJOUT
    })
    print(name)

with open("animals.json", "w") as f:
    json.dump(animals_data, f)