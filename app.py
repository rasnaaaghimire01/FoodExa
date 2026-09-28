# app.py
# Main Flask application for Foodexa.
# All routes (pages) of the website are written in this file.

from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from datetime import date, timedelta
import mysql.connector
import math
import os
import time
import config

# Create the Flask app
app = Flask(__name__)

# Secret key is needed for Flask sessions and flash messages
app.secret_key = config.SECRET_KEY


# Connect to the MySQL database using the settings in config.py
# and return the connection.
def get_db_connection():
    connection = mysql.connector.connect(
        host=config.DB_HOST,
        user=config.DB_USER,
        password=config.DB_PASSWORD,
        database=config.DB_NAME
    )
    return connection


# Read all categories, count how many food items each one has,
# and find the lowest price in each category.
# Returns a list like: [{'category_id': 1, 'category_name': 'Momo', 'item_count': 3, 'starting_price': 140}, ...]
def get_all_categories():
    connection = get_db_connection()
    # dictionary=True gives each row as a dictionary, so we can use row['category_name']
    cursor = connection.cursor(dictionary=True)
    # LEFT JOIN keeps a category even if it has no food items (its count will be 0).
    # GROUP BY makes one row per category, COUNT counts its food items
    # and MIN finds the cheapest item in that category.
    cursor.execute(
        "SELECT c.category_id, c.category_name, "
        "COUNT(f.food_id) AS item_count, MIN(f.price) AS starting_price "
        "FROM categories c "
        "LEFT JOIN food_items f ON f.category_id = c.category_id "
        "GROUP BY c.category_id, c.category_name "
        "ORDER BY c.category_id"
    )
    categories = cursor.fetchall()
    cursor.close()
    connection.close()
    return categories


# =====================================================
# Food Menu: show food items, filter by category, search
# =====================================================

# Read food items from the database.
# If category_id is given, only that category is shown.
# If search_text is given, only items whose name contains it are shown.
def get_food_items(category_id, search_text):
    # Start with a query that returns every food item with its category name
    sql = (
        "SELECT f.food_id, f.category_id, f.name, f.price, f.description, f.image, c.category_name "
        "FROM food_items f "
        "JOIN categories c ON c.category_id = f.category_id "
        "WHERE 1 = 1"      # always true, so we can add more conditions with AND
    )
    values = []

    # Add the category filter only if a category was chosen
    if category_id != "":
        sql = sql + " AND f.category_id = %s"
        values.append(category_id)

    # Add the search filter only if something was typed.
    # LIKE with % on both sides means "name contains this text".
    if search_text != "":
        sql = sql + " AND f.name LIKE %s"
        values.append("%" + search_text + "%")

    sql = sql + " ORDER BY c.category_id, f.price"

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)
    cursor.execute(sql, values)
    food_items = cursor.fetchall()
    cursor.close()
    connection.close()
    return food_items


# Read one food item by its id. Returns None if it does not exist.
def get_food_item_by_id(food_id):
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)
    cursor.execute(
        "SELECT f.food_id, f.name, f.price, c.category_name "
        "FROM food_items f "
        "JOIN categories c ON c.category_id = f.category_id "
        "WHERE f.food_id = %s",
        (food_id,)
    )
    food = cursor.fetchone()
    cursor.close()
    connection.close()
    return food


# Show prices as money, for example 1200 becomes "Rs. 1,200".
# In templates we use it like this: {{ item.price | money }}
@app.template_filter("money")
def format_money(amount):
    return "Rs. " + format(amount, ",.0f")


# Check if an image file really exists inside the static/images folder.
# Templates use it to show the picture, or a placeholder if the file is missing.
# Example: image_exists("chicken_momo.jpg") or image_exists("icons/momo.png")
def image_exists(filename):
    if not filename:
        return False
    file_path = os.path.join(app.static_folder, "images", filename)
    return os.path.isfile(file_path)


# Make image_exists() usable inside every template
app.jinja_env.globals["image_exists"] = image_exists


# Read 4 popular dishes for the home page: the first food item of each category.
# The inner SELECT finds the smallest food_id in every category.
def get_featured_items():
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)
    cursor.execute(
        "SELECT f.food_id, f.category_id, f.name, f.price, f.description, f.image, c.category_name "
        "FROM food_items f "
        "JOIN categories c ON c.category_id = f.category_id "
        "WHERE f.food_id IN (SELECT MIN(food_id) FROM food_items GROUP BY category_id) "
        "ORDER BY c.category_id "
        "LIMIT 4"
    )
    featured_items = cursor.fetchall()
    cursor.close()
    connection.close()
    return featured_items


