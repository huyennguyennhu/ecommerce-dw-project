import streamlit as st
import plotly.express as px
import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from utils.db import query

st.set_page_config(page_title="Customer Segments", layout="wide")
st.title("Phân khúc khách hàng")

# --- Global Slicers (Power BI style) ---
st.markdown("### Bộ lọc dữ liệu (Slicers)")
with st.expander("Tùy chỉnh bộ lọc", expanded=True):
    col_filter1, col_filter2 = st.columns(2)
    
    with col_filter1:
        cluster_list = query("SELECT DISTINCT cluster_label FROM main_gold.cluster_predictions")['cluster_label'].tolist()
        selected_cluster = st.selectbox("Nhóm khách hàng (Cluster):", ["Tất cả"] + cluster_list)

    with col_filter2:
        rfm_list = query("SELECT DISTINCT rfm_segment FROM main_gold.cluster_predictions")['rfm_segment'].tolist()
        selected_rfm = st.selectbox("Phân khúc RFM:", ["Tất cả"] + rfm_list)

# Xây dựng mệnh đề WHERE động
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
filter_caption = f"Nhóm = **{selected_cluster}** | RFM = **{selected_rfm}**"

# --- Phân bố cụm ---
col1, col2 = st.columns(2)

with col1:
    st.subheader("Phân bố theo cụm K-Means")
    st.caption(filter_caption)
    cluster_dist = query(f"""
        SELECT c.cluster_label, COUNT(*) AS cnt
        FROM main_gold.cluster_predictions c
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
        SELECT c.rfm_segment, COUNT(*) AS cnt
        FROM main_gold.cluster_predictions c
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
    SELECT
        f.user_id,
        f.recency_days,
        f.monetary,
        f.frequency,
        c.cluster_label
    FROM main_gold.gold_customer_features f
    JOIN main_gold.cluster_predictions c ON f.user_id = c.user_id
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
    SELECT
        c.cluster_label,
        COUNT(*)                        AS so_khach,
        ROUND(AVG(f.recency_days), 1)   AS avg_recency,
        ROUND(AVG(f.frequency), 1)      AS avg_frequency,
        ROUND(AVG(f.monetary), 0)       AS avg_monetary,
        ROUND(AVG(f.avg_order_value),0) AS avg_order_value
    FROM main_gold.gold_customer_features f
    JOIN main_gold.cluster_predictions c ON f.user_id = c.user_id
    {where_clause_c}
    GROUP BY c.cluster_label
    ORDER BY avg_monetary DESC
""")
if not stats.empty:
    st.dataframe(stats, use_container_width=True)
else:
    st.warning("Không có dữ liệu cho bảng thống kê.")
