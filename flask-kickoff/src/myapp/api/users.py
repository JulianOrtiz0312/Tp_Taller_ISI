from flask import Blueprint, jsonify, request, session

from myapp.services.user_service import update_user_data

users_api_bp = Blueprint("users_api", __name__, url_prefix="/api/users")


@users_api_bp.patch("/<int:user_id>")
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
