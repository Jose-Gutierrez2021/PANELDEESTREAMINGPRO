from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    session,
    flash
)

from models.user import User


auth_bp = Blueprint(
    "auth",
    __name__
)


@auth_bp.route(
    "/login",
    methods=["GET", "POST"]
)
def login():

    if request.method == "POST":

        username = request.form["username"]

        password = request.form["password"]

        user = User.query.filter_by(
            username=username,
            active=True
        ).first()

        if user and user.check_password(password):

            session["user_id"] = user.id

            session["name"] = user.name

            session["role"] = user.role

            return redirect(
                url_for("dashboard.index")
            )

        flash(
            "Usuario o contraseña incorrectos."
        )

    return render_template(
        "auth/login.html"
    )


@auth_bp.route("/logout")
def logout():

    session.clear()

    return redirect(
        url_for("auth.login")
    )
