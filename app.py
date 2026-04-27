from flask import Flask, render_template, request, redirect, url_for, session

app = Flask(__name__)
app.secret_key = "package-store-secret"

# Product data used by the website
products = [
    {"id": 1, "name": "Napa Valley Cabernet", "category": "Wine", "type": "Red", "price": 24.99, "tag": "Staff Pick", "image": "🍷"},
    {"id": 2, "name": "Italian Pinot Grigio", "category": "Wine", "type": "White", "price": 16.49, "tag": "New", "image": "🥂"},
    {"id": 3, "name": "Sparkling Rosé", "category": "Wine", "type": "Sparkling", "price": 19.99, "tag": "On Sale", "image": "🍾"},
    {"id": 4, "name": "Premium Bourbon Whiskey", "category": "Spirits", "type": "Whiskey", "price": 39.99, "tag": "Popular", "image": "🥃"},
    {"id": 5, "name": "Classic Vodka", "category": "Spirits", "type": "Vodka", "price": 21.99, "tag": "Deal", "image": "🍸"},
    {"id": 6, "name": "Silver Tequila", "category": "Spirits", "type": "Tequila", "price": 29.99, "tag": "Top Rated", "image": "🍹"},
    {"id": 7, "name": "Local Craft IPA 6 Pack", "category": "Beer", "type": "IPA", "price": 12.99, "tag": "Local", "image": "🍺"},
    {"id": 8, "name": "Light Lager 12 Pack", "category": "Beer", "type": "Lager", "price": 15.99, "tag": "Best Value", "image": "🍻"},
]

categories = ["All", "Wine", "Spirits", "Beer"]


def count_cart_items():
    cart = session.get("cart", {})
    total_items = 0

    for product_id in cart:
        total_items = total_items + cart[product_id]

    return total_items


def find_product(product_id):
    for product in products:
        if product["id"] == product_id:
            return product
    return None


@app.route("/")
def home():
    featured_products = products[0:4]
    cart_count = count_cart_items()

    return render_template(
        "home.html",
        products=featured_products,
        categories=categories,
        cart_count=cart_count
    )


@app.route("/shop")
def shop():
    selected_category = request.args.get("category", "All")
    search_text = request.args.get("search", "")

    filtered_products = []

    for product in products:
        category_matches = selected_category == "All" or product["category"] == selected_category
        search_matches = search_text.lower() in product["name"].lower() or search_text.lower() in product["type"].lower()

        if category_matches and search_matches:
            filtered_products.append(product)

    cart_count = count_cart_items()

    return render_template(
        "shop.html",
        products=filtered_products,
        categories=categories,
        selected=selected_category,
        search=search_text,
        cart_count=cart_count
    )


@app.route("/add/<int:product_id>")
def add_to_cart(product_id):
    cart = session.get("cart", {})
    product_id_text = str(product_id)

    if product_id_text in cart:
        cart[product_id_text] = cart[product_id_text] + 1
    else:
        cart[product_id_text] = 1

    session["cart"] = cart
    return redirect(url_for("shop"))


@app.route("/cart")
def cart():
    cart = session.get("cart", {})
    cart_products = []
    total = 0

    for product_id_text in cart:
        product = find_product(int(product_id_text))
        quantity = cart[product_id_text]

        if product is not None:
            subtotal = product["price"] * quantity
            total = total + subtotal
            cart_products.append({"product": product, "qty": quantity, "subtotal": subtotal})

    cart_count = count_cart_items()

    return render_template("cart.html", items=cart_products, total=total, cart_count=cart_count)


@app.route("/remove/<int:product_id>")
def remove_from_cart(product_id):
    cart = session.get("cart", {})
    product_id_text = str(product_id)

    if product_id_text in cart:
        del cart[product_id_text]

    session["cart"] = cart
    return redirect(url_for("cart"))


@app.route("/checkout", methods=["POST"])
def checkout():
    session["cart"] = {}
    return redirect(url_for("home"))


@app.route("/about")
def about():
    cart_count = count_cart_items()
    return render_template("about.html", cart_count=cart_count)


if __name__ == "__main__":
    app.run(debug=True)
