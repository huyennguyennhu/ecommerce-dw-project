import duckdb
import pandas as pd
import numpy as np
import warnings
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
from dotenv import load_dotenv
import os

warnings.filterwarnings('ignore')

load_dotenv('.env')
MOTHERDUCK_TOKEN = os.getenv('MOTHERDUCK_TOKEN')

print("=== CELL 2: Lấy dữ liệu ===")
conn = duckdb.connect(f"md:my_db?motherduck_token={MOTHERDUCK_TOKEN}")
df = conn.execute("""
    SELECT *
    FROM main_gold.gold_customer_features
    WHERE total_purchases > 0
""").df()
print(f"Số khách hàng đã mua hàng: {len(df):,}")

print("\n=== CELL 3: RFM ===")
df['R_score'] = pd.qcut(df['recency_days'], q=5, labels=[5,4,3,2,1], duplicates='drop')
df['F_score'] = pd.qcut(df['frequency'].rank(method='first'), q=5, labels=[1,2,3,4,5])
df['M_score'] = pd.qcut(df['monetary'].rank(method='first'),  q=5, labels=[1,2,3,4,5])

df['R_score'] = df['R_score'].astype(int)
df['F_score'] = df['F_score'].astype(int)
df['M_score'] = df['M_score'].astype(int)
df['RFM_score'] = df['R_score'] * 100 + df['F_score'] * 10 + df['M_score']

def rfm_segment(row):
    r, f, m = row['R_score'], row['F_score'], row['M_score']
    if r >= 4 and f >= 4 and m >= 4: return 'Champions'
    elif r >= 3 and f >= 3:           return 'Loyal Customers'
    elif r >= 4 and f <= 2:           return 'New Customers'
    elif r <= 2 and f >= 3 and m >= 3:return 'At Risk'
    elif r <= 2 and f <= 2:           return 'Lost'
    else:                             return 'Potential'

df['rfm_segment'] = df.apply(rfm_segment, axis=1)
print(df['rfm_segment'].value_counts().to_string())

print("\n=== CELL 4 & 5: K-Means ===")
features_cols = [
    'recency_days', 'frequency', 'monetary',
    'view_to_cart_rate', 'cart_to_purchase_rate', 'avg_order_value'
]
X = df[features_cols].fillna(0)
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

K_OPTIMAL = 4
kmeans = KMeans(n_clusters=K_OPTIMAL, random_state=42, n_init=10)
df['cluster'] = kmeans.fit_predict(X_scaled)

profile = df.groupby('cluster')[features_cols].mean().round(2)
print("Profile từng cụm:")
print(profile.to_string())

cluster_labels = {
    0: 'VIP — Mua nhiều, chi nhiều',
    1: 'Tiềm năng — Tích cực nhưng ít mua',
    2: 'Thụ động — Ít tương tác',
    3: 'Rủi ro — Lâu không quay lại'
}
df['cluster_label'] = df['cluster'].map(cluster_labels)
print("\nPhân bố cụm:")
print(df['cluster_label'].value_counts().to_string())

print("\n=== CELL 8: Lưu kết quả ===")
result_df = df[[
    'user_id', 'cluster', 'cluster_label',
    'R_score', 'F_score', 'M_score',
    'RFM_score', 'rfm_segment'
]].copy()

conn.execute("DROP TABLE IF EXISTS main_gold.cluster_predictions")
conn.register('result_df', result_df)
conn.execute("""
    CREATE TABLE main_gold.cluster_predictions AS
    SELECT * FROM result_df
""")

count = conn.execute("SELECT COUNT(*) FROM main_gold.cluster_predictions").fetchone()[0]
print(f"✅ Đã lưu {count:,} rows vào cluster_predictions")
conn.close()
