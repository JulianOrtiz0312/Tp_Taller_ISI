from flask import Blueprint, jsonify, request, session

from myapp.services.answer_service import (
    AnswerError,
    ErrorAnswerNotFound,
    ErrorAutor,
    ErrorQuestion,
    create_answer,
    set_answer_acceptance,
    toggle_answer_acceptance,
)

api_answers_bp = Blueprint("api_answers", __name__, url_prefix="/api")


@api_answers_bp.post("/questions/<int:question_id>/answers")
def post_answer(question_id: int):
    user_id = session.get("user_id")
    if not user_id:
        return jsonify({"error": "Debés iniciar sesión para responder."}), 401

    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify(
            {"error": "El cuerpo de la petición debe ser un JSON válido."}
        ), 400

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

@api_answers_bp.patch("/answers/<int:id_answer>/accept")
def accept_answer(id_answer: int):
    user_id = session.get("user_id")
    if not user_id:
        return jsonify({"error": "No autenticado"}), 401

    payload = request.get_json(silent=True) or {}
    accepted = payload.get("accepted")

    try:
        if accepted is None:
            answer = toggle_answer_acceptance(id_answer, user_id)
        elif isinstance(accepted, bool):
            answer = set_answer_acceptance(id_answer, user_id, accepted=accepted)
        else:
            return jsonify({"error": "El campo 'accepted' debe ser booleano"}), 400
    except ErrorAnswerNotFound as exc:
        return jsonify({"error": str(exc)}), 404
    except ErrorAutor as exc:
        return jsonify({"error": str(exc)}), 403
    except AnswerError as exc:
        return jsonify({"error": str(exc)}), 400

    data = answer.to_dict()
    if hasattr(data.get("fecha"), "isoformat"):
        data["fecha"] = data["fecha"].isoformat()
    return jsonify(data), 200
