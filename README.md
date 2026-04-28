# Package Store – Flask E-Commerce Website

## Description

This project is a simple e-commerce website built using Python and Flask.  
The main goal of this project is to understand how an online store works, including product display, search, filtering, and cart functionality.

The design is inspired by modern beverage store websites, but the implementation is kept simple and beginner-friendly.

---

## Features

- View products on home and shop pages  
- Search products by name or type  
- Filter products by category (Wine, Beer, Spirits)  
- Add items to cart  
- Remove items from cart  
- View total price  
- Checkout option (clears cart)  
- About page with store details  

---

## Technologies Used

- Python  
- Flask  
- HTML (Jinja templates)  
- CSS  
- JavaScript  

---

## Project Structure

package_store_flask_project/
│
├── app.py  
├── requirements.txt  
│
├── templates/  
│   ├── index.html  
│   ├── shop.html  
│   ├── cart.html  
│   ├── about.html  
│   └── base.html  
│
├── static/  
│   ├── css/  
│   ├── js/  
│   └── images/  

---

## How to Run

1. Download or clone the project

2. Open terminal and go to project folder

3. Install dependencies

pip install -r requirements.txt

4. Run the app

python app.py

5. Open in browser

http://127.0.0.1:5000

---

## Key Concepts

- Flask routing using @app.route()  
- Template rendering using render_template()  
- Handling user input using request  
- Session usage for cart storage  
- Basic frontend integration  

---

## Limitations

- No database (products are hardcoded)  
- Cart is temporary (session-based)  
- No user login system  
- No real payment integration  

---

## Future Improvements

- Add database (MySQL / SQLite)  
- User authentication  
- Persistent cart  
- Payment gateway  
- Admin panel  

---

## Author

Aravind Ganipisetty  
MS in Computer Science