# Home page: welcome section, our speciality, 4 popular dishes and our location
@app.route("/")
def index():
    categories = get_all_categories()
    featured_items = get_featured_items()

    # Find the Momo category, because momo is our special dish,
    # and read all momo items to list them on the home page
    momo_category = None
    momo_items = []
    total_dishes = 0
    for category in categories:
        total_dishes = total_dishes + category["item_count"]
        if category["category_name"] == "Momo":
            momo_category = category
            momo_items = get_food_items(str(category["category_id"]), "")

    return render_template(
        "index.html",
        featured_items=featured_items,
        momo_category=momo_category,
        momo_items=momo_items,
        total_dishes=total_dishes
    )


# Menu page: shows all food items grouped by category,
# with a category filter and a search box.
@app.route("/menu")
def menu():
    # Read the filter and search values from the address bar, e.g. /menu?category=1&search=momo
    selected_category = request.args.get("category", "")
    search_text = request.args.get("search", "").strip()

    # The category must be a number. Ignore anything else.
    if not selected_category.isdigit():
        selected_category = ""

    categories = get_all_categories()

    # We read the items of ALL categories (only the search is used here).
    # The chosen category is shown and the others are hidden on the page,
    # so the category buttons can switch instantly without reloading the page.
    food_items = get_food_items("", search_text)

    # Group the food items by category, so the page can show
    # one heading per category with its items below it.
    menu = []
    for category in categories:
        dishes = []
        for item in food_items:
            if item["category_id"] == category["category_id"]:
                dishes.append(item)
        if len(dishes) > 0:
            menu.append({"category": category, "dishes": dishes})

    return render_template(
        "menu.html",
        categories=categories,
        menu=menu,
        selected_category=selected_category,
        search_text=search_text,
        total_found=len(food_items)
    )


# =====================================================
# User Management: register, login and logout
# =====================================================

# Find one user by email. Returns the user as a dictionary,
# or None if no user has this email.
def get_user_by_email(email):
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)
    # %s is a placeholder. MySQL puts the email there safely (stops SQL injection).
    cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
    user = cursor.fetchone()
    cursor.close()
    connection.close()
    return user


# Register page: shows the form (GET) and saves a new customer (POST)
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        # Read the values typed in the form
        name = request.form["name"].strip()
        email = request.form["email"].strip().lower()
        phone = request.form["phone"].strip()
        password = request.form["password"]
        confirm_password = request.form["confirm_password"]

        # Check the form values
        if name == "" or email == "" or phone == "" or password == "":
            flash("Please fill in all the fields.", "error")
            return render_template("register.html")

        if len(password) < 6:
            flash("Password must be at least 6 characters long.", "error")
            return render_template("register.html")

        if password != confirm_password:
            flash("Passwords do not match.", "error")
            return render_template("register.html")

        # The email must not be used by another account
        if get_user_by_email(email) is not None:
            flash("This email is already registered. Please log in.", "error")
            return render_template("register.html")

        # Hash the password before saving it
        hashed_password = generate_password_hash(password)

        # Save the new customer in the users table
        connection = get_db_connection()
        cursor = connection.cursor()
        cursor.execute(
            "INSERT INTO users (name, email, password, phone, role) VALUES (%s, %s, %s, %s, 'customer')",
            (name, email, hashed_password, phone)
        )
        connection.commit()     # commit saves the change in the database
        cursor.close()
        connection.close()

        flash("Registration successful. Please log in.", "success")
        return redirect(url_for("login"))

    # GET request: just show the empty form
    return render_template("register.html")


# Login page: shows the form (GET) and checks email and password (POST)
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"].strip().lower()
        password = request.form["password"]

        user = get_user_by_email(email)

        # Check that the user exists and the password matches the saved hash
        if user is None or not check_password_hash(user["password"], password):
            flash("Wrong email or password.", "error")
            return render_template("login.html")

        # Login is correct: remember the user in the session
        session["user_id"] = user["user_id"]
        session["name"] = user["name"]
        session["role"] = user["role"]

        flash("Welcome, " + user["name"] + "!", "success")

        # The admin goes to the admin dashboard, customers go to the home page
        if user["role"] == "admin":
            return redirect(url_for("admin_dashboard"))
        return redirect(url_for("index"))

    # GET request: just show the empty form
    return render_template("login.html")


# Logout: remove everything from the session
@app.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out.", "success")
    return redirect(url_for("index"))


# =====================================================
# Shopping Cart
# The cart is stored in the Flask session (not in the database).
# It is a dictionary: { "food_id": quantity }, for example { "1": 2, "5": 1 }
# The food_id is stored as text because the session can only save text keys.
# =====================================================

