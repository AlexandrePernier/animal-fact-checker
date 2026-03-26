import pytest
from app import app, get_clean_max, modify_value


# ─────────────────────────────────────────
# Configuration du client de test
# ─────────────────────────────────────────

@pytest.fixture
def client():
    app.config["TESTING"] = True
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
    app.config["SECRET_KEY"] = "test-secret-key"

    with app.test_client() as client:
        with app.app_context():
            from models import db
            db.create_all()
        yield client


def start_game(client, username="TestUser"):
    """Helper : démarre une partie et retourne le client avec session active."""
    client.post("/start", json={"username": username})
    return client


# ─────────────────────────────────────────
# Tests /start
# ─────────────────────────────────────────

def test_start_with_username(client):
    res = client.post("/start", json={"username": "Alex"})
    assert res.status_code == 200
    assert res.get_json()["message"] == "Game started"


def test_start_without_username(client):
    res = client.post("/start", json={})
    assert res.status_code == 400
    assert "error" in res.get_json()


# ─────────────────────────────────────────
# Tests /answer
# ─────────────────────────────────────────

def test_answer_correct(client):
    start_game(client)

    with client.session_transaction() as sess:
        sess["correct_answer"] = True
        sess["real_value"] = "10 years"
        sess["streak"] = 0
        sess["score"] = 0
        sess["lives"] = 3

    res = client.post("/answer", json={"answer": True})
    data = res.get_json()

    assert data["correct"] is True
    assert data["score"] == 1
    assert data["streak"] == 1
    assert data["lives"] == 3


def test_answer_wrong(client):
    start_game(client)

    with client.session_transaction() as sess:
        sess["correct_answer"] = True
        sess["real_value"] = "10 years"
        sess["streak"] = 2
        sess["score"] = 2
        sess["lives"] = 3

    res = client.post("/answer", json={"answer": False})
    data = res.get_json()

    assert data["correct"] is False
    assert data["lives"] == 2
    assert data["streak"] == 0


def test_answer_streak_bonus_3(client):
    """Streak de 3 donne 2 points."""
    start_game(client)

    with client.session_transaction() as sess:
        sess["correct_answer"] = True
        sess["real_value"] = "10 years"
        sess["streak"] = 3
        sess["score"] = 0
        sess["lives"] = 3

    res = client.post("/answer", json={"answer": True})
    data = res.get_json()

    assert data["score"] == 2


def test_answer_streak_bonus_5(client):
    """Streak de 5 donne 3 points."""
    start_game(client)

    with client.session_transaction() as sess:
        sess["correct_answer"] = True
        sess["real_value"] = "10 years"
        sess["streak"] = 5
        sess["score"] = 0
        sess["lives"] = 3

    res = client.post("/answer", json={"answer": True})
    data = res.get_json()

    assert data["score"] == 3


def test_answer_game_over(client):
    """Répondre sans vies restantes retourne une erreur."""
    start_game(client)

    with client.session_transaction() as sess:
        sess["lives"] = 0

    res = client.post("/answer", json={"answer": True})
    assert "error" in res.get_json()


def test_answer_no_question(client):
    """Répondre sans question active retourne une erreur."""
    start_game(client)

    with client.session_transaction() as sess:
        sess["lives"] = 3
        # Pas de correct_answer en session

    res = client.post("/answer", json={"answer": True})
    assert res.status_code == 400


# ─────────────────────────────────────────
# Tests /leaderboard
# ─────────────────────────────────────────

def test_leaderboard_empty(client):
    res = client.get("/leaderboard")
    assert res.status_code == 200
    data = res.get_json()
    assert "top10" in data
    assert isinstance(data["top10"], list)


def test_leaderboard_returns_max_10(client):
    """Le leaderboard ne retourne jamais plus de 10 scores."""
    from models import db, Score
    with app.app_context():
        for i in range(15):
            db.session.add(Score(username=f"User{i}", score=i))
        db.session.commit()

    res = client.get("/leaderboard")
    data = res.get_json()
    assert len(data["top10"]) <= 10


# ─────────────────────────────────────────
# Tests /submit_score
# ─────────────────────────────────────────

def test_submit_score_without_session(client):
    res = client.post("/submit_score")
    assert res.status_code == 400
    assert "error" in res.get_json()


# ─────────────────────────────────────────
# Tests fonctions utilitaires
# ─────────────────────────────────────────

def test_get_clean_max_simple():
    assert get_clean_max("10 years") == "10 years"


def test_get_clean_max_range():
    """Doit retourner le max d'une plage de valeurs."""
    result = get_clean_max("5 to 10 years")
    assert result == "10 years"


def test_get_clean_max_with_parentheses():
    """Les parenthèses doivent être ignorées."""
    result = get_clean_max("10 years (in captivity 20)")
    assert result == "10 years"


def test_get_clean_max_no_numbers():
    """Sans chiffre, retourne la valeur brute."""
    assert get_clean_max("unknown") == "unknown"


def test_modify_value_diet():
    """Le régime modifié doit être différent du vrai."""
    result = modify_value("diet", "Carnivore")
    assert result != "Carnivore"
    assert result in ["Herbivore", "Omnivore", "Insectivore"]


def test_modify_value_numeric():
    """La valeur numérique modifiée doit être différente de l'originale."""
    result = modify_value("weight", "100 kg")
    assert result != "100"