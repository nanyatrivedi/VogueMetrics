import streamlit as st
import pandas as pd
import plotly.express as px
from sklearn.linear_model import LinearRegression
import sqlite3

# ---------------- DATABASE CONNECTION ---------------- #

conn = sqlite3.connect(
    'voguemetrics.db'
)

# ---------------- CATEGORY TRANSLATIONS ---------------- #

category_translation = {
    'beleza_saude': 'Beauty & Health',
    'esporte_lazer': 'Sports & Leisure',
    'moveis_decoracao': 'Furniture & Decor',
    'cama_mesa_banho': 'Bed Table Bath',
    'informatica_acessorios': 'IT Accessories',
    'utilidades_domesticas': 'Home Utilities',
    'relogios_presentes': 'Watches & Gifts',
    'telefonia_fixa': 'Telephony',
    'ferramentas_jardim': 'Garden Tools',
    'moveis_escritorio': 'Office Furniture'
}

# ---------------- PAGE CONFIG ---------------- #

st.set_page_config(
    page_title="VogueMetrics",
    layout="wide"
)

# ---------------- CUSTOM CSS ---------------- #

st.markdown("""
<style>

/* MAIN BACKGROUND */

.main {
    background-color: #050816;
    color: white;
}

/* REMOVE STREAMLIT HEADER SPACE */

.block-container {
    padding-top: 2rem;
    padding-bottom: 2rem;
    padding-left: 2rem;
    padding-right: 2rem;
}

/* KPI CARDS */

[data-testid="stMetric"] {
    background: rgba(255, 255, 255, 0.05);
    border: 1px solid rgba(255,255,255,0.1);
    padding: 20px;
    border-radius: 20px;
    backdrop-filter: blur(10px);
    text-align: center;
    box-shadow: 0px 4px 20px rgba(0,0,0,0.3);
    transition: 0.3s ease;
}
            
 [data-testid="stMetric"]:hover {
    transform: translateY(-5px);
    border: 1px solid #4DA6FF;
}           

/* HEADINGS */

h1 {
    font-size: 3rem !important;
    font-weight: 700 !important;
}

h2 {
    margin-top: 2rem;
    margin-bottom: 1rem;
}

/* SIDEBAR */

section[data-testid="stSidebar"] {
    background-color: #111827;
}

/* CHART CONTAINERS */

.stPlotlyChart {
    background: rgba(255,255,255,0.03);
    padding: 20px;
    border-radius: 20px;
}

</style>
""", unsafe_allow_html=True)

# ---------------- TITLE ---------------- #

st.title("VogueMetrics")
st.subheader("AI-Powered E-Commerce Analytics Platform")
st.caption(
    "Real-time business intelligence dashboard for sales, customer, and revenue analytics."
)
# ---------------- LOAD DATA ---------------- #

@st.cache_data
def load_data():

    orders = pd.read_csv("data/olist_orders_dataset.csv")
    order_items = pd.read_csv("data/olist_order_items_dataset.csv")
    payments = pd.read_csv("data/olist_order_payments_dataset.csv")
    customers = pd.read_csv("data/olist_customers_dataset.csv")
    products = pd.read_csv("data/olist_products_dataset.csv")

    return orders, order_items, payments, customers, products

orders, order_items, payments, customers, products = load_data()

# ---------------- STORE DATA IN SQL ---------------- #

orders.to_sql(
    'orders',
    conn,
    if_exists='replace',
    index=False
)

customers.to_sql(
    'customers',
    conn,
    if_exists='replace',
    index=False
)

payments.to_sql(
    'payments',
    conn,
    if_exists='replace',
    index=False
)

# ---------------- DATA CLEANING ---------------- #

orders['order_purchase_timestamp'] = pd.to_datetime(
    orders['order_purchase_timestamp']
)

orders['year'] = orders[
    'order_purchase_timestamp'
].dt.year

# ---------------- SIDEBAR FILTERS ---------------- #

st.sidebar.markdown("""
# VogueMetrics

### AI Analytics Suite
""")

st.sidebar.divider()

customer_states = customers['customer_state'].unique()

selected_state = st.sidebar.selectbox(
    "Select State",
    ['All'] + list(customer_states)
)

# YEAR FILTER

years = sorted(
    orders['year'].unique()
)

selected_year = st.sidebar.selectbox(
    "Select Year",
    ['All'] + list(years)
)

# ---------------- DATA MERGING ---------------- #

merged_df = orders.merge(
    customers,
    on='customer_id'
)

merged_df = merged_df.merge(
    payments,
    on='order_id'
)

merged_df = merged_df.merge(
    order_items,
    on='order_id'
)

merged_df = merged_df.merge(
    products,
    on='product_id'
)

# ---------------- APPLY FILTERS ---------------- #

if selected_state != 'All':
    merged_df = merged_df[
        merged_df['customer_state'] == selected_state
    ]

if selected_year != 'All':
    merged_df = merged_df[
        merged_df['year'] == selected_year
    ]

