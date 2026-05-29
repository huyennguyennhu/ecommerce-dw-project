SELECT
    ROW_NUMBER() OVER (ORDER BY event_time)  AS purchase_sk,
    user_id,
    product_id,
    date_id,
    price                                    AS purchase_price,
    user_session,
    event_time                               AS purchased_at
FROM {{ ref('fact_events') }}
WHERE event_type = 'purchase'
