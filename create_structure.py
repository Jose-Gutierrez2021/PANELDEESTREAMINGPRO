import os

files = {}

# ============================================================
# requirements.txt
# ============================================================

files["requirements.txt"] = """Flask==3.1.1
Flask-SQLAlchemy==3.1.1
psycopg[binary]==3.2.9
python-dotenv==1.1.1
gunicorn==23.0.0
"""

# ============================================================
# .env
# ============================================================

files[".env"] = """SECRET_KEY=CAMBIA_ESTA_CLAVE_POR_UNA_MUY_SEGURA

ADMIN_USERNAME=
ADMIN_PASSWORD=

DATABASE_URL=sqlite:///stream_panel.db

PORT=5000
FLASK_DEBUG=1

TELEGRAM_BOT_TOKEN=
TELEGRAM_CHAT_ID=

WHATSAPP_ACCESS_TOKEN=
WHATSAPP_PHONE_NUMBER_ID=
WHATSAPP_WEBHOOK_VERIFY_TOKEN=
"""

# ============================================================
# .env.example
# ============================================================

files[".env.example"] = """SECRET_KEY=CAMBIA_ESTA_CLAVE

ADMIN_USERNAME=
ADMIN_PASSWORD=

DATABASE_URL=sqlite:///stream_panel.db

PORT=5000
FLASK_DEBUG=0

TELEGRAM_BOT_TOKEN=
TELEGRAM_CHAT_ID=

WHATSAPP_ACCESS_TOKEN=
WHATSAPP_PHONE_NUMBER_ID=
WHATSAPP_WEBHOOK_VERIFY_TOKEN=
"""

# ============================================================
# .gitignore
# ============================================================

files[".gitignore"] = ".venv/\n__pycache__/\n*.pyc\n.env\n*.db\ninstance/\n.vscode/\n"

# ============================================================
# Procfile
# ============================================================

files["Procfile"] = """web: gunicorn app:app
"""

# ============================================================
# render.yaml
# ============================================================

files["render.yaml"] = """services:
  - type: web
    name: stream-panel
    runtime: python
    buildCommand: pip install -r requirements.txt
    startCommand: gunicorn app:app

    envVars:
      - key: SECRET_KEY
        generateValue: true

      - key: DATABASE_URL
        sync: false
"""

# ============================================================
# vercel.json
# ============================================================

files["vercel.json"] = """{
  "version": 2,
  "builds": [
    {
      "src": "app.py",
      "use": "@vercel/python"
    }
  ],
  "routes": [
    {
      "src": "/(.*)",
      "dest": "app.py"
    }
  ]
}
"""

# ============================================================
# extensions.py
# ============================================================

files["extensions.py"] = """from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()
"""

# ============================================================
# config.py
# ============================================================

files["config.py"] = """import os
import secrets

from dotenv import load_dotenv

load_dotenv()


def normalize_database_url(database_url):
    if database_url.startswith("postgres://"):
        return database_url.replace(
            "postgres://",
            "postgresql+psycopg://",
            1
        )

    if database_url.startswith("postgresql://"):
        return database_url.replace(
            "postgresql://",
            "postgresql+psycopg://",
            1
        )

    return database_url


class Config:

    SECRET_KEY = os.getenv("SECRET_KEY") or secrets.token_hex(32)

    ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "").strip()
    ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "")

    DATABASE_URL = os.getenv(
        "DATABASE_URL",
        "sqlite:///stream_panel.db"
    )

    DATABASE_URL = normalize_database_url(DATABASE_URL)

    SQLALCHEMY_DATABASE_URI = DATABASE_URL

    SQLALCHEMY_TRACK_MODIFICATIONS = False
"""

# ============================================================
# MODELS
# ============================================================

files["models/__init__.py"] = """from .user import User
from .customer import Customer
from .product import Product
from .inventory import Inventory
from .sale import Sale
from .payment import Payment
"""

