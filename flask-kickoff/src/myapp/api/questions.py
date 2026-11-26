from flask import Blueprint, jsonify, request, session

from myapp.services.question_service import( 
    QuestionServiceError, 
    create_question, 
    delete_question,
    ErrorDelete,
    ErrorPermiso,
    ErrorUser,
    QuestionServiceError,
    delete_question
    )

api_questions_bp = Blueprint("api_questions", __name__, url_prefix="/api/questions")


@api_questions_bp.get("/")
def get_questions():
    questions = list_questions()
    return jsonify([question.to_dict() for question in questions]), 200


@api_questions_bp.get("/<int:question_id>")
def get_question_detail(question_id: int):
    try:
        question = get_question(question_id)
    except ErrorDelete as exc:
        return jsonify({"error": str(exc)}), 404

    return jsonify(question.to_dict()), 200


@api_questions_bp.post("/create")
def api_create_question():
    user_id = session.get("user_id")
    if not user_id:
        return jsonify({"error": "Debes iniciar sesión para crear una pregunta."}), 401

    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        return jsonify(
            {"error": "El cuerpo de la solicitud debe ser un JSON válido."}
        ), 400

    raw_titulo = payload.get("titulo")
    raw_cuerpo = payload.get("cuerpo")
    raw_category_id = payload.get("category_id")

    if not all(isinstance(v, str) for v in (raw_titulo, raw_cuerpo)):
        return jsonify({"error": "Los campos titulo y cuerpo deben ser texto."}), 400

    if not isinstance(raw_category_id, int) or isinstance(raw_category_id, bool):
        return jsonify(
            {"error": "El campo category_id debe ser un número entero."}
        ), 400

    try:
        question = create_question(
            titulo=raw_titulo,
            cuerpo=raw_cuerpo,
            user_id=user_id,
            category_id=raw_category_id,
        )
        return jsonify(question.to_dict()), 201
    except QuestionServiceError as exc:
        return jsonify({"error": str(exc)}), 400

@api_questions_bp.delete("/<int:question_id>/delete")
def api_delete_question():
    user_id = session.get("user_id")
    if not user_id:
        return jsonify({"error": "Debes iniciar sesion para poder eliminar una pregunta"}), 401

    try:
        delete_question(question_id=question_id, user_id=user_id)
    except ErrorDelete as exc:
        return jsonify({"error": str(exc)}), 404
    except ErrorUser as exc:
        return jsonify({"error": str(exc)}), 401
    except ErrorPermiso as exc:
        return jsonify({"error": str(exc)}), 403
    except QuestionServiceError as exc:
        return jsonify({"error": str(exc)}), 400


    return jsonify({"message": "Pregunta eliminada correctamente"}), 200