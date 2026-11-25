import pytest

from myapp.extensions import db
from myapp.models.category import Category
from myapp.models.question import Question
from myapp.models.user import UserRole
from myapp.services.question_service import create_question
from myapp.services.user_service import register_user


@pytest.fixture
def seed_delete_category_data(app):
    with app.app_context():
        admin = register_user(
            name="Admin",
            email="admin@unrc.edu.ar",
            password="password123",
        )
        admin.role = UserRole.ADMIN

        regular_user = register_user(
            name="Usuario Normal",
            email="usuario@unrc.edu.ar",
            password="password123",
        )

        empty_category = Category(name="Java")
        busy_category = Category(name="HTML")
        db.session.add_all([empty_category, busy_category])
        db.session.commit()

        create_question(
            titulo="¿Como se declaran los arreglos?",
            cuerpo="Consulta sobre arreglos.",
            user_id=regular_user.id,
            category_id=busy_category.id,
        )

        return {
            "admin_id": admin.id,
            "regular_user_id": regular_user.id,
            "empty_category_id": empty_category.id,
            "busy_category_id": busy_category.id,
        }


def _login(client, user_id: int):
    with client.session_transaction() as sess:
        sess["user_id"] = user_id


def test_unauthenticated_cannot_delete_category(client, seed_delete_category_data):
    category_id = seed_delete_category_data["empty_category_id"]

    response = client.delete(
        f"/categories/{category_id}",
        json={"reason": "Sin sesion"},
    )

    assert response.status_code == 401


def test_non_admin_cannot_delete_category(client, app, seed_delete_category_data):
    _login(client, seed_delete_category_data["regular_user_id"])
    category_id = seed_delete_category_data["empty_category_id"]

    response = client.delete(
        f"/categories/{category_id}",
        json={"reason": "Intento no autorizado"},
    )

    assert response.status_code == 403
    with app.app_context():
        assert db.session.get(Category, category_id) is not None


def test_delete_nonexistent_category_returns_404(client, seed_delete_category_data):
    _login(client, seed_delete_category_data["admin_id"])

    response = client.delete(
        "/categories/99999",
        json={"reason": "No existe"},
    )

    assert response.status_code == 404


@pytest.mark.parametrize("payload", [{}, {"reason": ""}, {"reason": "  "}])
def test_delete_category_requires_non_empty_reason(
    client, app, seed_delete_category_data, payload
):
    _login(client, seed_delete_category_data["admin_id"])
    category_id = seed_delete_category_data["empty_category_id"]

    response = client.delete(f"/categories/{category_id}", json=payload)

    assert response.status_code == 400
    with app.app_context():
        assert db.session.get(Category, category_id) is not None


def test_cannot_delete_category_with_associated_questions(
    client, app, seed_delete_category_data
):
    _login(client, seed_delete_category_data["admin_id"])
    category_id = seed_delete_category_data["busy_category_id"]

    response = client.delete(
        f"/categories/{category_id}",
        json={"reason": "Categoria con preguntas"},
    )

    assert response.status_code == 409
    with app.app_context():
        assert db.session.get(Category, category_id) is not None
        assert (
            db.session.scalar(
                db.select(Question).where(Question.category_id == category_id)
            )
            is not None
        )


def test_admin_can_delete_category_without_questions(
    client, app, seed_delete_category_data
):
    _login(client, seed_delete_category_data["admin_id"])
    category_id = seed_delete_category_data["empty_category_id"]

    response = client.delete(
        f"/categories/{category_id}",
        json={"reason": "Categoria duplicada"},
    )

    assert response.status_code == 200
    with app.app_context():
        assert db.session.get(Category, category_id) is None
        remaining_ids = [c.id for c in db.session.scalars(db.select(Category)).all()]
        assert category_id not in remaining_ids