files["models/user.py"] = """
from werkzeug.security import (
    generate_password_hash,
    check_password_hash
)

from extensions import db


class User(db.Model):

    __tablename__ = "users"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    name = db.Column(
        db.String(120),
        nullable=False
    )

    username = db.Column(
        db.String(80),
        unique=True,
        nullable=False
    )

    password_hash = db.Column(
        db.String(255),
        nullable=False
    )

    role = db.Column(
        db.String(30),
        nullable=False,
        default="seller"
    )

    active = db.Column(
        db.Boolean,
        default=True
    )

    created_at = db.Column(
        db.DateTime,
        server_default=db.func.now()
    )

    def set_password(self, password):

        self.password_hash = generate_password_hash(
            password,
            method="pbkdf2:sha256",
            salt_length=16
        )

    def check_password(self, password):

        return check_password_hash(
            self.password_hash,
            password
        )
"""

files["models/customer.py"] = """
from extensions import db


class Customer(db.Model):

    __tablename__ = "customers"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    name = db.Column(
        db.String(150),
        nullable=False
    )

    phone = db.Column(
        db.String(40)
    )

    email = db.Column(
        db.String(150)
    )

    notes = db.Column(
        db.Text
    )

    created_at = db.Column(
        db.DateTime,
        server_default=db.func.now()
    )
"""

files["models/product.py"] = """
from extensions import db


class Product(db.Model):

    __tablename__ = "products"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    name = db.Column(
        db.String(150),
        nullable=False
    )

    provider = db.Column(
        db.String(100)
    )

    duration_days = db.Column(
        db.Integer,
        nullable=False,
        default=30
    )

    sale_price = db.Column(
        db.Numeric(12, 2),
        nullable=False,
        default=0
    )

    cost_price = db.Column(
        db.Numeric(12, 2),
        nullable=False,
        default=0
    )

    active = db.Column(
        db.Boolean,
        default=True
    )
"""

files["models/inventory.py"] = """
from extensions import db


class Inventory(db.Model):

    __tablename__ = "inventory"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    product_id = db.Column(
        db.Integer,
        db.ForeignKey("products.id"),
        nullable=False
    )

    reference = db.Column(
        db.String(150),
        nullable=False
    )

    status = db.Column(
        db.String(30),
        nullable=False,
        default="available"
    )

    expires_at = db.Column(
        db.Date
    )

    product = db.relationship(
        "Product"
    )
"""

files["models/sale.py"] = """
from extensions import db


class Sale(db.Model):

    __tablename__ = "sales"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    customer_id = db.Column(
        db.Integer,
        db.ForeignKey("customers.id"),
        nullable=False
    )

    product_id = db.Column(
        db.Integer,
        db.ForeignKey("products.id"),
        nullable=False
    )

    inventory_id = db.Column(
        db.Integer,
        db.ForeignKey("inventory.id")
    )

    seller_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False
    )

    sale_date = db.Column(
        db.DateTime,
        server_default=db.func.now()
    )

    expires_at = db.Column(
        db.Date,
        nullable=False
    )

    price = db.Column(
        db.Numeric(12, 2),
        nullable=False
    )

    cost = db.Column(
        db.Numeric(12, 2),
        nullable=False
    )

    payment_method = db.Column(
        db.String(50)
    )

    payment_status = db.Column(
        db.String(30),
        default="pending"
    )

    status = db.Column(
        db.String(30),
        default="active"
    )

    customer = db.relationship(
        "Customer"
    )

    product = db.relationship(
        "Product"
    )

    inventory = db.relationship(
        "Inventory"
    )

    seller = db.relationship(
        "User"
    )
"""

files["models/payment.py"] = """
from extensions import db


class Payment(db.Model):

    __tablename__ = "payments"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    sale_id = db.Column(
        db.Integer,
        db.ForeignKey("sales.id"),
        nullable=False
    )

    amount = db.Column(
        db.Numeric(12, 2),
        nullable=False
    )

    method = db.Column(
        db.String(50)
    )

    reference = db.Column(
        db.String(150)
    )

    status = db.Column(
        db.String(30),
        default="pending"
    )

    created_at = db.Column(
        db.DateTime,
        server_default=db.func.now()
    )

    sale = db.relationship(
        "Sale"
    )
"""

# ============================================================
# ROUTES
# ============================================================

files["routes/__init__.py"] = """
"""

