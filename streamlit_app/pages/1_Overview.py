import streamlit as st
import plotly.express as px
import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from utils.db import query

st.set_page_config(page_title="Overview", layout="wide")
st.title("Tổng quan kinh doanh")

# --- Global Slicers (Power BI style) ---
st.markdown("### Bộ lọc dữ liệu (Slicers)")
with st.expander("Tùy chỉnh bộ lọc", expanded=True):
    col_filter1, col_filter2 = st.columns(2)
    
    # 1. Lọc Brand
    with col_filter1:
        brand_list = query("""
            SELECT brand, COUNT(*) as cnt 
            FROM main_silver.silver_events_cleaned 
            WHERE brand != 'Unknown' 
            GROUP BY brand ORDER BY cnt DESC LIMIT 100
        """)['brand'].tolist()
        selected_brand = st.selectbox("Thương hiệu (Brand):", ["Tất cả"] + brand_list)

    # 2. Lọc Category (Động: Tùy thuộc vào Brand đã chọn)
    with col_filter2:
        cat_where = f"AND brand = '{selected_brand.replace(chr(39), chr(39)+chr(39))}'" if selected_brand != "Tất cả" else ""
        cat_list = query(f"""
            SELECT category_level1, COUNT(*) as cnt 
            FROM main_silver.silver_events_cleaned 
            WHERE category_level1 != 'Unknown' {cat_where}
            GROUP BY category_level1 ORDER BY cnt DESC LIMIT 50
        """)['category_level1'].tolist()
        selected_cat = st.selectbox("Danh mục (Category):", ["Tất cả"] + cat_list)

# Xây dựng mệnh đề WHERE động dựa trên Slicers
where_conditions = []
if selected_brand != "Tất cả":
    where_conditions.append(f"brand = '{selected_brand.replace(chr(39), chr(39)+chr(39))}'")
if selected_cat != "Tất cả":
    where_conditions.append(f"category_level1 = '{selected_cat.replace(chr(39), chr(39)+chr(39))}'")

where_clause = ""
if where_conditions:
    where_clause = "WHERE " + " AND ".join(where_conditions)

st.divider()

# Biến caption dùng chung cho tất cả biểu đồ
filter_caption = f"Brand = **{selected_brand}** | Category = **{selected_cat}**"

# --- Doanh thu theo ngày ---
st.subheader("Doanh thu theo ngày")
st.caption(filter_caption)
daily = query(f"""
    SELECT
        event_date,
        SUM(CASE WHEN is_purchase=1 THEN price ELSE 0 END) AS revenue,
        SUM(is_purchase) AS orders
    FROM main_silver.silver_events_cleaned
    {where_clause}
    GROUP BY event_date
    ORDER BY event_date
""")
if not daily.empty:
    fig = px.line(daily, x='event_date', y='revenue',
                  labels={'event_date': 'Ngày', 'revenue': 'Doanh thu (USD)'})
    fig.update_traces(line_color='#7F77DD')
    st.plotly_chart(fig, use_container_width=True)
else:
    st.warning("Không có dữ liệu khớp với bộ lọc.")

col1, col2 = st.columns(2)

# --- Phễu chuyển đổi ---
with col1:
    st.subheader("Phễu chuyển đổi")
    st.caption(filter_caption)
    funnel_data = query(f"""
        SELECT event_type, COUNT(*) AS cnt
        FROM main_silver.silver_events_cleaned
        {where_clause}
        GROUP BY event_type
        ORDER BY cnt DESC
    """)
    if not funnel_data.empty:
        fig2 = px.funnel(funnel_data, x='cnt', y='event_type',
                         color_discrete_sequence=['#7F77DD'])
        st.plotly_chart(fig2, use_container_width=True)
    else:
        st.warning("Không có dữ liệu khớp với bộ lọc.")

# --- Top 10 brand ---
with col2:
    st.subheader("Top 10 brand doanh thu cao nhất")
    st.caption(filter_caption)
    top_brand_where = where_clause + (" AND brand != 'Unknown'" if where_clause else "WHERE brand != 'Unknown'")
    top_brand = query(f"""
        SELECT brand,
               ROUND(SUM(CASE WHEN is_purchase=1 THEN price ELSE 0 END), 0) AS revenue
        FROM main_silver.silver_events_cleaned
        {top_brand_where}
        GROUP BY brand
        ORDER BY revenue DESC
        LIMIT 10
    """)
    if not top_brand.empty:
        fig3 = px.bar(top_brand, x='revenue', y='brand', orientation='h',
                      labels={'revenue': 'Doanh thu (USD)', 'brand': 'Brand'},
                      color_discrete_sequence=['#1D9E75'])
        fig3.update_layout(yaxis={'categoryorder': 'total ascending'})
        st.plotly_chart(fig3, use_container_width=True)
    else:
        st.warning("Không có dữ liệu khớp với bộ lọc.")

# --- Top 10 danh mục ---
st.subheader("Top 10 danh mục theo lượt mua")
st.caption(filter_caption)
top_cat_where = where_clause + (" AND category_level1 != 'Unknown'" if where_clause else "WHERE category_level1 != 'Unknown'")
top_cat = query(f"""
    SELECT category_level1,
           SUM(is_purchase) AS purchases
    FROM main_silver.silver_events_cleaned
    {top_cat_where}
    GROUP BY category_level1
    ORDER BY purchases DESC
    LIMIT 10
""")
if not top_cat.empty:
    fig4 = px.bar(top_cat, x='category_level1', y='purchases',
                  labels={'category_level1': 'Danh mục', 'purchases': 'Số đơn'},
                  color_discrete_sequence=['#D85A30'])
    st.plotly_chart(fig4, use_container_width=True)
else:
    st.warning("Không có dữ liệu khớp với bộ lọc.")
