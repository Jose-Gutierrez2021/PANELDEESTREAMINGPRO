from flask import Flask, url_for
from pathlib import Path

from config import Config
from extensions import db
from services.product_brands import get_product_brand


MUSIC_CONTENT_TYPES = {
    ".aac": "audio/aac",
    ".flac": "audio/flac",
    ".m4a": "audio/mp4",
    ".mp3": "audio/mpeg",
    ".oga": "audio/ogg",
    ".ogg": "audio/ogg",
    ".wav": "audio/wav",
    ".weba": "audio/webm",
}


def create_app():

    app = Flask(__name__)

    app.config.from_object(
        Config
    )

    @app.context_processor
    def provide_music_playlist():
        music_directory = Path(app.static_folder) / "music"
        tracks = []
        if music_directory.is_dir():
            for path in sorted(
                music_directory.iterdir(),
                key=lambda item: item.name.casefold(),
            ):
                content_type = MUSIC_CONTENT_TYPES.get(path.suffix.casefold())
                if path.is_file() and content_type:
                    is_known_track = path.stem == "peli-de-terror-koddy-g"
                    tracks.append(
                        {
                            "src": url_for(
                                "static",
                                filename=f"music/{path.name}",
                            ),
                            "title": "Peli De Terror" if is_known_track else path.stem,
                            "artist": "Køddy G" if is_known_track else "Audio local",
                        }
                    )

        return {"music_tracks": tracks}

    @app.context_processor
    def provide_product_brand_lookup():
        return {"product_brand": get_product_brand}

    db.init_app(app)

    from routes.auth import auth_bp
    from routes.dashboard import dashboard_bp
    from routes.products import products_bp
    from routes.inventory import inventory_bp
    from routes.sales import sales_bp
    from routes.payments import payments_bp
    from routes.renewals import renewals_bp
    from routes.users import users_bp
    from routes.reports import reports_bp
    from routes.wallet import wallet_bp
    from routes.reseller import reseller_bp

    app.register_blueprint(
        auth_bp
    )

    app.register_blueprint(
        dashboard_bp
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

    app.register_blueprint(wallet_bp)
    app.register_blueprint(reseller_bp)

    with app.app_context():

        from models import (
            User,
            Customer,
            Product,
            Inventory,
            Sale,
            Payment,
            WholesaleOffer,
            Wallet,
            WalletTopUp,
            WalletMovement,
            ResellerOrder,
            ResellerStock,
            ResellerPricing,
        )

        db.create_all()

        admin = User.query.filter_by(
            username=Config.ADMIN_USERNAME or "admin"
        ).first()

        if not admin:
            if bool(Config.ADMIN_USERNAME) != bool(Config.ADMIN_PASSWORD):
                raise RuntimeError(
                    "Configura ADMIN_USERNAME y ADMIN_PASSWORD juntos."
                )

            if Config.ADMIN_USERNAME:
                if len(Config.ADMIN_PASSWORD) < 12:
                    raise RuntimeError(
                        "ADMIN_PASSWORD debe tener al menos 12 caracteres."
                    )

                admin = User(
                    name="Administrador",
                    username=Config.ADMIN_USERNAME,
                    role="admin"
                )

                admin.set_password(Config.ADMIN_PASSWORD)

                db.session.add(admin)
                db.session.commit()
            else:
                app.logger.warning(
                    "No hay una cuenta administradora. Configura "
                    "ADMIN_USERNAME y ADMIN_PASSWORD para crearla."
                )

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
