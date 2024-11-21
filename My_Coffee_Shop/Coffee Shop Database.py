import sqlite3

# Connect to SQLite database (or create it if it doesn't exist) 
conn = sqlite3.connect("Coffee_Shop_Database.db") #this line must exist in every script to connect to the database
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE Users (
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

cursor.execute("""
CREATE TABLE Products (
    product_id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    description TEXT,
    price REAL NOT NULL CHECK(price > 0),
    category TEXT NOT NULL,
    stock_quantity INTEGER DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
""")

cursor.execute("""
CREATE TABLE Orders (
    order_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    total_price REAL NOT NULL CHECK(total_price >= 0),
    order_status TEXT CHECK(order_status IN ('Pending', 'Completed', 'Cancelled')) DEFAULT 'Pending',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES Users (user_id)
);
""")

cursor.execute("""
CREATE TABLE Orders (
    order_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    total_price REAL NOT NULL CHECK(total_price >= 0),
    order_status TEXT CHECK(order_status IN ('Pending', 'Completed', 'Cancelled')) DEFAULT 'Pending',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES Users (user_id)
);
""")

cursor.execute("""
CREATE TABLE OrderDetails (
    order_detail_id INTEGER PRIMARY KEY AUTOINCREMENT,
    order_id INTEGER NOT NULL,
    product_id INTEGER NOT NULL,
    quantity INTEGER NOT NULL CHECK(quantity > 0),
    price_per_unit REAL NOT NULL CHECK(price_per_unit > 0),
    FOREIGN KEY (order_id) REFERENCES Orders (order_id),
    FOREIGN KEY (product_id) REFERENCES Products (product_id)
);
""")

cursor.execute("""
CREATE TABLE Inventory (
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

cursor.execute("""
CREATE TABLE Payments (
    payment_id INTEGER PRIMARY KEY AUTOINCREMENT,
    order_id INTEGER NOT NULL,
    amount REAL NOT NULL CHECK(amount >= 0),
    payment_status TEXT CHECK(payment_status IN ('Paid', 'Failed', 'Refunded')) DEFAULT 'Paid',
    payment_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (order_id) REFERENCES Orders (order_id)
);
""")

#Example of select database querries
#cursor.execute("SELECT attendance_id, student_id, attendance_date, attendance_time, timetable_id FROM Attendance WHERE course_code = ?",(str(course_code),))

#Example of insert database querries
#cursor.execute("""INSERT INTO Attendance (student_id) VALUES (?, )""", (int(student_id_list[j]), ))
#conn.commit()
