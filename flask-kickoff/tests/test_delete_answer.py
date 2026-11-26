import pytest

from myapp.extensions import db
from myapp.models.answer import Answer
from myapp.models.category import Category
from myapp.models.user import UserRole
from myapp.services.auto_answer_service import AI_USER_EMAIL
from myapp.services.question_service import create_question
from myapp.services.user_service import register_user


@pytest.fixture
def seed_qa_data(app):
    with app.app_context():
        question_author = register_user(
            name="Autor Pregunta",
            email="autor_preg@unrc.edu.ar",
            password="password123",
        )
        answer_author = register_user(
            name="Autor Respuesta",
            email="autor_resp@unrc.edu.ar",
            password="password123",
        )
        other_user = register_user(
            name="Otro Usuario",
            email="otro_user@unrc.edu.ar",
            password="password123",
        )
        admin_user = register_user(
            name="Admin",
            email="admin_qa@unrc.edu.ar",
            password="password123",
        )
        admin_user.role = UserRole.ADMIN

        category = Category(name="Ingeniería de Software")
        db.session.add(category)
        db.session.commit()

        question_1 = create_question(
            titulo="¿Qué es una arquitectura en capas?",
            cuerpo="Quiero entender cómo separar modelos, servicios y rutas.",
            user_id=question_author.id,
            category_id=category.id,
        )
        question_2 = create_question(
            titulo="¿Cómo funciona SQLAlchemy?",
            cuerpo="Duda sobre sesiones y relaciones.",
            user_id=question_author.id,
            category_id=category.id,
        )

        ai_answer_1 = next(
            a for a in question_1.answers if a.autor and a.autor.email == AI_USER_EMAIL
        )
        ai_answer_2 = next(
            a for a in question_2.answers if a.autor and a.autor.email == AI_USER_EMAIL
        )

        normal_answer = Answer(
            cuerpo="Separa presentación, lógica de negocio y acceso a datos.",
            id_Autor=answer_author.id,
            id_Question=question_1.id,
            accept=False,
        )
        accepted_answer = Answer(
            cuerpo="Esta es la respuesta marcada como aceptada.",
            id_Autor=answer_author.id,
            id_Question=question_1.id,
            accept=True,
        )
        db.session.add_all([normal_answer, accepted_answer])
        db.session.commit()

        return {
            "question_author_id": question_author.id,
            "answer_author_id": answer_author.id,
            "other_user_id": other_user.id,
            "admin_user_id": admin_user.id,
            "normal_answer_id": normal_answer.id_answer,
            "accepted_answer_id": accepted_answer.id_answer,
            "ai_answer_1_id": ai_answer_1.id_answer,
            "ai_answer_2_id": ai_answer_2.id_answer,
        }


def _login(client, user_id: int):
    with client.session_transaction() as sess:
        sess["user_id"] = user_id


def test_delete_nonexistent_answer_returns_404(client, seed_qa_data):
    _login(client, seed_qa_data["answer_author_id"])

    response = client.delete("/api/answers/99999")
    assert response.status_code == 404


def test_cannot_delete_accepted_answer(client, app, seed_qa_data):
    accepted_id = seed_qa_data["accepted_answer_id"]

    for user_key in ("answer_author_id", "admin_user_id"):
        _login(client, seed_qa_data[user_key])
        response = client.delete(f"/api/answers/{accepted_id}")
        assert response.status_code == 400

    with app.app_context():
        assert db.session.get(Answer, accepted_id) is not None


def test_normal_answer_can_only_be_deleted_by_its_author(client, app, seed_qa_data):
    answer_id = seed_qa_data["normal_answer_id"]

    for forbidden_key in ("other_user_id", "question_author_id", "admin_user_id"):
        _login(client, seed_qa_data[forbidden_key])
        resp = client.delete(f"/api/answers/{answer_id}")
        assert resp.status_code == 403

    _login(client, seed_qa_data["answer_author_id"])
    resp_ok = client.delete(f"/api/answers/{answer_id}")
    assert resp_ok.status_code == 200

    with app.app_context():
        assert db.session.get(Answer, answer_id) is None


def test_autoria_answer_can_be_deleted_by_question_author_or_admin(
    client, app, seed_qa_data
):
    ai_1_id = seed_qa_data["ai_answer_1_id"]
    ai_2_id = seed_qa_data["ai_answer_2_id"]

    _login(client, seed_qa_data["other_user_id"])
    assert client.delete(f"/api/answers/{ai_1_id}").status_code == 403

    _login(client, seed_qa_data["question_author_id"])
    assert client.delete(f"/api/answers/{ai_1_id}").status_code == 200

    _login(client, seed_qa_data["admin_user_id"])
    assert client.delete(f"/api/answers/{ai_2_id}").status_code == 200

    with app.app_context():
        assert db.session.get(Answer, ai_1_id) is None
        assert db.session.get(Answer, ai_2_id) is None


def test_answers_persist_when_author_deletes_account(client, app, seed_qa_data):
    answer_author_id = seed_qa_data["answer_author_id"]
    normal_answer_id = seed_qa_data["normal_answer_id"]

    _login(client, answer_author_id)
    resp = client.delete(f"/api/users/{answer_author_id}")
    assert resp.status_code == 200

    with app.app_context():
        persisted = db.session.get(Answer, normal_answer_id)
        assert persisted is not None
        assert persisted.id_Autor is None
