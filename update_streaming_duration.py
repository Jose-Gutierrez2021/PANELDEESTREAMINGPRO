from app import create_app
from extensions import db
from models.product import Product

app = create_app()

updated = []

with app.app_context():
    streaming_products = Product.query.filter_by(provider="Streaming").all()
    for p in streaming_products:
        if p.duration_days != 30:
            p.duration_days = 30
            updated.append(p.name)
    if updated:
        db.session.commit()

print(f"Updated duration to 30 days for: {updated}")
