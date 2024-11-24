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
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders

# Email configuration
password = "password"  # Sender Password (make sure 2FA is not enabled)
from_email = "sender@gmail.com"  # Sender email

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

def send_email(invoice_buffer, to_email):
    subject = "Your Coffee Shop Invoice"
    body = (
        f"Dear Customer,\n\n"
        "Thank you for your order! Please find your invoice attached.\n\n"
        "Warm regards,\nCoffee Shop Team"
    )

    # Construct the email
    message = MIMEMultipart()
    message["From"] = from_email
    message["To"] = to_email
    message["Subject"] = subject
    message.attach(MIMEText(body, "plain"))

    # Attach the invoice PDF
    invoice_buffer.seek(0)  # Ensure the buffer is at the beginning
    attachment = MIMEBase('application', 'pdf')
    attachment.set_payload(invoice_buffer.read())
    encoders.encode_base64(attachment)
    attachment.add_header('Content-Disposition', 'attachment', filename="invoice.pdf")
    message.attach(attachment)

    try:
        # Send the email
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.set_debuglevel(1)
        server.starttls()
        server.login(from_email, password)
        server.sendmail(from_email, to_email, message.as_string())
        print("Invoice email sent successfully.")
        server.quit()
    except Exception as e:
        print(f"Failed to send email: {e}")


def get_email_by_username(username):
    # Create a new connection to the database for this thread
    conn = sqlite3.connect('Coffee_Shop_Database.db')
    cursor = conn.cursor()

    # Query to get the email of the user by username
    cursor.execute("SELECT email FROM Users WHERE username = ?", (username,))

    # Fetch the result
    result = cursor.fetchone()

    # If user is found, return the email
    email = result[0] if result else None
    cursor.close()
    conn.close()

    return email


def add_coffee(price, drink):
    st.session_state.order.append(drink)
    st.session_state.order_prices.append(price)
    st.session_state.total += price

    # Save the order details in user session (this could be a list of orders with details)
    order_details = {
        "order_date": st.session_state.order_date,
        "items": st.session_state.order.copy(),
        "total": st.session_state.total,
        "status": "Pending",  # Initial status
    }
    # Initialize orders if not already present
    if "orders" not in st.session_state["user"]:
        st.session_state["user"]["orders"] = []

    st.session_state["user"]["orders"].append(order_details)


def mark_order_as_prepared(order_index):
    if "orders" in st.session_state["user"]:
        order = st.session_state["user"]["orders"][order_index]
        order["status"] = "Prepared"
        st.session_state["user"]["orders"][order_index] = order  # Save the updated order back to session
        # Also, update the database
        cursor.execute("""
        UPDATE Orders SET status = ? WHERE order_id = ?
        """, ("Prepared", order["order_id"]))
        conn.commit()
        st.success(f"Order {order_index + 1} is now marked as Prepared!")


def get_connection():
    """Return a new database connection."""
    return sqlite3.connect("Coffee_Shop_Database.db")

def get_all_users():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM Users")
    users = cursor.fetchall()
    all_users = []
    
    for user in users:
        user_data = {
            "user_id": user[0],
            "username": user[1],
            "password": user[2],
            "full_name": user[3],
            "email": user[4],
            "phone": user[5],
            "role": user[6],
            "created_at": user[7],
            "orders": get_user_orders(user[0], cursor)  # Fetch orders for this user
        }
        all_users.append(user_data)
    
    conn.close()
    return all_users

def get_user_orders(user_id, cursor):
    cursor.execute("SELECT * FROM Orders WHERE user_id = ?", (user_id,))
    orders = cursor.fetchall()  # Fetch orders for the given user_id
    
    user_orders = []
    for order in orders:
        # Fetch order details (products and quantities)
        cursor.execute("""
            SELECT OD.quantity, P.name, OD.price_per_unit
            FROM OrderDetails OD
            JOIN Products P ON OD.product_id = P.product_id
            WHERE OD.order_id = ?
        """, (order[0],))
        order_details = cursor.fetchall()
        
        items = []
        for detail in order_details:
            item = f"{detail[0]} x {detail[1]} (RM {detail[2]:.2f})"
            items.append(item)

        order_data = {
            "order_date": order[4],  # Assuming created_at is in column 4
            "items": items,
            "total": order[2],  # Total price from Orders table
            "status": order[3]
        }
        user_orders.append(order_data)
    
    return user_orders

def clean_order():
    st.session_state.order = []
    st.session_state.order_prices = []
    st.session_state.total = 0

