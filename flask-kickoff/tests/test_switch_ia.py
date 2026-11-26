import pytest

from myapp.extensions import db
from myapp.models.category import Category
from myapp.models.ia_type import IAType
from myapp.models.user import User, UserRole
from myapp.services.ia_service import (
    IATypeNotFoundError,
    InactiveIAError,
    UnauthorizedIAError,
    create_ia_type,
    get_selected_ia_type,
    switch_ia_type,
)
from myapp.services.question_service import create_question


def _create_user(name: str, email: str, role: UserRole) -> User:
    user = User(name=name, email=email, password_hash="hash", role=role)
    db.session.add(user)
    db.session.commit()
    db.session.refresh(user)
    return user


def test_admin_can_switch_active_ia_and_preserve_previous_answers(app):
    with app.app_context():
        admin = _create_user("Admin", "admin@test.com", UserRole.ADMIN)
        student = _create_user("Alumno", "alumno@test.com", UserRole.GENERAL)

        cat = Category(name="Python")
        db.session.add(cat)
        db.session.commit()
        db.session.refresh(cat)

        ia_chatgpt = create_ia_type("chatgpt", user_id=admin.id)
        ia_gemini = create_ia_type("gemini", user_id=admin.id)

        assert get_selected_ia_type().id == ia_chatgpt.id

        # Primera pregunta respondida con chatgpt
        q1 = create_question(
            titulo="Error en lista",
            cuerpo="Tengo un error al recorrer una lista",
            user_id=student.id,
            category_id=cat.id,
        )
        assert len(q1.answers) == 1
        assert q1.answers[0].cuerpo.startswith("[chatgpt]")

        # Admin intercambia a gemini
        switched = switch_ia_type(ia_id=ia_gemini.id, user_id=admin.id)
        assert switched.id == ia_gemini.id
        assert switched.is_selected is True
        assert db.session.get(IAType, ia_chatgpt.id).is_selected is False

        # Criterio 3: respuesta anterior no se modifica
        db.session.refresh(q1)
        assert q1.answers[0].cuerpo.startswith("[chatgpt]")

        # Criterio 4: nueva pregunta usa la nueva IA (gemini)
        q2 = create_question(
            titulo="Como usar diccionarios",
            cuerpo="Como implementar un diccionario en Python",
            user_id=student.id,
            category_id=cat.id,
        )
        assert len(q2.answers) == 1
        assert q2.answers[0].cuerpo.startswith("[gemini]")


def test_non_admin_cannot_switch_ia(app):
    with app.app_context():
        admin = _create_user("Admin", "admin@test.com", UserRole.ADMIN)
        general = _create_user("User", "user@test.com", UserRole.GENERAL)

        create_ia_type("chatgpt", user_id=admin.id)
        ia_gemini = create_ia_type("gemini", user_id=admin.id)

        with pytest.raises(UnauthorizedIAError):
            switch_ia_type(ia_id=ia_gemini.id, user_id=general.id)


def test_cannot_switch_to_nonexistent_or_inactive_ia(app):
    with app.app_context():
        admin = _create_user("Admin", "admin@test.com", UserRole.ADMIN)
        create_ia_type("chatgpt", user_id=admin.id)
        ia_disabled = create_ia_type("claude", user_id=admin.id)
        ia_disabled.is_active = False
        db.session.commit()

        with pytest.raises(IATypeNotFoundError):
            switch_ia_type(ia_id=9999, user_id=admin.id)

        with pytest.raises(InactiveIAError):
            switch_ia_type(ia_id=ia_disabled.id, user_id=admin.id)