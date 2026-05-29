WITH base AS (
    SELECT
        user_id,
        SUM(is_view)                                              AS total_views,
        SUM(is_cart)                                              AS total_carts,
        SUM(is_purchase)                                          AS total_purchases,
        SUM(CASE WHEN is_purchase=1 THEN price ELSE 0 END)        AS total_spent,
        COUNT(DISTINCT event_date)                                AS active_days,
        COUNT(DISTINCT user_session)                              AS total_sessions,
        MAX(event_date)                                           AS last_purchase_date,
        MIN(event_date)                                           AS first_purchase_date
    FROM {{ ref('silver_events_cleaned') }}
    GROUP BY user_id
)

SELECT
    user_id,
    total_views,
    total_carts,
    total_purchases,
    ROUND(total_spent, 2)                                         AS total_spent,
    active_days,
    total_sessions,
    -- Conversion rates
    CASE WHEN total_views > 0
         THEN ROUND(total_carts * 1.0 / total_views, 4)
         ELSE 0 END                                               AS view_to_cart_rate,
    CASE WHEN total_carts > 0
         THEN ROUND(total_purchases * 1.0 / total_carts, 4)
         ELSE 0 END                                               AS cart_to_purchase_rate,
    -- AOV
    CASE WHEN total_purchases > 0
         THEN ROUND(total_spent / total_purchases, 2)
         ELSE 0 END                                               AS avg_order_value,
    -- RFM
    DATEDIFF('day', last_purchase_date, DATE '2019-11-30')        AS recency_days,
    total_purchases                                               AS frequency,
    ROUND(total_spent, 2)                                         AS monetary,
    first_purchase_date,
    last_purchase_date
FROM base
