from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    session,
    flash
)

from extensions import db
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
            "Usuario o contraseña incorrectos.",
            "error"
        )

    return render_template(
        "auth/login.html"
    )


@auth_bp.route(
    "/register",
    methods=["GET", "POST"]
)
def register():

    if request.method == "POST":

        name = request.form.get("name", "").strip()
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        password_confirmation = request.form.get(
            "password_confirmation",
            ""
        )

        if not name or not username or not password:
            flash(
                "Completa todos los campos.",
                "error"
            )
            return render_template("auth/register.html")

        if len(name) > 120 or len(username) > 80:
            flash(
                "El nombre o el usuario supera el máximo permitido.",
                "error"
            )
            return render_template("auth/register.html")

        if len(password) < 8:
            flash(
                "La contraseña debe tener al menos 8 caracteres.",
                "error"
            )
            return render_template("auth/register.html")

        if password != password_confirmation:
            flash(
                "Las contraseñas no coinciden.",
                "error"
            )
            return render_template("auth/register.html")

        if User.query.filter_by(username=username).first():
            flash(
                "Ese nombre de usuario ya está en uso.",
                "error"
            )
            return render_template("auth/register.html")

        user = User(
            name=name,
            username=username,
            role="reseller",
            active=True
        )
        user.set_password(password)

        db.session.add(user)
        db.session.commit()

        flash(
            "Cuenta creada correctamente. Ya puedes iniciar sesión.",
            "success"
        )
        return redirect(url_for("auth.login"))

    return render_template("auth/register.html")


@auth_bp.route("/logout")
def logout():

    session.clear()

    return redirect(
        url_for("auth.login")
    )
