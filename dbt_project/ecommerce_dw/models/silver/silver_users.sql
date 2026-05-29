SELECT
    user_id,
    MIN(event_date)                                          AS first_seen_date,
    MAX(event_date)                                          AS last_seen_date,
    COUNT(DISTINCT event_date)                               AS active_days,
    COUNT(DISTINCT user_session)                             AS total_sessions,
    COUNT(*)                                                 AS total_events,
    SUM(is_view)                                             AS total_views,
    SUM(is_cart)                                             AS total_carts,
    SUM(is_purchase)                                         AS total_purchases,
    SUM(CASE WHEN is_purchase = 1 THEN price ELSE 0 END)     AS total_spent,
    CASE WHEN SUM(is_purchase) > 0
         THEN ROUND(SUM(CASE WHEN is_purchase=1 THEN price ELSE 0 END)
              / SUM(is_purchase), 2)
         ELSE 0 END                                          AS avg_order_value
FROM {{ ref('silver_events_cleaned') }}
GROUP BY user_id
