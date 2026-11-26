from sqlalchemy.exc import IntegrityError

from myapp.extensions import db
from myapp.models.answer import Answer
from myapp.models.question import Question
from myapp.models.user import User, UserRole

AI_USER_EMAIL = "ia@sistema.local"


class AnswerError(ValueError):
    pass


class ErrorBody(AnswerError):
    pass


class ErrorAutor(AnswerError):
    pass


class ErrorQuestion(AnswerError):
    pass


class ErrorAnswerNotFound(AnswerError):
    pass


class AcceptedAnswerDeletionError(ValueError):
    """No se puede eliminar una respuesta aceptada."""


def create_answer(cuerpo: str, id_autor: int, id_question: int) -> Answer:

    if not isinstance(cuerpo, str):
        raise ErrorBody("El cuerpo debe ser un texto")

    cuerpo_clean = cuerpo.strip()

    if not cuerpo_clean:
        raise ErrorBody("No se permiten respuestas vacias")

    autor = db.session.get(User, id_autor)

    if autor is None:
        raise ErrorAutor("Se debe registrar para responder")

    question = db.session.get(Question, id_question)

    if question is None:
        raise ErrorQuestion("Debe seleccionar que pregunta responder")

    sqlAnswer = db.select(Answer).where(
        Answer.id_Autor == id_autor, Answer.id_Question == id_question
    )

    if db.session.execute(sqlAnswer).scalar_one_or_none() is not None:
        raise AnswerError("Ya respondiste a esta pregunta")

    answer = Answer(cuerpo=cuerpo_clean, id_Autor=id_autor, id_Question=id_question)

    db.session.add(answer)

    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        raise AnswerError("Error en la creacion de respuesta")

    db.session.refresh(answer)
    return answer


def set_answer_acceptance(id_answer: int, id_user: int, *, accepted: bool) -> Answer:
    answer = db.session.get(Answer, id_answer)
    if answer is None:
        raise ErrorAnswerNotFound("La respuesta no existe")

    question = answer.question or db.session.get(Question, answer.id_Question)
    if question is None:
        raise ErrorQuestion("La pregunta asociada no existe")

    if question.user_id is None or question.user_id != id_user:
        raise ErrorAutor(
            "Solo el autor de la pregunta puede aceptar o revertir respuestas"
        )

    answer.accept = bool(accepted)

    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        raise AnswerError("Error al actualizar el estado de la respuesta")

    db.session.refresh(answer)
    return answer


class ErrorModify(AnswerError):
    pass


class ErrorIDAnswer(AnswerError):
    pass


class ErrorAnswerAccept(AnswerError):
    pass


def modify_answer(answer_id: int, new_cuerpo: str, user_id: int) -> Answer:

    if not isinstance(new_cuerpo, str):
        raise ErrorBody("El cuerpo nuevo debe ser un texto")

    if not isinstance(answer_id, int):
        raise ErrorIDAnswer("debe ser un numero el id")

    if not isinstance(user_id, int):
        raise ErrorAutor("El ID del usuario debe ser un número")

    cuerpo = new_cuerpo.strip()

    if not cuerpo:
        raise ErrorBody("No se permiten respuestas vacias")

    user = db.session.get(User, user_id)

    if user is None:
        raise ErrorAutor("Se debe de registrar para modificar una respuesta")

    answer = db.session.get(Answer, answer_id)

    if answer is None:
        raise ErrorIDAnswer("No existe la respuesta que quieres modificar")

    if answer.accept is True:
        raise ErrorAnswerAccept("No se puede modificar una respuesta aceptada")

    if answer.autor.id != user_id and user.role != "admin":
        raise ErrorAutor("No tienes permiso de modificar la respuesta")

    answer.cuerpo = cuerpo

    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        raise ErrorModify("Hubo un error en la modificacion")

    db.session.refresh(answer)
    return answer


def toggle_answer_acceptance(id_answer: int, id_user: int) -> Answer:
    answer = db.session.get(Answer, id_answer)
    if answer is None:
        raise ErrorAnswerNotFound("La respuesta no existe")
    return set_answer_acceptance(id_answer, id_user, accepted=not answer.accept)


def delete_answer(acting_user_id: int, answer_id: int) -> None:
    answer = db.session.get(Answer, answer_id)
    if answer is None:
        raise LookupError("La respuesta no existe.")

    acting_user = db.session.get(User, acting_user_id)
    if acting_user is None:
        raise PermissionError("Usuario no válido o inexistente.")

    if answer.accept:
        raise AcceptedAnswerDeletionError(
            "No se puede eliminar una respuesta aceptada."
        )

    is_autoria = answer.autor is not None and answer.autor.email == AI_USER_EMAIL

    if is_autoria:
        is_question_author = (
            answer.question is not None and answer.question.user_id == acting_user_id
        )
        is_admin = acting_user.role == UserRole.ADMIN
        if not (is_question_author or is_admin):
            raise PermissionError(
                "Solo el autor de la pregunta o un administrador puede eliminar una respuesta de AutorIA."
            )
    else:
        if answer.id_Autor != acting_user_id:
            raise PermissionError("Solo el autor de la respuesta puede eliminarla.")

    db.session.delete(answer)
    db.session.commit()