# ---------------- KPI CALCULATIONS ---------------- #

total_orders = merged_df['order_id'].nunique()

total_customers = merged_df['customer_unique_id'].nunique()

total_revenue = merged_df['payment_value'].sum()

avg_order_value = total_revenue / total_orders

# ---------------- DASHBOARD TABS ---------------- #

tab1, tab2, tab3, tab4 = st.tabs([
    "Executive Overview",
    "Customer Analytics",
    "Product Analytics",
    "Forecasting & AI"
])

# ---------------- KPI SECTION ---------------- #
with tab1:
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            label="Total Revenue",
            value=f"R$ {total_revenue:,.0f}"
        )

    with col2:
        st.metric(
            label="Total Orders",
            value=f"{total_orders:,}"
        )

    with col3:
        st.metric(
            label="Total Customers",
            value=f"{total_customers:,}"
        )

    with col4:
        st.metric(
            label="Avg Order Value",
            value=f"R$ {avg_order_value:,.0f}"
        )

    # ---------------- SALES TREND ---------------- #

    st.markdown("## Monthly Sales Trend")

    sales_trend = orders.merge(
        payments,
        on='order_id'
    )

    sales_trend = merged_df.copy()

    sales_trend['month'] = sales_trend[
        'order_purchase_timestamp'
    ].dt.to_period('M').astype(str)

    monthly_sales = sales_trend.groupby(
        'month'
    )['payment_value'].sum().reset_index()

    # REMOVE INCOMPLETE FINAL MONTHS

    monthly_sales = monthly_sales.iloc[:-2]

    fig = px.line(
        monthly_sales,
        x='month',
        y='payment_value',
        markers=True,
        title='Monthly Revenue Trend'
    )

    fig.update_layout(
        template='plotly_dark',
        font=dict(size=14),
        xaxis_title='Month',
        yaxis_title='Revenue'
    )
    fig.update_layout(height=450)
    st.plotly_chart(fig, use_container_width=True)
    st.divider()
    # ---------------- CATEGORY ANALYTICS ---------------- #

    st.markdown("## Top Product Categories")

    category_sales = merged_df.groupby(
        'product_category_name'
    )['payment_value'].sum().reset_index()

    category_sales['product_category_name'] = (
        category_sales['product_category_name']
        .map(category_translation)
        .fillna(category_sales['product_category_name'])
    )

    category_sales = category_sales.sort_values(
        by='payment_value',
        ascending=False
    ).head(10)

    fig2 = px.bar(
        category_sales,
        x='payment_value',
        y='product_category_name',
        orientation='h',
        title='Top 10 Product Categories'
    )

    fig2.update_layout(
        template='plotly_dark',
        font=dict(size=14),
        xaxis_title='Revenue',
        yaxis_title='Category'
    )
    fig.update_layout(height=450)
    st.plotly_chart(fig2, use_container_width=True)
    st.divider()
    # ---------------- STATE REVENUE ANALYTICS ---------------- #

    st.markdown("## Revenue by State")

    state_revenue = merged_df.groupby(
        'customer_state'
    )['payment_value'].sum().reset_index()

    state_revenue = state_revenue.sort_values(
        by='payment_value',
        ascending=False
    )

    fig3 = px.bar(
        state_revenue.head(10),
        x='customer_state',
        y='payment_value',
        title='Top 10 States by Revenue',
        text_auto='.2s'
    )

    fig3.update_layout(
        template='plotly_dark',
        font=dict(size=14),
        xaxis_title='State',
        yaxis_title='Revenue'
    )
    fig.update_layout(height=450)
    st.plotly_chart(fig3, use_container_width=True)
    st.divider()
# ---------------- CUSTOMER SEGMENTATION ---------------- #

with tab2:
    st.markdown("## Customer Segmentation")

    customer_spending = merged_df.groupby(
        'customer_unique_id'
    )['payment_value'].sum().reset_index()

    # SEGMENT CUSTOMERS

    def segment_customer(amount):

        if amount > 1000:
            return 'High Value'

        elif amount > 500:
            return 'Medium Value'

        else:
            return 'Low Value'

    customer_spending['segment'] = customer_spending[
        'payment_value'
    ].apply(segment_customer)

    segment_counts = customer_spending[
        'segment'
    ].value_counts().reset_index()

    segment_counts.columns = ['segment', 'count']

    fig4 = px.pie(
        segment_counts,
        names='segment',
        values='count',
        title='Customer Segments'
    )

    fig4.update_layout(
        template='plotly_dark',
        font=dict(size=14)
    )
    fig.update_layout(height=450)
    st.plotly_chart(fig4, use_container_width=True)
    st.divider()
# ---------------- AI BUSINESS INSIGHTS ---------------- #

