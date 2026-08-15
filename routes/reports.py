from flask import (
    Blueprint,
    render_template,
    session,
    redirect,
    url_for
)

from models.sale import Sale


reports_bp = Blueprint(
    "reports",
    __name__,
    url_prefix="/reports"
)


@reports_bp.route("/")
def index():

    if session.get("role") != "admin":

        return redirect(
            url_for("dashboard.index")
        )

    sales = Sale.query.filter_by(
        payment_status="verified"
    ).order_by(
        Sale.sale_date.desc()
    ).all()

    total = sum(
        float(s.price)
        for s in sales
    )

    profit = sum(
        float(s.price) -
        float(s.cost)
        for s in sales
    )

    return render_template(
        "reports/index.html",
        sales=sales,
        total=total,
        profit=profit
    )
