import streamlit as st
import plotly.express as px
import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from utils.db import query

st.set_page_config(page_title="Customer Segments", layout="wide")
st.title("Phân khúc khách hàng")

# --- Phân bố cụm ---
col1, col2 = st.columns(2)

with col1:
    st.subheader("Phân bố theo cụm K-Means")
    cluster_dist = query("""
        SELECT cluster_label, COUNT(*) AS cnt
        FROM main_gold.cluster_predictions
        GROUP BY cluster_label
        ORDER BY cnt DESC
    """)
    fig1 = px.pie(cluster_dist, names='cluster_label', values='cnt',
                  color_discrete_sequence=px.colors.qualitative.Set2)
    st.plotly_chart(fig1, use_container_width=True)

with col2:
    st.subheader("Phân bố theo RFM Segment")
    rfm_dist = query("""
        SELECT rfm_segment, COUNT(*) AS cnt
        FROM main_gold.cluster_predictions
        GROUP BY rfm_segment
        ORDER BY cnt DESC
    """)
    fig2 = px.bar(rfm_dist, x='rfm_segment', y='cnt',
                  labels={'rfm_segment': 'Phân khúc', 'cnt': 'Số khách'},
                  color_discrete_sequence=['#534AB7'])
    st.plotly_chart(fig2, use_container_width=True)

# --- Scatter RFM ---
st.subheader("RFM Scatter — Recency vs Monetary")
scatter_data = query("""
    SELECT
        f.user_id,
        f.recency_days,
        f.monetary,
        f.frequency,
        c.cluster_label
    FROM main_gold.gold_customer_features f
    JOIN main_gold.cluster_predictions c ON f.user_id = c.user_id
    USING SAMPLE 5000
""")
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

# --- Bảng thống kê ---
st.subheader("Thống kê trung bình từng cụm")
stats = query("""
    SELECT
        c.cluster_label,
        COUNT(*)                        AS so_khach,
        ROUND(AVG(f.recency_days), 1)   AS avg_recency,
        ROUND(AVG(f.frequency), 1)      AS avg_frequency,
        ROUND(AVG(f.monetary), 0)       AS avg_monetary,
        ROUND(AVG(f.avg_order_value),0) AS avg_order_value
    FROM main_gold.gold_customer_features f
    JOIN main_gold.cluster_predictions c ON f.user_id = c.user_id
    GROUP BY c.cluster_label
    ORDER BY avg_monetary DESC
""")
st.dataframe(stats, use_container_width=True)
