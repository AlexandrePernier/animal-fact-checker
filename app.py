from flask import Flask, render_template, jsonify
import random
import re
import os
import json
import logging
from dotenv import load_dotenv
from config import Config
from models import db, Score
from flask import request, session
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


def get_animal():
    return random.choice(animal_cache)


def modify_value(category, real_value):
    if category == 'diet':
        options = ["Carnivore", "Herbivore", "Omnivore", "Insectivore"]
        if real_value in options:
            options.remove(real_value)
        return random.choice(options)

    clean_value = re.sub(r'\(.*\)', '', real_value)
    numbers = [int(n) for n in re.findall(r'\d+', clean_value)]

    if not numbers:
        return real_value

    max_val = max(numbers)

    factor = random.choice([
        random.uniform(0.5, 0.8),
        random.uniform(1.2, 1.8)
    ])

    fake_max = int(max_val * factor)
    return str(fake_max)


def get_clean_max(raw_value):
    clean = re.sub(r'\(.*\)', '', raw_value)
    numbers = [int(n) for n in re.findall(r'\d+', clean)]

    if not numbers:
        return raw_value

    unit_match = re.search(r'([a-zA-Z]+)\s*$', clean.strip())
    unit = unit_match.group(1) if unit_match else ""

    return f"{max(numbers)} {unit}".strip()


# ─────────────────────────────────────────
# Routes
# ─────────────────────────────────────────

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/question")
@limiter.limit("60 per minute")
def question():
    data = get_animal()
    if not data:
        logger.error("Failed to get animal from cache")
        return jsonify({"error": "API error"}), 500

    charac = data.get('characteristics', {})
    possible = [c for c in ['lifespan', 'weight', 'diet', 'top_speed', 'length', 'height'] if c in charac]

    if not possible:
        logger.warning(f"Animal '{data.get('name')}' has no usable characteristics")
        return jsonify({"error": "No usable data"}), 422

    cat = random.choice(possible)
    real_val = get_clean_max(charac[cat])
    is_true = random.choice([True, False])

    if cat == "diet":
        display = real_val if is_true else modify_value(cat, real_val)
        question_text = f"Is the diet of the {data['name']} {display}?"
    else:
        clean_val = re.sub(r'\(.*\)', '', real_val)
        numbers = [int(n) for n in re.findall(r'\d+', clean_val)]
        max_val = max(numbers) if numbers else 0

        unit_match = re.search(r'\d+\s*([a-zA-Z]+)', clean_val)
        unit = unit_match.group(1) if unit_match else ""

        if is_true:
            display = f"{max_val} {unit}".strip()
        else:
            fake = modify_value(cat, real_val)
            display = f"{fake} {unit}".strip()

        question_text = f"Is the max {cat} of the {data['name']} {display}?"

    image_url = data.get("image")

    session["correct_answer"] = is_true
    session["real_value"] = real_val

    logger.info(f"Question generated for '{data['name']}' — category: {cat}")

    return jsonify({
        "question": question_text,
        "real": real_val,
        "display": display,
        "image": image_url
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
    logger.info(f"Leaderboard requested — {len(top_scores)} entries returned")
    return jsonify({"top10": [s.to_dict() for s in top_scores]})


@app.route("/start", methods=["POST"])
@limiter.limit("20 per minute")
def start():
    data = request.json
    username = data.get("username")

    if not username:
        logger.warning("start called without username")
        return jsonify({"error": "Username required"}), 400

    session.clear()
    session["username"] = username
    session["score"] = 0
    session["streak"] = 0
    session["lives"] = 3

    logger.info(f"Game started for user: {username}")
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
    logger.warning(f"404 - Route not found: {request.path}")
    return jsonify({"error": "Resource not found"}), 404


@app.errorhandler(405)
def method_not_allowed(e):
    logger.warning(f"405 - Method not allowed: {request.method} {request.path}")
    return jsonify({"error": "Method not allowed"}), 405


@app.errorhandler(429)
def rate_limit_exceeded(e):
    logger.warning(f"429 - Rate limit exceeded for {get_remote_address()}")
    return jsonify({"error": "Too many requests, please slow down"}), 429


@app.errorhandler(500)
def internal_error(e):
    logger.error(f"500 - Internal server error: {e}")
    return jsonify({"error": "Internal server error"}), 500


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0")