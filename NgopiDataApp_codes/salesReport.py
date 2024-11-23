import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import plotly.express as px
from coffeeScript_db import execute_query  # Import the database query function
from datetime import datetime, timedelta

# Helper function to fetch sales and cost data
def get_sales_and_cost_data(date_filter=None):
    date_condition = ""
    if date_filter:
        date_condition = f"WHERE DATE(o.created_at) >= DATE(?)"
        
    query = f"""
    SELECT 
        p.name AS product_name, 
        SUM(od.quantity) AS total_quantity, 
        SUM(od.quantity * od.price_per_unit) AS total_revenue,
        SUM(od.quantity * (SELECT i.cost_per_item 
                           FROM Inventory i 
                           WHERE i.product_id = p.product_id
                           ORDER BY i.updated_at DESC LIMIT 1)) AS total_cost  -- Calculate total cost based on most recent cost
    FROM OrderDetails od
    INNER JOIN Products p ON od.product_id = p.product_id
    INNER JOIN Orders o ON od.order_id = o.order_id
    {date_condition}
    GROUP BY p.name
    ORDER BY total_revenue DESC;
    """
    
    return execute_query(query, params=[date_filter]) if date_filter else execute_query(query)

# Helper function to fetch best and worst sellers
def get_best_and_worst_sellers(date_filter=None):
    sales_and_cost_data = get_sales_and_cost_data(date_filter)
    if sales_and_cost_data.empty:
        return None, None  # Return None if no data

    # Best seller: highest total revenue
    best_seller = sales_and_cost_data.iloc[0]

    # Worst seller: lowest total revenue (filter out 0 revenue)
    worst_sellers = sales_and_cost_data[sales_and_cost_data['total_revenue'] > 0].nsmallest(1, 'total_revenue')
    
    return best_seller, worst_sellers

# Generate random color map for the products
def generate_color_map(products):
    color_map = {}
    colors = plt.cm.tab20c.colors  # You can change the color palette here
    for idx, product in enumerate(products):
        color_map[product] = colors[idx % len(colors)]  # Cycle through colors if more than available
    return color_map

