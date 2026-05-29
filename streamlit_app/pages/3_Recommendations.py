import streamlit as st
import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from utils.db import query

st.set_page_config(page_title="Recommendations", layout="wide")
st.title("Gợi ý sản phẩm cá nhân hóa")

st.markdown("Nhập `user_id` để xem top-10 sản phẩm được gợi ý bởi mô hình ALS.")

# Lấy danh sách toàn bộ user_id hợp lệ
all_users = query("""
    SELECT DISTINCT user_id
    FROM main_gold.gold_recommendations
    ORDER BY user_id
""")['user_id'].tolist()

user_id = st.selectbox(
    "Chọn hoặc gõ tìm kiếm user_id:", 
    options=all_users,
    help="Bạn có thể click vào và gõ trực tiếp số ID để tìm kiếm nhanh."
)

if st.button("Xem gợi ý", type="primary"):
    recs = query(f"""
        SELECT
            r.rank,
            r.product_id,
            p.category_code,
            p.category_level1,
            p.brand,
            ROUND(p.avg_price, 2) AS avg_price,
            ROUND(r.score, 4)     AS relevance_score
        FROM main_gold.gold_recommendations r
        LEFT JOIN main_gold.dim_product p ON r.product_id = p.product_id
        WHERE r.user_id = {user_id}
        ORDER BY r.rank
    """)

    if len(recs) == 0:
        st.warning(f"Không tìm thấy gợi ý cho user_id={user_id}. Thử user_id khác nhé!")
    else:
        st.success(f"Top 10 sản phẩm gợi ý cho user **{user_id}**:")
        st.dataframe(recs, use_container_width=True)

        # Segment của user này
        seg = query(f"""
            SELECT cluster_label, rfm_segment, R_score, F_score, M_score
            FROM main_gold.cluster_predictions
            WHERE user_id = {user_id}
        """)
        if len(seg) > 0:
            st.info(f"Phân khúc: **{seg.iloc[0]['cluster_label']}** | RFM: {seg.iloc[0]['rfm_segment']}")