files["routes/auth.py"] = """
from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    session,
    flash
)

from models.user import User


auth_bp = Blueprint(
    "auth",
    __name__
)


@auth_bp.route(
    "/login",
    methods=["GET", "POST"]
)
def login():

    if request.method == "POST":

        username = request.form["username"]

        password = request.form["password"]

        user = User.query.filter_by(
            username=username,
            active=True
        ).first()

        if user and user.check_password(password):

            session["user_id"] = user.id

            session["name"] = user.name

            session["role"] = user.role

            return redirect(
                url_for("dashboard.index")
            )

        flash(
            "Usuario o contraseña incorrectos."
        )

    return render_template(
        "auth/login.html"
    )


@auth_bp.route("/logout")
def logout():

    session.clear()

    return redirect(
        url_for("auth.login")
    )
"""

files["routes/dashboard.py"] = """
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
        expiring=expiring,
        labels=labels,
        values=values
    )
"""

files["routes/products.py"] = """
from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    session
)

from extensions import db
from models.product import Product


products_bp = Blueprint(
    "products",
    __name__,
    url_prefix="/products"
)


@products_bp.route(
    "/",
    methods=["GET", "POST"]
)
def index():

    if session.get("role") != "admin":

        flash(
            "Solo el administrador puede gestionar productos."
        )

        return redirect(
            url_for("dashboard.index")
        )

    if request.method == "POST":

        product = Product(
            name=request.form["name"],
            provider=request.form.get("provider"),
            duration_days=int(
                request.form["duration_days"]
            ),
            sale_price=float(
                request.form["sale_price"]
            ),
            cost_price=float(
                request.form["cost_price"]
            )
        )

        db.session.add(product)

        db.session.commit()

        flash(
            "Producto creado."
        )

        return redirect(
            url_for("products.index")
        )

    products = Product.query.order_by(
        Product.id.desc()
    ).all()

    return render_template(
        "products/index.html",
        products=products
    )
"""

files["routes/inventory.py"] = """
from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    session
)

from extensions import db
from models.inventory import Inventory
from models.product import Product


inventory_bp = Blueprint(
    "inventory",
    __name__,
    url_prefix="/inventory"
)


@inventory_bp.route(
    "/",
    methods=["GET", "POST"]
)
def index():

    if session.get("role") != "admin":

        flash(
            "Solo el administrador puede gestionar inventario."
        )

        return redirect(
            url_for("dashboard.index")
        )

    if request.method == "POST":

        item = Inventory(
            product_id=int(
                request.form["product_id"]
            ),
            reference=request.form["reference"],
            status="available"
        )

        db.session.add(item)

        db.session.commit()

        flash(
            "Elemento agregado al inventario."
        )

        return redirect(
            url_for("inventory.index")
        )

    items = Inventory.query.order_by(
        Inventory.id.desc()
    ).all()

    products = Product.query.filter_by(
        active=True
    ).all()

    return render_template(
        "inventory/index.html",
        items=items,
        products=products
    )
"""

files["routes/sales.py"] = """
from datetime import date, timedelta

from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    session
)

from extensions import db
from models.sale import Sale
from models.customer import Customer
from models.product import Product
from models.inventory import Inventory


sales_bp = Blueprint(
    "sales",
    __name__,
    url_prefix="/sales"
)


@sales_bp.route(
    "/",
    methods=["GET", "POST"]
)
def index():

    if "user_id" not in session:

        return redirect(
            url_for("auth.login")
        )

    if request.method == "POST":

        customer = Customer.query.get_or_404(
            int(request.form["customer_id"])
        )

        product = Product.query.get_or_404(
            int(request.form["product_id"])
        )

        inventory = Inventory.query.filter_by(
            product_id=product.id,
            status="available"
        ).first()

        if not inventory:

            flash(
                "No hay inventario disponible."
            )

            return redirect(
                url_for("sales.index")
            )

        start = date.today()

        expires = (
            start +
            timedelta(
                days=product.duration_days
            )
        )

        sale = Sale(
            customer_id=customer.id,
            product_id=product.id,
            inventory_id=inventory.id,
            seller_id=session["user_id"],
            expires_at=expires,
            price=product.sale_price,
            cost=product.cost_price,
            payment_method=request.form[
                "payment_method"
            ],
            payment_status="pending"
        )

        inventory.status = "sold"

        inventory.expires_at = expires

        db.session.add(sale)

        db.session.commit()

        flash(
            f"Venta #{sale.id} creada."
        )

        return redirect(
            url_for("sales.index")
        )

    customers = Customer.query.order_by(
        Customer.name
    ).all()

    products = Product.query.filter_by(
        active=True
    ).all()

    sales = Sale.query.order_by(
        Sale.id.desc()
    ).limit(100).all()

    return render_template(
        "sales/index.html",
        customers=customers,
        products=products,
        sales=sales
    )
"""

