#!/usr/bin/env python3
"""
Simple database inspector for the table ordering system
"""
import sqlite3
import json
from datetime import datetime

def inspect_database():
    """Inspect the database and display all data in a readable format"""
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    
    print("=" * 50)
    print("DATABASE INSPECTION REPORT")
    print("=" * 50)
    print(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Get table info
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    print(f"Tables found: {len(tables)}")
    for table in tables:
        print(f"  - {table[0]}")
    print()
    
    # Inspect orders table
    print("ORDERS TABLE:")
    print("-" * 20)
    
    # Get column info
    cursor.execute("PRAGMA table_info(orders);")
    columns = cursor.fetchall()
    print("Columns:")
    for col in columns:
        print(f"  {col[1]} ({col[2]}) - {'NOT NULL' if col[3] else 'NULL'}")
    print()
    
    # Get all orders
    cursor.execute("SELECT * FROM orders ORDER BY id;")
    orders = cursor.fetchall()
    
    print(f"Total orders: {len(orders)}")
    print()
    
    if orders:
        print("ORDER DETAILS:")
        print("-" * 40)
        for order in orders:
            # Handle both old and new schema
            if len(order) == 4:
                order_id, table_number, items, total = order
                status = "N/A"
                created_at = "N/A"
            elif len(order) == 5:
                order_id, table_number, items, total, status = order
                created_at = "N/A"
            else:
                order_id, table_number, items, total, created_at, status = order
            
            print(f"Order ID: {order_id}")
            print(f"Table: {table_number if table_number else 'Not specified'}")
            print(f"Items: {items}")
            print(f"Total: ${total:.2f}")
            print(f"Status: {status}")
            if created_at != "N/A":
                print(f"Created: {created_at}")
            print("-" * 40)
    else:
        print("No orders found in database.")
    
    # Get summary statistics
    cursor.execute("SELECT COUNT(*) as total_orders, SUM(total) as total_revenue FROM orders;")
    stats = cursor.fetchone()
    print(f"\nSUMMARY:")
    print(f"Total Orders: {stats[0]}")
    print(f"Total Revenue: ${stats[1]:.2f}" if stats[1] else "Total Revenue: $0.00")
    
    conn.close()

if __name__ == "__main__":
    inspect_database()
