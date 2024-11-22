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
if "order_date" not in st.session_state:  # Initialize the order_date
    st.session_state.order_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")  # Set the current date and time


DB_FILE = "Coffee_Shop_Database.db"

def add_sale_to_db(order_items, total_price):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    # Insert into Orders table (assuming user_id = 1, you might want to change this logic)
    cursor.execute(""" 
    INSERT INTO Orders (user_id, total_price, order_status)
    VALUES (1, ?, 'Completed')""", (total_price,))
    order_id = cursor.lastrowid  # Get the last inserted order id

    for item, price in zip(order_items, st.session_state.order_prices):
        # Check if product exists in the Products table
        cursor.execute("SELECT product_id FROM Products WHERE name = ?", (item,))
        product = cursor.fetchone()

        if not product:
            # If the product doesn't exist, insert it into the Products table
            cursor.execute("""
            INSERT INTO Products (name, price, category)
            VALUES (?, ?, ?)""", (item, price, 'Coffee'))  # Assuming 'Coffee' as category
            conn.commit()  # Commit to save the new product
            product_id = cursor.lastrowid  # Get the new product_id
            st.success(f"Product '{item}' has been added to the menu.")
        else:
            product_id = product[0]  # If the product exists, use the existing product_id

        # Insert into OrderDetails table
        cursor.execute("""
        INSERT INTO OrderDetails (order_id, product_id, quantity, price_per_unit)
        VALUES (?, ?, 1, ?)""", 
        (order_id, product_id, price))

    conn.commit()  # Commit changes to the database
    conn.close()  # Close the connection

# Function to generate the PDF invoice
def generate_invoice(order_items, total_amount):
    buffer = io.BytesIO()
    
    # Create a SimpleDocTemplate object with A5 size
    doc = SimpleDocTemplate(buffer, pagesize=A5)
    
    # Prepare the data for the table
    data = [["Drink", "Quantity", "Price"]]  # Table header
    
    # Add items, quantities, and prices to the table data
    for item, price in zip(order_items, st.session_state.order_prices):
        item_name = item[:25]  # Truncate item name to fit
        quantity = "1"  # Assuming quantity is always 1
        price_str = f"RM {price:.2f}"
        data.append([item_name, quantity, price_str])
    
    # Merge the first two cells in the last row for "Total Amount"
    data.append(["", "", ""])  # Empty row to fill the last cell
    data[-1][0] = f"Total Amount: RM {total_amount:.2f}"  # Set the total amount text in the merged cell
    
    # Get the current date (or use st.session_state.order_date if it's saved there)
    order_date = st.session_state.order_date if "order_date" in st.session_state else datetime.today().strftime('%Y-%m-%d')
    
    # Create the table
    table = Table(data, colWidths=[150, 50, 100])  # Adjust column widths as needed

    # Set table style
    table.setStyle(TableStyle([
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),  # Header text color
        ('ALIGN', (1, 0), (-1, -1), 'CENTER'),  # Center align quantity and price columns
        ('ALIGN', (0, 1), (0, -1), 'LEFT'),  # Left align only the first column (Item Name)
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),  # Set font size for all
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),  # Padding for all cells
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('LEFTPADDING', (0, 0), (-1, -1), 10),
        ('RIGHTPADDING', (0, 0), (-1, -1), 10),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.white),  # Invisible grid (no border lines)
        ('SPAN', (-3, -1), (0, -1)),  # Merge the first two cells in the last row
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),  
        ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),  # Apply bold to the last row
        ('FONTSIZE', (0, -1), (-1, -1), 12)
    ]))
    
    # Create title and order date as a paragraph
    styles = getSampleStyleSheet()
    title_style = styles["Title"]
    title_style.fontSize = 18  # Increase font size for the title
    title = Paragraph(f"<b>Invoice</b>", title_style)
    
    # Create the date paragraph
    date_style = styles["Normal"]
    date_style.alignment = 1
    date = Paragraph(f"Order Date: {order_date}", date_style)
    gap = Spacer(1, 15)
    
    # Create the document with the title, date, and table
    elements = [title, date, gap, table]
    
    # Build the PDF
    doc.build(elements)
    
    buffer.seek(0)
    return buffer


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

# Page navigation
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