with tab4:
    st.markdown("## AI Business Insights")

    # TOP STATE

    top_state = state_revenue.iloc[0]['customer_state']
    top_state_revenue = state_revenue.iloc[0]['payment_value']

    # TOP CATEGORY

    top_category = category_sales.iloc[0]['product_category_name']
    top_category_revenue = category_sales.iloc[0]['payment_value']

    # HIGH VALUE CUSTOMERS

    high_value_count = segment_counts[
        segment_counts['segment'] == 'High Value'
    ]['count'].values[0]

    total_customer_count = segment_counts['count'].sum()

    high_value_percentage = (
        high_value_count / total_customer_count
    ) * 100

    # INSIGHT CARDS

    insight1 = f"""
    Top performing state is **{top_state}**
    with revenue exceeding R$ {top_state_revenue:,.0f}.
    """

    insight2 = f"""
    Highest revenue category is **{top_category}**
    generating over R$ {top_category_revenue:,.0f}.
    """

    insight3 = f"""
    High value customers represent
    approximately **{high_value_percentage:.1f}%**
    of the customer base.
    """

    # DISPLAY INSIGHTS

    st.info(insight1)

    st.success(insight2)

    st.warning(insight3)

    # ---------------- SALES FORECASTING ---------------- #

    st.markdown("## Revenue Forecasting")

    # PREPARE MONTHLY SALES DATA

    forecast_df = monthly_sales.copy()

    forecast_df = forecast_df.reset_index(drop=True)

    forecast_df['month_number'] = range(len(forecast_df))

    # FEATURES & TARGET

    X = forecast_df[['month_number']]
    y = forecast_df['payment_value']

    # TRAIN MODEL

    # ---------------- SIMPLE TREND FORECAST ---------------- #

    recent_average = monthly_sales[
        'payment_value'
    ].tail(3).mean()

    future_predictions = []

    current_value = recent_average

    for i in range(6):

        current_value *= 1.02

        future_predictions.append(current_value)

    # CREATE FUTURE LABELS

    # CREATE FUTURE DATES

    last_date = pd.to_datetime(
        monthly_sales['month'].iloc[-1]
    )

    future_dates = pd.date_range(
        start=last_date,
        periods=7,
        freq='M'
    )[1:]

    future_labels = future_dates.strftime('%Y-%m')

    forecast_results = pd.DataFrame({
        'month': future_labels,
        'predicted_revenue': future_predictions
    })

    # COMBINE HISTORICAL + FORECAST

    historical_chart = monthly_sales.copy()

    historical_chart.columns = ['month', 'revenue']

    historical_chart['type'] = 'Historical'

    # ---------------- FORECAST CHART ---------------- #

    forecast_chart = forecast_results.copy()

    forecast_chart.columns = ['month', 'revenue']

    # CONNECT FORECAST TO LAST HISTORICAL POINT

    last_historical = historical_chart.iloc[-1:]

    forecast_chart = pd.concat([
        last_historical,
        forecast_chart
    ])

    forecast_chart['type'] = 'Forecast'

    combined_chart = pd.concat([
        historical_chart,
        forecast_chart
    ])

    # PLOT

    fig5 = px.line(
        combined_chart,
        x='month',
        y='revenue',
        color='type',
        markers=True,
        title='Revenue Forecast',
        line_dash='type'
    )

    fig5.update_layout(
        template='plotly_dark',
        font=dict(size=14),
        xaxis_title='Month',
        yaxis_title='Revenue'
    )

    fig5.update_xaxes(type='category')

    fig5.update_traces(
        mode='lines+markers',
        line=dict(width=4)
    )

    fig.update_layout(height=450)
    st.plotly_chart(fig5, use_container_width=True)

    st.divider()

# ---------------- TOP PRODUCTS ANALYTICS ---------------- #

with tab3:
    st.markdown("## Top Performing Products")

    top_products = merged_df.groupby(
        'product_id'
    ).agg({
        'payment_value': 'sum',
        'order_id': 'count'
    }).reset_index()

    top_products.columns = [
        'Product ID',
        'Revenue',
        'Total Orders'
    ]

    top_products = top_products.sort_values(
        by='Revenue',
        ascending=False
    ).head(15)

    top_products['Revenue'] = (
        top_products['Revenue']
        .round(2)
    )

    st.dataframe(
        top_products,
        use_container_width=True,
        hide_index=True
    )

    st.divider()

    # ---------------- SQL ANALYTICS ---------------- #

    st.markdown("## SQL-Based Revenue Analysis")

    query = """
    SELECT
        customer_state,
        ROUND(SUM(payment_value), 2) AS total_revenue
    FROM merged_df
    GROUP BY customer_state
    ORDER BY total_revenue DESC
    LIMIT 10;
    """

    try:

        merged_df.to_sql(
            'merged_df',
            conn,
            if_exists='replace',
            index=False
        )

        sql_results = pd.read_sql_query(
            query,
            conn
        )

        st.dataframe(
            sql_results,
            use_container_width=True,
            hide_index=True
        )

    except Exception as e:

        st.error(f"SQL Error: {e}")

st.divider()

st.caption(
    "VogueMetrics • AI-Powered E-Commerce Analytics Platform • Built with Python, SQL, Streamlit & Plotly"
)