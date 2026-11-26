from myapp.extensions import db
from myapp.models.user import User


def _create_user(name: str, email: str, password: str) -> User:
    user = User(name=name, email=email)
    user.set_password(password)
    db.session.add(user)
    db.session.commit()
    return user


def test_update_user_email_and_password_success(app, client):
    with app.app_context():
        user = _create_user("Braian", "braian@unrc.edu.ar", "ClaveVieja123")
        user_id = user.id

    response = client.patch(
        f"/api/users/{user_id}",
        headers={"X-User-Id": str(user_id)},
        json={
            "email": "braian.nuevo@unrc.edu.ar",
            "current_password": "ClaveVieja123",
            "new_password": "ClaveNueva456",
        },
    )

    assert response.status_code == 200
    assert response.json["email"] == "braian.nuevo@unrc.edu.ar"
    with app.app_context():
        updated = db.session.get(User, user_id)
        assert updated.check_password("ClaveNueva456")


def test_cannot_modify_other_user_account(app, client):
    with app.app_context():
        owner = _create_user("Owner", "owner@unrc.edu.ar", "Pass123")
        attacker = _create_user("Other", "other@unrc.edu.ar", "Pass123")
        owner_id, attacker_id = owner.id, attacker.id

    response = client.patch(
        f"/api/users/{owner_id}",
        headers={"X-User-Id": str(attacker_id)},
        json={"email": "hacked@unrc.edu.ar"},
    )
    assert response.status_code == 403


def test_reject_empty_or_same_email(app, client):
    with app.app_context():
        user = _create_user("Ana", "ana@unrc.edu.ar", "Pass123")
        user_id = user.id

    res_empty = client.patch(
        f"/api/users/{user_id}",
        headers={"X-User-Id": str(user_id)},
        json={"email": "   "},
    )
    res_same = client.patch(
        f"/api/users/{user_id}",
        headers={"X-User-Id": str(user_id)},
        json={"email": "ana@unrc.edu.ar"},
    )
    assert res_empty.status_code == 400
    assert res_same.status_code == 400


def test_reject_duplicate_email(app, client):
    with app.app_context():
        u1 = _create_user("User1", "u1@unrc.edu.ar", "Pass123")
        _create_user("User2", "u2@unrc.edu.ar", "Pass123")
        u1_id = u1.id

    response = client.patch(
        f"/api/users/{u1_id}",
        headers={"X-User-Id": str(u1_id)},
        json={"email": "u2@unrc.edu.ar"},
    )
    assert response.status_code == 400


def test_reject_password_change_without_valid_current_password(app, client):
    with app.app_context():
        user = _create_user("Luis", "luis@unrc.edu.ar", "Pass123")
        user_id = user.id

    response = client.patch(
        f"/api/users/{user_id}",
        headers={"X-User-Id": str(user_id)},
        json={"current_password": "Incorrecta", "new_password": "NuevaPass789"},
    )
    assert response.status_code == 400


def test_reject_empty_or_same_new_password(app, client):
    with app.app_context():
        user = _create_user("Mia", "mia@unrc.edu.ar", "Pass123")
        user_id = user.id

    res_empty = client.patch(
        f"/api/users/{user_id}",
        headers={"X-User-Id": str(user_id)},
        json={"current_password": "Pass123", "new_password": ""},
    )
    res_same = client.patch(
        f"/api/users/{user_id}",
        headers={"X-User-Id": str(user_id)},
        json={"current_password": "Pass123", "new_password": "Pass123"},
    )
    assert res_empty.status_code == 400
    assert res_same.status_code == 400


def test_cannot_modify_user_id(app, client):
    with app.app_context():
        user = _create_user("Leo", "leo@unrc.edu.ar", "Pass123")
        user_id = user.id

    response = client.patch(
        f"/api/users/{user_id}",
        headers={"X-User-Id": str(user_id)},
        json={"id": 999, "email": "leo.nuevo@unrc.edu.ar"},
    )
    assert response.status_code == 400
