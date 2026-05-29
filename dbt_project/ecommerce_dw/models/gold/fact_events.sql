SELECT
    ROW_NUMBER() OVER (ORDER BY e.event_time)          AS event_sk,
    e.user_id,
    e.product_id,
    CAST(strftime(e.event_date, '%Y%m%d') AS INTEGER)  AS date_id,
    e.event_type,
    e.price,
    e.is_view,
    e.is_cart,
    e.is_purchase,
    e.user_session,
    e.event_time
FROM {{ ref('silver_events_cleaned') }} e
