# dashboard.py
import sqlite3
import pandas as pd
import streamlit as st

# Helper function to execute SQL queries
def execute_query(query, params=None):
    """Execute a SQL query and return the result as a Pandas DataFrame."""
    conn = sqlite3.connect("Coffee_Shop_Database.db")
    try:
        if params:
            df = pd.read_sql_query(query, conn, params=params)
        else:
            df = pd.read_sql_query(query, conn)
    finally:
        conn.close()
    return df

# Function to get latest orders (Ordered by most recent)
def get_latest_orders():
    query = """
    SELECT O.order_id, U.username AS customer_name, O.total_price, O.order_status, O.created_at
    FROM Orders O
    JOIN Users U ON O.user_id = U.user_id
    ORDER BY O.created_at DESC
    LIMIT 5;
    """
    return execute_query(query)

# Function to get inventory levels
def get_inventory_levels():
    query = """
    SELECT P.name, P.stock_quantity
    FROM Products P
    ORDER BY P.name;
    """
    return execute_query(query)

# Function to get sales data for completed orders
def get_sales_data():
    query = """
    SELECT P.name, SUM(OD.quantity * OD.price_per_unit) AS total_sales
    FROM OrderDetails OD
    JOIN Products P ON OD.product_id = P.product_id
    JOIN Orders O ON OD.order_id = O.order_id
    WHERE O.order_status = 'Completed'
    GROUP BY P.name
    ORDER BY total_sales DESC;
    """
    return execute_query(query)

# Function to get low inventory items
def get_low_inventory(threshold=20):
    query = """
    SELECT P.name, P.stock_quantity
    FROM Products P
    WHERE P.stock_quantity < ?
    ORDER BY P.stock_quantity ASC;
    """
    return execute_query(query, (threshold,))

# The main function to display the dashboard content
def display_dashboard():
    st.title("Coffee Shop Analytics Dashboard")

    # Latest Orders Section
    st.header("🛍️ Latest Orders")
    latest_orders_data = get_latest_orders()
    if not latest_orders_data.empty:
        latest_orders_data = latest_orders_data.rename(columns={
            'order_id': 'Order ID',
            'customer_name': 'Customer Name',
            'total_price': 'Total Price (RM)',
            'order_status': 'Order Status',
            'created_at': 'Created At'
        })
        st.dataframe(latest_orders_data)
    else:
        st.write("No recent orders.")

    # Real-Time Monitoring Section
    st.divider()
    st.header("⏲️ Real-Time Monitoring")

    # Use columns to display inventory and sales data side by side
    col1, col2 = st.columns(2)

    # Display Inventory Levels in the first column
    with col1:
        st.subheader("Inventory Levels")
        inventory_data = get_inventory_levels()
        if not inventory_data.empty:
            inventory_data = inventory_data.rename(columns={
                'name': 'Product Name',
                'stock_quantity': 'Stock Quantity'
            })
            st.dataframe(inventory_data)
        else:
            st.write("No products in inventory.")

    # Display Sales Data in the second column
    with col2:
        st.subheader("Sales Data")
        sales_data = get_sales_data()
        if not sales_data.empty:
            sales_data = sales_data.rename(columns={
                'name': 'Product Name',
                'total_sales': 'Total Sales (RM)'
            })
            st.dataframe(sales_data)
        else:
            st.write("No sales data available.")

    # Inventory Health Check Section
    st.divider()
    st.header("📦 Inventory Health Check")

    # Display Low Inventory Items
    low_inventory_data = get_low_inventory()
    if not low_inventory_data.empty:
        low_inventory_data = low_inventory_data.rename(columns={
            'name': 'Product Name',
            'stock_quantity': 'Stock Quantity'
        })
        st.write("The following items are running low and need restocking soon:")
        st.dataframe(low_inventory_data)
    else:
        st.write("All items have sufficient stock.")
