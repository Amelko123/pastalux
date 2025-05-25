from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import os  # Needed for environment variables

app = Flask(__name__)

# Use DATABASE_URL if available (Render), otherwise fall back to local SQLite
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///pastalux.sqlite')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)


# --- MODELS ---
class MenuItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    price = db.Column(db.Float, nullable=False)
    vegetarian = db.Column(db.Boolean, default=False)
    vegan = db.Column(db.Boolean, default=False)
    gluten_free = db.Column(db.Boolean, default=False)
    image_filename = db.Column(db.String(100))  # New field


class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    customer_name = db.Column(db.String(100), nullable=False)
    customer_email = db.Column(db.String(100), nullable=False)
    customer_address = db.Column(db.Text)
    customer_phone = db.Column(db.String(20))
    pickup_time = db.Column(db.String(50), nullable=False)
    status = db.Column(db.String(50), default='pending')
    total_price = db.Column(db.Float, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    items = db.relationship('OrderItem', backref='order')


class OrderItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('order.id'))
    menu_item_id = db.Column(db.Integer, db.ForeignKey('menu_item.id'))
    quantity = db.Column(db.Integer, nullable=False)
    special_instructions = db.Column(db.Text)


class ContactMessage(db.Model):  # NEW MODEL
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), nullable=False)
    message = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


# --- ROUTES ---

@app.route('/')
def home():
    return render_template('index.html')


@app.route('/menu')
def menu():
    items = MenuItem.query.all()
    return render_template('menu.html', items=items)


@app.route('/locations')
def locations():
    return render_template('locations.html')


@app.route('/about')
def about():
    return render_template('about.html')


@app.route('/contact', methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        message = request.form.get('message')

        if not name or not email or not message:
            return "Missing required fields", 400

        # Save to database
        new_message = ContactMessage(name=name, email=email, message=message)
        db.session.add(new_message)
        db.session.commit()

        return redirect(url_for('contact_confirmation'))

    return render_template('contact.html')


@app.route('/contact/confirmation')
def contact_confirmation():
    return render_template('contact_confirmation.html')


@app.route('/admin/messages')
def admin_messages():
    messages = ContactMessage.query.all()
    return render_template('admin_messages.html', messages=messages)


@app.route('/order', methods=['GET', 'POST'])
def order():
    if request.method == 'POST':
        name = request.form.get('customer_name')
        email = request.form.get('customer_email')
        address = request.form.get('customer_address')
        phone = request.form.get('customer_phone')
        pickup_time = request.form.get('pickup_time')

        item_ids = request.form.getlist('item_id')
        quantities = request.form.getlist('quantity')

        total_price = 0
        order_items = []

        for i in range(len(item_ids)):
            item_id = int(item_ids[i])
            qty = int(quantities[i]) if quantities[i] else 1

            menu_item = MenuItem.query.get(item_id)
            if menu_item:
                total_price += menu_item.price * qty
                order_items.append(OrderItem(
                    menu_item_id=item_id,
                    quantity=qty
                ))

        if not name or not email or not pickup_time:
            return "Missing required customer information", 400

        # Create new order
        new_order = Order(
            customer_name=name,
            customer_email=email,
            customer_address=address,
            customer_phone=phone,
            pickup_time=pickup_time,
            total_price=total_price
        )

        db.session.add(new_order)
        db.session.commit()

        # Link items to order
        for item in order_items:
            item.order_id = new_order.id
            db.session.add(item)

        db.session.commit()

        return redirect(url_for('order_confirmation'))

    menu_items = MenuItem.query.all()
    return render_template('order_form.html', menu_items=menu_items)


@app.route('/confirmation')
def order_confirmation():
    return render_template('order_confirmation.html')


@app.route('/admin/orders')
def admin_orders():
    orders = Order.query.all()
    return render_template('admin_orders.html', orders=orders)


@app.route('/reset-db')
def reset_db():
    db.drop_all()
    db.create_all()

    # Re-seed sample data
    db.session.add(MenuItem(
        name="Truffle Tagliatelle",
        description="Hand-cut egg pasta with black truffle butter.",
        price=12.00,
        vegetarian=True,
        image_filename='dish-truffle-tagliatelle.jpg'
    ))
    db.session.add(MenuItem(
        name="Carbonara",
        description="Guanciale, pecorino, cracked black pepper.",
        price=10.50,
        image_filename='dish-carbonara.jpg'
    ))
    db.session.add(MenuItem(
        name="Pesto Trofie",
        description="Ligurian pasta with basil pesto and burrata cheese.",
        price=9.50,
        vegetarian=True,
        image_filename='dish-pesto-trofie.jpg'
    ))
    db.session.add(MenuItem(
        name="Garlic Bread",
        description="Sourdough with garlic herb butter.",
        price=3.50,
        image_filename='dish-garlic-bread.jpg'
    ))

    db.session.commit()
    return "Database Reset! Go to /menu"


# --- START APP ---
with app.app_context():
    db.create_all()

    if not MenuItem.query.all():
        db.session.add(MenuItem(
            name="Truffle Tagliatelle",
            description="Hand-cut egg pasta with black truffle butter.",
            price=12.00,
            vegetarian=True,
            image_filename='dish-truffle-tagliatelle.jpg'
        ))
        db.session.add(MenuItem(
            name="Carbonara",
            description="Guanciale, pecorino, cracked black pepper.",
            price=10.50,
            image_filename='dish-carbonara.jpg'
        ))
        db.session.add(MenuItem(
            name="Pesto Trofie",
            description="Ligurian pasta with basil pesto and burrata cheese.",
            price=9.50,
            vegetarian=True,
            image_filename='dish-pesto-trofie.jpg'
        ))
        db.session.add(MenuItem(
            name="Garlic Bread",
            description="Sourdough with garlic herb butter.",
            price=3.50,
            image_filename='dish-garlic-bread.jpg'
        ))
        db.session.commit()

    # Use $PORT if available (on hosting platforms), else fallback to 5000
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
