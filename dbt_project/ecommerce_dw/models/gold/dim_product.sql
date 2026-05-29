SELECT
    product_id,
    category_code,
    category_level1,
    category_level2,
    brand,
    min_price,
    max_price,
    avg_price,
    total_views,
    total_carts,
    total_purchases
FROM {{ ref('silver_products') }}
