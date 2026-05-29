WITH event_counts AS (
    SELECT 
        product_id,
        category_code,
        category_level1,
        category_level2,
        brand,
        COUNT(*) as brand_cnt
    FROM {{ ref('silver_events_cleaned') }}
    GROUP BY 1, 2, 3, 4, 5
),
ranked_brands AS (
    SELECT 
        *,
        ROW_NUMBER() OVER (PARTITION BY product_id ORDER BY brand_cnt DESC) as rn
    FROM event_counts
),
product_attributes AS (
    SELECT * FROM ranked_brands WHERE rn = 1
),
product_metrics AS (
    SELECT
        product_id,
        MIN(price)          AS min_price,
        MAX(price)          AS max_price,
        AVG(price)          AS avg_price,
        COUNT(*)            AS total_events,
        SUM(is_view)        AS total_views,
        SUM(is_cart)        AS total_carts,
        SUM(is_purchase)    AS total_purchases
    FROM {{ ref('silver_events_cleaned') }}
    GROUP BY product_id
)

SELECT
    m.product_id,
    m.min_price,
    m.max_price,
    m.avg_price,
    a.category_code,
    a.category_level1,
    a.category_level2,
    a.brand,
    m.total_events,
    m.total_views,
    m.total_carts,
    m.total_purchases
FROM product_metrics m
LEFT JOIN product_attributes a ON m.product_id = a.product_id
