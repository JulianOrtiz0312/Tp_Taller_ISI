import pytest

from myapp.models.user import UserRole
from myapp.services.user_service import register_user


@pytest.fixture
def seed_users(app):
    with app.app_context():
        admin_1 = register_user(
            name="Admin Uno",
            email="admin1@unrc.edu.ar",
            password="password123",
            role=UserRole.ADMIN,
        )
        general_1 = register_user(
            name="Usuario Uno",
            email="user1@unrc.edu.ar",
            password="password123",
            role=UserRole.GENERAL,
        )
        general_2 = register_user(
            name="Usuario Dos",
            email="user2@unrc.edu.ar",
            password="password123",
            role=UserRole.GENERAL,
        )
        return {
            "admin_1_id": admin_1.id,
            "general_1_id": general_1.id,
            "general_2_id": general_2.id,
        }


def _login(client, user_id: int):
    with client.session_transaction() as sess:
        sess["user_id"] = user_id


def test_admin_can_assign_role_successfully(client, seed_users):
    _login(client, seed_users["admin_1_id"])
    target_id = seed_users["general_1_id"]

    response = client.patch(
        f"/api/users/{target_id}/role",
        json={"role": "admin"},
    )

    assert response.status_code == 200
    data = response.get_json()
    assert data["id"] == target_id
    assert data["role"] == "admin"


def test_non_admin_cannot_assign_role(client, seed_users):
    _login(client, seed_users["general_1_id"])
    target_id = seed_users["general_2_id"]

    response = client.patch(
        f"/api/users/{target_id}/role",
        json={"role": "admin"},
    )

    assert response.status_code == 403


def test_unauthenticated_user_cannot_assign_role(client, seed_users):
    target_id = seed_users["general_1_id"]

    response = client.patch(
        f"/api/users/{target_id}/role",
        json={"role": "admin"},
    )

    assert response.status_code == 401


def test_restricted_functions_only_accessible_by_admins(client, seed_users):
    # Sin sesión -> 401
    resp_unauth = client.get("/api/users/admin/maintenance")
    assert resp_unauth.status_code == 401

    # Usuario general -> 403
    _login(client, seed_users["general_1_id"])
    resp_general = client.get("/api/users/admin/maintenance")
    assert resp_general.status_code == 403

    # Administrador -> 200
    _login(client, seed_users["admin_1_id"])
    resp_admin = client.get("/api/users/admin/maintenance")
    assert resp_admin.status_code == 200
    assert resp_admin.get_json()["total_users"] == 3


def test_assign_role_to_nonexistent_user_returns_404(client, seed_users):
    _login(client, seed_users["admin_1_id"])

    response = client.patch(
        "/api/users/99999/role",
        json={"role": "admin"},
    )

    assert response.status_code == 404


def test_assign_invalid_role_returns_400(client, seed_users):
    _login(client, seed_users["admin_1_id"])
    target_id = seed_users["general_1_id"]

    response = client.patch(
        f"/api/users/{target_id}/role",
        json={"role": "superadmin"},
    )

    assert response.status_code == 400


def test_multiple_admins_can_exchange_roles(client, seed_users):
    admin_1_id = seed_users["admin_1_id"]
    general_1_id = seed_users["general_1_id"]
    general_2_id = seed_users["general_2_id"]

    # 1. Admin 1 promueve a Usuario 1 a Admin
    _login(client, admin_1_id)
    resp_promote = client.patch(
        f"/api/users/{general_1_id}/role",
        json={"role": "admin"},
    )
    assert resp_promote.status_code == 200

    # 2. Ahora el nuevo Admin (general_1) cambia el rol de Usuario 2 y degrada a Admin 1
    _login(client, general_1_id)
    resp_promote_2 = client.patch(
        f"/api/users/{general_2_id}/role",
        json={"role": "admin"},
    )
    assert resp_promote_2.status_code == 200

    resp_demote_1 = client.patch(
        f"/api/users/{admin_1_id}/role",
        json={"role": "general"},
    )
    assert resp_demote_1.status_code == 200
    assert resp_demote_1.get_json()["role"] == "general"
