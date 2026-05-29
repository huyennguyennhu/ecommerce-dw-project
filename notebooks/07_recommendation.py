import duckdb
import pandas as pd
import numpy as np
from scipy.sparse import csr_matrix
from dotenv import load_dotenv
import os

load_dotenv()
MOTHERDUCK_TOKEN = os.getenv("MOTHERDUCK_TOKEN")

print("=== Bước 1: Kết nối MotherDuck & lấy dữ liệu ===")
conn = duckdb.connect(f"md:my_db?motherduck_token={MOTHERDUCK_TOKEN}")

# Lấy dữ liệu hành vi với trọng số
interactions = conn.execute("""
    SELECT
        user_id,
        product_id,
        SUM(is_view     * 1 +
            is_cart     * 3 +
            is_purchase * 5)  AS interaction_score
    FROM main_silver.silver_events_cleaned
    GROUP BY user_id, product_id
    HAVING SUM(is_view * 1 + is_cart * 3 + is_purchase * 5) > 0
""").df()

print(f"Số cặp (user, product): {len(interactions):,}")

print("\n=== Bước 2: Xây dựng ma trận user-item ===")
# Encode user_id và product_id thành index
user_ids    = interactions['user_id'].unique()
product_ids = interactions['product_id'].unique()

user_map        = {u: i for i, u in enumerate(user_ids)}
product_map     = {p: i for i, p in enumerate(product_ids)}
product_rev_map = {i: p for p, i in product_map.items()}
user_rev_map    = {i: u for u, i in user_map.items()}

interactions['user_idx']    = interactions['user_id'].map(user_map)
interactions['product_idx'] = interactions['product_id'].map(product_map)

# Ma trận user x item (implicit >= 0.5.0 yêu cầu user x item)
user_item_matrix = csr_matrix((
    interactions['interaction_score'].values,
    (interactions['user_idx'].values, interactions['product_idx'].values)
), shape=(len(user_ids), len(product_ids)))

print(f"Ma trận: {len(user_ids):,} users x {len(product_ids):,} sản phẩm")

print("\n=== Bước 3: Train ALS model ===")
try:
    import implicit
except ImportError:
    import subprocess, sys
    subprocess.check_call([sys.executable, "-m", "pip", "install", "implicit", "-q"])
    import implicit

model = implicit.als.AlternatingLeastSquares(
    factors=64,
    regularization=0.1,
    iterations=20,
    random_state=42
)
model.fit(user_item_matrix)
print("✅ Model đã được train xong")

print("\n=== Bước 4: Đánh giá Precision@10 và Recall@10 ===")
def evaluate_model(model, interactions_df, user_map, product_map,
                   user_item_matrix, K=10, n_users=500):
    precisions, recalls = [], []
    sample_users = np.random.choice(list(user_map.keys()),
                                    min(n_users, len(user_map)),
                                    replace=False)
    for user_id in sample_users:
        user_idx = user_map[user_id]
        bought = set(
            interactions_df[interactions_df['user_id'] == user_id]['product_id'].tolist()
        )
        if len(bought) < 2:
            continue
        rec_idxs, _ = model.recommend(
            user_idx,
            user_item_matrix[user_idx],
            N=K,
            filter_already_liked_items=False
        )
        recommended = set(product_rev_map[i] for i in rec_idxs)
        hits = len(recommended & bought)
        precisions.append(hits / K)
        recalls.append(hits / len(bought))

    if not precisions:
        print("Không đủ user sample để tính điểm")
        return 0, 0
    p = np.mean(precisions)
    r = np.mean(recalls)
    print(f"Precision@{K}: {p:.4f}  ({p*100:.2f}%)")
    print(f"Recall@{K}:    {r:.4f}  ({r*100:.2f}%)")
    return p, r

evaluate_model(model, interactions, user_map, product_map, user_item_matrix)

print("\n=== Bước 5: Tạo top-10 recommendations cho 10,000 users ===")
SAMPLE_SIZE = 10000
sample_users = np.random.choice(list(user_map.keys()),
                                min(SAMPLE_SIZE, len(user_map)),
                                replace=False)

recommendations = []
for user_id in sample_users:
    user_idx = user_map[user_id]
    rec_idxs, scores = model.recommend(
        user_idx,
        user_item_matrix[user_idx],
        N=10,
        filter_already_liked_items=True
    )
    for rank, (idx, score) in enumerate(zip(rec_idxs, scores), 1):
        recommendations.append({
            'user_id':    user_id,
            'product_id': product_rev_map[idx],
            'rank':       rank,
            'score':      round(float(score), 4)
        })

rec_df = pd.DataFrame(recommendations)
print(f"Tổng recommendations: {len(rec_df):,}")

print("\n=== Bước 6: Lưu vào MotherDuck ===")
conn.execute("DROP TABLE IF EXISTS main_gold.gold_recommendations")
conn.register('rec_df', rec_df)
conn.execute("""
    CREATE TABLE main_gold.gold_recommendations AS
    SELECT * FROM rec_df
""")
count = conn.execute("SELECT COUNT(*) FROM main_gold.gold_recommendations").fetchone()[0]
print(f"✅ Đã lưu {count:,} rows vào gold_recommendations")

print("\n=== Bước 7: Sample recommendations ===")
sample = conn.execute("""
    SELECT r.user_id, r.product_id, r.rank, r.score,
           p.category_code, p.brand, p.avg_price
    FROM main_gold.gold_recommendations r
    LEFT JOIN main_gold.dim_product p ON r.product_id = p.product_id
    WHERE r.user_id = (SELECT user_id FROM main_gold.gold_recommendations LIMIT 1)
    ORDER BY r.rank
""").df()
print("Top 10 gợi ý cho 1 user mẫu:")
print(sample.to_string(index=False))

conn.close()
print("\n✅ Task 7 hoàn thành!")
