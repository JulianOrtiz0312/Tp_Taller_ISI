from flask import Blueprint, jsonify, request, session

from myapp.decorators import admin_required
from myapp.services.user_service import (
    DuplicateEmailError,
    UserServiceError,
    assign_user_role,
    list_users,
    register_user,
    update_user_data,
)

api_users_bp = Blueprint("api_users", __name__, url_prefix="/api/users")


@api_users_bp.get("")
def get_users():
    users = list_users()
    return jsonify([u.to_dict() for u in users]), 200


@api_users_bp.post("/register")
def api_register():
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        return jsonify(
            {"error": "El cuerpo de la solicitud debe ser un JSON valido."}
        ), 400

    raw_name = payload.get("name")
    raw_email = payload.get("email")
    raw_password = payload.get("password")

    if not all(isinstance(v, str) for v in (raw_name, raw_email, raw_password)):
        return jsonify(
            {"error": "Los campos name, email y password deben ser texto."}
        ), 400

    try:
        user = register_user(name=raw_name, email=raw_email, password=raw_password)
        return jsonify(user.to_dict()), 201
    except DuplicateEmailError as exc:
        return jsonify({"error": str(exc)}), 409
    except UserServiceError as exc:
        return jsonify({"error": str(exc)}), 400


@api_users_bp.patch("/<int:user_id>")
def patch_user(user_id: int):
    data = request.get_json(silent=True) or {}

    if "id" in data or "id_usuario" in data:
        return jsonify({"error": "No se puede modificar el ID del usuario."}), 400

    acting_user_id = session.get("user_id") or request.headers.get(
        "X-User-Id", type=int
    )
    if acting_user_id is None:
        return jsonify({"error": "Usuario no autenticado."}), 401

    try:
        updated_user = update_user_data(
            acting_user_id=acting_user_id,
            target_user_id=user_id,
            new_email=data.get("email"),
            current_password=data.get("current_password"),
            new_password=data.get("new_password"),
        )
        return jsonify(updated_user.to_dict()), 200
    except PermissionError as exc:
        return jsonify({"error": str(exc)}), 403
    except LookupError as exc:
        return jsonify({"error": str(exc)}), 404
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400


@api_users_bp.patch("/<int:user_id>/role")
@admin_required
def patch_user_role(user_id: int):
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        return (
            jsonify({"error": "El cuerpo de la solicitud debe ser un JSON válido."}),
            400,
        )

    raw_role = payload.get("role")
    if not isinstance(raw_role, str):
        return jsonify(
            {"error": "El campo 'role' es obligatorio y debe ser texto."}
        ), 400

    try:
        updated_user = assign_user_role(target_user_id=user_id, new_role=raw_role)
        return jsonify(updated_user.to_dict()), 200
    except LookupError as exc:
        return jsonify({"error": str(exc)}), 404
    except UserServiceError as exc:
        return jsonify({"error": str(exc)}), 400


@api_users_bp.get("/admin/maintenance")
@admin_required
def admin_maintenance():
    users = list_users()
    return (
        jsonify(
            {
                "status": "ok",
                "message": "Acceso concedido a herramientas de mantenimiento.",
                "total_users": len(users),
            }
        ),
        200,
    )