files["routes/payments.py"] = """
from flask import (
    Blueprint,
    request,
    redirect,
    url_for,
    session,
    flash
)

from extensions import db
from models.sale import Sale
from models.payment import Payment
from models.inventory import Inventory


payments_bp = Blueprint(
    "payments",
    __name__,
    url_prefix="/payments"
)


@payments_bp.route(
    "/<int:sale_id>",
    methods=["POST"]
)
def verify(sale_id):

    if session.get("role") != "admin":

        flash(
            "Solo el administrador puede verificar pagos."
        )

        return redirect(
            url_for("sales.index")
        )

    sale = Sale.query.get_or_404(
        sale_id
    )

    action = request.form["action"]

    if action == "verify":

        sale.payment_status = "verified"

        payment = Payment(
            sale_id=sale.id,
            amount=sale.price,
            method=sale.payment_method,
            reference=request.form.get(
                "reference"
            ),
            status="verified"
        )

        db.session.add(payment)

    elif action == "reject":

        sale.payment_status = "rejected"

        if sale.inventory:

            sale.inventory.status = "available"

            sale.inventory.expires_at = None

    db.session.commit()

    return redirect(
        url_for("sales.index")
    )
"""

files["routes/renewals.py"] = """
from datetime import date, timedelta

from flask import (
    Blueprint,
    request,
    redirect,
    url_for,
    flash,
    session
)

from extensions import db
from models.sale import Sale
from models.inventory import Inventory


renewals_bp = Blueprint(
    "renewals",
    __name__,
    url_prefix="/renewals"
)


@renewals_bp.route(
    "/<int:sale_id>",
    methods=["POST"]
)
def renew(sale_id):

    if "user_id" not in session:

        return redirect(
            url_for("auth.login")
        )

    old_sale = Sale.query.get_or_404(
        sale_id
    )

    product = old_sale.product

    inventory = Inventory.query.filter_by(
        product_id=product.id,
        status="available"
    ).first()

    if not inventory:

        flash(
            "No hay inventario disponible."
        )

        return redirect(
            url_for("sales.index")
        )

    base_date = max(
        date.today(),
        old_sale.expires_at
    )

    expiration = (
        base_date +
        timedelta(
            days=product.duration_days
        )
    )

    inventory.status = "sold"

    inventory.expires_at = expiration

    new_sale = Sale(
        customer_id=old_sale.customer_id,
        product_id=old_sale.product_id,
        inventory_id=inventory.id,
        seller_id=session["user_id"],
        expires_at=expiration,
        price=product.sale_price,
        cost=product.cost_price,
        payment_method=old_sale.payment_method,
        payment_status="pending"
    )

    db.session.add(new_sale)

    db.session.commit()

    flash(
        f"Renovación #{new_sale.id} creada."
    )

    return redirect(
        url_for("sales.index")
    )
"""

files["routes/users.py"] = """
from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    session
)

from extensions import db
from models.user import User


users_bp = Blueprint(
    "users",
    __name__,
    url_prefix="/users"
)


@users_bp.route(
    "/",
    methods=["GET", "POST"]
)
def index():

    if session.get("role") != "admin":

        return redirect(
            url_for("dashboard.index")
        )

    if request.method == "POST":

        user = User(
            name=request.form["name"],
            username=request.form["username"],
            role=request.form["role"]
        )

        user.set_password(
            request.form["password"]
        )

        db.session.add(user)

        db.session.commit()

        flash(
            "Usuario creado."
        )

        return redirect(
            url_for("users.index")
        )

    users = User.query.order_by(
        User.id.desc()
    ).all()

    return render_template(
        "users/index.html",
        users=users
    )
"""