# Returns True if a user is logged in
def is_logged_in():
    return "user_id" in session


# Returns the cart from the session, or an empty cart
def get_cart():
    return session.get("cart", {})


# Saves the cart back into the session
def save_cart(cart):
    session["cart"] = cart


# The most of one dish a customer can have in the cart
MAX_QUANTITY = 20


# Removes dishes that the admin has deleted from the cart in the session,
# so the navbar count and the cart page always agree. Returns the cart.
def remove_deleted_foods_from_cart():
    cart = get_cart()
    changed = False
    for food_id in list(cart.keys()):      # list() makes a copy, so we can remove while looping
        if get_food_item_by_id(food_id) is None:
            cart.pop(food_id)
            changed = True
    if changed:
        save_cart(cart)
    return cart


# Makes "cart_count" (total number of items in the cart) and "site"
# (our settings from config.py, like the phone number and social links)
# available in every template, so the navbar and footer can show them.
@app.context_processor
def add_cart_count():
    cart = remove_deleted_foods_from_cart()
    return {"cart_count": sum(cart.values()), "site": config}


# Builds the list of items shown on the cart page.
# For each item it reads the name and price from the database
# and works out the item total. It also works out the grand total.
def get_cart_details():
    # Dishes deleted by the admin are taken out of the cart first
    cart = remove_deleted_foods_from_cart()
    cart_items = []
    grand_total = 0

    for food_id, quantity in cart.items():
        food = get_food_item_by_id(food_id)
        if food is None:
            continue    # safety check: skip a food that does not exist
        item_total = food["price"] * quantity
        grand_total = grand_total + item_total
        cart_items.append({
            "food_id": food["food_id"],
            "name": food["name"],
            "category_name": food["category_name"],
            "price": food["price"],
            "quantity": quantity,
            "item_total": item_total
        })

    return cart_items, grand_total


# After adding to the cart, send the user back to the page they came from
# (home page, or menu page with the same category and search).
# We only allow addresses inside our own website.
def get_back_url():
    back_url = request.form.get("back", "")
    if back_url.startswith("/") and not back_url.startswith("//"):
        return back_url
    return url_for("menu")


# Add one food item to the cart.
# "Add to cart" is sent by JavaScript in the background (fetch), so the page
# does not reload or jump. We then answer with a small JSON message instead of a page.
# "Order now" is a normal form send, and goes straight to the cart page.
@app.route("/cart/add", methods=["POST"])
def add_to_cart():
    # True when script.js sent the form in the background
    sent_by_javascript = request.headers.get("X-Requested-With") == "fetch"

    # Only logged in users can use the cart
    if not is_logged_in():
        if sent_by_javascript:
            return jsonify({"ok": False, "login_needed": True})
        flash("Please log in to add food to your cart.", "error")
        return redirect(url_for("login"))

    food_id = request.form.get("food_id", "")
    food = get_food_item_by_id(food_id)
    if food is None:
        if sent_by_javascript:
            return jsonify({"ok": False, "message": "Sorry, that food item was not found."})
        flash("Sorry, that food item was not found.", "error")
        return redirect(url_for("menu"))

    cart = get_cart()
    key = str(food["food_id"])

    # Stop at 20 of one dish, the same limit as the cart page
    if cart.get(key, 0) >= MAX_QUANTITY:
        limit_message = "You can order at most " + str(MAX_QUANTITY) + " of " + food["name"] + "."
        if sent_by_javascript:
            return jsonify({"ok": False, "limit_reached": True, "message": limit_message})
        flash(limit_message, "error")
        if request.form.get("action") == "order_now":
            return redirect(url_for("cart"))
        return redirect(get_back_url())

    # Increase the quantity by 1 (or start at 1 if it is not in the cart yet)
    cart[key] = cart.get(key, 0) + 1
    save_cart(cart)

    if request.form.get("action") == "order_now":
        flash(food["name"] + " is in your cart.", "success")
        return redirect(url_for("cart"))

    message = food["name"] + " added to your cart."

    # Background request: answer with JSON. script.js shows the message
    # and updates the cart numbers without reloading the page.
    if sent_by_javascript:
        return jsonify({
            "ok": True,
            "message": message,
            "cart_count": sum(cart.values()),     # all items in the cart
            "item_count": cart[key]               # how many of this food
        })

    # Without JavaScript: go back to the same page, with the message
    flash(message, "cart")
    return redirect(get_back_url())


