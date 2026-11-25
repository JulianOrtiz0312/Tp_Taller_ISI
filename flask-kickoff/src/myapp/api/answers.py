from flask import Blueprint, jsonify, request, session
from myapp.services.answer_service import (
    AnswerError,
    ErrorAutor,
    ErrorQuestion,
    create_answer,
)

api_answers_bp = Blueprint("api_answers", __name__, url_prefix="/api")


@api_answers_bp.post("/questions/<int:question_id>/answers")
def post_answer(question_id: int):
    user_id = session.get("user_id")
    if not user_id:
        return jsonify({"error": "Debés iniciar sesión para responder."}), 401

    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify({"error": "El cuerpo de la petición debe ser un JSON válido."}), 400

    cuerpo = data.get("cuerpo")

    try:
        answer = create_answer(
            cuerpo=cuerpo,
            id_autor=user_id,
            id_question=question_id,
        )
    except ErrorAutor as exc:
        return jsonify({"error": str(exc)}), 401
    except ErrorQuestion as exc:
        return jsonify({"error": str(exc)}), 404
    except AnswerError as exc:
        return jsonify({"error": str(exc)}), 400

    return jsonify(answer.to_dict()), 201