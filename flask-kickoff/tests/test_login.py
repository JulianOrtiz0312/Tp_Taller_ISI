from myapp.extensions import db
from myapp.models.user import User, UserRole


def _create_user(
    app, email="user@unrc.edu.ar", password="password123", role=UserRole.GENERAL
):
    with app.app_context():
        user = User(name="Test User", email=email.lower(), role=role)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        return user.id


def test_login_success_sets_session_and_returns_user(client, app):
    user_id = _create_user(app, email="login@unrc.edu.ar", password="password123")

    response = client.post(
        "/api/login",
        json={"email": " LOGIN@UNRC.edu.ar ", "password": "password123"},
    )
    assert response.status_code == 200
    data = response.get_json()
    assert data["user"]["id"] == user_id
    assert data["user"]["email"] == "login@unrc.edu.ar"
    assert data["user"]["role"] == "general"

    with client.session_transaction() as sess:
        assert sess.get("user_id") == user_id


def test_login_wrong_password_returns_401(client, app):
    _create_user(app, email="login@unrc.edu.ar", password="password123")

    response = client.post(
        "/api/login",
        json={"email": "login@unrc.edu.ar", "password": "wpassword"},
    )
    assert response.status_code == 401
    assert response.get_json() == {"error": "Invalid credentials"}

    with client.session_transaction() as sess:
        assert sess.get("user_id") is None


def test_login_unknown_email_returns_401(client):
    response = client.post(
        "/api/login",
        json={"email": "email@unrc.edu.ar", "password": "password123"},
    )
    assert response.status_code == 401
    assert response.get_json() == {"error": "Invalid credentials"}


def test_login_missing_fields_returns_400(client):
    response = client.post("/api/login", json={"email": "login@unrc.edu.ar"})
    assert response.status_code == 400
    assert response.get_json() == {"error": "Email and password are required"}


def test_login_invalid_json_returns_400(client):
    response = client.post("/api/login", data="no es json", content_type="text/plain")
    assert response.status_code == 400
    assert response.get_json() == {"error": "Invalid JSON body"}
