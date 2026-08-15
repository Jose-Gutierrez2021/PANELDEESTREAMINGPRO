from flask import Flask

from config import Config
from extensions import db


def create_app():

    app = Flask(__name__)

    app.config.from_object(
        Config
    )

    db.init_app(app)

    from routes.auth import auth_bp
    from routes.dashboard import dashboard_bp
    from routes.customers import customers_bp
    from routes.products import products_bp
    from routes.inventory import inventory_bp
    from routes.sales import sales_bp
    from routes.payments import payments_bp
    from routes.renewals import renewals_bp
    from routes.users import users_bp
    from routes.reports import reports_bp

    app.register_blueprint(
        auth_bp
    )

    app.register_blueprint(
        dashboard_bp
    )

    app.register_blueprint(
        customers_bp
    )

    app.register_blueprint(
        products_bp
    )

    app.register_blueprint(
        inventory_bp
    )

    app.register_blueprint(
        sales_bp
    )

    app.register_blueprint(
        payments_bp
    )

    app.register_blueprint(
        renewals_bp
    )

    app.register_blueprint(
        users_bp
    )

    app.register_blueprint(
        reports_bp
    )

    with app.app_context():

        from models import (
            User,
            Customer,
            Product,
            Inventory,
            Sale,
            Payment
        )

        db.create_all()

        admin = User.query.filter_by(
            username="admin"
        ).first()

        if not admin:

            admin = User(
                name="Administrador",
                username="admin",
                role="admin"
            )

            admin.set_password(
                "Admin123!"
            )

            db.session.add(
                admin
            )

            db.session.commit()

    @app.route("/health")
    def health():

        return {
            "status": "ok"
        }

    return app


app = create_app()


if __name__ == "__main__":

    app.run(
        host="0.0.0.0",
        port=5000,
        debug=True
    )
