import duckdb
import pandas as pd
import shap
import matplotlib.pyplot as plt
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
from dotenv import load_dotenv
import os

load_dotenv('.env')
MOTHERDUCK_TOKEN = os.getenv('MOTHERDUCK_TOKEN')
conn = duckdb.connect(f"md:my_db?motherduck_token={MOTHERDUCK_TOKEN}")

print("=== 1. TRUY VẤN MOTHERDUCK ===")
res = conn.execute('''
SELECT cluster_label, COUNT(*) as cnt
FROM main_gold.cluster_predictions
GROUP BY cluster_label
ORDER BY cnt DESC;
''').df()
print(res.to_string(index=False))

print("\n=== 2. TẠO BIỂU ĐỒ SHAP ===")
df = conn.execute("""
    SELECT f.recency_days, f.frequency, f.monetary, 
           f.view_to_cart_rate, f.cart_to_purchase_rate, f.avg_order_value,
           p.cluster, p.cluster_label
    FROM main_gold.gold_customer_features f
    JOIN main_gold.cluster_predictions p ON f.user_id = p.user_id
    WHERE f.total_purchases > 0
""").df()

features_cols = [
    'recency_days', 'frequency', 'monetary',
    'view_to_cart_rate', 'cart_to_purchase_rate', 'avg_order_value'
]

X = df[features_cols].fillna(0)
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

rf = RandomForestClassifier(n_estimators=50, random_state=42, n_jobs=-1)
rf.fit(X_scaled, df['cluster'])

explainer = shap.TreeExplainer(rf)
shap_values = explainer.shap_values(X_scaled[:1000])

# Map cluster labels correctly for the legend
unique_clusters = df['cluster'].unique()
unique_clusters.sort()
class_names = [df[df['cluster'] == c]['cluster_label'].iloc[0] for c in unique_clusters]

plt.figure(figsize=(12, 8))
shap.summary_plot(
    shap_values,
    pd.DataFrame(X_scaled[:1000], columns=features_cols),
    plot_type='bar',
    class_names=class_names,
    show=False
)
plt.savefig('notebooks/shap_summary.png', bbox_inches='tight', dpi=300)
print("✅ Biểu đồ SHAP đã được lưu thành công tại: notebooks/shap_summary.png")
conn.close()
