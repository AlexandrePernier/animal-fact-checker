from flask import Flask, render_template, jsonify
import random
import re
import os
import json
from dotenv import load_dotenv 
from config import Config
from models import db, Score
from flask import request 
from flask import session

load_dotenv()  

app = Flask(__name__)
app.config.from_object(Config)

db.init_app(app)
app.secret_key = os.getenv("SECRET_KEY")
with app.app_context():
    db.create_all()
    
with open("animals.json") as f:
    animal_cache = json.load(f)

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

    # 🎯 valeurs plus crédibles
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

    # Cherche l'unité = dernier mot alphabétique de la chaîne
    unit_match = re.search(r'([a-zA-Z]+)\s*$', clean.strip())
    unit = unit_match.group(1) if unit_match else ""

    return f"{max(numbers)} {unit}".strip()

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/question")
def question():
    data = get_animal()
    if not data:
        return jsonify({"error": "API error"})

    charac = data.get('characteristics', {})

    possible = [c for c in ['lifespan', 'weight', 'diet'] if c in charac]
    if not possible:
        return jsonify({"error": "No usable data"})

    cat = random.choice(possible)
    real_val = get_clean_max(charac[cat])

    is_true = random.choice([True, False])

    if cat == "diet":
        display = real_val if is_true else modify_value(cat, real_val)
        question = f"Is the diet of the {data['name']} {display}?"
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
            
        
        
        question = f"Is the max {cat} of the {data['name']} {display}?"
    
    image_url = data.get("image")
    
    session["correct_answer"] = is_true
    session["real_value"] = real_val

    return jsonify({
        "question": question,
        "real": real_val,
        "display": display,
        "image": image_url
    })
    
@app.route("/submit_score", methods=["POST"])
def submit_score():
    username = session.get("username")
    score = session.get("score", 0)

    if not username:
        return jsonify({"error": "No session"}), 400

    # récupérer top 10
    top_scores = Score.query.order_by(Score.score.desc()).limit(10).all()

    # si pas encore 10 scores OU meilleur que le dernier
    if len(top_scores) < 10 or score > top_scores[-1].score:

        # ajouter score
        new_score = Score(username=username, score=score)
        db.session.add(new_score)
        db.session.commit()

        # re-fetch et nettoyer si >10
        top_scores = Score.query.order_by(Score.score.desc()).all()

        if len(top_scores) > 10:
            for s in top_scores[10:]:
                db.session.delete(s)

        db.session.commit()

    return jsonify({"message": "Score processed"})

@app.route("/leaderboard")
def leaderboard():
    top_scores = Score.query.order_by(Score.score.desc()).limit(10).all()

    return jsonify({
        "top10": [s.to_dict() for s in top_scores]
    })

@app.route("/start", methods=["POST"])
def start():
    data = request.json
    username = data.get("username")

    if not username:
        return jsonify({"error": "Username required"}), 400

    session.clear()
    session["username"] = username
    session["score"] = 0
    session["streak"] = 0
    session["lives"] = 3

    return jsonify({"message": "Game started"})

@app.route("/answer", methods=["POST"])
def answer():
    
    if session.get("lives", 0) <= 0:
        return jsonify({"error": "Game over"})

    data = request.json
    user_choice = data.get("answer")

    correct = session.get("correct_answer")

    if correct is None:
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

    return jsonify({
        "correct": is_correct,
        "score": session["score"],
        "streak": session["streak"],
        "lives": session["lives"],
        "real": session.get("real_value")
    })

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0")