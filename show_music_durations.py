from app import create_app
from models.product import Product

app = create_app()

with app.app_context():
    music = Product.query.filter_by(provider="Música").order_by(Product.id).all()
    if not music:
        music = Product.query.filter_by(provider="Musica").order_by(Product.id).all()
    for p in music:
        print(f"{p.id}\t{p.name}\tduration_days={p.duration_days}")
