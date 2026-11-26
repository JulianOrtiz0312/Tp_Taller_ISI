from sqlalchemy import inspect, text

from myapp.extensions import db
from myapp.models.answer import Answer
from myapp.models.question import Question
from myapp.models.user import User, UserRole
from myapp.services.answer_service import create_answer

AI_USER_EMAIL = "ia@sistema.local"
DEFAULT_AI_NAME = "Asistente IA"


def get_or_create_ai_user() -> User:
    ai_user = db.session.scalar(db.select(User).where(User.email == AI_USER_EMAIL))
    if ai_user is not None:
        return ai_user

    ai_user = User(
        name=DEFAULT_AI_NAME,
        email=AI_USER_EMAIL,
        password_hash="",
        role=UserRole.GENERAL,
    )
    db.session.add(ai_user)
    db.session.commit()
    db.session.refresh(ai_user)
    return ai_user


def _get_active_ai_name() -> str:
    """Obtiene el nombre de una IA activa si existe la tabla ia_types; si no, usa el valor por defecto."""
    inspector = inspect(db.engine)
    if not inspector.has_table("ia_types"):
        return DEFAULT_AI_NAME

    row = db.session.execute(
        text("SELECT name FROM ia_types WHERE is_active = 1 ORDER BY id ASC LIMIT 1")
    ).first()
    if row and row[0]:
        return str(row[0])

    return DEFAULT_AI_NAME


def build_simulated_response(question: Question, ai_name: str = DEFAULT_AI_NAME) -> str:
    category_name = question.category.name if question.category else "General"
    titulo = question.titulo.strip()
    cuerpo_lower = question.cuerpo.lower()

    if any(word in cuerpo_lower for word in ("error", "falla", "excepcion", "bug")):
        orientacion = (
            "Te recomiendo revisar el mensaje de error completo, aislar el bloque de "
            "código o configuración donde ocurre y verificar los datos de entrada."
        )
    elif any(
        word in cuerpo_lower
        for word in ("como", "cómo", "implementar", "crear", "usar")
    ):
        orientacion = (
            "Un buen punto de partida es dividir el problema en pasos pequeños, "
            "revisar la documentación oficial de la herramienta y validar cada parte por separado."
        )
    else:
        orientacion = (
            "Para facilitar una respuesta más precisa de la comunidad, podés sumar "
            "contexto adicional, ejemplos concretos o lo que ya intentaste."
        )

    return (
        f"[{ai_name}] Respuesta preliminar sobre '{titulo}' "
        f"(Categoría: {category_name}): {orientacion}"
    )


def generate_automatic_answer(question: Question) -> Answer | None:
    ai_user = get_or_create_ai_user()

    existing_ai_answer = db.session.scalar(
        db.select(Answer).where(
            Answer.id_Question == question.id,
            Answer.id_Autor == ai_user.id,
        )
    )
    if existing_ai_answer is not None:
        return None

    ai_name = _get_active_ai_name()
    response_body = build_simulated_response(question, ai_name=ai_name)

    return create_answer(
        cuerpo=response_body,
        id_autor=ai_user.id,
        id_question=question.id,
    )
