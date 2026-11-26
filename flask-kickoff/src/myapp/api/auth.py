import logging

from flask import Blueprint, jsonify, request, session

from myapp.extensions import db
from myapp.models.user import User

logger = logging.getLogger(__name__)
auth_bp = Blueprint("auth", __name__, url_prefix="/api")


@auth_bp.post("/login")
def login():
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify({"error": "Invalid JSON body"}), 400

    email = (data.get("email") or "").strip().lower()
    password = data.get("password")

    if not email or not isinstance(password, str) or not password:
        return jsonify({"error": "Email and password are required"}), 400

    user = db.session.scalar(db.select(User).where(User.email == email))

    if user is None or not user.check_password(password):
        logger.warning("Failed login attempt")
        return jsonify({"error": "Invalid credentials"}), 401

    session.clear()
    session["user_id"] = user.id
    session.permanent = True

    logger.info("User logged in: id=%s", user.id)
    return jsonify({"user": user.to_dict()}), 200
