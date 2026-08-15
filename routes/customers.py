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
from models.customer import Customer


customers_bp = Blueprint(
    "customers",
    __name__,
    url_prefix="/customers"
)


def required_login():

    return "user_id" in session


@customers_bp.route(
    "/",
    methods=["GET", "POST"]
)
def index():

    if not required_login():

        return redirect(
            url_for("auth.login")
        )

    if request.method == "POST":

        customer = Customer(
            name=request.form["name"],
            phone=request.form.get("phone"),
            email=request.form.get("email"),
            notes=request.form.get("notes")
        )

        db.session.add(customer)

        db.session.commit()

        flash(
            "Cliente creado correctamente."
        )

        return redirect(
            url_for("customers.index")
        )

    customers = Customer.query.order_by(
        Customer.id.desc()
    ).all()

    return render_template(
        "customers/index.html",
        customers=customers
    )