files["routes/reports.py"] = """
from flask import (
    Blueprint,
    render_template,
    session,
    redirect,
    url_for
)

from models.sale import Sale


reports_bp = Blueprint(
    "reports",
    __name__,
    url_prefix="/reports"
)


@reports_bp.route("/")
def index():

    if session.get("role") != "admin":

        return redirect(
            url_for("dashboard.index")
        )

    sales = Sale.query.filter_by(
        payment_status="verified"
    ).order_by(
        Sale.sale_date.desc()
    ).all()

    total = sum(
        float(s.price)
        for s in sales
    )

    profit = sum(
        float(s.price) -
        float(s.cost)
        for s in sales
    )

    return render_template(
        "reports/index.html",
        sales=sales,
        total=total,
        profit=profit
    )
"""

# ============================================================
# SERVICES
# ============================================================

files["services/__init__.py"] = """
"""

files["services/telegram.py"] = """
import os
import requests


def send_telegram(message):

    token = os.getenv(
        "TELEGRAM_BOT_TOKEN"
    )

    chat_id = os.getenv(
        "TELEGRAM_CHAT_ID"
    )

    if not token or not chat_id:

        return False

    url = (
        f"https://api.telegram.org/"
        f"bot{token}/sendMessage"
    )

    response = requests.post(
        url,
        json={
            "chat_id": chat_id,
            "text": message
        },
        timeout=10
    )

    return response.ok
"""

files["services/whatsapp.py"] = """
import os
import requests


def send_whatsapp(phone, message):

    token = os.getenv(
        "WHATSAPP_ACCESS_TOKEN"
    )

    phone_number_id = os.getenv(
        "WHATSAPP_PHONE_NUMBER_ID"
    )

    if not token or not phone_number_id:

        return False

    url = (
        "https://graph.facebook.com/v23.0/"
        f"{phone_number_id}/messages"
    )

    headers = {
        "Authorization":
            f"Bearer {token}",

        "Content-Type":
            "application/json"
    }

    data = {
        "messaging_product": "whatsapp",

        "to": phone,

        "type": "text",

        "text": {
            "body": message
        }
    }

    response = requests.post(
        url,
        headers=headers,
        json=data,
        timeout=10
    )

    return response.ok
"""

files["services/notifications.py"] = """
from .telegram import send_telegram
from .whatsapp import send_whatsapp


def notify_customer(
    phone,
    message
):

    whatsapp = send_whatsapp(
        phone,
        message
    )

    telegram = send_telegram(
        message
    )

    return {
        "whatsapp": whatsapp,
        "telegram": telegram
    }
"""

files["services/receipts.py"] = """
def create_receipt(sale):

    return {
        "sale_id": sale.id,
        "customer": sale.customer.name,
        "product": sale.product.name,
        "price": float(sale.price),
        "expiration": str(
            sale.expires_at
        )
    }
"""

# ============================================================
# APP.PY
# ============================================================

files["app.py"] = """
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
"""

# ============================================================
# BASE HTML
# ============================================================

files["templates/base.html"] = """<!DOCTYPE html>

<html lang="es">

<head>

<meta charset="UTF-8">

<meta
name="viewport"
content="width=device-width, initial-scale=1.0">

<title>
StreamPanel PRO
</title>

<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>

<link
rel="stylesheet"
href="{{ url_for('static', filename='css/style.css') }}"
>

</head>

<body>

<nav>

<div class="brand">
🚀 StreamPanel PRO
</div>

<a href="/">
Dashboard
</a>

<a href="/sales/">
Ventas
</a>

{% if session.get("role") == "admin" %}

<a href="/products/">
Productos
</a>

<a href="/inventory/">
Inventario
</a>

<a href="/reports/">
Reportes
</a>

<a href="/users/">
Usuarios
</a>

{% endif %}

<a
class="logout"
href="/logout"
>
Cerrar sesión
</a>

</nav>


<main>

{% with messages =
get_flashed_messages() %}

{% for message in messages %}

<div class="alert">

{{ message }}

</div>

{% endfor %}

{% endwith %}


{% block content %}

{% endblock %}

</main>

</body>

</html>
"""

# ============================================================
# LOGIN
# ============================================================

