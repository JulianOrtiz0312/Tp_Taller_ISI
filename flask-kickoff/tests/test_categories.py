from myapp.extensions import db
from myapp.models import Category, Question, User, UserRole


def _create_user(name: str, email: str, role: UserRole) -> User:
    user = User(name=name, email=email, role=role)
    user.set_password("Pass1234")
    db.session.add(user)
    db.session.commit()
    return user


def _login_session(client, user_id: int) -> None:
    with client.session_transaction() as sess:
        sess["user_id"] = user_id


def test_admin_can_update_category_and_reflects_in_questions(app, client):
    with app.app_context():
        admin = _create_user("Admin", "admin_cat@unrc.edu.ar", UserRole.ADMIN)
        cat = Category(name="Algebra")
        db.session.add(cat)
        db.session.commit()

        question = Question(
            titulo="Consulta sobre matrices",
            cuerpo="¿Cómo se calcula el determinante?",
            user_id=admin.id,
            category_id=cat.id,
        )
        db.session.add(question)
        db.session.commit()

        admin_id, cat_id, q_id = admin.id, cat.id, question.id

    _login_session(client, admin_id)
    response = client.patch(
        f"/categories/{cat_id}",
        json={"name": "Álgebra Lineal"},
    )

    assert response.status_code == 200
    assert response.json == {"id": cat_id, "name": "Álgebra Lineal"}

    with app.app_context():
        updated_question = db.session.get(Question, q_id)
        assert updated_question is not None
        assert updated_question.category.name == "Álgebra Lineal"


def test_unauthenticated_user_cannot_update_category(app, client):
    with app.app_context():
        cat = Category(name="Física")
        db.session.add(cat)
        db.session.commit()
        cat_id = cat.id

    response = client.patch(f"/categories/{cat_id}", json={"name": "Física I"})
    assert response.status_code == 401


def test_non_admin_cannot_update_category(app, client):
    non_admin_role = next(role for role in UserRole if role != UserRole.ADMIN)
    with app.app_context():
        user = _create_user("Alumno", "alumno_cat@unrc.edu.ar", non_admin_role)
        cat = Category(name="Química")
        db.session.add(cat)
        db.session.commit()
        user_id, cat_id = user.id, cat.id

    _login_session(client, user_id)
    response = client.patch(f"/categories/{cat_id}", json={"name": "Química Orgánica"})
    assert response.status_code == 403


def test_update_nonexistent_category_returns_404(app, client):
    with app.app_context():
        admin = _create_user("Admin 2", "admin2_cat@unrc.edu.ar", UserRole.ADMIN)
        admin_id = admin.id

    _login_session(client, admin_id)
    response = client.patch("/categories/9999", json={"name": "Inexistente"})
    assert response.status_code == 404


def test_reject_empty_or_duplicate_category_name(app, client):
    with app.app_context():
        admin = _create_user("Admin 3", "admin3_cat@unrc.edu.ar", UserRole.ADMIN)
        cat1 = Category(name="Programación")
        cat2 = Category(name="Bases de Datos")
        db.session.add_all([cat1, cat2])
        db.session.commit()
        admin_id, cat1_id = admin.id, cat1.id

    _login_session(client, admin_id)

    res_empty = client.patch(f"/categories/{cat1_id}", json={"name": "   "})
    assert res_empty.status_code == 400

    res_dup = client.patch(f"/categories/{cat1_id}", json={"name": "bases de datos"})
    assert res_dup.status_code == 409


def test_cannot_modify_category_id(app, client):
    with app.app_context():
        admin = _create_user("Admin 4", "admin4_cat@unrc.edu.ar", UserRole.ADMIN)
        cat = Category(name="Redes")
        db.session.add(cat)
        db.session.commit()
        admin_id, cat_id = admin.id, cat.id

    _login_session(client, admin_id)
    response = client.patch(
        f"/categories/{cat_id}",
        json={"id": 999, "name": "Redes de Datos"},
    )
    assert response.status_code == 400
