from flask import Blueprint, jsonify, request, session
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError

from myapp.extensions import db
from myapp.models import Category, User, UserRole

categories_bp = Blueprint("categories", __name__, url_prefix="/categories")


def _get_current_admin() -> tuple[User | None, int | None]:
    user_id = session.get("user_id")
    if not user_id:
        return None, 401

    user = db.session.get(User, user_id)
    if user is None:
        return None, 401

    if user.role != UserRole.ADMIN:
        return None, 403

    return user, None


@categories_bp.post("")
def create_category():
    _, auth_error = _get_current_admin()
    if auth_error == 401:
        return jsonify({"error": "Debes iniciar sesion para crear categorias."}), 401
    if auth_error == 403:
        return jsonify({"error": "Solo un administrador puede crear categorias."}), 403

    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        return jsonify(
            {"error": "El cuerpo de la solicitud debe ser un JSON valido."}
        ), 400

    raw_name = payload.get("name")
    if not isinstance(raw_name, str) or not raw_name.strip():
        return jsonify(
            {"error": "El nombre de la categoria no puede estar vacio."}
        ), 400

    name = raw_name.strip()

    existing = Category.query.filter(func.lower(Category.name) == name.lower()).first()
    if existing:
        return jsonify({"error": "Ya existe una categoria con ese nombre."}), 409

    category = Category(name=name)
    db.session.add(category)

    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return jsonify({"error": "Ya existe una categoria con ese nombre."}), 409

    return jsonify(category.to_dict()), 201
