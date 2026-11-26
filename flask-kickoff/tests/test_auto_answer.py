import pytest
from sqlalchemy import text

from myapp.extensions import db
from myapp.models.answer import Answer
from myapp.models.category import Category
from myapp.models.question import Question
from myapp.models.user import User
from myapp.services import question_service
from myapp.services.auto_answer_service import (
    AI_USER_EMAIL,
    generate_automatic_answer,
)
from myapp.services.question_service import create_question
from myapp.services.user_service import register_user


@pytest.fixture
def seed_data(app):
    with app.app_context():
        user = register_user(
            name="Braian",
            email="braian@unrc.edu.ar",
            password="password123",
        )
        category = Category(name="Bases de Datos")
        db.session.add(category)
        db.session.commit()
        return {"user_id": user.id, "category_id": category.id}


def test_question_creation_generates_coherent_ai_answer(app, seed_data):
    with app.app_context():
        question = create_question(
            titulo="¿Cómo optimizar una consulta SQL?",
            cuerpo="Tengo un error de rendimiento en una tabla grande.",
            user_id=seed_data["user_id"],
            category_id=seed_data["category_id"],
        )

        answers = db.session.scalars(
            db.select(Answer).where(Answer.id_Question == question.id)
        ).all()
        assert len(answers) == 1

        ai_answer = answers[0]
        assert "¿Cómo optimizar una consulta SQL?" in ai_answer.cuerpo
        assert "Bases de Datos" in ai_answer.cuerpo

        ai_user = db.session.get(User, ai_answer.id_Autor)
        assert ai_user is not None
        assert ai_user.email == AI_USER_EMAIL


def test_question_cannot_have_two_ai_answers(app, seed_data):
    with app.app_context():
        question = create_question(
            titulo="Pregunta con una sola respuesta IA",
            cuerpo="Probando idempotencia del servicio.",
            user_id=seed_data["user_id"],
            category_id=seed_data["category_id"],
        )

        second_attempt = generate_automatic_answer(question)
        assert second_attempt is None

        answers = db.session.scalars(
            db.select(Answer).where(Answer.id_Question == question.id)
        ).all()
        assert len(answers) == 1


def test_ai_error_does_not_affect_question_creation(app, seed_data, monkeypatch):
    def _broken_ai(_question):
        raise RuntimeError("Falla simulada en el servicio de IA")

    monkeypatch.setattr(question_service, "generate_automatic_answer", _broken_ai)

    with app.app_context():
        question = create_question(
            titulo="Pregunta resiliente a fallos",
            cuerpo="Debe guardarse aunque falle la IA.",
            user_id=seed_data["user_id"],
            category_id=seed_data["category_id"],
        )

        saved_question = db.session.get(Question, question.id)
        assert saved_question is not None
        assert saved_question.titulo == "Pregunta resiliente a fallos"

        answers = db.session.scalars(
            db.select(Answer).where(Answer.id_Question == question.id)
        ).all()
        assert len(answers) == 0


def test_uses_active_ia_type_when_table_exists(app, seed_data):
    with app.app_context():
        db.session.execute(
            text(
                "CREATE TABLE ia_types ("
                "id INTEGER PRIMARY KEY, "
                "name VARCHAR(120) NOT NULL, "
                "is_active BOOLEAN NOT NULL)"
            )
        )
        db.session.execute(
            text(
                "INSERT INTO ia_types (id, name, is_active) "
                "VALUES (1, 'IA Inactiva', 0), (2, 'Tutor UNRC AI', 1)"
            )
        )
        db.session.commit()

        question = create_question(
            titulo="Consulta con IA configurada",
            cuerpo="Probando compatibilidad con ia_types.",
            user_id=seed_data["user_id"],
            category_id=seed_data["category_id"],
        )

        ai_answer = db.session.scalar(
            db.select(Answer).where(Answer.id_Question == question.id)
        )
        assert ai_answer is not None
        assert "[Tutor UNRC AI]" in ai_answer.cuerpo
