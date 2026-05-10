# Package Store Flask Website

Final-project version of a Flask-based Package Store web app. The application lets users browse beverage products, search and filter inventory, register/login, add items to a session cart, remove items from the cart, and complete a realistic demo checkout with customer details, delivery options, payment choices, tax, delivery fee, and order confirmation.

## GitHub Repo

https://github.com/araWINd-AR/PackageStore

## Implemented Assignment Features

- Decorators
  - Flask route decorators such as `@app.route(...)`
  - `@contextmanager` for database connection handling
- Generators
  - `DatabaseManager.connection()` uses `yield`
  - `ProductRepository.keyword_generator()` yields product search keywords
- Iterators
  - `CartService.build_cart_items()` uses `iter(session_cart.items())`
- Object Oriented Design
  - `DatabaseManager`
  - `ProductRepository`
  - `UserRepository`
  - `CartService`
- Functional Programming
  - `filter()` and `lambda` are used for in-stock and valid product filtering
- Comprehensions
  - Product/category/result conversion uses list comprehensions
- Dictionary
  - Product seed data, delivery options, payment options, and order summaries use dictionaries
- MySQL or Postgres Database
  - SQLite runs by default for easy local demo
  - PostgreSQL is supported through the `DATABASE_URL` environment variable
- Requests Library
  - `/project-status` uses `requests` to fetch GitHub repo information with an offline fallback
- Random Library
  - Random homepage featured products and demo order number generation
- yFinance Library
  - `/market-watch` uses `yfinance` for beverage-related company watchlist data with an offline fallback
- Generated `requirements.txt`
- Used Logging
  - Logs request/yFinance/database/checkout failures
- Exception Handling
  - `try/except` blocks protect routes, database operations, API calls, and checkout
- Created Test Cases
  - Pytest tests are in `tests/test_app.py`
- Used a Responsive UI Framework
  - Bootstrap 5 is included through CDN
- User Management/Auth and Session
  - Register, login, logout, hashed passwords, and Flask sessions
- CRUD Operation with Search
  - Search/filter products
  - Add cart item
  - Remove cart item
  - Clear cart on checkout
  - Inventory stock decreases/restores
- Used Slicing
  - Featured products are limited using slicing: `products[:limit]`

## Realistic Demo Checkout

The cart page now includes:

- Customer name, email, phone, and promo code fields
- Delivery options
  - Store Pickup
  - Standard Delivery
  - Express Delivery
- Delivery address fields
- Payment options
  - Credit/Debit Card
  - PayPal
  - Apple Pay
  - Pay at Pickup
- Demo card fields
- Age confirmation checkbox
- Subtotal, estimated tax, delivery fee, and final total
- Order confirmation/receipt page

Important: this project does **not** process real payments and does **not** store card information. It is a safe demo checkout for class.

## Important Routes

```text
http://127.0.0.1:5000/
http://127.0.0.1:5000/shop
http://127.0.0.1:5000/add/1
http://127.0.0.1:5000/remove/1
http://127.0.0.1:5000/cart
http://127.0.0.1:5000/checkout
http://127.0.0.1:5000/order-confirmation
http://127.0.0.1:5000/register
http://127.0.0.1:5000/login
http://127.0.0.1:5000/logout
http://127.0.0.1:5000/project-status
http://127.0.0.1:5000/market-watch
```

## Database

The app uses SQLite automatically:

```text
data/package_store.db
```

To use PostgreSQL instead, set a PostgreSQL connection string before running the app:

```bash
# macOS/Linux
export DATABASE_URL="postgresql://username:password@localhost:5432/package_store"

# Windows PowerShell
$env:DATABASE_URL="postgresql://username:password@localhost:5432/package_store"
```

The app creates the `products` and `users` tables automatically and seeds default products.

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

## Run Test Cases

```bash
pytest
```

## Main Files Updated

```text
app.py
requirements.txt
pytest.ini
README.md
tests/test_app.py
templates/base.html
templates/home.html
templates/shop.html
templates/product_card.html
templates/cart.html
templates/order_confirmation.html
templates/register.html
templates/login.html
templates/project_status.html
templates/market_watch.html
static/css/style.css
static/js/script.js
```
