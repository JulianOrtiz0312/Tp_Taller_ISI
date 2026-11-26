from sqlalchemy.exc import IntegrityError

from myapp.extensions import db
from myapp.models.category import Category
from myapp.models.question import Question
from myapp.models.user import User


class QuestionServiceError(ValueError):
    pass


class TittleError(QuestionServiceError):
    pass


class BodyError(QuestionServiceError):
    pass


class UserorCategoryError(QuestionServiceError):
    pass


def create_question(
    titulo: str,
    cuerpo: str,
    user_id: int,
    category_id: int,
) -> Question:
    if not isinstance(titulo, str):
        raise TittleError("El título debe ser una cadena de texto.")

    if not isinstance(cuerpo, str):
        raise BodyError("El cuerpo debe ser una cadena de texto.")

    titulo_clean = titulo.strip()
    cuerpo_clean = cuerpo.strip()

    if not titulo_clean or len(titulo_clean) > 200:
        raise TittleError("El título es obligatorio y debe tener hasta 200 caracteres.")

    if not cuerpo_clean:
        raise BodyError("El cuerpo es obligatorio.")

    category = db.session.get(Category, category_id)
    if category is None:
        raise UserorCategoryError("La categoría no existe.")

    user = db.session.get(User, user_id)
    if user is None:
        raise UserorCategoryError("El usuario no existe.")

    sql = db.select(Question).where(
        Question.titulo == titulo_clean,
        Question.user_id == user_id,
    )

    if db.session.execute(sql).scalar_one_or_none() is not None:
        raise TittleError("Ya hiciste una pregunta con este título.")

    question = Question(
        titulo=titulo_clean,
        cuerpo=cuerpo_clean,
        category=category,
        user=user,
    )

    db.session.add(question)

    try:
        db.session.commit()
    except IntegrityError as exc:
        db.session.rollback()
        raise UserorCategoryError("Error en la integridad en la creación.") from exc

    db.session.refresh(question)
    return question


class ErrorDelete(QuestionServiceError):
    pass


class ErrorPermiso(QuestionServiceError):
    pass


class ErrorUser(QuestionServiceError):
    pass


class ErrorQuestion(QuestionServiceError):
    pass


def delete_question(question_id: int, user_id: int) -> None:
    question = db.session.get(Question, question_id)

    if question is None:
        raise ErrorQuestion("No existe la pregunta que quieres eliminar")

    user = db.session.get(User, user_id)

    if user is None:
        raise ErrorUser("Tienes que registrarte para eliminar la pregunta")

    if user_id != question.user.id and user.role != "admin":
        raise ErrorPermiso("No tienes permiso de borrar esta pregunta")

    db.session.delete(question)

    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        raise ErrorDelete("Hubo un error en eliminar la pregunta")


def list_questions() -> list[Question]:
    return list(
        db.session.scalars(db.select(Question).order_by(Question.id.desc())).all()
    )


def get_question(question_id: int) -> Question:
    question = db.session.get(Question, question_id)
    if question is None:
        raise ErrorDelete("La pregunta no existe.")
    return question
