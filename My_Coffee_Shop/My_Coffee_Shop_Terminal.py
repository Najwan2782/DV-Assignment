import streamlit as st

# Global variables to store order data
if "order" not in st.session_state:
    st.session_state.order = []
if "total" not in st.session_state:
    st.session_state.total = 0

# Functions
def add_coffee(price, drink):
    st.session_state.order.append(drink)
    st.session_state.total += price

def clean_order():
    st.session_state.order = []
    st.session_state.total = 0

def checkout():
    st.session_state.page = "checkout"

def go_back():
    st.session_state.page = "menu"

def continue_to_payment():
    st.session_state.page = "payment"

def finish_payment():
    st.session_state.page = "thank_you"

def new_order():
    st.session_state.order = []
    st.session_state.total = 0
    st.session_state.page = "menu"

# Page navigation
if "page" not in st.session_state:
    st.session_state.page = "menu"

# Pages
if st.session_state.page == "menu":
    st.title("My Coffee Shop Terminal")
    st.write("### Menu")

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
            st.write(f"**{drink['name']}** - RM {drink['price']:.2f}")
            st.button(
                f"Add {drink['name']}",
                key=f"add_{drink['name']}",
                on_click=add_coffee,
                args=(drink["price"], drink["name"]),
            )

    st.write("### Order Summary")
    st.write("\n".join(st.session_state.order) or "No items added.")
    st.write(f"**Total: RM {st.session_state.total:.2f} **")
    st.button("Clean Order", on_click=clean_order)
    st.button("Check Out", on_click=checkout)

elif st.session_state.page == "checkout":
    st.title("Order Summary")
    st.write("### Items:")
    st.write("\n".join(st.session_state.order) or "No items.")
    st.write(f"**Total: RM {st.session_state.total:.2f} **")
    st.button("Go Back to Menu", on_click=go_back)
    st.button("Continue to Payment", on_click=continue_to_payment)

elif st.session_state.page == "payment":
    st.title("Payment")
    st.write(f"Total Amount: RM {st.session_state.total:.2f} ")
    st.write("Online transfer to this account: 0123 4567 8910")
    st.button("Finish Payment", on_click=finish_payment)
    st.button("Cancel Order", on_click=new_order)

elif st.session_state.page == "thank_you":
    st.title("Thank You!")
    st.write("Your payment has been received. Have a great day!")
    st.button("New Order", on_click=new_order)
