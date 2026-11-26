from flask import Blueprint, flash, redirect, render_template, request, session, url_for

from myapp.services.ia_service import IAServiceError,UnauthorizedIAError,create_ia_type,list_ia_types

ia_bp = Blueprint("ia", __name__, url_prefix="/ia")


@ia_bp.route("/create", methods=["GET", "POST"])
def create():
    user_id = session.get("user_id")
    if not user_id:
        flash("debe iniciar sesión para añadir una Inteligencia Artificial")
        return redirect(url_for("users.index"))

    ia_types = list_ia_types()

    if request.method == "POST":
        name = request.form.get("name", "")

        try:
            create_ia_type(name=name, user_id=user_id)
            flash("inteligencia artificial añadida correctamente")
            return redirect(url_for("ia.create"))
        except UnauthorizedIAError as exc:
            return (
                render_template(
                    "ia/create.html",
                    error=str(exc),
                    name=name,
                    ia_types=ia_types,
                ),
                403,
            )
        except IAServiceError as exc:
            return (
                render_template(
                    "ia/create.html",
                    error=str(exc),
                    name=name,
                    ia_types=ia_types,
                ),
                400,
            )

    return render_template("ia/create.html", ia_types=ia_types)