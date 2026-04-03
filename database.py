import sqlite3
import random
from datetime import datetime, timedelta

conn = sqlite3.connect("sales.db")
cursor = conn.cursor()

print("🔧 Setting up database...")

# -----------------------------
# CREATE TABLES
# -----------------------------

cursor.execute("""
CREATE TABLE IF NOT EXISTS customers (
    id INTEGER PRIMARY KEY,
    name TEXT,
    city TEXT
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS orders (
    id INTEGER PRIMARY KEY,
    customer_id INTEGER,
    amount INTEGER,
    date TEXT
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS products (
    id INTEGER PRIMARY KEY,
    name TEXT,
    price INTEGER
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS order_items (
    id INTEGER PRIMARY KEY,
    order_id INTEGER,
    product_id INTEGER,
    quantity INTEGER
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS payments (
    id INTEGER PRIMARY KEY,
    order_id INTEGER,
    payment_method TEXT,
    status TEXT
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS employees (
    id INTEGER PRIMARY KEY,
    name TEXT,
    department TEXT
)
""")

# -----------------------------
# INSERT DATA (with more variety)
# -----------------------------

# Customers
customers_data = [
    (1, 'Aman Kumar', 'Delhi'),
    (2, 'Riya Sharma', 'Mumbai'),
    (3, 'Rahul Singh', 'Kolkata'),
    (4, 'Sneha Patel', 'Bangalore'),
    (5, 'Arjun Mehta', 'Delhi'),
    (6, 'Priya Reddy', 'Hyderabad'),
    (7, 'Vikas Gupta', 'Mumbai'),
    (8, 'Anita Das', 'Kolkata'),
    (9, 'Rohit Verma', 'Pune'),
    (10, 'Kavita Joshi', 'Bangalore')
]

cursor.executemany("INSERT OR IGNORE INTO customers VALUES (?, ?, ?)", customers_data)

# Products
products_data = [
    (1, 'Laptop', 50000),
    (2, 'Smartphone', 20000),
    (3, 'Tablet', 15000),
    (4, 'Headphones', 2000),
    (5, 'Smartwatch', 8000),
    (6, 'Keyboard', 1500),
    (7, 'Mouse', 800),
    (8, 'Monitor', 12000)
]

cursor.executemany("INSERT OR IGNORE INTO products VALUES (?, ?, ?)", products_data)

# Orders with dates
orders_data = []
base_date = datetime(2024, 1, 1)

for i in range(1, 51):  # 50 orders
    customer_id = random.randint(1, 10)
    amount = random.randint(500, 5000)
    order_date = (base_date + timedelta(days=random.randint(0, 90))).strftime('%Y-%m-%d')
    orders_data.append((i, customer_id, amount, order_date))

cursor.executemany("INSERT OR IGNORE INTO orders VALUES (?, ?, ?, ?)", orders_data)

# Order Items
order_items_data = []
for i in range(1, 81):  # 80 order items
    order_id = random.randint(1, 50)
    product_id = random.randint(1, 8)
    quantity = random.randint(1, 5)
    order_items_data.append((i, order_id, product_id, quantity))

cursor.executemany("INSERT OR IGNORE INTO order_items VALUES (?, ?, ?, ?)", order_items_data)

# Payments
payments_data = []
payment_methods = ['UPI', 'Card', 'Net Banking', 'Cash']
statuses = ['Success', 'Pending', 'Failed']

for i in range(1, 51):  # Payment for each order
    method = random.choice(payment_methods)
    status = random.choices(statuses, weights=[80, 15, 5])[0]  # 80% success rate
    payments_data.append((i, i, method, status))

cursor.executemany("INSERT OR IGNORE INTO payments VALUES (?, ?, ?, ?)", payments_data)

# Employees
employees_data = [
    (1, 'Rohit Kumar', 'Sales'),
    (2, 'Neha Singh', 'Support'),
    (3, 'Amit Patel', 'Marketing'),
    (4, 'Sonia Sharma', 'Sales'),
    (5, 'Rajesh Verma', 'IT'),
    (6, 'Pooja Reddy', 'HR'),
    (7, 'Vikram Mehta', 'Finance'),
    (8, 'Anjali Gupta', 'Operations')
]

cursor.executemany("INSERT OR IGNORE INTO employees VALUES (?, ?, ?)", employees_data)

conn.commit()

# -----------------------------
# VERIFY DATA
# -----------------------------

print("\n✅ Database setup complete!\n")
print("📊 Data Summary:")
print(f"   • Customers: {cursor.execute('SELECT COUNT(*) FROM customers').fetchone()[0]}")
print(f"   • Orders: {cursor.execute('SELECT COUNT(*) FROM orders').fetchone()[0]}")
print(f"   • Products: {cursor.execute('SELECT COUNT(*) FROM products').fetchone()[0]}")
print(f"   • Order Items: {cursor.execute('SELECT COUNT(*) FROM order_items').fetchone()[0]}")
print(f"   • Payments: {cursor.execute('SELECT COUNT(*) FROM payments').fetchone()[0]}")
print(f"   • Employees: {cursor.execute('SELECT COUNT(*) FROM employees').fetchone()[0]}")

total_revenue = cursor.execute('SELECT SUM(amount) FROM orders').fetchone()[0]
print(f"\n💰 Total Revenue: ₹{total_revenue:,}")

conn.close()

print("\n🚀 Ready to run the app!")
print("   Run: streamlit run app.py")
