from flask import Flask, render_template, request, jsonify, redirect, url_for
import sqlite3

app = Flask(__name__)

# In-memory menu
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
            status TEXT NOT NULL DEFAULT 'new',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )"""
    )

    # Migrations
    c.execute("PRAGMA table_info(orders)")
    cols = [row[1] for row in c.fetchall()]

    if "status" not in cols:
        c.execute("ALTER TABLE orders ADD COLUMN status TEXT NOT NULL DEFAULT 'new'")

    if "created_at" not in cols:
        # Can't add with a non-constant default in older sqlite
        c.execute("ALTER TABLE orders ADD COLUMN created_at TIMESTAMP")
        # Backfill the value
        c.execute("UPDATE orders SET created_at = CURRENT_TIMESTAMP WHERE created_at IS NULL")

    if "order_type" not in cols:
        c.execute("ALTER TABLE orders ADD COLUMN order_type TEXT NOT NULL DEFAULT 'table'")
        # Backfill existing orders as table orders
        c.execute("UPDATE orders SET order_type = 'table' WHERE order_type IS NULL")

    conn.commit()
    conn.close()

def db():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def query_all_orders():
    with db() as conn:
        cur = conn.cursor()
        cur.execute("""SELECT id, table_number, items, total, created_at, status, order_type
                       FROM orders
                       ORDER BY id DESC""")
        return [dict(r) for r in cur.fetchall()]

def get_order(order_id: int):
    with db() as conn:
        cur = conn.cursor()
        cur.execute("""SELECT id, table_number, items, total, created_at, status, order_type
                       FROM orders WHERE id = ?""", (order_id,))
        row = cur.fetchone()
        return dict(row) if row else None

def get_orders_for_table(table_number: str, include_done: bool = True):
    with db() as conn:
        cur = conn.cursor()
        if include_done:
            cur.execute("""SELECT id, table_number, items, total, created_at, status
                           FROM orders
                           WHERE table_number = ?
                           ORDER BY id DESC""", (table_number,))
        else:
            cur.execute("""SELECT id, table_number, items, total, created_at, status
                           FROM orders
                           WHERE table_number = ? AND status != 'done'
                           ORDER BY id DESC""", (table_number,))
        return [dict(r) for r in cur.fetchall()]

@app.route("/")
def index():
    return render_template("index.html", menu=MENU)

@app.route("/takeout")
def takeout():
    return render_template("takeout.html", menu=MENU)

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

    with db() as conn:
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO orders (table_number, items, total, status, order_type) VALUES (?, ?, ?, ?, ?)",
            (table_number, items_str, total, "new", "table"),
        )
        order_id = cur.lastrowid

    # 👉 Redirect the guest to their tracking page
    return redirect(url_for("track_order_page", order_id=order_id))

@app.route("/takeout-order", methods=["POST"])
def takeout_order():
    customer_name = request.form.get("customer_name", "").strip()
    phone_number = request.form.get("phone_number", "").strip()
    
    if not customer_name:
        return "Please provide a customer name.", 400
    if not phone_number:
        return "Please provide a phone number.", 400

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
    # Use customer name and phone as the "table_number" for takeout orders
    table_identifier = f"{customer_name} ({phone_number})"

    with db() as conn:
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO orders (table_number, items, total, status, order_type) VALUES (?, ?, ?, ?, ?)",
            (table_identifier, items_str, total, "new", "takeout"),
        )
        order_id = cur.lastrowid

    # Redirect to tracking page
    return redirect(url_for("track_order_page", order_id=order_id))

# --- Staff dashboard (existing) ---
@app.route("/orders")
def orders_page():
    return render_template("orders.html")

@app.route("/orders.json")
def orders_json():
    filter_type = request.args.get('filter', 'all')
    
    with db() as conn:
        cur = conn.cursor()
        
        if filter_type == 'active':
            # Active means new or prepping (not done)
            cur.execute("""SELECT id, table_number, items, total, created_at, status, order_type
                           FROM orders 
                           WHERE status IN ('new', 'prepping')
                           ORDER BY id DESC""")
        elif filter_type == 'done':
            cur.execute("""SELECT id, table_number, items, total, created_at, status, order_type
                           FROM orders 
                           WHERE status = 'done'
                           ORDER BY id DESC""")
        else:  # 'all' or any other value
            cur.execute("""SELECT id, table_number, items, total, created_at, status, order_type
                           FROM orders
                           ORDER BY id DESC""")
        
        orders = [dict(r) for r in cur.fetchall()]
    
    return jsonify({"orders": orders})

@app.route("/orders/<int:order_id>/status", methods=["POST"])
def update_status(order_id: int):
    status = (request.json or {}).get("status") if request.is_json else request.form.get("status")
    if not status or status not in VALID_STATUSES:
        return jsonify({"ok": False, "error": "invalid status"}), 400

    with db() as conn:
        cur = conn.cursor()
        cur.execute("UPDATE orders SET status = ? WHERE id = ?", (status, order_id))
        updated = cur.rowcount

    if updated == 0:
        return jsonify({"ok": False, "error": "order not found"}), 404
    return jsonify({"ok": True, "id": order_id, "status": status})

# --- NEW: Single-order tracking page ---
@app.route("/track/<int:order_id>")
def track_order_page(order_id: int):
    return render_template("track_order.html", order_id=order_id)

# JSON for the single-order tracker
@app.route("/order/<int:order_id>.json")
def order_json(order_id: int):
    o = get_order(order_id)
    if not o:
        return jsonify({"ok": False, "error": "not found"}), 404
    return jsonify({"ok": True, "order": o})

# --- NEW: Table tracking page (all orders for a table) ---
@app.route("/table/<table_number>")
def table_orders_page(table_number: str):
    # show active orders first; you can toggle include_done via query param later if needed
    return render_template("table_orders.html", table_number=table_number)

# JSON for the table tracker
@app.route("/table/<table_number>.json")
def table_orders_json(table_number: str):
    include_done = request.args.get("all", "0") == "1"
    data = get_orders_for_table(table_number, include_done=include_done)
    return jsonify({"ok": True, "orders": data})

if __name__ == "__main__":
    init_db()
    app.run(debug=True, port=8080)
