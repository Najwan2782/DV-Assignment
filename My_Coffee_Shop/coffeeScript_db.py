import sqlite3
import pandas as pd

DB_FILE = "Coffee_Shop_Database.db"

def create_tables():
    """Create all tables in the database if they do not exist."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    # Create Users table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS Users (
        user_id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL UNIQUE,
        password TEXT NOT NULL,
        full_name TEXT NOT NULL,
        email TEXT UNIQUE,
        phone TEXT,
        role TEXT CHECK(role IN ('Customer', 'Staff', 'Admin')) NOT NULL,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # Create Products table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS Products (
        product_id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        description TEXT,
        price REAL NOT NULL CHECK(price > 0),
        category TEXT NOT NULL,
        stock_quantity INTEGER DEFAULT 0,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # Create Orders table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS Orders (
        order_id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        total_price REAL NOT NULL CHECK(total_price >= 0),
        order_status TEXT CHECK(order_status IN ('Pending', 'Completed', 'Cancelled')) DEFAULT 'Pending',
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES Users (user_id)
    );
    """)

    # Create OrderDetails table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS OrderDetails (
        order_detail_id INTEGER PRIMARY KEY AUTOINCREMENT,
        order_id INTEGER NOT NULL,
        product_id INTEGER NOT NULL,
        quantity INTEGER NOT NULL CHECK(quantity > 0),
        price_per_unit REAL NOT NULL CHECK(price_per_unit > 0),
        FOREIGN KEY (order_id) REFERENCES Orders (order_id),
        FOREIGN KEY (product_id) REFERENCES Products (product_id)
    );
    """)

    # Create Inventory table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS Inventory (
        inventory_id INTEGER PRIMARY KEY AUTOINCREMENT,
        product_id INTEGER NOT NULL,
        change_type TEXT CHECK(change_type IN ('Restock', 'Consumption')) NOT NULL,
        quantity_changed INTEGER NOT NULL,
        updated_by INTEGER NOT NULL,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (product_id) REFERENCES Products (product_id),
        FOREIGN KEY (updated_by) REFERENCES Users (user_id)
    );
    """)

    # Create Payments table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS Payments (
        payment_id INTEGER PRIMARY KEY AUTOINCREMENT,
        order_id INTEGER NOT NULL,
        amount REAL NOT NULL CHECK(amount >= 0),
        payment_status TEXT CHECK(payment_status IN ('Paid', 'Failed', 'Refunded')) DEFAULT 'Paid',
        payment_date DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (order_id) REFERENCES Orders (order_id)
    );
    """)

    # Indexes for performance
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_orders_created_at ON Orders(created_at);")

    conn.commit()
    conn.close()

def execute_query(query, params=None):
    """Execute a SQL query and return the result as a Pandas DataFrame."""
    conn = sqlite3.connect(DB_FILE)
    try:
        if params:
            df = pd.read_sql_query(query, conn, params=params)
        else:
            df = pd.read_sql_query(query, conn)
    finally:
        conn.close()
    return df

def get_connection():
    """Return a new database connection."""
    return sqlite3.connect(DB_FILE)

# Call this function only when setting up the database initially
if __name__ == "__main__":
    create_tables()
