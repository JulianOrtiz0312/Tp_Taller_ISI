from flask import Blueprint, flash, redirect, render_template, request, session, url_for

from myapp.extensions import db
from myapp.models.category import Category
from myapp.services.question_service import (
    QuestionServiceError, 
    create_question,
    delete_question,
    ErrorDelete,
    ErrorPermiso,
    ErrorUser,
    )

questions_bp = Blueprint("questions", __name__, url_prefix="/questions")

@questions_bp.get("/")
def index():
    questions = list_questions()
    return render_template("questions/index.html", questions=questions)


@questions_bp.get("/<int:question_id>")
def detail(question_id: int):
    try:
        question = get_question(question_id)
    except ErrorDelete:
        abort(404)

    return render_template("questions/detail.html", question=question)


@questions_bp.route("/create", methods=["GET", "POST"])
def create():
    user_id = session.get("user_id")
    if not user_id:
        flash("Debes iniciar sesión para publicar una pregunta.")
        return redirect(url_for("users.login"))

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
            return redirect(url_for("questions.index"))
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


@questions_bp.route("/<int:question_id>/delete", methods=["POST"])
def delete(question_id: int):
    user_id = session.get("user_id")
    if not user_id:
        flash("Debés iniciar sesión para eliminar una pregunta.", "error")
        return redirect(url_for("auth.login"))

    try:
        delete_question(question_id=question_id, user_id=user_id)
        flash("Pregunta eliminada correctamente.", "success")
    except ErrorDelete:
        abort(404)
    except ErrorUser as exc:
        flash(str(exc), "error")
        return redirect(url_for("users.login"))
    except ErrorPermiso as exc:
        flash(str(exc), "error")
    except QuestionServiceError as exc:
        flash(str(exc), "error")

    
    return redirect(url_for("questions.index"))
