from flask import Blueprint, jsonify, request
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError

from myapp.extensions import db
from myapp.models import Category

categories_bp = Blueprint("categories", __name__, url_prefix="/categories")

def _is_admin(payload: dict) -> bool:
    header_admin = request.headers.get("X-Admin", "").strip().lower() in {"1", "true", "yes"}
    body_admin = bool(payload.get("is_admin")) or (isinstance(payload.get("role"), str) and payload.get("role").strip().lower() == "admin")
    return header_admin or body_admin

@categories_bp.post("")
def create_category():
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        return jsonify({"error": "El cuerpo de la solicitud debe ser un JSON valido."}), 400

    if not _is_admin(payload):
        return jsonify({"error": "Solo un administrador puede crear categorias."}), 403

    raw_name = payload.get("name")
    if not isinstance(raw_name, str) or not raw_name.strip():
        return jsonify({"error": "El nombre de la categoria no puede estar vacio."}), 400

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
