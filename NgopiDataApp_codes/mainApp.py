import sqlite3
import streamlit as st
import dashboard
import salesReport
import coffee_inv
import feedbackMech
import hashlib
import pandas as pd
from reportlab.lib.pagesizes import A5
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
import io
from datetime import datetime

# Database Connection
conn = sqlite3.connect("Coffee_Shop_Database.db")
cursor = conn.cursor()

# Ensure the Users table exists
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
conn.commit()

# Global variables for terminal state
if "order" not in st.session_state:
    st.session_state.order = []
if "order_prices" not in st.session_state:
    st.session_state.order_prices = []
if "total" not in st.session_state:
    st.session_state.total = 0
if "order_date" not in st.session_state:
    st.session_state.order_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

# Predefined staff IDs
valid_staff_ids = ["ADM001", "ADM002", "ADM003"]

# Functions for authentication and registration
def register_user(username, password, full_name, role, email, phone):
    try:
        hashed_password = hashlib.sha256(password.encode()).hexdigest()
        cursor.execute("""
        INSERT INTO Users (username, password, full_name, role, email, phone)
        VALUES (?, ?, ?, ?, ?, ?)
        """, (username, hashed_password, full_name, role, email, phone))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False

def check_credentials(username, password):
    cursor.execute("""
    SELECT role, full_name, password FROM Users WHERE username = ?
    """, (username,))
    result = cursor.fetchone()
    if result and hashlib.sha256(password.encode()).hexdigest() == result[2]:
        return result[:2]
    return None

# Coffee Terminal Functions
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
    st.success("Payment received! Generating invoice...")
    buffer = generate_invoice(st.session_state.order, st.session_state.total)
    st.download_button("Download Invoice", data=buffer, file_name="invoice.pdf", mime="application/pdf")
    render_thank_you()
    
def new_order():
    # Reset order data
    st.session_state.order = []
    st.session_state.order_prices = []
    st.session_state.total = 0
    st.session_state.order_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Show the terminal and initial summary again
    st.session_state['show_terminal'] = True
    st.session_state['show_int_summary'] = True
    st.session_state['show_message'] = True

    # Navigate back to the home page (main screen)
    st.session_state.page = "Home"


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
    elements = [Paragraph("Invoice", styles["Title"]), Spacer(1, 15), table]
    doc.build(elements)
    buffer.seek(0)
    return buffer

def render_terminal():
    if st.session_state.get('show_terminal', True):  # Only show terminal if the flag is True
        st.title("☕ NgopiData")
        st.subheader("Order Your Favorite Drink")
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

        cols = st.columns(5)
        for i, drink in enumerate(drinks):
            with cols[i % 5]:
                st.image(drink["image"], use_column_width=True)
                st.markdown(f"**{drink['name']}**")
                st.markdown(f"**RM {drink['price']:.2f}**")
                st.button(f"Add {drink['name']}", key=f"add_{drink['name']}", on_click=add_coffee, args=(drink["price"], drink["name"]))
        st.write("Your order summary is below.")

def render_order_summary():
    if st.session_state.get('show_int_summary', True):
        st.markdown("---")
        st.subheader("🛒 Order Summary")
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
    elif not st.session_state.order:
        st.write("No items added yet.")

    if st.session_state.get('show_int_summary', True):  # Only show if we are not in checkout
        col1, col2 = st.columns(2)
        with col1:
            st.button("🧹 Clean Order", on_click=clean_order)
        with col2:
            st.button("✅ Check Out", on_click=render_checkout)



def render_checkout():
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
        st.button("⬅️ Back to Menu", on_click=new_order)
    with col2:
        st.button("💳 Continue to Payment", on_click=render_payment)

    # Hide the terminal on checkout
    st.session_state['show_terminal'] = False
    st.session_state['show_int_summary'] = False
    st.session_state['show_message'] = False



def render_payment():
    st.title("💳 Payment")
    st.write(f"**Total Amount: RM {st.session_state.total:.2f}**")
    st.write("Please transfer to the following account:")
    st.code("0123 4567 8910")

    col1, col2 = st.columns(2)
    with col1:
        st.button("✅ Finish Payment", on_click=finish_payment)
    with col2:
        st.button("❌ Cancel Order", on_click=new_order)


def render_thank_you():
    st.title("🎉 Thank You!")
    st.subheader("Your payment has been received.")
    st.write("We appreciate your business. Have a wonderful day!")
    st.button("🆕 Start a New Order", on_click=new_order)

def message(full_name):
    if st.session_state.get('show_message', True):
        st.header(f"Welcome, {full_name}!")
        st.divider()
        

# Streamlit App
st.title("NgopiData Cafe")

if "page" not in st.session_state:
    st.session_state["page"] = "Login"

if "user" not in st.session_state:
    st.session_state["user"] = {}

def navigate_to(page_name):
    st.session_state["page"] = page_name

# Ensure user is taken to Login page first if not authenticated
if not st.session_state["user"]:
    st.session_state["page"] = "Login"

