# Package Store Flask Website

This updated project includes the required Flask route, try/except handling, object-oriented Python classes, SQLite database storage, Bootstrap CSS framework, and inventory stock behavior.

## Implemented Requirements

- Flask route format: `http://127.0.0.1:5000/remove/<product_id>`
  - Example: `http://127.0.0.1:5000/remove/1`
- Object-oriented implementation:
  - `DatabaseManager`
  - `ProductRepository`
  - `CartService`
- SQL database:
  - SQLite database is created automatically at `data/package_store.db`
  - Product stock is stored in the `products` table
- CSS framework:
  - Bootstrap 5 is linked in `templates/base.html`
- Pythonic implementation:
  - classes, helper methods, context managers, list comprehensions, and clean route logic
- Try/except format:
  - database routes use `try`, `except sqlite3.Error`, and flash messages
- Inventory behavior:
  - when a user adds an item to cart, product stock decreases by 1
  - when a user removes an item from cart, product stock is restored
  - out-of-stock products cannot be added

## Run Locally

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# macOS/Linux
source venv/bin/activate

pip install -r requirements.txt
python app.py
```

Open:

```text
http://127.0.0.1:5000/
```

## Main Files Updated

```text
app.py
requirements.txt
templates/base.html
templates/home.html
templates/shop.html
templates/product_card.html
templates/cart.html
static/css/style.css
```