def finish_payment():
    st.success("Payment received! Generating invoice...")
    username = st.session_state.get("username")
    invoice = generate_invoice(st.session_state.order, st.session_state.total)

    # Display the download button
    st.download_button("Download Invoice", data=invoice, file_name="invoice.pdf", mime="application/pdf", on_click=new_order)

    # Send email (this happens independently of button click)
    to_email = get_email_by_username(username)  # Receiver email
    send_email(invoice, to_email)  # Send the email with the invoice

    # Update session state and render the next page manually
    st.session_state.page = "thank_you"
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
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),  # Header text color
        ('ALIGN', (1, 0), (-1, -1), 'CENTER'),  # Center alignment for Quantity and Price
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),  # Bold header
        ('BOTTOMPADDING', (0, 0), (-1, 0), 10),  # Add padding to header
        ('FONTSIZE', (0, 0), (-1, -1), 12),  # Font size for all cells
        ('GRID', (0, 0), (-1, -1), 0.5, colors.white),  # Grid lines
        ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),  # Bold font for the "Total" row
        ('TEXTCOLOR', (0, -1), (-1, -1), colors.black),  # Text color for the "Total" row
        ('TOPPADDING', (0, -1), (-1, -1), 10),
        ('BACKGROUND', (0, -1), (-1, -1), colors.lightgrey),  # Background color for "Total" row
    ]))

    styles = getSampleStyleSheet()
    head = Paragraph("NgopiData Cafe", styles["Title"])
    title = Paragraph("Invoice", styles["Title"])
    date = Paragraph(f"Order Date: {st.session_state.order_date}", styles["Normal"])
    elements = [head, Spacer(1, 7), title, Spacer(1, 15), date, Spacer(1, 15), table]

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

############################# P R O M O ######################################
def render_promo():
    # Ensure that the session state is set up
    if "total" not in st.session_state:
        st.session_state.total = 0.0  # Set initial total amount
    if "promo_applied" not in st.session_state:
        st.session_state.promo_applied = False  # Flag to check if promo is applied

    # Display the promo code input field
    code = st.text_input("Enter the promo code:", key="promo_code")

    # When the user submits the promo code
    if code:
        # Check if the promo code is valid
        if code == "kopi_1234" and not st.session_state.promo_applied:
            # Apply a discount (10% in this case)
            discount = 0.10  # 10% discount
            st.session_state.total *= (1 - discount)  # Update the total with discount
            st.session_state.promo_applied = True  # Mark promo code as applied
            st.success(f"Promo code applied! Your new total is RM {st.session_state.total:.2f}")
        elif st.session_state.promo_applied:
            st.warning("Promo code has already been applied!")
        else:
            st.error("Invalid promo code!")

    # Display the total and promo status
    st.write(f"Current total: RM {st.session_state.total:.2f}")
    
    # Navigation buttons
    col1, col2 = st.columns(2)
    with col1:
        st.button("Continue", on_click=finish_payment)  # Assuming finish_payment function exists
    with col2:
        st.button("Back to Payment", on_click=render_payment)  # Assuming render_payment function exists

############################# PROMO PART ENDS ######################################

def get_pending_orders():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM Orders WHERE order_status = 'Pending'")
    orders = cursor.fetchall()
    
    pending_orders = []
    for order in orders:
        cursor.execute("""
            SELECT P.name, OD.quantity, OD.price_per_unit
            FROM OrderDetails OD
            JOIN Products P ON OD.product_id = P.product_id
            WHERE OD.order_id = ?
        """, (order[0],))
        order_details = cursor.fetchall()
        
        items = [f"{detail[1]} x {detail[0]} (RM {detail[2]:.2f})" for detail in order_details]
        
        pending_orders.append({
            "order_id": order[0],
            "order_date": order[4],
            "items": items,
            "total": order[2],
            "status": order[3],
        })
    
    conn.close()
    return pending_orders


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

    st.button("Enter Promo Code", on_click=render_promo)

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

def get_orders_by_status(status_filter="All"):
    """Fetch orders based on the selected filter (All, Pending, Completed, Cancelled)."""
    conn = get_connection()
    cursor = conn.cursor()
    
    # If status is 'All', fetch all orders; otherwise, filter by status
    if status_filter == "All":
        cursor.execute("""
            SELECT order_id, user_id, total_price, order_status, created_at FROM Orders
        """)
    else:
        cursor.execute("""
            SELECT order_id, user_id, total_price, order_status, created_at FROM Orders WHERE order_status = ?
        """, (status_filter,))
    
    orders = cursor.fetchall()
    conn.close()
    return orders