# Cart page: shows every item, its quantity, item total and grand total
@app.route("/cart")
def cart():
    if not is_logged_in():
        flash("Please log in to see your cart.", "error")
        return redirect(url_for("login"))

    cart_items, grand_total = get_cart_details()
    return render_template("cart.html", cart_items=cart_items, grand_total=grand_total)


# Change the quantity of one item. A quantity of 0 removes the item.
@app.route("/cart/update", methods=["POST"])
def update_cart():
    if not is_logged_in():
        return redirect(url_for("login"))

    food_id = request.form.get("food_id", "")
    quantity_text = request.form.get("quantity", "")

    # The quantity must be a whole number
    if not quantity_text.isdigit():
        flash("Please enter a valid quantity.", "error")
        return redirect(url_for("cart"))

    quantity = int(quantity_text)
    cart = get_cart()

    if food_id in cart:
        if quantity == 0:
            cart.pop(food_id)
        else:
            cart[food_id] = min(quantity, MAX_QUANTITY)   # allow at most 20 of one item
        save_cart(cart)

    return redirect(url_for("cart"))


# Remove one item from the cart
@app.route("/cart/remove", methods=["POST"])
def remove_from_cart():
    if not is_logged_in():
        return redirect(url_for("login"))

    food_id = request.form.get("food_id", "")
    cart = get_cart()

    if food_id in cart:
        cart.pop(food_id)
        save_cart(cart)
        flash("Item deleted from your cart.", "success")

    return redirect(url_for("cart"))


# =====================================================
# Order Management (customer side)
# Place an order, show the confirmation page and the order history.
# =====================================================

# Read the food items inside one order (name, quantity and price)
def get_order_items(order_id):
    return fetch_all(
        "SELECT f.name, oi.quantity, oi.price "
        "FROM order_items oi "
        "JOIN food_items f ON f.food_id = oi.food_id "
        "WHERE oi.order_id = %s",
        (order_id,)
    )


# Place order: save the cart as a new order, then empty the cart
@app.route("/place-order", methods=["POST"])
def place_order():
    if not is_logged_in():
        flash("Please log in to place an order.", "error")
        return redirect(url_for("login"))

    # get_cart_details() reads the prices from the database,
    # so nobody can change a price from the browser
    cart_items, grand_total = get_cart_details()

    if len(cart_items) == 0:
        flash("Your cart is empty. Add some food first.", "error")
        return redirect(url_for("menu"))

    connection = get_db_connection()
    cursor = connection.cursor()

    try:
        # 1. Save one row in the orders table.
        #    order_date and status (Pending) are filled in by MySQL automatically.
        cursor.execute(
            "INSERT INTO orders (user_id, total_amount) VALUES (%s, %s)",
            (session["user_id"], grand_total)
        )
        # lastrowid is the order_id MySQL just gave to the new order
        order_id = cursor.lastrowid

        # 2. Save one row in order_items for every item in the cart,
        #    with the price at the time of the order
        for item in cart_items:
            cursor.execute(
                "INSERT INTO order_items (order_id, food_id, quantity, price) VALUES (%s, %s, %s, %s)",
                (order_id, item["food_id"], item["quantity"], item["price"])
            )

        # 3. Save everything together. If anything failed above,
        #    rollback() cancels it, so we never save half an order.
        connection.commit()
    except mysql.connector.Error:
        connection.rollback()
        flash("Sorry, your order could not be placed. Please try again.", "error")
        return redirect(url_for("cart"))
    finally:
        cursor.close()
        connection.close()

    # 4. Empty the cart
    save_cart({})

    return redirect(url_for("order_success", order_id=order_id))


# Order confirmation page, shown right after placing an order
@app.route("/order-success/<int:order_id>")
def order_success(order_id):
    if not is_logged_in():
        return redirect(url_for("login"))

    # Only show the order if it belongs to the logged in customer
    order = fetch_one(
        "SELECT order_id, order_date, total_amount, status FROM orders "
        "WHERE order_id = %s AND user_id = %s",
        (order_id, session["user_id"])
    )
    if order is None:
        flash("That order was not found.", "error")
        return redirect(url_for("my_orders"))

    order_items = get_order_items(order_id)
    return render_template("order_success.html", order=order, order_items=order_items)


# Order history of the logged in customer, newest first
@app.route("/my-orders")
def my_orders():
    if not is_logged_in():
        flash("Please log in to see your orders.", "error")
        return redirect(url_for("login"))

    orders = fetch_all(
        "SELECT order_id, order_date, total_amount, status FROM orders "
        "WHERE user_id = %s "
        "ORDER BY order_date DESC",
        (session["user_id"],)
    )
    for order in orders:
        order["items"] = get_order_items(order["order_id"])

    return render_template("my_orders.html", orders=orders)


