import logging
import os
import random
import sqlite3
from contextlib import contextmanager
from typing import Dict, Iterable, Iterator, List, Optional, Tuple

import requests
from flask import Flask, flash, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE_PATH = os.path.join(BASE_DIR, "data", "package_store.db")
DATABASE_URL = os.environ.get("DATABASE_URL", DATABASE_PATH)
GITHUB_REPO_API_URL = "https://api.github.com/repos/araWINd-AR/PackageStore"
MARKET_TICKERS = ["BUD", "DEO", "STZ"]
SALES_TAX_RATE = 0.0635

DELIVERY_OPTIONS = {
    "pickup": {"label": "Store Pickup", "fee": 0.00, "eta": "Ready today"},
    "standard": {"label": "Standard Delivery", "fee": 5.99, "eta": "2-3 business days"},
    "express": {"label": "Express Delivery", "fee": 12.99, "eta": "Next business day"},
}

PAYMENT_OPTIONS = {
    "card": "Credit / Debit Card",
    "paypal": "PayPal",
    "apple_pay": "Apple Pay",
    "pickup": "Pay at Pickup",
}

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

# Dictionary-based seed data requirement.
DEFAULT_PRODUCTS = [
    {"id": 1, "name": "Napa Valley Cabernet", "category": "Wine", "type": "Red", "price": 24.99, "tag": "Staff Pick", "image": "🍷", "stock": 12},
    {"id": 2, "name": "Italian Pinot Grigio", "category": "Wine", "type": "White", "price": 16.49, "tag": "New", "image": "🥂", "stock": 10},
    {"id": 3, "name": "Sparkling Rosé", "category": "Wine", "type": "Sparkling", "price": 19.99, "tag": "On Sale", "image": "🍾", "stock": 8},
    {"id": 4, "name": "Premium Bourbon Whiskey", "category": "Spirits", "type": "Whiskey", "price": 39.99, "tag": "Popular", "image": "🥃", "stock": 7},
    {"id": 5, "name": "Classic Vodka", "category": "Spirits", "type": "Vodka", "price": 21.99, "tag": "Deal", "image": "🍸", "stock": 11},
    {"id": 6, "name": "Silver Tequila", "category": "Spirits", "type": "Tequila", "price": 29.99, "tag": "Top Rated", "image": "🍹", "stock": 9},
    {"id": 7, "name": "Local Craft IPA 6 Pack", "category": "Beer", "type": "IPA", "price": 12.99, "tag": "Local", "image": "🍺", "stock": 16},
    {"id": 8, "name": "Light Lager 12 Pack", "category": "Beer", "type": "Lager", "price": 15.99, "tag": "Best Value", "image": "🍻", "stock": 14},
]


def money(value: float) -> float:
    """Small pure helper function used by checkout calculations."""
    return round(float(value), 2)


