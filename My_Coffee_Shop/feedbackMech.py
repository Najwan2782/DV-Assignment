# feedback.py
import sqlite3
import streamlit as st
import pandas as pd

# Connect to SQLite database with foreign key enforcement
conn = sqlite3.connect("Coffee_Shop_Database.db", check_same_thread=False)
conn.execute("PRAGMA foreign_keys = ON;")  # Ensure foreign key constraints are enforced
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
except sqlite3.OperationalError as e:
    st.error(f"Database error: {e}")

# Function to submit feedback
def submit_feedback(username, rating, comments):
    try:
        # Validate input
        if not username:
            print("Error: Username is missing.")
            return False
        if not (1 <= rating <= 5):
            print("Error: Rating must be between 1 and 5.")
            return False
        if not comments.strip():
            print("Error: Comments cannot be empty.")
            return False

        # Check if username exists in Users table
        cursor.execute("SELECT COUNT(*) FROM Users WHERE username = ?", (username,))
        if cursor.fetchone()[0] == 0:
            print(f"Error: Username '{username}' does not exist in Users table.")
            return False

        # Insert feedback
        print(f"Submitting feedback: {username}, {rating}, {comments}")  # Debug log
        cursor.execute("""
        INSERT INTO Feedback (username, rating, comments)
        VALUES (?, ?, ?)
        """, (username, rating, comments))
        conn.commit()
        return True
    except sqlite3.Error as e:
        print(f"Database error: {e}")  # Debug log
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

    # Conditional content based on user role
    if role == "Admin":
        feedback = get_all_feedback()
        
        if feedback:
            # Create a filter for selecting rating
            rating_filter = st.slider("Filter feedback by rating (1-5):", 1, 5, 5)
            
            # Filter feedback based on the selected rating
            filtered_feedback = [f for f in feedback if f[1] == rating_filter]  # f[1] is the rating
            
            if filtered_feedback:
                # Convert the filtered feedback data into a pandas DataFrame
                feedback_df = pd.DataFrame(filtered_feedback, columns=["Username", "Rating", "Comments"])
                
                # Hide the 'Username' column by dropping it from the DataFrame
                feedback_df = feedback_df.drop(columns=["Username"])
                
                # Display the table (without Username column)
                st.subheader(f"Customer Feedback (Rating: {rating_filter} stars)")
                st.table(feedback_df)  # Display as a static table
                # Alternatively, use st.dataframe for an interactive table
                # st.dataframe(feedback_df)
            else:
                st.write(f"No feedback found with {rating_filter} stars.")
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
                if not username:
                    st.error("An error occurred. Username not found.")
                    return
                if submit_feedback(username, rating, comments):
                    st.success("Thank you for your feedback!")
                else:
                    st.error("An error occurred while submitting your feedback. Please try again.")