# =====================================================
# Admin Dashboard
# Every admin page first checks that the logged in user has the role "admin".
# =====================================================

# The allowed values for the status of an order
ORDER_STATUSES = ["Pending", "Preparing", "Ready to Deliver", "Delivered", "Cancelled"]

# The order moves step by step. This says which status comes next.
# Delivered and Cancelled are the end, so they have no next step.
NEXT_STATUS = {
    "Pending": "Preparing",
    "Preparing": "Ready to Deliver",
    "Ready to Deliver": "Delivered"
}

# The text on the button for each next step
NEXT_BUTTON_TEXT = {
    "Pending": "Start preparing",
    "Preparing": "Ready to deliver",
    "Ready to Deliver": "Mark as delivered"
}

# Orders that are not finished yet
ACTIVE_STATUSES = ["Pending", "Preparing", "Ready to Deliver"]

# The allowed file types for food photos
ALLOWED_IMAGE_TYPES = ["jpg", "jpeg", "png", "webp"]


# Returns True if the logged in user is the admin
def is_admin():
    return session.get("role") == "admin"


# Sends a visitor who is not the admin to the login page
def redirect_to_admin_login():
    flash("Only the admin can open that page. Please log in as admin.", "error")
    return redirect(url_for("login"))


# Small helpers so the admin pages do not repeat the same database code.

# In the three helpers below, "finally" always runs, even when the query fails.
# So the cursor and the connection are always closed, and no database row stays locked.

# Run a SELECT query and return all rows (a list of dictionaries)
def fetch_all(sql, values=()):
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)
    try:
        cursor.execute(sql, values)
        return cursor.fetchall()
    finally:
        cursor.close()
        connection.close()


# Run a SELECT query and return only the first row (or None)
def fetch_one(sql, values=()):
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)
    try:
        cursor.execute(sql, values)
        return cursor.fetchone()
    finally:
        cursor.close()
        connection.close()


# Run an INSERT, UPDATE or DELETE query and save the change
def run_change(sql, values=()):
    connection = get_db_connection()
    cursor = connection.cursor()
    try:
        cursor.execute(sql, values)
        connection.commit()
    finally:
        # If the query failed, closing without commit() cancels the change
        cursor.close()
        connection.close()


# ---------- Dashboard ----------

# Read orders with the customer's name and phone, and the food items inside each order.
# statuses is a list like ["Pending", "Preparing"], or None to read every order.
def get_admin_orders(statuses, oldest_first):
    sql = (
        "SELECT o.order_id, o.order_date, o.total_amount, o.status, "
        "u.name AS customer_name, u.phone AS customer_phone "
        "FROM orders o "
        "JOIN users u ON u.user_id = o.user_id "
    )
    values = []

    if statuses:
        # One %s for each status, e.g. "IN (%s, %s, %s)". The values are still
        # passed separately, so this is still a safe parameterized query.
        placeholders = ", ".join(["%s"] * len(statuses))
        sql = sql + "WHERE o.status IN (" + placeholders + ") "
        values = statuses

    # The kitchen works on the oldest order first
    if oldest_first:
        sql = sql + "ORDER BY o.order_date ASC"
    else:
        sql = sql + "ORDER BY o.order_date DESC"

    orders = fetch_all(sql, values)
    for order in orders:
        order["items"] = get_order_items(order["order_id"])
    return orders


# Admin home: simple counts, and the orders that still need work
@app.route("/admin")
def admin_dashboard():
    if not is_admin():
        return redirect_to_admin_login()

    total_orders = fetch_one("SELECT COUNT(*) AS total FROM orders")["total"]
    new_orders = fetch_one("SELECT COUNT(*) AS total FROM orders WHERE status = 'Pending'")["total"]
    total_customers = fetch_one("SELECT COUNT(*) AS total FROM users WHERE role = 'customer'")["total"]
    total_food_items = fetch_one("SELECT COUNT(*) AS total FROM food_items")["total"]

    # Orders that are Pending, Preparing or Ready to Deliver
    active_orders = get_admin_orders(ACTIVE_STATUSES, True)

    return render_template(
        "admin/dashboard.html",
        total_orders=total_orders,
        new_orders=new_orders,
        total_customers=total_customers,
        total_food_items=total_food_items,
        active_orders=active_orders,
        next_status=NEXT_STATUS,
        next_button_text=NEXT_BUTTON_TEXT
    )


# ---------- Manage food items ----------

# List of all food items
@app.route("/admin/food")
def admin_food():
    if not is_admin():
        return redirect_to_admin_login()

    food_items = get_food_items("", "")     # empty category and search = all items
    return render_template("admin/food_list.html", food_items=food_items)


