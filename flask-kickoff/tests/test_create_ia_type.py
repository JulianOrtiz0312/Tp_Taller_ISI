import pytest

from myapp.extensions import db
from myapp.models.ia_type import IAType
from myapp.models.user import UserRole
from myapp.services.ia_service import list_ia_types
from myapp.services.user_service import register_user


@pytest.fixture
def seed_users(app):
    with app.app_context():
        admin = register_user(
            name="Admin",
            email="admin@unrc.edu.ar",
            password="password123",
        )
        admin.role = UserRole.ADMIN

        regular_user = register_user(
            name="Claudio",
            email="claudio@unrc.edu.ar",
            password="password123",
        )
        db.session.commit()
        return {"admin_id": admin.id, "user_id": regular_user.id}


def _login_session(client, user_id: int):
    with client.session_transaction() as sess:
        sess["user_id"] = user_id


def test_create_ia_web_admin_success(client, app, seed_users):
    _login_session(client, seed_users["admin_id"])

    response = client.post("/ia/create", data={"name": "Gemini"})

    assert response.status_code == 302

    with app.app_context():
        saved = db.session.scalar(db.select(IAType).where(IAType.name == "gemini"))
        assert saved is not None
        assert saved.is_active is True

        active_ias = list_ia_types(only_active=True)
        assert any(ia.id == saved.id for ia in active_ias)


def test_create_ia_web_unauthenticated_redirects(client):
    response = client.post("/ia/create", data={"name": "Gemini"})
    assert response.status_code == 302


def test_create_ia_web_non_admin_forbidden(client, app, seed_users):
    _login_session(client, seed_users["user_id"])

    response = client.post("/ia/create", data={"name": "Gemini"})

    assert response.status_code == 403

    with app.app_context():
        assert db.session.scalar(db.select(IAType)) is None


def test_create_ia_web_duplicate_fails(client, app, seed_users):
    _login_session(client, seed_users["admin_id"])

    first = client.post("/ia/create", data={"name": "ChatGPT"})
    assert first.status_code == 302

    # Prueba duplicado con distintas mayúsculas y espacios
    second = client.post("/ia/create", data={"name": "  chatgpt  "})
    assert second.status_code == 400

    with app.app_context():
        all_ias = list_ia_types()
        assert len(all_ias) == 1


def test_create_ia_web_empty_name_fails(client, seed_users):
    _login_session(client, seed_users["admin_id"])

    response = client.post("/ia/create", data={"name": "   "})
    assert response.status_code == 400


def test_create_multiple_ias_do_not_interfere(client, app, seed_users):
    _login_session(client, seed_users["admin_id"])

    assert client.post("/ia/create", data={"name": "Gemini"}).status_code == 302
    assert client.post("/ia/create", data={"name": "ChatGPT"}).status_code == 302

    with app.app_context():
        active_ias = list_ia_types(only_active=True)
        names = {ia.name for ia in active_ias}
        assert names == {"gemini", "chatgpt"}