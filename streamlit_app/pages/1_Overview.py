import streamlit as st
import plotly.express as px
import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from utils.db import query

st.set_page_config(page_title="Overview", layout="wide")
st.title("Tổng quan kinh doanh")

def clear_filters():
    st.session_state.ov_brand = "Tất cả"
    st.session_state.ov_cat = "Tất cả"
    st.session_state.seg_cluster = "Tất cả"
    st.session_state.seg_rfm = "Tất cả"

# --- Global Slicers (Power BI style) ---
with st.sidebar:
    # 1. Lọc Brand
    brand_list = query("""
        SELECT brand, COUNT(*) as cnt 
        FROM main_silver.silver_events_cleaned 
        WHERE brand != 'Unknown' 
        GROUP BY brand ORDER BY cnt DESC LIMIT 100
    """)['brand'].tolist()
    selected_brand = st.selectbox("Thương hiệu (Brand):", ["Tất cả"] + brand_list, key="ov_brand")

    # 2. Lọc Category (Động: Tùy thuộc vào Brand đã chọn)
    cat_where_sidebar = f"AND brand = '{selected_brand.replace(chr(39), chr(39)+chr(39))}'" if selected_brand != "Tất cả" else ""
    cat_list = query(f"""
        SELECT category_level1, COUNT(*) as cnt 
        FROM main_silver.silver_events_cleaned 
        WHERE category_level1 != 'Unknown' {cat_where_sidebar}
        GROUP BY category_level1 ORDER BY cnt DESC LIMIT 50
    """)['category_level1'].tolist()
    selected_cat = st.selectbox("Danh mục (Category):", ["Tất cả"] + cat_list, key="ov_cat")

    # 3. Lọc Cluster
    cluster_list = query("SELECT DISTINCT cluster_label FROM main_gold.cluster_predictions")['cluster_label'].tolist()
    selected_cluster = st.selectbox("Nhóm khách hàng (Cluster):", ["Tất cả"] + cluster_list, key="seg_cluster")

    # 4. Lọc RFM
    rfm_list = query("SELECT DISTINCT rfm_segment FROM main_gold.cluster_predictions")['rfm_segment'].tolist()
    selected_rfm = st.selectbox("Phân khúc RFM:", ["Tất cả"] + rfm_list, key="seg_rfm")

    st.button("Xóa bộ lọc", on_click=clear_filters, use_container_width=True)

# --- Logic Lọc Chéo (Cross-filtering) từ Cluster/RFM sang Events ---
cross_conditions = []
if selected_cluster != "Tất cả":
    cross_conditions.append(f"cluster_label = '{selected_cluster.replace(chr(39), chr(39)+chr(39))}'")
if selected_rfm != "Tất cả":
    cross_conditions.append(f"rfm_segment = '{selected_rfm.replace(chr(39), chr(39)+chr(39))}'")

cte_clause = ""
join_clause = ""
if cross_conditions:
    where_cross = "WHERE " + " AND ".join(cross_conditions)
    cte_clause = f"WITH filtered_clusters AS (SELECT user_id FROM main_gold.cluster_predictions {where_cross}) "
    join_clause = "JOIN filtered_clusters fc ON e.user_id = fc.user_id"

# Xây dựng mệnh đề WHERE động cho Brand/Category
where_conditions = []
if selected_brand != "Tất cả":
    where_conditions.append(f"e.brand = '{selected_brand.replace(chr(39), chr(39)+chr(39))}'")
if selected_cat != "Tất cả":
    where_conditions.append(f"e.category_level1 = '{selected_cat.replace(chr(39), chr(39)+chr(39))}'")

where_clause = ""
if where_conditions:
    where_clause = "WHERE " + " AND ".join(where_conditions)

st.divider()

# Biến caption dùng chung cho tất cả biểu đồ
filter_caption = f"Brand = **{selected_brand}** | Category = **{selected_cat}** | Nhóm = **{selected_cluster}** | RFM = **{selected_rfm}**"

# --- Doanh thu theo ngày ---
st.subheader("Doanh thu theo ngày")
st.caption(filter_caption)
daily = query(f"""
    {cte_clause}
    SELECT
        e.event_date,
        SUM(CASE WHEN e.is_purchase=1 THEN e.price ELSE 0 END) AS revenue,
        SUM(e.is_purchase) AS orders
    FROM main_silver.silver_events_cleaned e
    {join_clause}
    {where_clause}
    GROUP BY e.event_date
    ORDER BY e.event_date
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
        {cte_clause}
        SELECT e.event_type, COUNT(*) AS cnt
        FROM main_silver.silver_events_cleaned e
        {join_clause}
        {where_clause}
        GROUP BY e.event_type
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
    top_brand_where = where_clause + (" AND e.brand != 'Unknown'" if where_clause else "WHERE e.brand != 'Unknown'")
    top_brand = query(f"""
        {cte_clause}
        SELECT e.brand,
               ROUND(SUM(CASE WHEN e.is_purchase=1 THEN e.price ELSE 0 END), 0) AS revenue
        FROM main_silver.silver_events_cleaned e
        {join_clause}
        {top_brand_where}
        GROUP BY e.brand
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
top_cat_where = where_clause + (" AND e.category_level1 != 'Unknown'" if where_clause else "WHERE e.category_level1 != 'Unknown'")
top_cat = query(f"""
    {cte_clause}
    SELECT e.category_level1,
           SUM(e.is_purchase) AS purchases
    FROM main_silver.silver_events_cleaned e
    {join_clause}
    {top_cat_where}
    GROUP BY e.category_level1
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
