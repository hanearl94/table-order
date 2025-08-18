from flask import Flask, render_template, request, redirect, url_for
import sqlite3
import os

app = Flask(__name__)

# Temporary menu data
MENU = [
    {"id": 1, "name": "Cheeseburger", "price": 8.99},
    {"id": 2, "name": "Margherita Pizza", "price": 12.50},
    {"id": 3, "name": "Caesar Salad", "price": 7.25},
    {"id": 4, "name": "Spaghetti Bolognese", "price": 11.00},
    {"id": 5, "name": "Coke", "price": 2.50},
    {"id": 6, "name": "Iced Tea", "price": 2.75},
    {"id": 7, "name": "Mix Combo Small", "price": 75.00},
]

DB_FILE = "database.db"

def init_db():
    """Create database and orders table if not exists"""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute(
        """CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            table_number TEXT,
            items TEXT,
            total REAL
        )"""
    )
    conn.commit()
    conn.close()

@app.route("/")
def index():
    return render_template("index.html", menu=MENU)

@app.route("/order", methods=["POST"])
def order():
    table_number = request.form.get("table")
    items = []
    total = 0

    for item in MENU:
        qty = int(request.form.get(f"qty_{item['id']}", 0))
        if qty > 0:
            items.append(f"{qty}x {item['name']}")
            total += qty * item["price"]

    if not items:
        return "No items selected. Please go back and add items."

    items_str = ", ".join(items)

    # Save into DB
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("INSERT INTO orders (table_number, items, total) VALUES (?, ?, ?)",
              (table_number, items_str, total))
    conn.commit()
    conn.close()

    return f"✅ Order saved for Table {table_number}: {items_str} (Total: ${total:.2f})"

if __name__ == "__main__":
    init_db()
    app.run(debug=True)