class DatabaseManager:
    """Object-oriented database layer: SQLite by default, PostgreSQL through DATABASE_URL."""

    def __init__(self, database_url: str):
        self.database_url = database_url
        self.is_postgres = database_url.startswith(("postgresql://", "postgres://"))
        self.initialize_database()

    def _connect(self):
        if self.is_postgres:
            import psycopg2
            from psycopg2.extras import RealDictCursor

            return psycopg2.connect(self.database_url, cursor_factory=RealDictCursor)

        sqlite_path = self.database_url
        if sqlite_path != ":memory:":
            data_directory = os.path.dirname(os.path.abspath(sqlite_path))
            if data_directory:
                os.makedirs(data_directory, exist_ok=True)

        connection = sqlite3.connect(sqlite_path)
        connection.row_factory = sqlite3.Row
        return connection

    def placeholder(self) -> str:
        return "%s" if self.is_postgres else "?"

    def create_products_table_sql(self) -> str:
        if self.is_postgres:
            return """
                CREATE TABLE IF NOT EXISTS products (
                    id INTEGER PRIMARY KEY,
                    name VARCHAR(255) NOT NULL,
                    category VARCHAR(80) NOT NULL,
                    type VARCHAR(80) NOT NULL,
                    price NUMERIC(10, 2) NOT NULL,
                    tag VARCHAR(80) NOT NULL,
                    image VARCHAR(20) NOT NULL,
                    stock INTEGER NOT NULL CHECK(stock >= 0)
                )
            """

        return """
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                category TEXT NOT NULL,
                type TEXT NOT NULL,
                price REAL NOT NULL,
                tag TEXT NOT NULL,
                image TEXT NOT NULL,
                stock INTEGER NOT NULL CHECK(stock >= 0)
            )
        """

    def create_users_table_sql(self) -> str:
        if self.is_postgres:
            return """
                CREATE TABLE IF NOT EXISTS users (
                    id SERIAL PRIMARY KEY,
                    full_name VARCHAR(120) NOT NULL,
                    email VARCHAR(255) UNIQUE NOT NULL,
                    password_hash VARCHAR(255) NOT NULL
                )
            """

        return """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                full_name TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL
            )
        """

    @contextmanager
    def connection(self):
        """Generator/context-manager pattern. The yield makes this a generator-based helper."""
        connection = self._connect()
        try:
            yield connection
            connection.commit()
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()

    def initialize_database(self) -> None:
        with self.connection() as connection:
            cursor = connection.cursor()
            cursor.execute(self.create_products_table_sql())
            cursor.execute(self.create_users_table_sql())

            for product in DEFAULT_PRODUCTS:
                placeholder = self.placeholder()
                cursor.execute(f"SELECT id FROM products WHERE id = {placeholder}", (product["id"],))
                existing_product = cursor.fetchone()

                if existing_product is None:
                    if self.is_postgres:
                        cursor.execute(
                            """
                            INSERT INTO products (id, name, category, type, price, tag, image, stock)
                            VALUES (%(id)s, %(name)s, %(category)s, %(type)s, %(price)s, %(tag)s, %(image)s, %(stock)s)
                            """,
                            product,
                        )
                    else:
                        cursor.execute(
                            """
                            INSERT INTO products (id, name, category, type, price, tag, image, stock)
                            VALUES (:id, :name, :category, :type, :price, :tag, :image, :stock)
                            """,
                            product,
                        )


