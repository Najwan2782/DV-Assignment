import sqlite3
import pandas as pd
import streamlit as st

# Connect to the database
conn = sqlite3.connect("Coffee_Shop_Database.db", check_same_thread=False)
cursor = conn.cursor()

# Function to fetch product names and their corresponding IDs
def get_product_names():
    cursor.execute("""
        SELECT product_id, name FROM Products ORDER BY name;
    """)
    results = cursor.fetchall()
    return {name: product_id for product_id, name in results}

# Function to monitor inventory and get current stock levels along with the latest cost and total cost
def monitor_inventory():
    cursor.execute("""
        SELECT p.product_id, p.name, p.stock_quantity, 
               (SELECT i.cost_per_item 
                FROM Inventory i 
                WHERE i.product_id = p.product_id
                ORDER BY i.updated_at DESC LIMIT 1) AS cost_per_item
        FROM Products p
        ORDER BY p.product_id;
    """)
    results = cursor.fetchall()
    
    # Calculate total cost for each product
    inventory_data = []
    for product_id, name, stock_quantity, cost_per_item in results:
        if cost_per_item is None:
            cost_per_item = 0.0
        total_cost = stock_quantity * cost_per_item
        inventory_data.append([product_id, name, stock_quantity, cost_per_item, total_cost])
    return inventory_data

# Function to check for low inventory and send alerts
def check_low_inventory(threshold=20):
    cursor.execute("""
        SELECT product_id, name, stock_quantity
        FROM Products
        WHERE stock_quantity < ?;
    """, (threshold,))
    results = cursor.fetchall()
    return results

# Function to add inventory when restocking
def add_inventory(product_id, quantity_added, cost_per_item, updated_by):
    cursor.execute("""
        SELECT stock_quantity, name FROM Products WHERE product_id = ?;
    """, (product_id,))
    result = cursor.fetchone()
    
    if result:
        current_stock, name = result
        
        # Update the stock quantity in Products table
        new_stock = current_stock + quantity_added
        cursor.execute("""
            UPDATE Products SET stock_quantity = ? WHERE product_id = ?;
        """, (new_stock, product_id))
        
        # Calculate the total cost for the restock entry
        total_cost = quantity_added * cost_per_item
        
        # Log the change in the Inventory table
        cursor.execute("""
            INSERT INTO Inventory (product_id, change_type, quantity_changed, cost_per_item, total_cost, updated_by)
            VALUES (?, 'Restock', ?, ?, ?, ?);
        """, (product_id, quantity_added, cost_per_item, total_cost, updated_by))
        
        conn.commit()
        return f"Inventory added successfully for {name}."
    return f"Error: Product ID {product_id} not found."

# Function to simulate sending notifications (can be replaced with real email functionality)
def send_notification(product_name, stock_quantity):
    return f"Notification: {product_name} stock is low ({stock_quantity} units). Please restock!"

# The main function for this page
def render_inventory_page():
    # Streamlit app setup
    st.title("☕ Coffee Shop Inventory Management")

    # Low Stock Notifications
    st.header("Low Stock Notifications")
    low_stock_data = check_low_inventory()

    if low_stock_data:
        for product_id, name, stock_quantity in low_stock_data:
            alert_message = send_notification(name, stock_quantity)
            st.warning(alert_message)
    else:
        st.info("No low stock items detected.")

    st.divider()

    # Display current inventory
    st.header("Current Inventory Levels")
    inventory_data = monitor_inventory()

    # Show current inventory in a table with cost and total cost
    inventory_df = pd.DataFrame(inventory_data, columns=["Product ID", "Product Name", "Stock Quantity", "Cost Per Item (RM)", "Total Cost (RM)"])
    st.dataframe(inventory_df)

    # Display a bar chart for stock levels
    st.subheader("Stock Levels Visualization")
    stock_levels = {item[1]: item[2] for item in inventory_data}  # Mapping product names to stock quantities
    st.bar_chart(stock_levels)

    # Get product names for dropdown selection
    product_names = get_product_names()
    product_names_list = list(product_names.keys())

    # Add Inventory (restock items)
    st.divider()
    st.header("Add Inventory (Restock)")
    with st.form(key="restock_form"):
        product_name_restock = st.selectbox("Select Product", product_names_list)
        quantity_added = st.number_input("Quantity to Add", min_value=1, step=1)
        cost_per_item = st.number_input("Cost Per Item (RM)", min_value=0.01, step=0.01, format="%.2f")
        updated_by_restock = st.number_input("Updated By (Employee ID)", min_value=1, step=1)
        submit_button_restock = st.form_submit_button("Add Inventory")
        
        if submit_button_restock:
            product_id = product_names[product_name_restock]
            restock_message = add_inventory(product_id, quantity_added, cost_per_item, updated_by_restock)
            st.success(restock_message)

    # Close the database connection at the end of the app session
 
