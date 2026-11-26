from flask import Blueprint, flash, redirect, render_template, request, session, url_for

from myapp.extensions import db
from myapp.models import User
from myapp.services.user_service import UserServiceError, list_users, register_user

users_bp = Blueprint("users", __name__, url_prefix="/users")


@users_bp.get("")
def index():
    users = list_users()
    return render_template("users/index.html", users=users)


@users_bp.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form.get("name", "")
        email = request.form.get("email", "")
        password = request.form.get("password", "")
        try:
            register_user(name=name, email=email, password=password)
            flash("Usuario registrado correctamente.")
            return redirect(url_for("users.login"))
        except UserServiceError as exc:
            return (
                render_template(
                    "users/register.html",
                    error=str(exc),
                    name=name,
                    email=email,
                ),
                400,
            )

    return render_template("users/register.html")


@users_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        user = db.session.scalar(db.select(User).where(User.email == email))
        if user is None or not user.check_password(password):
            return (
                render_template(
                    "users/login.html",
                    error="Correo o contraseña incorrectos.",
                    email=email,
                ),
                401,
            )

        session["user_id"] = user.id
        flash("Sesión iniciada correctamente.")
        return redirect(url_for("questions.index"))

    return render_template("users/login.html")
