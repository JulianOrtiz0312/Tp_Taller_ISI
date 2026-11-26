from functools import wraps

from flask import jsonify, session

from myapp.extensions import db
from myapp.models.user import User, UserRole


def login_required(view_func):
    @wraps(view_func)
    def wrapped_view(*args, **kwargs):
        user_id = session.get("user_id")
        if not user_id:
            return jsonify({"error": "Debes iniciar sesión para continuar."}), 401

        user = db.session.get(User, user_id)
        if user is None:
            session.clear()
            return jsonify({"error": "Sesión inválida o usuario inexistente."}), 401

        return view_func(*args, **kwargs)

    return wrapped_view


def admin_required(view_func):
    @wraps(view_func)
    def wrapped_view(*args, **kwargs):
        user_id = session.get("user_id")
        if not user_id:
            return jsonify({"error": "Debes iniciar sesión para continuar."}), 401

        user = db.session.get(User, user_id)
        if user is None:
            session.clear()
            return jsonify({"error": "Sesión inválida o usuario inexistente."}), 401

        if user.role != UserRole.ADMIN:
            return (
                jsonify(
                    {
                        "error": "Acceso denegado. Se requieren permisos de administrador."
                    }
                ),
                403,
            )

        return view_func(*args, **kwargs)

    return wrapped_view
