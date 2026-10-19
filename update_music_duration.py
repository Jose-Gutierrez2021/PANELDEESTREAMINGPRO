from app import create_app
from extensions import db
from models.product import Product

app = create_app()

updated = []

with app.app_context():
    music_products = Product.query.filter_by(provider="Música").all()
    # fallback: try without accent
    if not music_products:
        music_products = Product.query.filter_by(provider="Musica").all()

    for p in music_products:
        if p.duration_days != 30:
            p.duration_days = 30
            updated.append(p.name)
    if updated:
        db.session.commit()

print(f"Updated duration to 30 days for: {updated}")
