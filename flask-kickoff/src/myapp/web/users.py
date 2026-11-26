from flask import Blueprint, flash, redirect, render_template, request, session, url_for

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
            return redirect(url_for("users.index"))
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


@users_bp.post("/logout")
def logout():
    if "user_id" not in session:
        flash("no hay sesion activa")
        return redirect(url_for("users.index"))

    session.clear()
    flash("sesion cerrada correctamente")
    return redirect(url_for("users.index"))
