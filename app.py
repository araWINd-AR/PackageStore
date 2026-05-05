import os
import sqlite3
from contextlib import contextmanager
from typing import Dict, List, Optional, Tuple

from flask import Flask, flash, redirect, render_template, request, session, url_for

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE_PATH = os.path.join(BASE_DIR, "data", "package_store.db")

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


class DatabaseManager:
    """Handles SQLite connection, table creation, and seed data."""

    def __init__(self, database_path: str):
        self.database_path = database_path
        self.initialize_database()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.database_path)
        connection.row_factory = sqlite3.Row
        return connection

    @contextmanager
    def connection(self):
        connection = self._connect()
        try:
            yield connection
            connection.commit()
        except sqlite3.Error:
            connection.rollback()
            raise
        finally:
            connection.close()

    def initialize_database(self) -> None:
        os.makedirs(os.path.dirname(self.database_path), exist_ok=True)
        with self.connection() as connection:
            connection.execute(
                """
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
            )

            for product in DEFAULT_PRODUCTS:
                existing_product = connection.execute(
                    "SELECT id FROM products WHERE id = ?", (product["id"],)
                ).fetchone()

                if existing_product is None:
                    connection.execute(
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
    def _to_dict(row: Optional[sqlite3.Row]) -> Optional[dict]:
        return dict(row) if row else None

    def get_categories(self) -> List[str]:
        with self.database.connection() as connection:
            rows = connection.execute(
                "SELECT DISTINCT category FROM products ORDER BY category"
            ).fetchall()
        return ["All", *[row["category"] for row in rows]]

    def get_featured_products(self, limit: int = 4) -> List[dict]:
        with self.database.connection() as connection:
            rows = connection.execute(
                "SELECT * FROM products ORDER BY id LIMIT ?", (limit,)
            ).fetchall()
        return [dict(row) for row in rows]

    def search_products(self, selected_category: str = "All", search_text: str = "") -> List[dict]:
        search_value = f"%{search_text.strip()}%"

        if selected_category == "All":
            query = """
                SELECT * FROM products
                WHERE name LIKE ? OR type LIKE ? OR category LIKE ?
                ORDER BY category, name
            """
            parameters = (search_value, search_value, search_value)
        else:
            query = """
                SELECT * FROM products
                WHERE category = ? AND (name LIKE ? OR type LIKE ? OR category LIKE ?)
                ORDER BY name
            """
            parameters = (selected_category, search_value, search_value, search_value)

        with self.database.connection() as connection:
            rows = connection.execute(query, parameters).fetchall()
        return [dict(row) for row in rows]

    def find_product(self, product_id: int) -> Optional[dict]:
        with self.database.connection() as connection:
            row = connection.execute(
                "SELECT * FROM products WHERE id = ?", (product_id,)
            ).fetchone()
        return self._to_dict(row)

    def decrease_stock(self, product_id: int, quantity: int = 1) -> bool:
        """Decrease inventory only when enough stock exists."""
        with self.database.connection() as connection:
            result = connection.execute(
                """
                UPDATE products
                SET stock = stock - ?
                WHERE id = ? AND stock >= ?
                """,
                (quantity, product_id, quantity),
            )
        return result.rowcount == 1

    def increase_stock(self, product_id: int, quantity: int = 1) -> None:
        with self.database.connection() as connection:
            connection.execute(
                "UPDATE products SET stock = stock + ? WHERE id = ?",
                (quantity, product_id),
            )


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
        total = 0.0

        for product_id_text, quantity in self.get_cart().items():
            product = product_repository.find_product(int(product_id_text))
            if product:
                subtotal = product["price"] * quantity
                total += subtotal
                cart_items.append(
                    {"product": product, "qty": quantity, "subtotal": subtotal}
                )

        return cart_items, total


def create_app() -> Flask:
    app = Flask(__name__)
    app.secret_key = os.environ.get("SECRET_KEY", "package-store-secret")

    database = DatabaseManager(DATABASE_PATH)
    product_repository = ProductRepository(database)
    cart_service = CartService()

    @app.context_processor
    def inject_common_values():
        return {"cart_count": cart_service.count_items()}

    @app.route("/")
    def home():
        try:
            return render_template(
                "home.html",
                products=product_repository.get_featured_products(),
                categories=product_repository.get_categories(),
            )
        except sqlite3.Error as error:
            app.logger.exception("Home page database error: %s", error)
            flash("Database error while loading the home page.", "danger")
            return render_template("home.html", products=[], categories=["All"])

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
        except sqlite3.Error as error:
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

        except sqlite3.Error as error:
            app.logger.exception("Add to cart database error: %s", error)
            flash("Could not add product because of a database error.", "danger")
        except ValueError as error:
            app.logger.exception("Invalid product id: %s", error)
            flash("Invalid product selected.", "danger")

        return redirect(request.referrer or url_for("shop"))

    @app.route("/cart")
    def cart():
        try:
            items, total = cart_service.build_cart_items(product_repository)
            return render_template("cart.html", items=items, total=total)
        except sqlite3.Error as error:
            app.logger.exception("Cart page database error: %s", error)
            flash("Database error while loading your cart.", "danger")
            return render_template("cart.html", items=[], total=0)

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

        except sqlite3.Error as error:
            app.logger.exception("Remove from cart database error: %s", error)
            flash("Could not remove product because of a database error.", "danger")
        except ValueError as error:
            app.logger.exception("Invalid remove product id: %s", error)
            flash("Invalid product selected.", "danger")

        return redirect(url_for("cart"))

    @app.route("/checkout", methods=["POST"])
    def checkout():
        cart_service.clear()
        flash("Demo order placed successfully. Stock changes are saved in SQLite.", "success")
        return redirect(url_for("home"))

    @app.route("/about")
    def about():
        return render_template("about.html")

    return app


app = create_app()

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)
