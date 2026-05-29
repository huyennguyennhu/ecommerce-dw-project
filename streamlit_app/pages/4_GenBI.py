import streamlit as st
import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from utils.db import query
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

st.set_page_config(page_title="GenBI", page_icon="🤖", layout="wide")
st.title("🤖 GenBI — Hỏi đáp kinh doanh bằng AI")
st.markdown("Đặt câu hỏi bằng tiếng Việt, AI sẽ trả lời dựa trên dữ liệu thực tế.")

# Lấy context dữ liệu thực
@st.cache_data(ttl=3600)
def get_summary():
    kpi = query("""
        SELECT
            ROUND(SUM(CASE WHEN is_purchase=1 THEN price END), 0) AS revenue,
            COUNT(DISTINCT user_id)                               AS users,
            SUM(is_purchase)                                      AS orders,
            ROUND(AVG(CASE WHEN is_purchase=1 THEN price END), 2) AS aov
        FROM main_silver.silver_events_cleaned
    """).iloc[0]

    top_brands = query("""
        SELECT brand,
               ROUND(SUM(CASE WHEN is_purchase=1 THEN price ELSE 0 END),0) AS rev
        FROM main_silver.silver_events_cleaned
        WHERE brand != 'Unknown'
        GROUP BY brand ORDER BY rev DESC LIMIT 5
    """).to_dict(orient='records')

    top_cats = query("""
        SELECT category_level1,
               SUM(is_purchase) AS purchases
        FROM main_silver.silver_events_cleaned
        WHERE category_level1 != 'Unknown'
        GROUP BY category_level1 ORDER BY purchases DESC LIMIT 5
    """).to_dict(orient='records')

    segments = query("""
        SELECT cluster_label, COUNT(*) AS cnt
        FROM main_gold.cluster_predictions
        GROUP BY cluster_label ORDER BY cnt DESC
    """).to_dict(orient='records')

    return kpi, top_brands, top_cats, segments

kpi, top_brands, top_cats, segments = get_summary()

SYSTEM_PROMPT = f"""
Bạn là chuyên gia phân tích kinh doanh thương mại điện tử. 
Dưới đây là dữ liệu THỰC TẾ từ hệ thống (tháng 11/2019):

📊 KPIs TỔNG QUAN:
- Tổng doanh thu: ${kpi['revenue']:,.0f} USD
- Tổng người dùng: {kpi['users']:,}
- Tổng đơn hàng: {kpi['orders']:,}
- Giá trị đơn trung bình (AOV): ${kpi['aov']:,.2f} USD

🏆 TOP 5 BRAND DOANH THU:
{chr(10).join([f"- {b['brand']}: ${b['rev']:,.0f}" for b in top_brands])}

📦 TOP 5 DANH MỤC MUA NHIỀU:
{chr(10).join([f"- {c['category_level1']}: {c['purchases']:,} đơn" for c in top_cats])}

👥 PHÂN KHÚC KHÁCH HÀNG:
{chr(10).join([f"- {s['cluster_label']}: {s['cnt']:,} người" for s in segments])}

Hãy:
1. Trả lời bằng tiếng Việt, ngắn gọn, súc tích
2. Dựa vào số liệu thực tế trên để minh chứng
3. Đưa ra insights và đề xuất hành động cụ thể
4. Nếu câu hỏi ngoài phạm vi dữ liệu, nói rõ là không có dữ liệu
"""

# Gợi ý câu hỏi mẫu
st.markdown("**💡 Câu hỏi gợi ý:**")
sample_qs = [
    "Brand nào đang dẫn đầu doanh thu và tại sao?",
    "Làm thế nào để tăng tỷ lệ chuyển đổi từ cart sang purchase?",
    "Nên tập trung marketing vào nhóm khách hàng nào nhất?",
    "Danh mục nào nên nhập thêm hàng tháng tới?",
    "Phân tích điểm mạnh yếu của từng phân khúc khách hàng?"
]
cols = st.columns(len(sample_qs))
for i, q in enumerate(sample_qs):
    if cols[i].button(q, key=f"sq_{i}", use_container_width=True):
        st.session_state['auto_question'] = q

st.divider()

# Chat interface
if "messages" not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    st.chat_message(msg["role"]).write(msg["content"])

# Xử lý câu hỏi tự động từ nút gợi ý
if 'auto_question' in st.session_state:
    prompt = st.session_state.pop('auto_question')
else:
    prompt = st.chat_input("Nhập câu hỏi của bạn...")

if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})
    st.chat_message("user").write(prompt)

    try:
        groq_key = os.getenv("GROQ_API_KEY") or st.secrets.get("GROQ_API_KEY", "")
        client = Groq(api_key=groq_key)

        response = client.chat.completions.create(
            model="llama3-8b-8192",
            messages=[{"role": "system", "content": SYSTEM_PROMPT}]
                     + st.session_state.messages,
            max_tokens=1000
        )
        reply = response.choices[0].message.content
    except Exception as e:
        reply = f"❌ Lỗi kết nối Groq API: {e}"

    st.session_state.messages.append({"role": "assistant", "content": reply})
    st.chat_message("assistant").write(reply)

    if st.button("🗑 Xóa lịch sử chat"):
        st.session_state.messages = []
        st.rerun()
