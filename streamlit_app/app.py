import streamlit as st

st.set_page_config(
    page_title="eCommerce Analytics",
    layout="wide"
)

def home_page():
    st.title("eCommerce Behavior Analytics")
    st.markdown("""
    Hệ thống phân tích hành vi **67 triệu sự kiện** từ sàn thương mại điện tử (Nov 2019).
    
    Điều hướng qua menu bên trái:
    - **Tổng quan** — Doanh thu, phễu chuyển đổi, top sản phẩm
    - **Phân khúc** — Phân khúc khách hàng RFM + Clustering
    - **Gợi ý sản phẩm** — Gợi ý sản phẩm cá nhân hóa
    - **Trợ lý AI** — Hỏi đáp kinh doanh bằng AI
    """)
    
    st.divider()
    
    # KPI nhanh
    from utils.db import query
    try:
        kpis = query("""
            SELECT
                COUNT(DISTINCT user_id)                             AS total_users,
                SUM(is_purchase)                                    AS total_purchases,
                ROUND(SUM(CASE WHEN is_purchase=1 THEN price END),0) AS total_revenue,
                ROUND(SUM(is_purchase)*100.0/COUNT(*), 2)           AS conversion_rate
            FROM main_silver.silver_events_cleaned
        """).iloc[0]
    
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Người dùng",      f"{int(kpis.total_users):,}")
        c2.metric("Đơn hàng",        f"{int(kpis.total_purchases):,}")
        c3.metric("Doanh thu (USD)", f"${kpis.total_revenue:,.0f}")
        c4.metric("Tỷ lệ chuyển đổi", f"{kpis.conversion_rate}%")
    except Exception as e:
        st.error(f"Lỗi kết nối: {e}")

pg = st.navigation([
    st.Page(home_page, title="Trang chủ"),
    st.Page("pages/1_Overview.py", title="Tổng quan"),
    st.Page("pages/2_Segments.py", title="Phân khúc"),
    st.Page("pages/3_Recommendations.py", title="Gợi ý sản phẩm"),
    st.Page("pages/4_GenBI.py", title="Trợ lý AI"),
])

pg.run()
