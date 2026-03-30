from flask import Flask, render_template, jsonify, request, session
import random
import os
import json
import logging
from dotenv import load_dotenv
from config import Config
from models import db, Score
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

load_dotenv()

# ─────────────────────────────────────────
# Logging
# ─────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
)
logger = logging.getLogger(__name__)

# ─────────────────────────────────────────
# App
# ─────────────────────────────────────────

app = Flask(__name__)
app.config.from_object(Config)
app.secret_key = os.getenv("SECRET_KEY")

db.init_app(app)

with app.app_context():
    db.create_all()

# ─────────────────────────────────────────
# Rate limiting
# ─────────────────────────────────────────

limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=["200 per day", "50 per hour"],
    storage_uri="memory://",
)

# ─────────────────────────────────────────
# Données animaux
# ─────────────────────────────────────────

with open("animals.json") as f:
    animal_cache = json.load(f)
    logger.info(f"Loaded {len(animal_cache)} animals from cache")

# Chargement des traductions
with open("static/locales/en.json", encoding="utf-8") as f:
    translations_en = json.load(f)
with open("static/locales/fr.json", encoding="utf-8") as f:
    translations_fr = json.load(f)

def get_translations():
    lang = request.headers.get("Accept-Language", "en")[:2]
    return translations_fr if lang == "fr" else translations_en

def tr_value(trans, value):
    """Traduit une valeur (diet, habitat...) selon la langue."""
    return trans["values"].get(value, value)

def tr_animal(trans, name):
    """Traduit un nom d'animal."""
    return trans["animals"].get(name, name)

def tr_label(trans, field):
    clean = field.replace("_years","").replace("_mph","").replace("_cm","").replace("_kg","")
    entry = trans["questions"].get(clean, {})
    if isinstance(entry, dict):
        return entry.get("text", clean), entry.get("gender", "f")
    return entry, "f"

def get_preposition(animal_name):
    voyelles = "AEIOUÀÂÄÉÈÊËÎÏÔÙÛÜŒaeiouàâäéèêëîïôùûüœ"
    if animal_name[0] in voyelles:
        return "de l'"
    return "du "

# Champs exploitables et leurs unités d'affichage
FIELD_CONFIG = {
    "diet":           {"label": "diet",         "unit": "", "type": "text",
                       "options": ["Carnivore", "Herbivore", "Omnivore", "Insectivore"]},
    "skin_type":      {"label": "skin type",    "unit": "", "type": "text",
                       "options": ["Fur", "Feathers", "Scales", "Shell", "Hair", "Smooth", "Spikes", "Leather"]},
    "habitat":        {"label": "habitat",      "unit": "", "type": "text",
                       "options": ["Forest", "Ocean", "Desert", "Grassland", "Rainforest", "Tundra", "Savannah", "Mountains"]},
    "group_behavior": {"label": "group behavior","unit": "", "type": "text",
                       "options": ["Solitary", "Herd", "Pack", "Pride", "Colony", "Flock", "Troop"]},
    "lifestyle":      {"label": "lifestyle",    "unit": "", "type": "text",
                       "options": ["Nocturnal", "Diurnal", "Crepuscular"]},
    "animal_type":    {"label": "type",         "unit": "", "type": "text",
                       "options": ["Mammal", "Bird", "Reptile", "Fish", "Amphibian", "Insect", "Arachnid"]},
    "lifespan_years": {"label": "lifespan",     "unit": "years", "type": "number"},
    "weight_kg":      {"label": "weight",       "unit": "kg",    "type": "number"},
    "top_speed_mph":  {"label": "top speed",    "unit": "km/h",  "type": "number"},
    "length_cm":      {"label": "length",       "unit": "cm",    "type": "number"},
    "height_cm":      {"label": "height",       "unit": "cm",    "type": "number"},
}

DIET_OPTIONS = ["Carnivore", "Herbivore", "Omnivore", "Insectivore"]


def modify_value(field, real_value):
    """Génère une valeur fausse mais crédible."""
    config = FIELD_CONFIG.get(field, {})

    if config.get("type") == "text":
        options = [o for o in config.get("options", []) if o.lower() != str(real_value).lower()]
        return random.choice(options) if options else real_value

    factor = random.choice([
        random.uniform(0.4, 0.75),
        random.uniform(1.3, 2.0)
    ])
    fake = int(real_value * factor)
    if fake == real_value:
        fake = real_value + random.choice([-1, 1]) * max(1, int(real_value * 0.1))
    return max(1, fake)


# ─────────────────────────────────────────
# Routes
# ─────────────────────────────────────────

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/question")
@limiter.limit("60 per minute")
def question():
    queue = session.get("queue", [])
    if not queue:
        queue = list(range(len(animal_cache)))
        random.shuffle(queue)

    index = queue.pop(0)
    session["queue"] = queue
    animal = animal_cache[index]

    possible = [
        field for field in FIELD_CONFIG
        if animal.get(field) is not None
    ]

    if not possible:
        logger.warning(f"Animal '{animal.get('name')}' has no usable fields")
        return jsonify({"error": "No usable data"}), 422

    field = random.choice(possible)
    config = FIELD_CONFIG[field]
    real_value = animal[field]
    is_true = random.choice([True, False])

    # Conversion mph → km/h pour l'affichage
    if field == "top_speed_mph":
        real_value = int(real_value * 1.60934)

    if config["type"] == "text":
        display = real_value if is_true else modify_value(field, real_value)
    else:
        display = real_value if is_true else modify_value(field, real_value)

