from datetime import date, timedelta

from flask import (
    Blueprint,
    render_template,
    session,
    redirect,
    url_for
)

from models.sale import Sale
from models.customer import Customer



dashboard_bp = Blueprint(
    "dashboard",
    __name__
)


@dashboard_bp.route("/")
def index():

    if "user_id" not in session:

        return redirect(
            url_for("auth.login")
        )

    sales = Sale.query.all()

    verified = [
        sale
        for sale in sales
        if sale.payment_status == "verified"
    ]

    revenue = sum(
        float(sale.price)
        for sale in verified
    )

    profit = sum(
        float(sale.price) -
        float(sale.cost)
        for sale in verified
    )

    today = date.today()

    expiring = Sale.query.filter(
        Sale.expires_at >= today,
        Sale.expires_at <= (
            today + timedelta(days=7)
        ),
        Sale.status == "active"
    ).count()

    labels = []

    values = []

    for i in range(6, -1, -1):

        current = today - timedelta(days=i)

        labels.append(
            current.strftime("%d/%m")
        )

        total = sum(
            float(sale.price)
            for sale in verified
            if sale.sale_date.date() == current
        )

        values.append(total)

    return render_template(
        "dashboard/index.html",
        revenue=revenue,
        profit=profit,
        customers=Customer.query.count(),
        expiring=expiring,
        labels=labels,
        values=values
    )