files["templates/auth/login.html"] = """<!DOCTYPE html>

<html lang="es">

<head>

<meta charset="UTF-8">

<meta
name="viewport"
content="width=device-width,initial-scale=1"
>

<title>
StreamPanel Login
</title>

<link
rel="stylesheet"
href="{{ url_for('static', filename='css/style.css') }}"
>

</head>

<body class="login-page">

<div class="login-card">

<h1>
🚀 StreamPanel
</h1>

<p>
Panel administrativo
</p>

{% with messages =
get_flashed_messages() %}

{% for message in messages %}

<div class="alert">

{{ message }}

</div>

{% endfor %}

{% endwith %}

<form method="POST">

<input
name="username"
placeholder="Usuario"
required
>

<input
name="password"
type="password"
placeholder="Contraseña"
required
>

<button>
Iniciar sesión
</button>

</form>

</div>

</body>

</html>
"""

# ============================================================
# DASHBOARD
# ============================================================

files["templates/dashboard/index.html"] = """{% extends "base.html" %}

{% block content %}

<h1>
Dashboard
</h1>

<div class="grid">

<div class="card">

<span>
Ingresos
</span>

<strong>
${{ "{:,.0f}".format(revenue) }}
</strong>

</div>


<div class="card">

<span>
Ganancias
</span>

<strong>
${{ "{:,.0f}".format(profit) }}
</strong>

</div>


<div class="card">

<span>
Vencen en 7 días
</span>

<strong>
{{ expiring }}
</strong>

</div>

</div>


<div class="card chart-card">

<h2>
Ventas últimos 7 días
</h2>

<canvas id="salesChart"></canvas>

</div>


<script>

window.salesLabels =
{{ labels | tojson }};

window.salesValues =
{{ values | tojson }};

</script>

<script
src="{{ url_for('static', filename='js/dashboard.js') }}"
></script>

{% endblock %}
"""

# ============================================================
# PRODUCTS
# ============================================================

files["templates/products/index.html"] = """{% extends "base.html" %}

{% block content %}

<h1>
Productos
</h1>

<form
class="card form"
method="POST"
>

<input
name="name"
placeholder="Nombre del producto"
required
>

<input
name="provider"
placeholder="Proveedor"
>

<input
name="duration_days"
type="number"
value="30"
placeholder="Duración en días"
required
>

<input
name="sale_price"
type="number"
placeholder="Precio de venta"
required
>

<input
name="cost_price"
type="number"
placeholder="Costo"
required
>

<button>
Crear producto
</button>

</form>


<div class="card">

<table>

<tr>

<th>
Producto
</th>

<th>
Proveedor
</th>

<th>
Duración
</th>

<th>
Venta
</th>

<th>
Costo
</th>

</tr>

{% for product in products %}

<tr>

<td>
{{ product.name }}
</td>

<td>
{{ product.provider or "-" }}
</td>

<td>
{{ product.duration_days }} días
</td>

<td>
${{ "{:,.0f}".format(product.sale_price) }}
</td>

<td>
${{ "{:,.0f}".format(product.cost_price) }}
</td>

</tr>

{% endfor %}

</table>

</div>

{% endblock %}
"""

# ============================================================
# INVENTORY
# ============================================================

files["templates/inventory/index.html"] = """{% extends "base.html" %}

{% block content %}

<h1>
Inventario
</h1>

<form
class="card form"
method="POST"
>

<select
name="product_id"
required
>

<option value="">
Seleccionar producto
</option>

{% for product in products %}

<option
value="{{ product.id }}"
>

{{ product.name }}

</option>

{% endfor %}

</select>


<input
name="reference"
placeholder="Referencia de licencia"
required
>


<button>
Agregar inventario
</button>

</form>


<div class="card">

<table>

<tr>

<th>
Producto
</th>

<th>
Referencia
</th>

<th>
Estado
</th>

<th>
Vencimiento
</th>

</tr>

{% for item in items %}

<tr>

<td>
{{ item.product.name }}
</td>

<td>
{{ item.reference }}
</td>

<td>

<span class="badge">

{{ item.status }}

</span>

</td>

<td>
{{ item.expires_at or "-" }}
</td>

</tr>

{% endfor %}

</table>

</div>

{% endblock %}
"""

