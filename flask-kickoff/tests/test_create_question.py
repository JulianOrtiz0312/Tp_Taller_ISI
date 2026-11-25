import pytest

from myapp.extensions import db
from myapp.models.category import Category
from myapp.models.question import Question
from myapp.services.user_service import register_user


@pytest.fixture
def seed_user_and_category(app):
    with app.app_context():
        user = register_user(
            name="Julián",
            email="julian@unrc.edu.ar",
            password="password123",
        )
        category = Category(name="Programación")
        db.session.add(category)
        db.session.commit()
        return {"user_id": user.id, "category_id": category.id}


def _login_session(client, user_id: int):
    with client.session_transaction() as sess:
        sess["user_id"] = user_id


# --- TESTS API (/api/questions) ---


def test_create_question_api_success(client, app, seed_user_and_category):
    user_id = seed_user_and_category["user_id"]
    category_id = seed_user_and_category["category_id"]
    _login_session(client, user_id)

    response = client.post(
        "/api/questions",
        json={
            "titulo": "¿Cómo funciona Blueprint en Flask?",
            "cuerpo": "Necesito entender cómo se registran las rutas en create_app.",
            "category_id": category_id,
        },
    )

    assert response.status_code == 201
    data = response.get_json()
    assert data["titulo"] == "¿Cómo funciona Blueprint en Flask?"
    assert data["autor"] == user_id
    assert data["categoria"] == category_id

    with app.app_context():
        saved = db.session.scalar(
            db.select(Question).where(
                Question.titulo == "¿Cómo funciona Blueprint en Flask?"
            )
        )
        assert saved is not None


def test_create_question_api_unauthenticated(client, seed_user_and_category):
    response = client.post(
        "/api/questions",
        json={
            "titulo": "Pregunta sin login",
            "cuerpo": "Debería fallar con 401.",
            "category_id": seed_user_and_category["category_id"],
        },
    )
    assert response.status_code == 401


def test_create_question_api_empty_title(client, seed_user_and_category):
    _login_session(client, seed_user_and_category["user_id"])

    response = client.post(
        "/api/questions",
        json={
            "titulo": "   ",
            "cuerpo": "Cuerpo válido",
            "category_id": seed_user_and_category["category_id"],
        },
    )
    assert response.status_code == 400


def test_create_question_api_invalid_category(client, seed_user_and_category):
    _login_session(client, seed_user_and_category["user_id"])

    response = client.post(
        "/api/questions",
        json={
            "titulo": "Pregunta con categoría falsa",
            "cuerpo": "Cuerpo válido",
            "category_id": 9999,
        },
    )
    assert response.status_code == 400


def test_create_question_api_duplicate_title_same_user(client, seed_user_and_category):
    _login_session(client, seed_user_and_category["user_id"])
    payload = {
        "titulo": "Pregunta repetida",
        "cuerpo": "Primer intento",
        "category_id": seed_user_and_category["category_id"],
    }

    first = client.post("/api/questions", json=payload)
    assert first.status_code == 201

    second = client.post("/api/questions", json=payload)
    assert second.status_code == 400


# --- TESTS WEB (/questions/create) ---


def test_create_question_web_success(client, app, seed_user_and_category):
    user_id = seed_user_and_category["user_id"]
    category_id = seed_user_and_category["category_id"]
    _login_session(client, user_id)

    response = client.post(
        "/questions/create",
        data={
            "titulo": "Consulta desde la web",
            "cuerpo": "Probando el formulario HTML.",
            "category_id": str(category_id),
        },
    )

    assert response.status_code == 302

    with app.app_context():
        saved = db.session.scalar(
            db.select(Question).where(Question.titulo == "Consulta desde la web")
        )
        assert saved is not None
        assert saved.user_id == user_id
        assert saved.category_id == category_id


def test_create_question_web_invalid_body(client, seed_user_and_category):
    _login_session(client, seed_user_and_category["user_id"])

    response = client.post(
        "/questions/create",
        data={
            "titulo": "Título válido",
            "cuerpo": "",
            "category_id": str(seed_user_and_category["category_id"]),
        },
    )

    assert response.status_code == 400
