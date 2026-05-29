SELECT
    user_id,
    first_seen_date,
    last_seen_date,
    active_days,
    total_sessions,
    total_events,
    total_views,
    total_carts,
    total_purchases,
    total_spent,
    avg_order_value,
    CASE
        WHEN total_purchases = 0             THEN 'Viewer Only'
        WHEN total_purchases BETWEEN 1 AND 2 THEN 'Occasional Buyer'
        WHEN total_purchases BETWEEN 3 AND 9 THEN 'Regular Buyer'
        ELSE                                      'Heavy Buyer'
    END AS buyer_segment
FROM {{ ref('silver_users') }}
