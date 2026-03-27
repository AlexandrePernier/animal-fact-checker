import pytest
from app import app, modify_value, FIELD_CONFIG


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


def test_start_initializes_session(client):
    """La session doit être correctement initialisée après /start."""
    res = client.post("/start", json={"username": "Alex"})
    assert res.status_code == 200


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
    assert res.get_json()["score"] == 2


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
    assert res.get_json()["score"] == 3


def test_answer_game_over(client):
    start_game(client)

    with client.session_transaction() as sess:
        sess["lives"] = 0

    res = client.post("/answer", json={"answer": True})
    assert "error" in res.get_json()


def test_answer_no_question(client):
    start_game(client)

    with client.session_transaction() as sess:
        sess["lives"] = 3

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
    from models import db, Score
    with app.app_context():
        for i in range(15):
            db.session.add(Score(username=f"User{i}", score=i))
        db.session.commit()

    res = client.get("/leaderboard")
    assert len(res.get_json()["top10"]) <= 10


# ─────────────────────────────────────────
# Tests /submit_score
# ─────────────────────────────────────────

def test_submit_score_without_session(client):
    res = client.post("/submit_score")
    assert res.status_code == 400
    assert "error" in res.get_json()


# ─────────────────────────────────────────
# Tests /question
# ─────────────────────────────────────────

def test_question_returns_200(client):
    start_game(client)
    res = client.get("/question")
    assert res.status_code == 200


def test_question_response_structure(client):
    """La réponse de /question doit avoir les bons champs."""
    start_game(client)
    res = client.get("/question")
    data = res.get_json()
    assert "question" in data
    assert "real" in data
    assert "display" in data
    assert "image" in data


# ─────────────────────────────────────────
# Tests modify_value
# ─────────────────────────────────────────

def test_modify_value_diet():
    result = modify_value("diet", "Carnivore")
    assert result != "Carnivore"
    assert result in FIELD_CONFIG["diet"]["options"]


def test_modify_value_skin_type():
    result = modify_value("skin_type", "Fur")
    assert result != "Fur"
    assert result in FIELD_CONFIG["skin_type"]["options"]


def test_modify_value_lifestyle():
    result = modify_value("lifestyle", "Nocturnal")
    assert result != "Nocturnal"
    assert result in FIELD_CONFIG["lifestyle"]["options"]


def test_modify_value_numeric():
    result = modify_value("weight_kg", 100)
    assert result != 100
    assert result > 0


def test_modify_value_numeric_always_positive():
    for _ in range(20):
        result = modify_value("lifespan_years", 5)
        assert result > 0


# ─────────────────────────────────────────
# Tests FIELD_CONFIG
# ─────────────────────────────────────────

def test_field_config_text_fields_have_options():
    """Tous les champs texte doivent avoir des options."""
    for field, config in FIELD_CONFIG.items():
        if config["type"] == "text":
            assert "options" in config, f"{field} missing options"
            assert len(config["options"]) >= 2, f"{field} needs at least 2 options"


def test_field_config_number_fields_have_unit():
    """Tous les champs numériques doivent avoir une unité."""
    for field, config in FIELD_CONFIG.items():
        if config["type"] == "number":
            assert "unit" in config, f"{field} missing unit"