if st.session_state["page"] == "Login":
    st.header("Login")

    username = st.text_input("Username", key="login_username")
    password = st.text_input("Password", type="password", key="login_password")

    if st.button("Login"):
        user_data = check_credentials(username, password)
        if user_data:
            role, full_name = user_data
            st.session_state["user"] = {"username": username, "role": role, "full_name": full_name}
            st.success(f"Welcome {full_name}! You are logged in as a {role}.")
            if role == "Admin":
                navigate_to("AdminDashboard")
            else:
                navigate_to("Home")
        else:
            st.error("Invalid username or password.")

    if st.button("Go to Register"):
        navigate_to("Register")

elif st.session_state["page"] == "Register":
    st.header("Register")

    full_name = st.text_input("Full Name", key="register_full_name")
    username = st.text_input("Create a Username", key="register_username")
    password = st.text_input("Create a Password", type="password", key="register_password")
    email = st.text_input("Email Address", key="register_email")
    phone = st.text_input("Phone Number", key="register_phone")
    role = st.radio("Register as", ["Customer", "Admin"], key="register_role")

    staff_id = None
    if role == "Admin":
        st.warning("Admin registration requires a valid staff ID.")
        staff_id = st.text_input("Staff ID", key="register_staff_id")

    if st.button("Register"):
        if role == "Admin" and staff_id not in valid_staff_ids:
            st.error("Invalid Staff ID. Please contact the administrator.")
        else:
            result = register_user(username, password, full_name, role, email, phone)
            if result:
                st.success("Registration successful! You can now log in.")
                navigate_to("Login")
            else:
                st.error("Registration failed. Username or email already exists.")

    if st.button("Back to Login"):
        navigate_to("Login")

####################### C U S T O M E R #########################
elif st.session_state["page"] == "Home":
    # Customer Navigation Sidebar
    st.sidebar.title("Customer Navigation")
    customer_page = st.sidebar.radio(
        "Navigate to:",
        ["Order Coffee", "My Orders", "Feedback"]
    )

    # Add the Logout button to the sidebar
    if st.sidebar.button("Logout"):
        # Clear session and navigate to Login page
        st.session_state["user"] = {}  # Clear user data from session
        navigate_to("Login")  # Navigate to the login page
        st.write("You have successfully logged out.")  # Optionally show a message

    user = st.session_state.get("user", {})
    full_name = user.get("full_name", "User")
    role = user.get("role", "")

    if customer_page == "Order Coffee":
        message(full_name)
        render_terminal()

        # Call the order summary display function
        render_order_summary()  # Display order summary with price and total

    elif customer_page == "My Orders":
        st.header(f"Welcome, {full_name}!")
        st.subheader("Your Orders")
        if "orders" in user:
            for order in user["orders"]:
                st.write(order)
        else:
            st.write("You have no orders yet.")

    elif customer_page == "Feedback":
        st.header(f"Welcome, {full_name}!")
        st.subheader("Feedback")
        st.write("We value your feedback! Please rate our coffee and service.")

        # Feedback form for customers only
        with st.form(key="feedback_form"):
            rating = st.slider("Rate your experience (1-5):", 1, 5, 3)
            comments = st.text_area("Leave your comments:")
            submitted = st.form_submit_button("Submit Feedback")

            if submitted:
                username = user.get("username")
                if feedbackMech.submit_feedback(username, rating, comments):  # Call the submit_feedback function from feedbackMech.py
                    st.success("Thank you for your feedback!")
                else:
                    st.error("An error occurred while submitting your feedback. Please try again.")

    # Implementing the checkout, payment, and thank-you flow
    if st.session_state.page == "checkout":
        render_checkout()  # Display checkout page

    elif st.session_state.page == "payment":
        render_payment()  # Display payment page

    elif st.session_state.page == "thank_you":
        render_thank_you()  # Display thank-you page


########################## A D M I N ###########################
elif st.session_state["page"] == "AdminDashboard":
    # Admin Dashboard
    st.sidebar.title("Admin Navigation")
    admin_page = st.sidebar.radio(
        "Navigate to:",
        ["Dashboard", "Sales Report", "Check Inventory", "Check Feedback"]
    )

    # Add the Logout button to the sidebar
    if st.sidebar.button("Logout"):
        # Clear session and navigate to Login page
        st.session_state["user"] = {}  # Clear user data from session
        navigate_to("Login")  # Navigate to the login page
        st.write("You have successfully logged out.")  # Optionally show a message

    if admin_page == "Dashboard":
        st.header("Admin Dashboard")
        st.write("Welcome to the Admin Panel.")
        
        # Example: Manage Users
        dashboard.display_dashboard()

    elif admin_page == "Sales Report":
        salesReport.display_sales_report()

    elif admin_page == "Check Inventory":
        coffee_inv.render_inventory_page()

    elif admin_page == "Check Feedback":
        st.header("Customer Feedbacks")
        feedback_data = feedbackMech.get_all_feedback()
        if feedback_data:
            feedbackMech.display_feedback()
        else:
            st.write("No feedback available.")
