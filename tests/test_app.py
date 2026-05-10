import os
import tempfile

import pytest

from app import ProductRepository, create_app


@pytest.fixture()
def client():
    db_fd, db_path = tempfile.mkstemp(suffix=".db")
    os.close(db_fd)

    app = create_app({
        "TESTING": True,
        "DATABASE_URL": db_path,
        "SECRET_KEY": "test-secret-key",
    })

    with app.test_client() as test_client:
        yield test_client

    if os.path.exists(db_path):
        os.remove(db_path)


def test_home_page_loads(client):
    response = client.get("/")
    assert response.status_code == 200
    assert b"Package" in response.data
    assert b"Generator keyword preview" in response.data


def test_shop_search_loads_matching_product(client):
    response = client.get("/shop?search=Cabernet")
    assert response.status_code == 200
    assert b"Napa Valley Cabernet" in response.data


def test_add_to_cart_updates_session(client):
    response = client.get("/add/1", follow_redirects=True)
    assert response.status_code == 200

    with client.session_transaction() as session:
        assert session["cart"]["1"] == 1


def test_cart_shows_realistic_checkout_fields(client):
    client.get("/add/1")
    response = client.get("/cart")
    assert response.status_code == 200
    assert b"Customer Details" in response.data
    assert b"Delivery Options" in response.data
    assert b"Payment Options" in response.data
    assert b"Demo Card Details" in response.data


def test_remove_from_cart_clears_item(client):
    client.get("/add/1")
    response = client.get("/remove/1", follow_redirects=True)
    assert response.status_code == 200

    with client.session_transaction() as session:
        assert "1" not in session.get("cart", {})


def test_checkout_creates_order_confirmation(client):
    client.get("/add/1")
    response = client.post(
        "/checkout",
        data={
            "full_name": "Demo Customer",
            "email": "demo@example.com",
            "phone": "2035550100",
            "delivery_method": "standard",
            "street": "123 Main Street",
            "city": "New Haven",
            "state": "CT",
            "zip_code": "06511",
            "payment_method": "card",
            "card_name": "Demo Customer",
            "card_number": "4242424242424242",
            "card_expiry": "12/30",
            "card_cvv": "123",
            "age_confirmed": "yes",
        },
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert b"Order Confirmed" in response.data
    assert b"Standard Delivery" in response.data
    assert b"Card ending in 4242" in response.data

    with client.session_transaction() as session:
        assert session.get("cart") == {}


def test_project_status_page_loads(client, monkeypatch):
    monkeypatch.setattr("app.fetch_project_status", lambda: {
        "source": "test",
        "repo": "araWINd-AR/PackageStore",
        "stars": 0,
        "language": "Python",
        "url": "https://github.com/araWINd-AR/PackageStore",
    })
    response = client.get("/project-status")
    assert response.status_code == 200
    assert b"araWINd-AR/PackageStore" in response.data


def test_market_watch_page_loads(client, monkeypatch):
    monkeypatch.setattr("app.fetch_market_watchlist", lambda: [
        {"ticker": "BUD", "last_price": "Demo", "currency": "USD", "source": "test"}
    ])
    response = client.get("/market-watch")
    assert response.status_code == 200
    assert b"BUD" in response.data


def test_register_and_login_session(client):
    register_response = client.post("/register", data={
        "full_name": "Demo User",
        "email": "demo@example.com",
        "password": "password123",
    }, follow_redirects=True)
    assert register_response.status_code == 200

    with client.session_transaction() as session:
        assert session["user_email"] == "demo@example.com"

    client.get("/logout")
    login_response = client.post("/login", data={
        "email": "demo@example.com",
        "password": "password123",
    }, follow_redirects=True)
    assert login_response.status_code == 200

    with client.session_transaction() as session:
        assert session["user_email"] == "demo@example.com"
