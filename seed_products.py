from app import create_app
from extensions import db
from models.product import Product

streaming = [
    "Netflix",
    "Disney+",
    "Max",
    "Prime Video",
    "Paramount+",
    "Crunchyroll",
    "Apple TV+",
    "ViX",
    "Star+",
    "Hulu",
]

music = [
    "Spotify",
    "Apple Music",
    "YouTube Music",
    "Deezer",
    "Tidal",
    "Amazon Music",
]

app = create_app()

inserted = []

with app.app_context():
    for name in streaming:
        if not Product.query.filter_by(name=name).first():
            p = Product(
                name=name,
                provider="Streaming",
                duration_days=30,
                sale_price=0,
                cost_price=0,
                active=True,
            )
            db.session.add(p)
            inserted.append(name)

    for name in music:
        if not Product.query.filter_by(name=name).first():
            p = Product(
                name=name,
                provider="Música",
                duration_days=30,
                sale_price=0,
                cost_price=0,
                active=True,
            )
            db.session.add(p)
            inserted.append(name)

    if inserted:
        db.session.commit()

print(f"Inserted products: {inserted}")
