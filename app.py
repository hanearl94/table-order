from flask import Flask, render_template, request, jsonify
import sqlite3

app = Flask(__name__)

# In-memory menu (DB for menu can come later)
MENU = [
    {"id": 1, "name": "Cheeseburger", "price": 8.99},
    {"id": 2, "name": "Margherita Pizza", "price": 12.50},
    {"id": 3, "name": "Caesar Salad", "price": 7.25},
    {"id": 4, "name": "Spaghetti Bolognese", "price": 11.00},
    {"id": 5, "name": "Coke", "price": 2.50},
    {"id": 6, "name": "Iced Tea", "price": 2.75},
]

DB_FILE = "database.db"
VALID_STATUSES = {"new", "prepping", "done"}

def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    # Base table
    c.execute(
        """CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            table_number TEXT NOT NULL,
            items TEXT NOT NULL,
            total REAL NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )"""
    )
    # --- Migration: add status column if missing ---
    c.execute("PRAGMA table_info(orders)")
    cols = [row[1] for row in c.fetchall()]  # row[1] is column name
    if "status" not in cols:
        c.execute("ALTER TABLE orders ADD COLUMN status TEXT NOT NULL DEFAULT 'new'")
    conn.commit()
    conn.close()

def query_all_orders():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute("""SELECT id, table_number, items, total, created_at, status
                   FROM orders
                   ORDER BY id DESC""")
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
        "INSERT INTO orders (table_number, items, total, status) VALUES (?, ?, ?, ?)",
        (table_number, items_str, total, "new"),
    )
    conn.commit()
    conn.close()

    return f"✅ Saved: Table {table_number} — {items_str} (Total: ${total:.2f})"

# Dashboard (HTML)
@app.route("/orders")
def orders_page():
    return render_template("orders.html")

# Data endpoint for dashboard
@app.route("/orders.json")
def orders_json():
    return jsonify({"orders": query_all_orders()})

# --- NEW: update status endpoint ---
@app.route("/orders/<int:order_id>/status", methods=["POST"])
def update_status(order_id: int):
    # Accept JSON or form data
    status = (request.json or {}).get("status") if request.is_json else request.form.get("status")
    if not status or status not in VALID_STATUSES:
        return jsonify({"ok": False, "error": "invalid status"}), 400

    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("UPDATE orders SET status = ? WHERE id = ?", (status, order_id))
    conn.commit()
    updated = c.rowcount
    conn.close()

    if updated == 0:
        return jsonify({"ok": False, "error": "order not found"}), 404

    return jsonify({"ok": True, "id": order_id, "status": status})

if __name__ == "__main__":
    init_db()
    app.run(debug=True)
