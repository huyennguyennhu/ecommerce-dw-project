import streamlit as st
import plotly.express as px
import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from utils.db import query

st.set_page_config(page_title="Overview", layout="wide")
st.title("Tổng quan kinh doanh")

# --- Doanh thu theo ngày ---
st.subheader("Doanh thu theo ngày")
daily = query("""
    SELECT
        event_date,
        SUM(CASE WHEN is_purchase=1 THEN price ELSE 0 END) AS revenue,
        SUM(is_purchase) AS orders
    FROM main_silver.silver_events_cleaned
    GROUP BY event_date
    ORDER BY event_date
""")
fig = px.line(daily, x='event_date', y='revenue',
              title='Doanh thu hàng ngày (USD)',
              labels={'event_date': 'Ngày', 'revenue': 'Doanh thu (USD)'})
fig.update_traces(line_color='#7F77DD')
st.plotly_chart(fig, use_container_width=True)

col1, col2 = st.columns(2)

# --- Phễu chuyển đổi ---
with col1:
    st.subheader("Phễu chuyển đổi")
    funnel_data = query("""
        SELECT event_type, COUNT(*) AS cnt
        FROM main_silver.silver_events_cleaned
        GROUP BY event_type
        ORDER BY cnt DESC
    """)
    fig2 = px.funnel(funnel_data, x='cnt', y='event_type',
                     color_discrete_sequence=['#7F77DD'])
    st.plotly_chart(fig2, use_container_width=True)

# --- Top 10 brand ---
with col2:
    st.subheader("Top 10 brand doanh thu cao nhất")
    top_brand = query("""
        SELECT brand,
               ROUND(SUM(CASE WHEN is_purchase=1 THEN price ELSE 0 END), 0) AS revenue
        FROM main_silver.silver_events_cleaned
        WHERE brand != 'Unknown'
        GROUP BY brand
        ORDER BY revenue DESC
        LIMIT 10
    """)
    fig3 = px.bar(top_brand, x='revenue', y='brand', orientation='h',
                  labels={'revenue': 'Doanh thu (USD)', 'brand': 'Brand'},
                  color_discrete_sequence=['#1D9E75'])
    fig3.update_layout(yaxis={'categoryorder': 'total ascending'})
    st.plotly_chart(fig3, use_container_width=True)

# --- Top 10 danh mục ---
st.subheader("Top 10 danh mục theo lượt mua")
top_cat = query("""
    SELECT category_level1,
           SUM(is_purchase) AS purchases
    FROM main_silver.silver_events_cleaned
    WHERE category_level1 != 'Unknown'
    GROUP BY category_level1
    ORDER BY purchases DESC
    LIMIT 10
""")
fig4 = px.bar(top_cat, x='category_level1', y='purchases',
              labels={'category_level1': 'Danh mục', 'purchases': 'Số đơn'},
              color_discrete_sequence=['#D85A30'])
st.plotly_chart(fig4, use_container_width=True)
