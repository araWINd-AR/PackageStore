Package Store – Flask E-Commerce Website

This project is a simple e-commerce website built using Python and Flask.
The idea is to create a basic online store where users can browse products, search, filter, and manage a cart.

The design is inspired by modern beverage store websites, but the implementation is kept simple and beginner-friendly.

Project Overview

The website allows users to:

View products on the home and shop pages
Search products by name or type
Filter products by category (Wine, Beer, Spirits)
Add items to a cart
Remove items from the cart
View total price
Perform a simple checkout (clears cart)
View store details on the About page

The cart is handled using Flask sessions, so data is stored temporarily while the app is running.

Technologies Used
Python
Flask
HTML (Jinja templates)
CSS
JavaScript (basic interactions)
Project Structure
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
How to Run the Project
Download or clone the repository
git clone <your-repo-link>
cd package_store_flask_project
Install dependencies
pip install -r requirements.txt
Run the Flask app
python app.py
Open in browser
http://127.0.0.1:5000
Key Concepts Used
Flask routing using @app.route()
Template rendering using render_template()
Form and query handling using request
Session management for cart functionality
Basic frontend integration (HTML + CSS)
Limitations

This is a basic academic project, so:

No database is used (products are hardcoded)
Cart is not persistent (clears when session ends)
No user authentication/login
No real payment integration
Future Improvements

If extended further, the project can include:

Database integration (MySQL / SQLite)
User login and authentication
Persistent cart storage
Payment gateway integration
Admin panel for managing products
Author

Aravind Ganipisetty
MS in Computer Science
