from datetime import date, timedelta

from flask import (
    Blueprint,
    render_template,
    session,
    redirect,
    url_for
)

from models.sale import Sale

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

    if session.get("role") == "reseller":
        return redirect(url_for("reseller.index"))

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

    daily_totals = {}
    for sale in verified:
        if sale.sale_date:
            sale_day = sale.sale_date.date()
            daily_totals[sale_day] = (
                daily_totals.get(sale_day, 0) + float(sale.price)
            )

    for i in range(6, -1, -1):

        current = today - timedelta(days=i)

        labels.append(
            current.strftime("%d/%m")
        )

        values.append(daily_totals.get(current, 0))

    recent_sales = Sale.query.order_by(
        Sale.sale_date.desc(),
        Sale.id.desc()
    ).limit(5).all()

    return render_template(
        "dashboard/index.html",
        revenue=revenue,
        profit=profit,
        today_label=f"HOY · {today.strftime('%d/%m/%Y')}",
        expiring=expiring,
        verified_sales=len(verified),
        recent_sales=recent_sales,
        labels=labels,
        values=values
    )
