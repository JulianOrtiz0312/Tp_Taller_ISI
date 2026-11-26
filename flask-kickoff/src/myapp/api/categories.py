from flask import Blueprint, jsonify, request, session
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError

from myapp.extensions import db
from myapp.models import Category, Question, User, UserRole
from myapp.services.category_service import (
    CategoryConflictError,
    CategoryNotFoundError,
    CategoryValidationError,
    update_category,
)

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


@categories_bp.patch("/<int:category_id>")
def patch_category(category_id: int):
    _, auth_error = _get_current_admin()
    if auth_error == 401:
        return jsonify(
            {"error": "Debes iniciar sesion para modificar categorias."}
        ), 401
    if auth_error == 403:
        return jsonify(
            {"error": "Solo un administrador puede modificar categorias."}
        ), 403

    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        return jsonify(
            {"error": "El cuerpo de la solicitud debe ser un JSON valido."}
        ), 400

    if "id" in payload:
        return jsonify({"error": "No se puede modificar el ID de la categoria."}), 400

    try:
        updated = update_category(
            category_id=category_id,
            raw_name=payload.get("name"),
        )
        return jsonify(updated.to_dict()), 200
    except CategoryNotFoundError as exc:
        return jsonify({"error": str(exc)}), 404
    except CategoryConflictError as exc:
        return jsonify({"error": str(exc)}), 409
    except CategoryValidationError as exc:
        return jsonify({"error": str(exc)}), 400


@categories_bp.delete("/<int:category_id>")
def delete_category(category_id: int):
    _, auth_error = _get_current_admin()
    if auth_error == 401:
        return jsonify({"error": "Debes iniciar sesion para eliminar categorias."}), 401
    if auth_error == 403:
        return jsonify(
            {"error": "Solo un administrador puede eliminar categorias."}
        ), 403

    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        return jsonify(
            {"error": "El cuerpo de la solicitud debe ser un JSON valido."}
        ), 400

    raw_reason = payload.get("reason")
    if not isinstance(raw_reason, str) or not raw_reason.strip():
        return jsonify(
            {"error": "Debes especificar una razon para eliminar la categoria."}
        ), 400

    category = db.session.get(Category, category_id)
    if category is None:
        return jsonify({"error": "La categoria no existe."}), 404

    has_questions = (
        db.session.scalar(
            db.select(Question.id).where(Question.category_id == category.id).limit(1)
        )
        is not None
    )
    if has_questions:
        return jsonify(
            {
                "error": "No se puede eliminar una categoria que tiene preguntas asociadas."
            }
        ), 409

    reason = raw_reason.strip()
    db.session.delete(category)

    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return jsonify(
            {
                "error": "No se puede eliminar una categoria que tiene preguntas asociadas."
            }
        ), 409

    return jsonify(
        {
            "message": "Categoria eliminada correctamente.",
            "deleted_category_id": category_id,
            "reason": reason,
        }
    ), 200
