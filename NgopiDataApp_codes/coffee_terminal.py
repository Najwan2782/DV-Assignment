import streamlit as st
import sqlite3
import pandas as pd
from reportlab.lib.pagesizes import A5
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
import io
from datetime import datetime

# Global variables to store order data
if "order" not in st.session_state:
    st.session_state.order = []
if "order_prices" not in st.session_state:
    st.session_state.order_prices = []
if "total" not in st.session_state:
    st.session_state.total = 0
if "order_date" not in st.session_state:
    st.session_state.order_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

DB_FILE = "Coffee_Shop_Database.db"

def reduce_inventory(order_items):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    user_id = 1  # Example user_id, replace with actual user handling.

    for item in order_items:
        cursor.execute("SELECT product_id, stock_quantity, price FROM Products WHERE name = ?", (item,))
        product = cursor.fetchone()

        if product:
            product_id, stock_quantity, price = product
            if stock_quantity > 0:
                new_stock_quantity = stock_quantity - 1
                cursor.execute("""
                    UPDATE Products SET stock_quantity = ? WHERE product_id = ?
                """, (new_stock_quantity, product_id))
                cursor.execute("""
                    INSERT INTO Inventory (product_id, change_type, quantity_changed, cost_per_item, total_cost, updated_by)
                    VALUES (?, 'Consumption', -1, ?, ?, ?)
                """, (product_id, price, price, user_id))
            else:
                st.warning(f"Sorry, {item} is out of stock.")
                return False
        else:
            st.warning(f"Product '{item}' not found.")
            return False

    conn.commit()
    conn.close()
    return True

def add_sale_to_db(order_items, total_price):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    try:
        cursor.execute("INSERT INTO Orders (user_id, total_price, order_status) VALUES (1, ?, 'Completed')", (total_price,))
        order_id = cursor.lastrowid

        for item, price in zip(order_items, st.session_state.order_prices):
            cursor.execute("SELECT product_id FROM Products WHERE name = ?", (item,))
            product = cursor.fetchone()

            if product:
                product_id = product[0]
            else:
                cursor.execute("INSERT INTO Products (name, price, category) VALUES (?, ?, 'Coffee')", (item, price))
                product_id = cursor.lastrowid

            cursor.execute("INSERT INTO OrderDetails (order_id, product_id, quantity, price_per_unit) VALUES (?, ?, 1, ?)", 
                           (order_id, product_id, price))
        conn.commit()
    except sqlite3.Error as e:
        st.error(f"Database error: {e}")
        conn.rollback()
    finally:
        conn.close()

