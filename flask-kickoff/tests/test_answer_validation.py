from myapp.extensions import db
from myapp.models.answer import Answer
from myapp.models.category import Category
from myapp.models.question import Question
from myapp.models.user import User


def _login_as(client, user_id: int) -> None:
    with client.session_transaction() as sess:
        sess["user_id"] = user_id


def _create_user(name: str) -> User:
    user = User(username=name, email=f"{name}@test.com", password="secret")
    db.session.add(user)
    db.session.flush()
    return user


def _create_question_and_answers(author_id: int, responder_id: int):
    category = Category(name="General")
    db.session.add(category)
    db.session.flush()

    question = Question(
        titulo="Pregunta de prueba",
        cuerpo="Cuerpo de pregunta",
        user_id=author_id,
        category_id=category.id,
    )
    db.session.add(question)
    db.session.flush()

    ans_1 = Answer(cuerpo="Respuesta 1", id_Autor=responder_id, id_Question=question.id)
    ans_2 = Answer(cuerpo="Respuesta 2", id_Autor=author_id, id_Question=question.id)
    db.session.add_all([ans_1, ans_2])
    db.session.commit()
    return question, ans_1, ans_2


def test_only_question_author_can_accept_answer(app, client):
    with app.app_context():
        q_author = _create_user("q_author")
        other_user = _create_user("other_user")
        _, ans_1, _ = _create_question_and_answers(q_author.id, other_user.id)
        ans_id = ans_1.id_answer
        other_id = other_user.id

    _login_as(client, other_id)
    resp = client.patch(f"/api/answers/{ans_id}/accept", json={"accepted": True})

    assert resp.status_code == 403
    with app.app_context():
        assert db.session.get(Answer, ans_id).accept is False


def test_question_author_can_accept_multiple_answers(app, client):
    with app.app_context():
        q_author = _create_user("q_author2")
        responder = _create_user("responder2")
        _, ans_1, ans_2 = _create_question_and_answers(q_author.id, responder.id)
        ans_1_id = ans_1.id_answer
        ans_2_id = ans_2.id_answer
        author_id = q_author.id

    _login_as(client, author_id)
    resp_1 = client.patch(f"/api/answers/{ans_1_id}/accept", json={"accepted": True})
    resp_2 = client.patch(f"/api/answers/{ans_2_id}/accept", json={"accepted": True})

    assert resp_1.status_code == 200
    assert resp_2.status_code == 200
    assert resp_1.get_json()["accept"] is True
    assert resp_2.get_json()["accept"] is True

    with app.app_context():
        assert db.session.get(Answer, ans_1_id).accept is True
        assert db.session.get(Answer, ans_2_id).accept is True


def test_accept_nonexistent_answer_returns_404(app, client):
    with app.app_context():
        q_author = _create_user("q_author3")
        author_id = q_author.id

    _login_as(client, author_id)
    resp = client.patch("/api/answers/999999/accept", json={"accepted": True})

    assert resp.status_code == 404


def test_question_author_can_revert_accepted_answer(app, client):
    with app.app_context():
        q_author = _create_user("q_author4")
        responder = _create_user("responder4")
        _, ans_1, _ = _create_question_and_answers(q_author.id, responder.id)
        ans_1.accept = True
        db.session.commit()
        ans_1_id = ans_1.id_answer
        author_id = q_author.id

    _login_as(client, author_id)
    resp = client.patch(f"/api/answers/{ans_1_id}/accept", json={"accepted": False})

    assert resp.status_code == 200
    assert resp.get_json()["accept"] is False
    with app.app_context():
        assert db.session.get(Answer, ans_1_id).accept is False