from flask import Blueprint, flash, redirect, render_template, request, session, url_for
from sqlalchemy.exc import IntegrityError

from myapp.extensions import db
from myapp.models import Category, Question, User, UserRole

web_categories_bp = Blueprint("web_categories", __name__, url_prefix="/categories")


def _get_current_web_user() -> User | None:
    user_id = session.get("user_id")
    if not user_id:
        return None
    return db.session.get(User, user_id)


@web_categories_bp.get("/manage")
def manage():
    user = _get_current_web_user()
    if user is None:
        flash("Debes iniciar sesión para gestionar categorías.")
        return redirect(url_for("users.login"))

    categories = (
        db.session.execute(db.select(Category).order_by(Category.name)).scalars().all()
    )
    return render_template(
        "categories/manage.html",
        categories=categories,
        is_admin=(user.role == UserRole.ADMIN),
    )


@web_categories_bp.post("/<int:category_id>/delete")
def delete_category_web(category_id: int):
    user = _get_current_web_user()
    if user is None:
        flash("Debes iniciar sesión para eliminar categorías.")
        return redirect(url_for("users.login"))

    if user.role != UserRole.ADMIN:
        flash("Solo un administrador puede eliminar categorías.")
        return redirect(url_for("web_categories.manage")), 403

    reason = request.form.get("reason", "").strip()
    if not reason:
        flash("Debes especificar una razón para eliminar la categoría.")
        return redirect(url_for("web_categories.manage")), 400

    category = db.session.get(Category, category_id)
    if category is None:
        flash("La categoría no existe.")
        return redirect(url_for("web_categories.manage")), 404

    has_questions = (
        db.session.scalar(
            db.select(Question.id).where(Question.category_id == category.id).limit(1)
        )
        is not None
    )
    if has_questions:
        flash("No se puede eliminar una categoría que tiene preguntas asociadas.")
        return redirect(url_for("web_categories.manage")), 409

    db.session.delete(category)
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        flash("No se puede eliminar una categoría que tiene preguntas asociadas.")
        return redirect(url_for("web_categories.manage")), 409

    flash(f"Categoría eliminada (motivo: {reason}).")
    return redirect(url_for("web_categories.manage"))