class ProductRepository:
    """Object-oriented database operations for products and inventory."""

    def __init__(self, database: DatabaseManager):
        self.database = database

    @staticmethod
    def _to_dict(row) -> Optional[dict]:
        return dict(row) if row else None

    def get_categories(self) -> List[str]:
        with self.database.connection() as connection:
            cursor = connection.cursor()
            cursor.execute("SELECT DISTINCT category FROM products ORDER BY category")
            rows = cursor.fetchall()
        # List comprehension requirement.
        return ["All", *[row["category"] for row in rows]]

    def get_all_products(self) -> List[dict]:
        with self.database.connection() as connection:
            cursor = connection.cursor()
            cursor.execute("SELECT * FROM products ORDER BY id")
            rows = cursor.fetchall()
        # List comprehension requirement.
        return [dict(row) for row in rows]

    def keyword_generator(self, products: Iterable[dict]) -> Iterator[str]:
        """Explicit generator requirement: yields searchable product keywords."""
        for product in products:
            yield product["name"].lower()
            yield product["category"].lower()
            yield product["type"].lower()

    def get_featured_products(self, limit: int = 4) -> List[dict]:
        """Uses random library and slicing to choose homepage products."""
        products = self.get_all_products()
        random.shuffle(products)
        return products[:limit]  # slicing requirement

    def search_products(self, selected_category: str = "All", search_text: str = "") -> List[dict]:
        placeholder = self.database.placeholder()
        search_value = f"%{search_text.strip()}%"

        if selected_category == "All":
            query = f"""
                SELECT * FROM products
                WHERE name LIKE {placeholder} OR type LIKE {placeholder} OR category LIKE {placeholder}
                ORDER BY category, name
            """
            parameters = (search_value, search_value, search_value)
        else:
            query = f"""
                SELECT * FROM products
                WHERE category = {placeholder}
                AND (name LIKE {placeholder} OR type LIKE {placeholder} OR category LIKE {placeholder})
                ORDER BY name
            """
            parameters = (selected_category, search_value, search_value, search_value)

        with self.database.connection() as connection:
            cursor = connection.cursor()
            cursor.execute(query, parameters)
            rows = cursor.fetchall()

        products = [dict(row) for row in rows]
        # Functional programming requirement: filter/lambda keeps valid products.
        valid_products = filter(lambda product: product["stock"] >= 0, products)
        return list(valid_products)

    def get_in_stock_products(self) -> List[dict]:
        """Functional programming example using filter/lambda."""
        products = self.get_all_products()
        return list(filter(lambda product: product["stock"] > 0, products))

    def find_product(self, product_id: int) -> Optional[dict]:
        placeholder = self.database.placeholder()
        with self.database.connection() as connection:
            cursor = connection.cursor()
            cursor.execute(f"SELECT * FROM products WHERE id = {placeholder}", (product_id,))
            row = cursor.fetchone()
        return self._to_dict(row)

    def decrease_stock(self, product_id: int, quantity: int = 1) -> bool:
        """Decrease inventory only when enough stock exists."""
        placeholder = self.database.placeholder()
        with self.database.connection() as connection:
            cursor = connection.cursor()
            cursor.execute(
                f"""
                UPDATE products
                SET stock = stock - {placeholder}
                WHERE id = {placeholder} AND stock >= {placeholder}
                """,
                (quantity, product_id, quantity),
            )
            rowcount = cursor.rowcount
        return rowcount == 1

    def increase_stock(self, product_id: int, quantity: int = 1) -> None:
        placeholder = self.database.placeholder()
        with self.database.connection() as connection:
            cursor = connection.cursor()
            cursor.execute(
                f"UPDATE products SET stock = stock + {placeholder} WHERE id = {placeholder}",
                (quantity, product_id),
            )


class UserRepository:
    """Simple user-management operations for registration and login sessions."""

    def __init__(self, database: DatabaseManager):
        self.database = database

    def find_by_email(self, email: str) -> Optional[dict]:
        placeholder = self.database.placeholder()
        with self.database.connection() as connection:
            cursor = connection.cursor()
            cursor.execute(f"SELECT * FROM users WHERE email = {placeholder}", (email.lower().strip(),))
            row = cursor.fetchone()
        return dict(row) if row else None

    def create_user(self, full_name: str, email: str, password: str) -> bool:
        if self.find_by_email(email):
            return False

        placeholder = self.database.placeholder()
        password_hash = generate_password_hash(password)
        with self.database.connection() as connection:
            cursor = connection.cursor()
            cursor.execute(
                f"""
                INSERT INTO users (full_name, email, password_hash)
                VALUES ({placeholder}, {placeholder}, {placeholder})
                """,
                (full_name.strip(), email.lower().strip(), password_hash),
            )
        return True

    def validate_login(self, email: str, password: str) -> bool:
        user = self.find_by_email(email)
        if not user:
            return False
        return check_password_hash(user["password_hash"], password)


