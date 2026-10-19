from app import create_app
from extensions import db
from models.product import Product

app = create_app()

with app.app_context():
    products = Product.query.order_by(Product.id).all()

    if not products:
        print("No products found.")
    else:
        for p in products:
            print(
                f"{p.id}\t{p.name}\t{p.provider}\tactive={p.active}\tsale_price={float(p.sale_price)}\tcost_price={float(p.cost_price)}"
            )
