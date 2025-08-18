import sqlite3
import os

DB_FILE = "database.db"

def fix_and_recreate_db():
    # 1. Connect to the existing database
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()

    # 2. Read all data from the orders table
    try:
        c.execute("SELECT id, table_number, items, total, status, created_at FROM orders")
        orders = c.fetchall()
    except sqlite3.OperationalError as e:
        print(f"Could not read from database (maybe it's already fixed?): {e}")
        conn.close()
        return

    # 3. Close the connection and delete the old file
    conn.close()
    os.remove(DB_FILE)

    # 4. Re-initialize the database with the correct schema from app.py
    from app import init_db
    init_db()

    # 5. Connect to the new, clean database
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()

    # 6. Insert the corrected data
    for order in orders:
        # The data is swapped: status is in col 5, created_at in col 4
        order_id, table, items, total, created_at, status = order
        # If status is a timestamp, it's a bad row
        if ' ' in str(status) or status is None:
            # Swap them back to the correct order
            status, created_at = created_at, status

        # If status is still None, default it to 'new'
        if status is None:
            status = 'new'
        
        c.execute(
            "INSERT INTO orders (id, table_number, items, total, status, created_at) VALUES (?, ?, ?, ?, ?, ?)",
            (order_id, table, items, total, status, created_at)
        )

    # 7. Commit changes and close
    conn.commit()
    conn.close()
    print(f"Database '{DB_FILE}' has been repaired and repopulated with {len(orders)} orders.")

if __name__ == "__main__":
    fix_and_recreate_db()