def generate_invoice(order_items, total_amount):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A5)

    data = [["Drink", "Quantity", "Price"]]
    for item, price in zip(order_items, st.session_state.order_prices):
        data.append([item, "1", f"RM {price:.2f}"])

    data.append(["Total", "", f"RM {total_amount:.2f}"])

    table = Table(data, colWidths=[150, 50, 100])
    table.setStyle(TableStyle([
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
        ('ALIGN', (1, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
        ('FONTSIZE', (0, 0), (-1, -1), 12),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
    ]))

    styles = getSampleStyleSheet()
    title = Paragraph("Invoice", styles["Title"])
    date = Paragraph(f"Order Date: {st.session_state.order_date}", styles["Normal"])
    elements = [title, Spacer(1, 15), date, Spacer(1, 15), table]

    doc.build(elements)
    buffer.seek(0)
    return buffer

def finish_payment():
    try:
        # Reduce inventory and check stock availability
        if not reduce_inventory(st.session_state.order):
            return

        # Add the order details to the database
        add_sale_to_db(st.session_state.order, st.session_state.total)

        # Generate and provide the invoice PDF for download
        invoice_buffer = generate_invoice(st.session_state.order, st.session_state.total)
        st.download_button(
            label="📄 Download Invoice",
            data=invoice_buffer,
            file_name="invoice.pdf",
            mime="application/pdf"
        )

        # Thank the user
        st.session_state.page = "thank_you"

    except Exception as e:
        st.error(f"An unexpected error occurred: {e}")

# Functions for the menu, checkout, payment, etc.
def add_coffee(price, drink):
    st.session_state.order.append(drink)
    st.session_state.order_prices.append(price)
    st.session_state.total += price

def clean_order():
    st.session_state.order = []
    st.session_state.order_prices = []
    st.session_state.total = 0

def checkout():
    st.session_state.page = "checkout"

def go_back():
    st.session_state.page = "menu"

def continue_to_payment():
    st.session_state.page = "payment"

def finish_payment():
    # Add sale to the database after payment is completed
    add_sale_to_db(st.session_state.order, st.session_state.total)

    # Reduce inventory based on the items ordered
    reduce_inventory(st.session_state.order)

    # Generate the invoice PDF after payment
    invoice_buffer = generate_invoice(st.session_state.order, st.session_state.total)

    # Allow the user to download the invoice
    st.download_button(
        label="Download Invoice",
        data=invoice_buffer,
        file_name="invoice.pdf",
        mime="application/pdf"
    )
    st.session_state.page = "thank_you"

def new_order():
    st.session_state.order = []
    st.session_state.order_prices = []
    st.session_state.total = 0
    st.session_state.page = "menu"


# Render the terminal
def render_terminal():
    if "page" not in st.session_state:
        st.session_state.page = "menu"

    # Pages
    if st.session_state.page == "menu":
        st.title("☕ NgopiData")
        st.subheader("Explore Our Menu and Order Your Favorite Drink!")

        # Drink data
        drinks = [
            {"name": "Espresso", "price": 4.90, "image": "https://raw.githubusercontent.com/Najwan2782/DV-Assignment/refs/heads/main/My_Coffee_Shop/assets/images/ecspresso.jpeg"},
            {"name": "Americano", "price": 6.90, "image": "https://raw.githubusercontent.com/Najwan2782/DV-Assignment/refs/heads/main/My_Coffee_Shop/assets/images/americano.jpeg"},
            {"name": "Capucino", "price": 9.90, "image": "https://raw.githubusercontent.com/Najwan2782/DV-Assignment/refs/heads/main/My_Coffee_Shop/assets/images/capucino.jpeg"},
            {"name": "Latte", "price": 9.90, "image": "https://raw.githubusercontent.com/Najwan2782/DV-Assignment/refs/heads/main/My_Coffee_Shop/assets/images/latte.jpeg"},
            {"name": "Mocha", "price": 11.90, "image": "https://raw.githubusercontent.com/Najwan2782/DV-Assignment/refs/heads/main/My_Coffee_Shop/assets/images/mocha.jpeg"},
            {"name": "Ice Espresso", "price": 6.90, "image": "https://raw.githubusercontent.com/Najwan2782/DV-Assignment/refs/heads/main/My_Coffee_Shop/assets/images/ice_espresso.jpeg"},
            {"name": "Ice Americano", "price": 8.90, "image": "https://raw.githubusercontent.com/Najwan2782/DV-Assignment/refs/heads/main/My_Coffee_Shop/assets/images/ice_americano.jpeg"},
            {"name": "Ice Capucino", "price": 11.90, "image": "https://raw.githubusercontent.com/Najwan2782/DV-Assignment/refs/heads/main/My_Coffee_Shop/assets/images/ice_capucino.jpeg"},
            {"name": "Ice Latte", "price": 11.90, "image": "https://raw.githubusercontent.com/Najwan2782/DV-Assignment/refs/heads/main/My_Coffee_Shop/assets/images/ice_latte.jpeg"},
            {"name": "Ice Mocha", "price": 13.90, "image": "https://raw.githubusercontent.com/Najwan2782/DV-Assignment/refs/heads/main/My_Coffee_Shop/assets/images/ice_mocha.jpeg"},
        ]

        # Display drinks
        cols = st.columns(5)
        for i, drink in enumerate(drinks):
            with cols[i % 5]:
                st.image(drink["image"], use_column_width=True)
                st.markdown(f"**{drink['name']}**")
                st.markdown(f"**RM {drink['price']:.2f}**")
                st.button(
                    f"Add {drink['name']}",
                    key=f"add_{drink['name']}",
                    on_click=add_coffee,
                    args=(drink["price"], drink["name"]),
                )

        st.markdown("---")
        st.subheader("🛒 Order Summary")
        if st.session_state.order:
            # Prepare the data for the table
            order_data = {
                "Item": st.session_state.order,
                "Price (RM)": [f"RM {price:.2f}" for price in st.session_state.order_prices],
            }
            # Create a DataFrame and display it as a table
            order_df = pd.DataFrame(order_data)
            st.table(order_df)

            # Total
            st.markdown(f"**Total: RM {st.session_state.total:.2f}**")
        else:
            st.write("No items added yet.")
        
        col1, col2 = st.columns(2)
        with col1:
            st.button("🧹 Clean Order", on_click=clean_order)
        with col2:
            st.button("✅ Check Out", on_click=checkout)

    elif st.session_state.page == "checkout":
        st.title("🧾 Order Summary")
        st.subheader("Your Items:")
        if st.session_state.order:
            # Prepare the data for the table
            order_data = {
                "Item": st.session_state.order,
                "Price (RM)": [f"RM {price:.2f}" for price in st.session_state.order_prices],
            }
            # Create a DataFrame and display it as a table
            order_df = pd.DataFrame(order_data)
            st.table(order_df)

            st.markdown(f"**Total: RM {st.session_state.total:.2f}**")
        else:
            st.write("No items in your order.")
        
        st.markdown("---")
        col1, col2 = st.columns(2)
        with col1:
            st.button("⬅️ Back to Menu", on_click=go_back)
        with col2:
            st.button("💳 Continue to Payment", on_click=continue_to_payment)

    elif st.session_state.page == "payment":
        st.title("💳 Payment")
        st.write(f"**Total Amount: RM {st.session_state.total:.2f}**")
        st.write("Please transfer to the following account:")
        st.code("0123 4567 8910")
        col1, col2 = st.columns(2)
        with col1:
            st.button("✅ Finish Payment", on_click=finish_payment)
        with col2:
            st.button("❌ Cancel Order", on_click=new_order)

    elif st.session_state.page == "thank_you":
        st.title("🎉 Thank You!")
        st.subheader("Your payment has been received.")
        st.write("We appreciate your business. Have a wonderful day!")
        st.button("🆕 Start a New Order", on_click=new_order)

    if st.session_state.page == "checkout" and not st.session_state.order:
        st.warning("Your order is empty. Please add items to proceed.")
        st.button("Back to Menu", on_click=go_back)

render_terminal()