# Checks the values typed in the add / edit food form.
# Returns an error message, or None if everything is correct.
def check_food_form(name, category_id, price_text, image_file):
    if name == "":
        return "Please enter the name of the food."

    if not category_id.isdigit():
        return "Please choose a category."

    # The category must really exist in the categories table
    if fetch_one("SELECT category_id FROM categories WHERE category_id = %s", (category_id,)) is None:
        return "Please choose a valid category."

    # The price must be a number bigger than 0
    try:
        price = float(price_text)
    except ValueError:
        return "Please enter a valid price, for example 250."

    # float() also accepts "nan" (not a number) and "inf" (infinity), so we refuse them here
    if math.isnan(price) or math.isinf(price):
        return "Please enter a valid price, for example 250."
    if price <= 0:
        return "The price must be more than 0."

    # The price column is DECIMAL(10, 2), so the biggest price it can hold is 99999999.99
    if price > 99999999.99:
        return "The price must not be more than 99,999,999.99."

    # A photo is optional, but if one is chosen it must be an image file
    if image_file and image_file.filename != "":
        extension = image_file.filename.rsplit(".", 1)[-1].lower()
        if extension not in ALLOWED_IMAGE_TYPES:
            return "The photo must be a JPG, PNG or WEBP file."

    return None


# Makes the file name for an uploaded photo. Returns None if no photo was chosen.
# The file itself is saved later, only after the database change has worked.
def make_image_name(image_file):
    if not image_file or image_file.filename == "":
        return None

    # secure_filename removes dangerous characters from the file name.
    # We add the current time in front so two photos never get the same name.
    return str(int(time.time())) + "_" + secure_filename(image_file.filename)


# Saves the uploaded photo into static/images with the given file name
def save_image_file(image_file, file_name):
    image_file.save(os.path.join(app.static_folder, "images", file_name))


# Deletes a photo file from static/images, but only if no other food item still uses it
def delete_image_if_unused(file_name):
    if not file_name:
        return
    used = fetch_one("SELECT COUNT(*) AS n FROM food_items WHERE image = %s", (file_name,))["n"]
    file_path = os.path.join(app.static_folder, "images", file_name)
    if used == 0 and os.path.isfile(file_path):
        os.remove(file_path)


# Add a new food item
@app.route("/admin/food/add", methods=["GET", "POST"])
def admin_add_food():
    if not is_admin():
        return redirect_to_admin_login()

    categories = get_all_categories()

    if request.method == "POST":
        name = request.form["name"].strip()
        category_id = request.form.get("category_id", "")
        price_text = request.form["price"].strip()
        description = request.form["description"].strip()
        image_file = request.files.get("image")

        error = check_food_form(name, category_id, price_text, image_file)
        if error:
            flash(error, "error")
            # Show the form again with the values the admin already typed
            return render_template("admin/food_form.html", categories=categories, food=request.form, is_edit=False)

        image_name = make_image_name(image_file)

        run_change(
            "INSERT INTO food_items (category_id, name, price, description, image) VALUES (%s, %s, %s, %s, %s)",
            (category_id, name, price_text, description, image_name)
        )

        # The insert worked, so now we save the photo file
        if image_name:
            save_image_file(image_file, image_name)

        flash(name + " was added to the menu.", "success")
        return redirect(url_for("admin_food"))

    # GET request: show an empty form
    return render_template("admin/food_form.html", categories=categories, food=None, is_edit=False)


# Edit a food item
@app.route("/admin/food/edit/<int:food_id>", methods=["GET", "POST"])
def admin_edit_food(food_id):
    if not is_admin():
        return redirect_to_admin_login()

    food = fetch_one("SELECT * FROM food_items WHERE food_id = %s", (food_id,))
    if food is None:
        flash("That food item was not found.", "error")
        return redirect(url_for("admin_food"))

    categories = get_all_categories()

    if request.method == "POST":
        name = request.form["name"].strip()
        category_id = request.form.get("category_id", "")
        price_text = request.form["price"].strip()
        description = request.form["description"].strip()
        image_file = request.files.get("image")

        error = check_food_form(name, category_id, price_text, image_file)
        if error:
            flash(error, "error")
            # Show the form again with what the admin typed, and the current photo
            typed_values = dict(request.form)
            typed_values["food_id"] = food_id
            typed_values["image"] = food["image"]
            return render_template("admin/food_form.html", categories=categories, food=typed_values, is_edit=True)

        # Keep the old photo if no new photo was chosen
        new_image_name = make_image_name(image_file)
        if new_image_name is None:
            image_name = food["image"]
        else:
            image_name = new_image_name

        run_change(
            "UPDATE food_items SET category_id = %s, name = %s, price = %s, description = %s, image = %s "
            "WHERE food_id = %s",
            (category_id, name, price_text, description, image_name, food_id)
        )

        # The update worked, so now we save the new photo file (if one was chosen)
        if new_image_name:
            save_image_file(image_file, new_image_name)

        flash(name + " was updated.", "success")
        return redirect(url_for("admin_food"))

    # GET request: show the form filled with the current values
    return render_template("admin/food_form.html", categories=categories, food=food, is_edit=True)


