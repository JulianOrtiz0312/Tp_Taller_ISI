from flask import Blueprint, flash, redirect, render_template, request, session, url_for

from myapp.extensions import db
from myapp.models.category import Category
from myapp.services.question_service import QuestionServiceError, create_question

questions_bp = Blueprint("questions", __name__, url_prefix="/questions")


@questions_bp.route("/create", methods=["GET", "POST"])
def create():
    user_id = session.get("user_id")
    if not user_id:
        flash("Debes iniciar sesión para publicar una pregunta.")
        return redirect(url_for("users.index"))

    categories = (
        db.session.execute(db.select(Category).order_by(Category.name)).scalars().all()
    )

    if request.method == "POST":
        titulo = request.form.get("titulo", "")
        cuerpo = request.form.get("cuerpo", "")
        raw_category_id = request.form.get("category_id", "")

        try:
            category_id = int(raw_category_id)
        except (TypeError, ValueError):
            return (
                render_template(
                    "questions/create.html",
                    error="Debes seleccionar una categoría válida.",
                    titulo=titulo,
                    cuerpo=cuerpo,
                    categories=categories,
                ),
                400,
            )

        try:
            create_question(
                titulo=titulo,
                cuerpo=cuerpo,
                user_id=user_id,
                category_id=category_id,
            )
            flash("Pregunta publicada correctamente.")
            return redirect(url_for("questions.create"))
        except QuestionServiceError as exc:
            return (
                render_template(
                    "questions/create.html",
                    error=str(exc),
                    titulo=titulo,
                    cuerpo=cuerpo,
                    selected_category_id=category_id,
                    categories=categories,
                ),
                400,
            )

    return render_template("questions/create.html", categories=categories)
