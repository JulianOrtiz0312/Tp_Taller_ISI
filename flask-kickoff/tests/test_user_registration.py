from myapp.extensions import db
from myapp.models.user import User, UserRole


def test_register_user_web_success(client, app):
    response = client.post(
        "/users/register",
        data={
            "name": "Matías",
            "email": "Matias@UNRC.edu.ar",
            "password": "secreto123",
        },
    )
    assert response.status_code == 302

    with app.app_context():
        user = db.session.scalar(
            db.select(User).where(User.email == "matias@unrc.edu.ar")
        )
        assert user is not None
        assert user.name == "Matías"
        assert user.role == UserRole.GENERAL
        assert user.check_password("secreto123")
        assert user.password_hash != "secreto123"


def test_register_user_duplicate_email_api(client):
    client.post(
        "/api/users/register",
        json={"name": "Ana", "email": "ana@unrc.edu.ar", "password": "password123"},
    )
    response = client.post(
        "/api/users/register",
        json={"name": "Ana 2", "email": "ana@unrc.edu.ar", "password": "password456"},
    )
    assert response.status_code == 409


def test_register_user_short_password_api(client):
    response = client.post(
        "/api/users/register",
        json={"name": "Juan", "email": "juan@unrc.edu.ar", "password": "123"},
    )
    assert response.status_code == 400


def test_register_user_api_success(client):
    response = client.post(
        "/api/users/register",
        json={"name": "Ada", "email": "ada@unrc.edu.ar", "password": "password123"},
    )
    assert response.status_code == 201
    data = response.get_json()
    assert data["email"] == "ada@unrc.edu.ar"
    assert data["role"] == "general"
