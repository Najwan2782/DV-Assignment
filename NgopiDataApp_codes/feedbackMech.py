# feedback.py
import sqlite3
import streamlit as st

# Connect to SQLite database
conn = sqlite3.connect("Coffee_Shop_Database.db")
cursor = conn.cursor()

# Create feedback table
try:
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS Feedback (
        feedback_id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT,
        rating INTEGER,
        comments TEXT,
        FOREIGN KEY (username) REFERENCES Users (username)
    )
    """)
    conn.commit()
except sqlite3.OperationalError:
    pass

# Function to submit feedback
def submit_feedback(username, rating, comments):
    try:
        cursor.execute("""
        INSERT INTO Feedback (username, rating, comments)
        VALUES (?, ?, ?)
        """, (username, rating, comments))
        conn.commit()
        return True
    except sqlite3.Error as e:
        return False

# Function to retrieve all feedback
def get_all_feedback():
    cursor.execute("SELECT username, rating, comments FROM Feedback")
    return cursor.fetchall()

# Feedback display function
def display_feedback(user):
    if user is None or "username" not in user:
        st.error("You must be logged in to access this page.")
        st.stop()  # Stop the rest of the page from rendering

    full_name = user.get("full_name", "User")  # Use 'full_name' for consistency
    role = user.get("role", "")

    st.header(f"Welcome {full_name}")
    st.write(f"Hello {full_name}, welcome to the Coffee Shop App!")
    st.write(f"You are logged in as a {role}.")

    # Conditional content based on user role
    if role == "Admin":
        st.subheader("Customer Feedback")
        feedback = get_all_feedback()
        if feedback:
            for username, rating, comments in feedback:
                st.markdown(f"**User:** {username}")
                st.markdown(f"**Rating:** {rating}/5")
                st.markdown(f"**Comments:** {comments}")
                st.markdown("---")
        else:
            st.write("No feedback available.")
    elif role == "Customer":
        st.markdown("---")
        st.subheader("Feedback")
        st.write("We value your feedback! Please rate our coffee and service.")

        # Feedback form for customers only
        with st.form(key="feedback_form"):
            rating = st.slider("Rate your experience (1-5):", 1, 5, 3)
            comments = st.text_area("Leave your comments:")
            submitted = st.form_submit_button("Submit Feedback")

            if submitted:
                username = user.get("username")
                if submit_feedback(username, rating, comments):
                    st.success("Thank you for your feedback!")
                else:
                    st.error("An error occurred while submitting your feedback. Please try again.")