# Delete a food item
@app.route("/admin/food/delete/<int:food_id>", methods=["POST"])
def admin_delete_food(food_id):
    if not is_admin():
        return redirect_to_admin_login()

    # Remember the photo file name before the row is deleted
    food = fetch_one("SELECT image FROM food_items WHERE food_id = %s", (food_id,))

    # A food item that is already inside an order cannot be deleted,
    # because the order_items table still points to it (foreign key).
    # MySQL then gives an IntegrityError, and we show a friendly message.
    try:
        run_change("DELETE FROM food_items WHERE food_id = %s", (food_id,))
        flash("The food item was deleted.", "success")

        # The row is gone, so also delete its photo file (if no other food uses it)
        if food:
            delete_image_if_unused(food["image"])
    except mysql.connector.IntegrityError:
        flash("This food item is part of earlier orders, so it cannot be deleted. You can edit it instead.", "error")

    return redirect(url_for("admin_food"))


# ---------- Manage orders ----------

# Orders page with 4 sections:
#   active    = Pending, Preparing and Ready to Deliver (still need work)
#   completed = Delivered
#   cancelled = Cancelled
#   all       = every order
@app.route("/admin/orders")
def admin_orders():
    if not is_admin():
        return redirect_to_admin_login()

    section = request.args.get("section", "active")

    if section == "completed":
        orders = get_admin_orders(["Delivered"], False)
    elif section == "cancelled":
        orders = get_admin_orders(["Cancelled"], False)
    elif section == "all":
        orders = get_admin_orders(None, False)
    else:
        section = "active"
        orders = get_admin_orders(ACTIVE_STATUSES, True)

    # How many orders are in each section (shown on the section buttons)
    counts = {
        "active": fetch_one("SELECT COUNT(*) AS n FROM orders WHERE status IN ('Pending', 'Preparing', 'Ready to Deliver')")["n"],
        "completed": fetch_one("SELECT COUNT(*) AS n FROM orders WHERE status = 'Delivered'")["n"],
        "cancelled": fetch_one("SELECT COUNT(*) AS n FROM orders WHERE status = 'Cancelled'")["n"],
        "all": fetch_one("SELECT COUNT(*) AS n FROM orders")["n"]
    }

    return render_template(
        "admin/orders.html",
        orders=orders,
        section=section,
        counts=counts,
        next_status=NEXT_STATUS,
        next_button_text=NEXT_BUTTON_TEXT
    )


# Move an order to its next status, or cancel it.
# Only the correct next step is allowed, e.g. Pending can only become Preparing (or Cancelled).
@app.route("/admin/orders/<int:order_id>/status", methods=["POST"])
def admin_update_order_status(order_id):
    if not is_admin():
        return redirect_to_admin_login()

    order = fetch_one("SELECT status FROM orders WHERE order_id = %s", (order_id,))
    new_status = request.form.get("status", "")

    if order is None:
        flash("That order was not found.", "error")
    else:
        current_status = order["status"]

        # The move is allowed if it is the next step, or a cancel of an unfinished order
        is_next_step = (new_status == NEXT_STATUS.get(current_status))
        is_cancel = (new_status == "Cancelled" and current_status in ACTIVE_STATUSES)

        if is_next_step or is_cancel:
            run_change("UPDATE orders SET status = %s WHERE order_id = %s", (new_status, order_id))
            if new_status == "Delivered":
                flash("Order #" + str(order_id) + " is delivered and moved to Completed.", "success")
            else:
                flash("Order #" + str(order_id) + " is now " + new_status + ".", "success")
        else:
            flash("Order #" + str(order_id) + " cannot change from " + current_status + " to " + new_status + ".", "error")

    # Go back to the page the admin came from
    if request.form.get("back") == "dashboard":
        return redirect(url_for("admin_dashboard"))
    return redirect(url_for("admin_orders", section=request.form.get("back") or "active"))


# ---------- Customer details ----------