# Function to display the sales report
def display_sales_report():
    st.title("☕ Coffee Shop Sales Reporting")

    # Date filter options on the main page
    st.header("🗓 Date Filters")
    report_type = st.radio("Select Report Type", ["Daily", "Weekly", "Monthly"], index=0)

    if report_type == "Daily":
        start_date = st.date_input("Select Date", datetime.now().date())
        start_date_str = start_date.strftime("%Y-%m-%d")
    elif report_type == "Weekly":
        start_date = st.date_input("Start of the Week", datetime.now().date() - timedelta(days=7))
        start_date_str = start_date.strftime("%Y-%m-%d")
    elif report_type == "Monthly":
        start_date = st.date_input("Start of the Month", datetime.now().replace(day=1))
        start_date_str = start_date.strftime("%Y-%m-%d")

    # Fetch sales and cost data
    sales_and_cost_data = get_sales_and_cost_data(start_date_str)

    # Fetch best and worst sellers
    best_seller, worst_sellers = get_best_and_worst_sellers(start_date_str)

    # Process the sales and cost data
    if not sales_and_cost_data.empty:
        # Rename columns for better readability
        sales_and_cost_data.rename(columns={
            'product_name': 'Product Name',
            'total_quantity': 'Total Quantity Sold',
            'total_revenue': 'Total Revenue (RM)',
            'total_cost': 'Total Cost (RM)'  # New column for total cost
        }, inplace=True)

        # Convert 'Total Revenue' and 'Total Cost' to float first, then format as currency
        sales_and_cost_data['Total Revenue (RM)'] = sales_and_cost_data['Total Revenue (RM)'].apply(lambda x: float(x))
        sales_and_cost_data['Total Revenue (RM)'] = sales_and_cost_data['Total Revenue (RM)'].apply(lambda x: f"RM {x:,.2f}")
        
        sales_and_cost_data['Total Cost (RM)'] = sales_and_cost_data['Total Cost (RM)'].apply(lambda x: float(x))
        sales_and_cost_data['Total Cost (RM)'] = sales_and_cost_data['Total Cost (RM)'].apply(lambda x: f"RM {x:,.2f}")
        
        # Calculate Profit and Profit Margin
        sales_and_cost_data['Profit (RM)'] = sales_and_cost_data['Total Revenue (RM)'].apply(lambda x: float(x.replace('RM ', '').replace(',', ''))) - sales_and_cost_data['Total Cost (RM)'].apply(lambda x: float(x.replace('RM ', '').replace(',', '')))
        sales_and_cost_data['Profit Margin (%)'] = (sales_and_cost_data['Profit (RM)'] / sales_and_cost_data['Total Revenue (RM)'].apply(lambda x: float(x.replace('RM ', '').replace(',', '')))) * 100

        # Display results
        total_profit = sales_and_cost_data['Profit (RM)'].sum()
        st.header(f"💰 Total Profit: RM {total_profit:,.2f}")
        
        st.divider()
        st.subheader("📊 Coffee Sales and Profit Breakdown")
        st.dataframe(sales_and_cost_data)
        st.divider()

        # Generate color map
        color_map = generate_color_map(sales_and_cost_data['Product Name'])

        # Create two columns for best and worst sellers
        col1, col2 = st.columns(2)

        with col1:
            if best_seller is not None:
                st.subheader("🌟 Best Seller")
                st.markdown(f"**Product:** {best_seller['product_name']}", unsafe_allow_html=True)
                st.markdown(f"**Total Quantity Sold:** {best_seller['total_quantity']}", unsafe_allow_html=True)

        with col2:
            if not worst_sellers.empty:
                st.subheader("📉 Worst Seller")
                worst_seller = worst_sellers.iloc[0]
                st.markdown(f"**Product:** {worst_seller['product_name']}", unsafe_allow_html=True)
                st.markdown(f"**Total Quantity Sold:** {worst_seller['total_quantity']}", unsafe_allow_html=True)

        # Sales Charts Section
        st.divider()
        st.subheader("📈 Sales Visualizations")

        # Bar Chart for Revenue Breakdown
        fig, ax = plt.subplots()
        for idx, row in sales_and_cost_data.iterrows():
            ax.bar(row['Product Name'], float(row['Total Revenue (RM)'].replace('RM ', '').replace(',', '')), color=color_map[row['Product Name']])

        ax.set_xlabel('Product Name', fontsize=12)
        ax.set_ylabel('Total Revenue (RM)', fontsize=12)
        ax.set_title('Revenue Breakdown by Product', fontsize=14)
        plt.xticks(rotation=45, ha="right")
        st.pyplot(fig)

        # Pie Chart for Sales Distribution
        sales_and_cost_data['Total Revenue (RM) Numeric'] = sales_and_cost_data['Total Revenue (RM)'].apply(
            lambda x: float(x.replace('RM ', '').replace(',', '')) if isinstance(x, str) else x)

        fig_pie = px.pie(sales_and_cost_data, names='Product Name', values='Total Revenue (RM) Numeric', 
                        title='Sales Distribution by Product', color='Product Name', color_discrete_map=color_map)
        
        fig_pie.update_layout(
        title_font_size=30
        )

        st.plotly_chart(fig_pie)

        # Sales and Profit Charts Section
        st.divider()
        st.subheader("📈 Sales and Revenue Visualizations")

        # Bar Chart for Revenue vs Cost (Side-by-Side)
        fig, ax = plt.subplots(figsize=(10, 6))

        bar_width = 0.35  # Width of the bars
        index = range(len(sales_and_cost_data))  # X-axis positions for each product

        ax.bar([i - bar_width/2 for i in index], sales_and_cost_data['Total Revenue (RM)'], width=bar_width, color='green', label='Revenue')
        ax.bar([i + bar_width/2 for i in index], sales_and_cost_data['Total Cost (RM)'], width=bar_width, color='red', label='Cost')

        ax.set_xlabel('Product Name', fontsize=12)
        ax.set_ylabel('Amount (RM)', fontsize=12)
        ax.set_title('Revenue vs Cost by Product', fontsize=14)
        ax.set_xticks(index)
        ax.set_xticklabels(sales_and_cost_data['Product Name'], rotation=45, ha="right")
        ax.legend()

        plt.tight_layout()
        st.pyplot(fig)

        # Bar chart for Profit Margin
        fig_profit_margin = plt.figure(figsize=(10, 6))
        ax_profit_margin = fig_profit_margin.add_subplot(111)
        ax_profit_margin.bar(sales_and_cost_data['Product Name'], sales_and_cost_data['Profit Margin (%)'], color='blue')

        ax_profit_margin.set_xlabel('Product Name', fontsize=12)
        ax_profit_margin.set_ylabel('Profit Margin (%)', fontsize=12)
        ax_profit_margin.set_title('Profit Margin by Product', fontsize=14)
        plt.xticks(rotation=45, ha="right")
        st.pyplot(fig_profit_margin)

    else:
        st.warning("⚠️ No sales data available for the selected period.")
