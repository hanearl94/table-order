from flask import Flask, render_template, request, redirect, url_for, jsonify
import sqlite3

app = Flask(__name__)

# Temporary in-memory menu
MENU = [
    {"id": 1, "name": "Cheeseburger", "price": 8.99},
    {"id": 2, "name": "Margherita Pizza", "price": 12.50},
    {"id": 3, "name": "Caesar Salad", "price": 7.25},
    {"id": 4, "name": "Spaghetti Bolognese", "price": 11.00},
    {"id": 5, "name": "Coke", "price": 2.50},
    {"id": 6, "name": "Iced Tea", "price": 2.75},
]

DB_FILE = "database.db"

def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute(
        """CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            table_number TEXT NOT NULL,
            items TEXT NOT NULL,
            total REAL NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )"""
    )
    conn.commit()
    conn.close()

def query_all_orders():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute("SELECT id, table_number, items, total, created_at FROM orders ORDER BY id DESC")
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows

@app.route("/")
def index():
    return render_template("index.html", menu=MENU)

@app.route("/order", methods=["POST"])
def order():
    table_number = request.form.get("table", "").strip()
    if not table_number:
        return "Please provide a table number.", 400

    items = []
    total = 0.0
    for item in MENU:
        qty_str = request.form.get(f"qty_{item['id']}", "0").strip()
        qty = int(qty_str or 0)
        if qty > 0:
            items.append(f"{qty}x {item['name']}")
            total += qty * item["price"]

    if not items:
        return "No items selected. Please go back and add items.", 400

    items_str = ", ".join(items)

    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute(
        "INSERT INTO orders (table_number, items, total) VALUES (?, ?, ?)",
        (table_number, items_str, total),
    )
    conn.commit()
    conn.close()

    return f"✅ Saved: Table {table_number} — {items_str} (Total: ${total:.2f})"

# --- NEW: Dashboard page (HTML)
@app.route("/orders")
def orders_page():
    return render_template("orders.html")

# --- NEW: Data endpoint (JSON) for live refresh
@app.route("/orders.json")
def orders_json():
    return jsonify({"orders": query_all_orders()})

if __name__ == "__main__":
    init_db()
    app.run(debug=True)
