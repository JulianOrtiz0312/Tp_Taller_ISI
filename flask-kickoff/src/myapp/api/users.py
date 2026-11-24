from flask import Blueprint, jsonify, request

from myapp.services.user_service import (
    DuplicateEmailError,
    UserServiceError,
    list_users,
    register_user,
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