# List of all customers and how many orders each one has placed
@app.route("/admin/customers")
def admin_customers():
    if not is_admin():
        return redirect_to_admin_login()

    # LEFT JOIN keeps customers who have not ordered yet (their count is 0)
    customers = fetch_all(
        "SELECT u.user_id, u.name, u.email, u.phone, COUNT(o.order_id) AS order_count "
        "FROM users u "
        "LEFT JOIN orders o ON o.user_id = u.user_id "
        "WHERE u.role = 'customer' "
        "GROUP BY u.user_id, u.name, u.email, u.phone "
        "ORDER BY u.name"
    )
    return render_template("admin/customers.html", customers=customers)


# ---------- Order reports ----------

# Report of orders and total sales between two dates
@app.route("/admin/reports")
def admin_reports():
    if not is_admin():
        return redirect_to_admin_login()

    # By default, show the last 30 days
    today = date.today()
    start_text = request.args.get("start_date", "")
    end_text = request.args.get("end_date", "")

    # Turn the text from the form into real dates.
    # If the text is empty or wrong, use the default dates.
    try:
        start_date = date.fromisoformat(start_text)
    except ValueError:
        start_date = today - timedelta(days=30)
    try:
        end_date = date.fromisoformat(end_text)
    except ValueError:
        end_date = today

    if start_date > end_date:
        flash("The start date must be before the end date.", "error")
        start_date, end_date = end_date, start_date     # swap them

    # All orders between the two dates (DATE() removes the time part)
    orders = fetch_all(
        "SELECT o.order_id, o.order_date, o.total_amount, o.status, u.name AS customer_name "
        "FROM orders o "
        "JOIN users u ON u.user_id = o.user_id "
        "WHERE DATE(o.order_date) BETWEEN %s AND %s "
        "ORDER BY o.order_date",
        (start_date, end_date)
    )

    # Work out the totals. Cancelled orders are not counted as sales.
    total_sales = 0
    status_counts = {}
    for status in ORDER_STATUSES:
        status_counts[status] = 0

    for order in orders:
        status_counts[order["status"]] = status_counts[order["status"]] + 1
        if order["status"] != "Cancelled":
            total_sales = total_sales + order["total_amount"]

    # The 5 dishes sold most in these dates
    top_dishes = fetch_all(
        "SELECT f.name, SUM(oi.quantity) AS quantity_sold, SUM(oi.quantity * oi.price) AS amount "
        "FROM order_items oi "
        "JOIN orders o ON o.order_id = oi.order_id "
        "JOIN food_items f ON f.food_id = oi.food_id "
        "WHERE DATE(o.order_date) BETWEEN %s AND %s AND o.status <> 'Cancelled' "
        "GROUP BY f.food_id, f.name "
        "ORDER BY quantity_sold DESC "
        "LIMIT 5",
        (start_date, end_date)
    )

    return render_template(
        "admin/reports.html",
        orders=orders,
        start_date=start_date,
        end_date=end_date,
        total_sales=total_sales,
        status_counts=status_counts,
        top_dishes=top_dishes
    )


# ---------- Admin settings: change password ----------

# Shows the admin's account details and a form to change the password
@app.route("/admin/settings", methods=["GET", "POST"])
def admin_settings():
    if not is_admin():
        return redirect_to_admin_login()

    # Read the admin's own account from the database
    admin_user = fetch_one(
        "SELECT user_id, name, email, phone, password FROM users WHERE user_id = %s",
        (session["user_id"],)
    )

    if request.method == "POST":
        current_password = request.form.get("current_password", "")
        new_password = request.form.get("new_password", "")
        confirm_password = request.form.get("confirm_password", "")

        # 1. The current password must be correct
        if not check_password_hash(admin_user["password"], current_password):
            flash("Your current password is wrong.", "error")

        # 2. The new password must be at least 6 characters
        elif len(new_password) < 6:
            flash("The new password must be at least 6 characters long.", "error")

        # 3. Both new password boxes must match
        elif new_password != confirm_password:
            flash("The new passwords do not match.", "error")

        # 4. The new password must be different from the old one
        elif new_password == current_password:
            flash("The new password must be different from your current password.", "error")

        else:
            # Everything is correct: save the new password as a hash
            run_change(
                "UPDATE users SET password = %s WHERE user_id = %s",
                (generate_password_hash(new_password), admin_user["user_id"])
            )
            flash("Your password was changed. Use the new password next time you log in.", "success")
            return redirect(url_for("admin_settings"))

    return render_template("admin/settings.html", admin_user=admin_user)


# Start the app when we run: python app.py
if __name__ == "__main__":
    app.run(debug=True)
