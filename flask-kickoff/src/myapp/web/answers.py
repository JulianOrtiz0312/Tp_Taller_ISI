from flask import (
    Blueprint,
    abort,
    flash,
    redirect,
    render_template,
    request,
    session,
    url_for,
)

from myapp.extensions import db
from myapp.models.question import Question
from myapp.services.answer_service import (
    AnswerError,
    ErrorAutor,
    ErrorQuestion,
    create_answer,
)

answers_bp = Blueprint("answers", __name__, url_prefix="/questions")


@answers_bp.route("/<int:question_id>/answers/create", methods=["GET", "POST"])
def create(question_id: int):
    user_id = session.get("user_id")
    if not user_id:
        flash("Debés iniciar sesión para responder una pregunta.", "error")
        return redirect(url_for("users.login"))

    question = db.session.get(Question, question_id)
    if question is None:
        abort(404)

    if request.method == "POST":
        cuerpo = request.form.get("cuerpo", "")

        try:
            create_answer(
                cuerpo=cuerpo,
                id_autor=user_id,
                id_question=question_id,
            )
            flash("Respuesta publicada correctamente.", "success")
            return redirect(url_for("questions.create"))
        except ErrorQuestion:
            abort(404)
        except ErrorAutor as exc:
            flash(str(exc), "error")
            return redirect(url_for("auth.login"))
        except AnswerError as exc:
            flash(str(exc), "error")
            return render_template(
                "answers/create.html",
                question=question,
                cuerpo=cuerpo,
            )

    return render_template(
        "answers/create.html",
        question=question,
        cuerpo="",
    )

from flask import Blueprint, abort, flash, redirect, render_template, request, session, url_for

from myapp.extensions import db
from myapp.models.answer import Answer
from myapp.services.answer_service import (
    AnswerError,
    ErrorAnswerAccept,
    ErrorAutor,
    ErrorBody,
    ErrorIDAnswer,
    ErrorModify,
    modify_answer,
)


@answers_bp.route("/<int:answer_id>/edit", methods=["GET", "POST"])
def edit(answer_id: int):
    user_id = session.get("user_id")
    if not user_id:
        flash("Debes iniciar sesión para editar una respuesta.", "error")
        return redirect(url_for("users.login"))

    answer = db.session.get(Answer, answer_id)
    if answer is None:
        abort(404)

    if answer.accept:
        flash("No se puede modificar una respuesta aceptada.", "error")
        return redirect(url_for("questions.detail", question_id=answer.question_id))

    if request.method == "POST":
        new_cuerpo = request.form.get("cuerpo", "")

        try:
            updated_answer = modify_answer(
                answer_id=answer_id,
                new_cuerpo=new_cuerpo,
                user_id=user_id,
            )
            flash("Respuesta actualizada correctamente.", "success")
            return redirect(url_for("questions.detail", question_id=updated_answer.question_id))
        except (ErrorBody, ErrorAutor, ErrorAnswerAccept, ErrorIDAnswer, ErrorModify, AnswerError) as exc:
            flash(str(exc), "error")
            return render_template("answers/edit.html", answer=answer, cuerpo=new_cuerpo)

    return render_template("answers/edit.html", answer=answer, cuerpo=answer.cuerpo)
