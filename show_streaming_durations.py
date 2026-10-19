from app import create_app
from models.product import Product

app = create_app()

with app.app_context():
    streaming_products = Product.query.filter_by(provider="Streaming").order_by(Product.id).all()
    if not streaming_products:
        print("No streaming products found.")
    else:
        for p in streaming_products:
            print(f"{p.id}\t{p.name}\tduration_days={p.duration_days}")
