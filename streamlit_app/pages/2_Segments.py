import streamlit as st
import plotly.express as px
import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from utils.db import query

st.set_page_config(page_title="Customer Segments", layout="wide")
st.title("Phân khúc khách hàng")

# --- Global Slicers (Power BI style) ---
with st.sidebar:
    # 1. Lọc Brand (Đồng bộ với Overview)
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

    # Nút Xóa bộ lọc tổng hợp
    if st.button("Xóa bộ lọc", use_container_width=True):
        st.session_state.ov_brand = "Tất cả"
        st.session_state.ov_cat = "Tất cả"
        st.session_state.seg_cluster = "Tất cả"
        st.session_state.seg_rfm = "Tất cả"
        st.rerun()

# --- Logic Lọc Chéo (Cross-filtering) ---
cross_conditions = []
if selected_brand != "Tất cả":
    cross_conditions.append(f"brand = '{selected_brand.replace(chr(39), chr(39)+chr(39))}'")
if selected_cat != "Tất cả":
    cross_conditions.append(f"category_level1 = '{selected_cat.replace(chr(39), chr(39)+chr(39))}'")

cte_clause = ""
join_clause = ""
if cross_conditions:
    where_cross = "WHERE " + " AND ".join(cross_conditions)
    cte_clause = f"WITH filtered_users AS (SELECT DISTINCT user_id FROM main_silver.silver_events_cleaned {where_cross}) "
    join_clause = "JOIN filtered_users u ON c.user_id = u.user_id"

# Xây dựng mệnh đề WHERE động cho Cluster/RFM
where_conditions = []
if selected_cluster != "Tất cả":
    where_conditions.append(f"c.cluster_label = '{selected_cluster.replace(chr(39), chr(39)+chr(39))}'")
if selected_rfm != "Tất cả":
    where_conditions.append(f"c.rfm_segment = '{selected_rfm.replace(chr(39), chr(39)+chr(39))}'")

where_clause_c = ""
if where_conditions:
    where_clause_c = "WHERE " + " AND ".join(where_conditions)

st.divider()

# Biến caption dùng chung
filter_caption = f"Brand = **{selected_brand}** | Category = **{selected_cat}** | Nhóm = **{selected_cluster}** | RFM = **{selected_rfm}**"

# --- Phân bố cụm ---
col1, col2 = st.columns(2)

with col1:
    st.subheader("Phân bố theo cụm K-Means")
    st.caption(filter_caption)
    cluster_dist = query(f"""
        {cte_clause}
        SELECT c.cluster_label, COUNT(*) AS cnt
        FROM main_gold.cluster_predictions c
        {join_clause}
        {where_clause_c}
        GROUP BY c.cluster_label
        ORDER BY cnt DESC
    """)
    if not cluster_dist.empty:
        fig1 = px.pie(cluster_dist, names='cluster_label', values='cnt',
                      color_discrete_sequence=px.colors.qualitative.Set2)
        st.plotly_chart(fig1, use_container_width=True)
    else:
        st.warning("Không có dữ liệu cho bộ lọc này.")

with col2:
    st.subheader("Phân bố theo RFM Segment")
    st.caption(filter_caption)
    rfm_dist = query(f"""
        {cte_clause}
        SELECT c.rfm_segment, COUNT(*) AS cnt
        FROM main_gold.cluster_predictions c
        {join_clause}
        {where_clause_c}
        GROUP BY c.rfm_segment
        ORDER BY cnt DESC
    """)
    if not rfm_dist.empty:
        fig2 = px.bar(rfm_dist, x='rfm_segment', y='cnt',
                      labels={'rfm_segment': 'Phân khúc', 'cnt': 'Số khách'},
                      color_discrete_sequence=['#534AB7'])
        st.plotly_chart(fig2, use_container_width=True)
    else:
        st.warning("Không có dữ liệu cho bộ lọc này.")

# --- Scatter RFM ---
st.subheader("RFM Scatter — Recency vs Monetary")
st.caption(filter_caption)
scatter_data = query(f"""
    {cte_clause}
    SELECT
        f.user_id,
        f.recency_days,
        f.monetary,
        f.frequency,
        c.cluster_label
    FROM main_gold.gold_customer_features f
    JOIN main_gold.cluster_predictions c ON f.user_id = c.user_id
    {join_clause}
    {where_clause_c}
    USING SAMPLE 5000
""")
if not scatter_data.empty:
    fig3 = px.scatter(
        scatter_data,
        x='recency_days', y='monetary',
        color='cluster_label',
        size='frequency',
        hover_data=['user_id'],
        labels={'recency_days': 'Recency (ngày)', 'monetary': 'Monetary (USD)'},
        title='Phân bố khách hàng theo RFM'
    )
    st.plotly_chart(fig3, use_container_width=True)
else:
    st.warning("Không có dữ liệu để vẽ biểu đồ phân tán.")

# --- Bảng thống kê ---
st.subheader("Thống kê trung bình từng cụm")
st.caption(filter_caption)
stats = query(f"""
    {cte_clause}
    SELECT
        c.cluster_label,
        COUNT(*)                        AS so_khach,
        ROUND(AVG(f.recency_days), 1)   AS avg_recency,
        ROUND(AVG(f.frequency), 1)      AS avg_frequency,
        ROUND(AVG(f.monetary), 0)       AS avg_monetary,
        ROUND(AVG(f.avg_order_value),0) AS avg_order_value
    FROM main_gold.gold_customer_features f
    JOIN main_gold.cluster_predictions c ON f.user_id = c.user_id
    {join_clause}
    {where_clause_c}
    GROUP BY c.cluster_label
    ORDER BY avg_monetary DESC
""")
if not stats.empty:
    # Đổi tên cột cho dễ đọc
    stats = stats.rename(columns={
        'cluster_label': 'Nhóm khách hàng',
        'so_khach': 'Số lượng khách',
        'avg_recency': 'Recency TB (ngày)',
        'avg_frequency': 'Frequency TB (đơn)',
        'avg_monetary': 'Monetary TB (USD)',
        'avg_order_value': 'Giá trị đơn TB (USD)'
    })
    st.dataframe(stats, use_container_width=True)
else:
    st.warning("Không có dữ liệu cho bảng thống kê.")
