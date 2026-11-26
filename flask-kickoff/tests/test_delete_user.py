import pytest

from myapp.extensions import db
from myapp.models.category import Category
from myapp.models.question import Question
from myapp.models.user import User
from myapp.services.question_service import create_question
from myapp.services.user_service import register_user


@pytest.fixture
def seed_users_and_question(app):
    with app.app_context():
        user_1 = register_user(
            name="Matías",
            email="matias@unrc.edu.ar",
            password="password123",
        )
        user_2 = register_user(
            name="Otro Usuario",
            email="otro@unrc.edu.ar",
            password="password123",
        )
        category = Category(name="Bases de Datos")
        db.session.add(category)
        db.session.commit()

        question = create_question(
            titulo="¿Cómo funciona ON DELETE SET NULL?",
            cuerpo="Quiero que las preguntas persistan al borrar un usuario.",
            user_id=user_1.id,
            category_id=category.id,
        )

        return {
            "user_1_id": user_1.id,
            "user_1_email": user_1.email,
            "user_2_id": user_2.id,
            "question_id": question.id,
        }


def _login(client, user_id: int):
    with client.session_transaction() as sess:
        sess["user_id"] = user_id


def test_user_can_delete_own_account_and_data_leaves_no_trace(
    client, app, seed_users_and_question
):
    user_id = seed_users_and_question["user_1_id"]
    user_email = seed_users_and_question["user_1_email"]
    _login(client, user_id)

    response = client.delete(f"/api/users/{user_id}")

    assert response.status_code == 200

    with client.session_transaction() as sess:
        assert "user_id" not in sess

    with app.app_context():
        assert db.session.get(User, user_id) is None
        by_email = db.session.scalar(db.select(User).where(User.email == user_email))
        assert by_email is None


def test_questions_persist_after_user_deletion(client, app, seed_users_and_question):
    user_id = seed_users_and_question["user_1_id"]
    question_id = seed_users_and_question["question_id"]
    _login(client, user_id)

    response = client.delete(f"/api/users/{user_id}")
    assert response.status_code == 200

    with app.app_context():
        persisted_question = db.session.get(Question, question_id)
        assert persisted_question is not None
        assert persisted_question.titulo == "¿Cómo funciona ON DELETE SET NULL?"
        assert persisted_question.user_id is None


def test_user_cannot_delete_another_users_account(client, app, seed_users_and_question):
    user_1_id = seed_users_and_question["user_1_id"]
    user_2_id = seed_users_and_question["user_2_id"]
    _login(client, user_1_id)

    response = client.delete(f"/api/users/{user_2_id}")
    assert response.status_code == 403

    with app.app_context():
        assert db.session.get(User, user_2_id) is not None


def test_delete_nonexistent_user_returns_404(client, seed_users_and_question):
    _login(client, seed_users_and_question["user_1_id"])

    response = client.delete("/api/users/99999")
    assert response.status_code == 404


def test_unauthenticated_user_cannot_delete_account(client, seed_users_and_question):
    user_1_id = seed_users_and_question["user_1_id"]

    response = client.delete(f"/api/users/{user_1_id}")
    assert response.status_code == 401