def get_order_items(order_id):
    """Fetch the items for a given order from the OrderDetails and Products tables."""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT p.name, od.quantity, od.price_per_unit 
        FROM OrderDetails od
        JOIN Products p ON od.product_id = p.product_id
        WHERE od.order_id = ?
    """, (order_id,))
    
    items = cursor.fetchall()
    conn.close()
    return items

def check_orders_page():
    """Display orders and allow status updates on the 'Check Orders' page."""
    st.header("All Orders")
    
    # Dropdown or radio button to filter orders by status
    status_filter = st.selectbox("Filter Orders by Status", ["All", "Pending", "Completed", "Cancelled"])
    
    orders = get_orders_by_status(status_filter)
    
    if orders:
        # Prepare a list of orders with their items
        order_data = []
        for order in orders:
            order_id, user_id, total_price, order_status, created_at = order
            
            # Get items for the specific order
            items = get_order_items(order_id)
            item_list = [f"{item[0]} (x{item[1]}) - RM {item[1] * item[2]:.2f}" for item in items]
            item_details = ", ".join(item_list)
            
            order_data.append([order_id, created_at, item_details, f"RM {total_price:.2f}", order_status])
        
        # Create a DataFrame for better visualization
        order_df = pd.DataFrame(order_data, columns=["Order ID", "Order Date", "Items", "Total", "Status"])
        
        # Display the orders in a table
        st.dataframe(order_df)
        
        # Button to mark the order as 'Prepared', 'Completed', or 'Cancelled'
        for order in orders:
            order_id, _, _, order_status, _ = order
            
            if order_status == "Pending":
                col1, col2, col3 = st.columns(3)
                with col1:
                    if st.button(f"Mark Order {order_id} as Prepared"):
                        conn = get_connection()
                        cursor = conn.cursor()
                        cursor.execute("""
                            UPDATE Orders SET order_status = 'Prepared' WHERE order_id = ?
                        """, (order_id,))
                        conn.commit()
                        conn.close()
                        st.success(f"Order {order_id} is now marked as Prepared!")
                with col2:
                    if st.button(f"Mark Order {order_id} as Completed"):
                        conn = get_connection()
                        cursor = conn.cursor()
                        cursor.execute("""
                            UPDATE Orders SET order_status = 'Completed' WHERE order_id = ?
                        """, (order_id,))
                        conn.commit()
                        conn.close()
                        st.success(f"Order {order_id} is now marked as Completed!")
                with col3:
                    if st.button(f"Mark Order {order_id} as Cancelled"):
                        conn = get_connection()
                        cursor = conn.cursor()
                        cursor.execute("""
                            UPDATE Orders SET order_status = 'Cancelled' WHERE order_id = ?
                        """, (order_id,))
                        conn.commit()
                        conn.close()
                        st.success(f"Order {order_id} is now marked as Cancelled!")
    else:
        st.write("No orders found.")
      
# Streamlit App
st.title("NgopiData Cafe")

if "page" not in st.session_state:
    st.session_state["page"] = "Login"

if "user" not in st.session_state:
    st.session_state["user"] = {}

def navigate_to(page_name):
    st.session_state["page"] = page_name

# Ensure user is taken to Login page first if not authenticated
if not st.session_state["user"] and st.session_state["page"] not in ["Login", "Register"]:
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
        st.success("You have successfully logged out.")  # Optionally show a message

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
        if "orders" in st.session_state["user"] and st.session_state["user"]["orders"]:
            for idx, order in enumerate(st.session_state["user"]["orders"]):
                st.write(f"Order Date: {order['order_date']}")
                st.write("Items:")
                for item in order["items"]:
                    st.write(f"- {item}")
                st.write(f"Total: RM {order['total']:.2f}")
                st.write(f"Status: {order['status']}")  # Show status
                
                # If the order is "Prepared", show a message
                if order["status"] == "Prepared":
                    st.success("Your coffee is ready for pickup!")
                st.markdown("---")  # Separate orders with a line
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
    
    elif st. session_state.page == "promo":
        render_promo()
      
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
        ["Dashboard", "Sales Report", "Check Inventory", "Check Orders", "Check Feedback"]
    )

    # Add the Logout button to the sidebar
    if st.sidebar.button("Logout"):
        # Clear session and navigate to Login page
        st.session_state["user"] = {}  # Clear user data from session
        navigate_to("Login")  # Navigate to the login page
        st.success("You have successfully logged out.")  # Optionally show a message

    if admin_page == "Dashboard":
        st.header("Admin Dashboard")
        st.write("Welcome to the Admin Panel.")
        
        # Example: Manage Users
        dashboard.display_dashboard()

    elif admin_page == "Sales Report":
        salesReport.display_sales_report()

    elif admin_page == "Check Inventory":
        coffee_inv.render_inventory_page()
    
    elif admin_page == "Check Orders":
        check_orders_page()

    elif admin_page == "Check Feedback":
        st.header("Customer Feedbacks")
        feedback_data = feedbackMech.get_all_feedback()
        if feedback_data:
            feedbackMech.display_feedback(st.session_state.get("user"))
        else:
            st.write("No feedback available.")