class CartService:
    """Session-based cart logic kept separate from route functions."""

    @staticmethod
    def get_cart() -> Dict[str, int]:
        return session.get("cart", {})

    def count_items(self) -> int:
        return sum(self.get_cart().values())

    def add_item(self, product_id: int) -> None:
        cart = self.get_cart()
        product_id_key = str(product_id)
        cart[product_id_key] = cart.get(product_id_key, 0) + 1
        session["cart"] = cart
        session.modified = True

    def remove_item(self, product_id: int) -> int:
        cart = self.get_cart()
        product_id_key = str(product_id)
        removed_quantity = cart.pop(product_id_key, 0)
        session["cart"] = cart
        session.modified = True
        return removed_quantity

    def clear(self) -> None:
        session["cart"] = {}
        session.modified = True

    def build_cart_items(self, product_repository: ProductRepository) -> Tuple[List[dict], float]:
        cart_items = []
        subtotal = 0.0

        # Explicit iterator requirement.
        cart_iterator = iter(self.get_cart().items())
        for product_id_text, quantity in cart_iterator:
            product = product_repository.find_product(int(product_id_text))
            if product:
                item_subtotal = money(product["price"] * quantity)
                subtotal += item_subtotal
                cart_items.append({"product": product, "qty": quantity, "subtotal": item_subtotal})

        return cart_items, money(subtotal)

    def build_order_summary(self, subtotal: float, delivery_method: str = "pickup") -> dict:
        delivery = DELIVERY_OPTIONS.get(delivery_method, DELIVERY_OPTIONS["pickup"])
        tax = money(subtotal * SALES_TAX_RATE)
        delivery_fee = money(delivery["fee"])
        total = money(subtotal + tax + delivery_fee)
        return {
            "subtotal": money(subtotal),
            "tax": tax,
            "delivery_fee": delivery_fee,
            "total": total,
            "delivery_label": delivery["label"],
            "delivery_eta": delivery["eta"],
        }


def fetch_project_status() -> dict:
    """Uses the requests library with a safe fallback for offline demos."""
    try:
        response = requests.get(GITHUB_REPO_API_URL, timeout=3)
        response.raise_for_status()
        data = response.json()
        return {
            "source": "GitHub API using requests",
            "repo": data.get("full_name", "araWINd-AR/PackageStore"),
            "stars": data.get("stargazers_count", 0),
            "language": data.get("language", "Python"),
            "url": data.get("html_url", "https://github.com/araWINd-AR/PackageStore"),
        }
    except requests.RequestException as error:
        logging.warning("Requests API fallback used: %s", error)
        return {
            "source": "Offline fallback after requests exception handling",
            "repo": "araWINd-AR/PackageStore",
            "stars": "Unavailable offline",
            "language": "Python / Flask",
            "url": "https://github.com/araWINd-AR/PackageStore",
        }


def fetch_market_watchlist() -> List[dict]:
    """Uses yFinance to show related beverage-company stock data with fallback values."""
    try:
        import yfinance as yf

        market_rows = []
        for ticker in MARKET_TICKERS:
            stock = yf.Ticker(ticker)
            fast_info = stock.fast_info
            last_price = fast_info.get("last_price") or 0
            market_rows.append(
                {
                    "ticker": ticker,
                    "last_price": money(last_price),
                    "currency": fast_info.get("currency", "USD"),
                    "source": "yFinance live data",
                }
            )
        return market_rows
    except Exception as error:
        logging.warning("yFinance fallback used: %s", error)
        return [
            {"ticker": "BUD", "last_price": "Demo unavailable", "currency": "USD", "source": "Offline fallback"},
            {"ticker": "DEO", "last_price": "Demo unavailable", "currency": "USD", "source": "Offline fallback"},
            {"ticker": "STZ", "last_price": "Demo unavailable", "currency": "USD", "source": "Offline fallback"},
        ]