# ── Traductions ──────────────────────────────
    trans = get_translations()
    lang = request.headers.get("Accept-Language", "en")[:2]
    animal_name = tr_animal(trans, animal["name"])
    label, gender = tr_label(trans, field)
    verb = "est-il" if gender == "m" else "est-elle"

    if lang == "fr":
        prep = get_preposition(animal_name)
        if config["type"] == "text":
            display_translated = tr_value(trans, str(display))
            question_text = f"{label} {prep}{animal_name} est-il \"{display_translated}\" ?"
        else:
            question_text = f"{label} {prep}{animal_name} {verb} {display} {config['unit']} ?"
    else:
        if config["type"] == "text":
            display_translated = tr_value(trans, str(display))
            question_text = f"{label} of the {animal_name} {display_translated}?"
        else:
            question_text = f"{label} of the {animal_name} {display} {config['unit']}?"

    session["correct_answer"] = is_true
    session["real_value"] = f"{tr_value(trans, str(real_value))} {config['unit']}".strip() \
        if config["type"] == "text" else f"{real_value} {config['unit']}".strip()
    # ─────────────────────────────────────────────

    logger.info(f"Question — '{animal['name']}' / {field}")

    return jsonify({
        "question": question_text,
        "real": session["real_value"],
        "display": str(display_translated if config["type"] == "text" else display),
        "image": animal.get("image")
    })

@app.route("/submit_score", methods=["POST"])
@limiter.limit("10 per minute")
def submit_score():
    username = session.get("username")
    score = session.get("score", 0)

    if not username:
        logger.warning("submit_score called without active session")
        return jsonify({"error": "No session"}), 400

    top_scores = Score.query.order_by(Score.score.desc()).limit(10).all()

    if len(top_scores) < 10 or score > top_scores[-1].score:
        new_score = Score(username=username, score=score)
        db.session.add(new_score)
        db.session.commit()

        top_scores = Score.query.order_by(Score.score.desc()).all()
        if len(top_scores) > 10:
            for s in top_scores[10:]:
                db.session.delete(s)
        db.session.commit()

        logger.info(f"Score saved — user: {username}, score: {score}")
    else:
        logger.info(f"Score not saved (too low) — user: {username}, score: {score}")

    return jsonify({"message": "Score processed"})


@app.route("/leaderboard")
@limiter.limit("30 per minute")
def leaderboard():
    top_scores = Score.query.order_by(Score.score.desc()).limit(10).all()
    logger.info(f"Leaderboard — {len(top_scores)} entries")
    return jsonify({"top10": [s.to_dict() for s in top_scores]})


@app.route("/start", methods=["POST"])
@limiter.limit("20 per minute")
def start():
    data = request.json
    username = data.get("username")

    if not username:
        logger.warning("start called without username")
        return jsonify({"error": "Username required"}), 400

    # Mélange tous les animaux et stocke leurs index en session
    indices = list(range(len(animal_cache)))
    random.shuffle(indices)

    session.clear()
    session["username"] = username
    session["score"] = 0
    session["streak"] = 0
    session["lives"] = 3
    session["queue"] = indices  # ← queue des animaux à venir

    logger.info(f"Game started — user: {username}")
    return jsonify({"message": "Game started"})


@app.route("/answer", methods=["POST"])
@limiter.limit("60 per minute")
def answer():
    if session.get("lives", 0) <= 0:
        return jsonify({"error": "Game over"}), 400

    data = request.json
    user_choice = data.get("answer")
    correct = session.get("correct_answer")

    if correct is None:
        logger.warning("answer called without active question")
        return jsonify({"error": "No question"}), 400

    is_correct = (user_choice == correct)

    if is_correct:
        session["streak"] += 1
        points = 1
        if session["streak"] >= 5:
            points = 3
        elif session["streak"] >= 3:
            points = 2
        session["score"] += points
    else:
        session["streak"] = 0
        session["lives"] -= 1

    logger.info(
        f"Answer — user: {session.get('username')}, "
        f"correct: {is_correct}, score: {session['score']}, lives: {session['lives']}"
    )

    return jsonify({
        "correct": is_correct,
        "score": session["score"],
        "streak": session["streak"],
        "lives": session["lives"],
        "real": session.get("real_value")
    })


# ─────────────────────────────────────────
# Gestion d'erreurs globale
# ─────────────────────────────────────────

@app.errorhandler(404)
def not_found(e):
    logger.warning(f"404 — {request.path}")
    return jsonify({"error": "Resource not found"}), 404


@app.errorhandler(405)
def method_not_allowed(e):
    logger.warning(f"405 — {request.method} {request.path}")
    return jsonify({"error": "Method not allowed"}), 405


@app.errorhandler(429)
def rate_limit_exceeded(e):
    logger.warning(f"429 — Rate limit exceeded for {get_remote_address()}")
    return jsonify({"error": "Too many requests, please slow down"}), 429


@app.errorhandler(500)
def internal_error(e):
    logger.error(f"500 — {e}")
    return jsonify({"error": "Internal server error"}), 500


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0")