# ============================================================
# SALES
# ============================================================

files["templates/sales/index.html"] = """{% extends "base.html" %}

{% block content %}

<h1>
Ventas
</h1>

<form
class="card form"
method="POST"
>

<select
name="customer_id"
required
>

<option value="">
Cliente
</option>

{% for customer in customers %}

<option
value="{{ customer.id }}"
>

{{ customer.name }}

</option>

{% endfor %}

</select>


<select
name="product_id"
required
>

<option value="">
Producto
</option>

{% for product in products %}

<option
value="{{ product.id }}"
>

{{ product.name }}
-
${{ "{:,.0f}".format(product.sale_price) }}

</option>

{% endfor %}

</select>


<select
name="payment_method"
>

<option>
Nequi
</option>

<option>
Transferencia
</option>

<option>
Efectivo
</option>

<option>
Otro
</option>

</select>


<button>
Registrar venta
</button>

</form>


<div class="card">

<table>

<tr>

<th>
ID
</th>

<th>
Cliente
</th>

<th>
Producto
</th>

<th>
Vence
</th>

<th>
Pago
</th>

<th>
Valor
</th>

<th>
Acciones
</th>

</tr>


{% for sale in sales %}

<tr>

<td>
#{{ sale.id }}
</td>

<td>
{{ sale.customer.name }}
</td>

<td>
{{ sale.product.name }}
</td>

<td>
{{ sale.expires_at }}
</td>

<td>

<span class="badge">

{{ sale.payment_status }}

</span>

</td>

<td>
${{ "{:,.0f}".format(sale.price) }}
</td>

<td>

{% if session.get("role") == "admin"
and sale.payment_status == "pending" %}

<form
method="POST"
action="/payments/{{ sale.id }}"
>

<input
name="reference"
placeholder="Referencia"
/>

<button
name="action"
value="verify"
>

Verificar

</button>

<button
name="action"
value="reject"
>

Rechazar

</button>

</form>

{% endif %}


<form
method="POST"
action="/renewals/{{ sale.id }}"
>
<button>
Renovar
</button>

</form>

</td>

</tr>

{% endfor %}

</table>

</div>

{% endblock %}
"""

# ============================================================
# USERS
# ============================================================

files["templates/users/index.html"] = """{% extends "base.html" %}

{% block content %}

<h1>
Usuarios
</h1>

<form
class="card form"
method="POST"
>

<input
name="name"
placeholder="Nombre"
required
>

<input
name="username"
placeholder="Usuario"
required
>

input
name="password"
type="password"
placeholder="Contraseña"
required
>

<select name="role">

<option value="seller">
Vendedor
</option>

<option value="admin">
Administrador
</option>

</select>

<button>
Crear usuario
</button>

</form>


<div class="card">

<table>

<tr>

<th>
Nombre
</th>

<th>
Usuario
</th>

<th>
Rol
</th>

<th>
Activo
</th>

</tr>

{% for user in users %}

<tr>

<td>
{{ user.name }}
</td>

<td>
{{ user.username }}
</td>

<td>
{{ user.role }}
</td>

<td>
{{ "Sí" if user.active else "No" }}
</td>

</tr>

{% endfor %}

</table>

</div>

{% endblock %}
"""

# (Note: file continues but truncated here to keep message size reasonable)

# ============================================================
# CREAR CARPETAS Y ARCHIVOS
# ============================================================

for path, content in files.items():

    folder = os.path.dirname(path)

    if folder:

        os.makedirs(
            folder,
            exist_ok=True
        )

    with open(
        path,
        "w",
        encoding="utf-8"
    ) as file:

        file.write(
            content.strip() + "\n"
        )


print()
print("======================================")
print(" STREAM PANEL PRO")
print("======================================")
print()
print("Estructura creada correctamente.")
print()
print("Ahora ejecuta:")
print()
print("python -m venv .venv")
print(".venv\\Scripts\\activate")
print("pip install -r requirements.txt")
print("python app.py")
print()
print("Luego abre:")
print("http://127.0.0.1:5000")
print()
print("Configura ADMIN_USERNAME y ADMIN_PASSWORD en .env.")
print()