def create_app(test_config: Optional[dict] = None) -> Flask:
    app = Flask(__name__)
    app.secret_key = os.environ.get("SECRET_KEY", "package-store-secret")

    if test_config:
        app.config.update(test_config)

    database_url = app.config.get("DATABASE_URL", DATABASE_URL)
    database = DatabaseManager(database_url)
    product_repository = ProductRepository(database)
    user_repository = UserRepository(database)
    cart_service = CartService()

    @app.context_processor
    def inject_common_values():
        return {
            "cart_count": cart_service.count_items(),
            "current_user_email": session.get("user_email"),
        }

    @app.route("/")
    def home():
        try:
            products = product_repository.get_featured_products()
            keyword_preview = list(product_repository.keyword_generator(products))[:6]
            return render_template(
                "home.html",
                products=products,
                categories=product_repository.get_categories(),
                in_stock_count=len(product_repository.get_in_stock_products()),
                keyword_preview=keyword_preview,
            )
        except Exception as error:
            app.logger.exception("Home page database error: %s", error)
            flash("Database error while loading the home page.", "danger")
            return render_template("home.html", products=[], categories=["All"], in_stock_count=0, keyword_preview=[])

    @app.route("/shop")
    def shop():
        selected_category = request.args.get("category", "All")
        search_text = request.args.get("search", "")

        try:
            return render_template(
                "shop.html",
                products=product_repository.search_products(selected_category, search_text),
                categories=product_repository.get_categories(),
                selected=selected_category,
                search=search_text,
            )
        except Exception as error:
            app.logger.exception("Shop page database error: %s", error)
            flash("Database error while loading products.", "danger")
            return render_template(
                "shop.html",
                products=[],
                categories=["All"],
                selected="All",
                search=search_text,
            )

    @app.route("/add/<int:product_id>")
    def add_to_cart(product_id: int):
        try:
            product = product_repository.find_product(product_id)

            if product is None:
                flash("Product was not found.", "warning")
            elif product["stock"] <= 0:
                flash(f"{product['name']} is currently out of stock.", "warning")
            elif product_repository.decrease_stock(product_id):
                cart_service.add_item(product_id)
                flash(f"{product['name']} added to cart. Inventory stock decreased by 1.", "success")
            else:
                flash(f"{product['name']} is currently out of stock.", "warning")

        except Exception as error:
            app.logger.exception("Add to cart error: %s", error)
            flash("Could not add product because of an application error.", "danger")

        return redirect(request.referrer or url_for("shop"))

    @app.route("/cart")
    def cart():
        try:
            items, subtotal = cart_service.build_cart_items(product_repository)
            default_summary = cart_service.build_order_summary(subtotal, "pickup")
            return render_template(
                "cart.html",
                items=items,
                total=subtotal,
                order_summary=default_summary,
                delivery_options=DELIVERY_OPTIONS,
                payment_options=PAYMENT_OPTIONS,
            )
        except Exception as error:
            app.logger.exception("Cart page database error: %s", error)
            flash("Database error while loading your cart.", "danger")
            return render_template(
                "cart.html",
                items=[],
                total=0,
                order_summary=cart_service.build_order_summary(0, "pickup"),
                delivery_options=DELIVERY_OPTIONS,
                payment_options=PAYMENT_OPTIONS,
            )

    @app.route("/remove/<int:product_id>")
    def remove_from_cart(product_id: int):
        """Correct URL format: http://127.0.0.1:5000/remove/1"""
        try:
            removed_quantity = cart_service.remove_item(product_id)

            if removed_quantity > 0:
                product_repository.increase_stock(product_id, removed_quantity)
                flash("Product removed from cart. Inventory stock restored.", "info")
            else:
                flash("Product was not in your cart.", "warning")

        except Exception as error:
            app.logger.exception("Remove from cart error: %s", error)
            flash("Could not remove product because of an application error.", "danger")

        return redirect(url_for("cart"))

    @app.route("/checkout", methods=["POST"])
    def checkout():
        try:
            items, subtotal = cart_service.build_cart_items(product_repository)
            if not items:
                flash("Your cart is empty.", "warning")
                return redirect(url_for("cart"))

            full_name = request.form.get("full_name", "").strip()
            email = request.form.get("email", "").strip()
            phone = request.form.get("phone", "").strip()
            delivery_method = request.form.get("delivery_method", "pickup")
            payment_method = request.form.get("payment_method", "")
            age_confirmed = request.form.get("age_confirmed") == "yes"

            required_fields = [full_name, email, phone, delivery_method, payment_method]
            if not all(required_fields):
                flash("Please complete customer details, delivery method, and payment method.", "warning")
                return redirect(url_for("cart"))

            if not age_confirmed:
                flash("Please confirm that you are 21 or older before placing the order.", "warning")
                return redirect(url_for("cart"))

            if payment_method == "card":
                card_fields = [
                    request.form.get("card_name", "").strip(),
                    request.form.get("card_number", "").strip(),
                    request.form.get("card_expiry", "").strip(),
                    request.form.get("card_cvv", "").strip(),
                ]
                if not all(card_fields):
                    flash("Please complete the demo card details or choose another payment option.", "warning")
                    return redirect(url_for("cart"))

            summary = cart_service.build_order_summary(subtotal, delivery_method)
            order_number = f"PS-{random.randint(100000, 999999)}"
            last_four = request.form.get("card_number", "")[-4:] if payment_method == "card" else ""

            session["last_order"] = {
                "order_number": order_number,
                "customer": full_name,
                "email": email,
                "phone": phone,
                "delivery_label": summary["delivery_label"],
                "delivery_eta": summary["delivery_eta"],
                "payment_label": PAYMENT_OPTIONS.get(payment_method, "Demo Payment"),
                "card_last_four": last_four,
                "subtotal": summary["subtotal"],
                "tax": summary["tax"],
                "delivery_fee": summary["delivery_fee"],
                "total": summary["total"],
                "items": [{"name": item["product"]["name"], "qty": item["qty"], "subtotal": item["subtotal"]} for item in items],
            }
            cart_service.clear()
            flash("Demo order placed successfully. This project does not process real payments or store card details.", "success")
            return redirect(url_for("order_confirmation"))
        except Exception as error:
            app.logger.exception("Checkout error: %s", error)
            flash("Could not place the demo order because of an application error.", "danger")
            return redirect(url_for("cart"))

    @app.route("/order-confirmation")
    def order_confirmation():
        order = session.get("last_order")
        if not order:
            flash("No recent order found.", "warning")
            return redirect(url_for("home"))
        return render_template("order_confirmation.html", order=order)

    @app.route("/project-status")
    def project_status():
        status = fetch_project_status()
        return render_template("project_status.html", status=status)

    @app.route("/market-watch")
    def market_watch():
        market_rows = fetch_market_watchlist()
        return render_template("market_watch.html", market_rows=market_rows)

    @app.route("/register", methods=["GET", "POST"])
    def register():
        if request.method == "POST":
            full_name = request.form.get("full_name", "").strip()
            email = request.form.get("email", "").strip().lower()
            password = request.form.get("password", "")

            if not full_name or not email or not password:
                flash("Please complete all registration fields.", "warning")
                return redirect(url_for("register"))

            try:
                if user_repository.create_user(full_name, email, password):
                    session["user_email"] = email
                    flash("Account created successfully. You are now logged in.", "success")
                    return redirect(url_for("home"))
                flash("An account with this email already exists.", "warning")
            except Exception as error:
                app.logger.exception("Registration error: %s", error)
                flash("Could not create account because of an application error.", "danger")

        return render_template("register.html")

    @app.route("/login", methods=["GET", "POST"])
    def login():
        if request.method == "POST":
            email = request.form.get("email", "").strip().lower()
            password = request.form.get("password", "")

            try:
                if user_repository.validate_login(email, password):
                    session["user_email"] = email
                    flash("Logged in successfully.", "success")
                    return redirect(url_for("home"))
                flash("Invalid email or password.", "danger")
            except Exception as error:
                app.logger.exception("Login error: %s", error)
                flash("Could not log in because of an application error.", "danger")

        return render_template("login.html")

    @app.route("/logout")
    def logout():
        session.pop("user_email", None)
        flash("Logged out successfully.", "info")
        return redirect(url_for("home"))

    @app.route("/about")
    def about():
        return render_template("about.html")

    return app


app = create_app()

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)
