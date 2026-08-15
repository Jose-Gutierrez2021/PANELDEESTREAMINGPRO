from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    session
)

from extensions import db
from models.user import User


users_bp = Blueprint(
    "users",
    __name__,
    url_prefix="/users"
)


@users_bp.route(
    "/",
    methods=["GET", "POST"]
)
def index():

    if session.get("role") != "admin":

        return redirect(
            url_for("dashboard.index")
        )

    if request.method == "POST":

        user = User(
            name=request.form["name"],
            username=request.form["username"],
            role=request.form["role"]
        )

        user.set_password(
            request.form["password"]
        )

        db.session.add(user)

        db.session.commit()

        flash(
            "Usuario creado."
        )

        return redirect(
            url_for("users.index")
        )

    users = User.query.order_by(
        User.id.desc()
    ).all()

    return render_template(
        "users/index.html",
        users=users
    )
