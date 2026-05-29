WITH raw AS (
    SELECT *
    FROM {{ source('bronze', 'bronze_events_raw') }}
),

parsed AS (
    SELECT
        event_time,
        event_type,
        product_id,
        category_id,
        COALESCE(NULLIF(TRIM(category_code), ''), 'Unknown') AS category_code,
        COALESCE(NULLIF(TRIM(brand), ''), 'Unknown')         AS brand,
        CAST(price AS DOUBLE)                                AS price,
        user_id,
        user_session
    FROM raw
    WHERE user_id IS NOT NULL
      AND product_id IS NOT NULL
),

cleaned AS (
    SELECT *
    FROM parsed
    WHERE event_time IS NOT NULL
      AND price > 0
      AND event_type IN ('view', 'cart', 'purchase')
),

bot_users AS (
    SELECT user_id
    FROM cleaned
    GROUP BY user_id
    HAVING COUNT(*) > 1000
),

no_bots AS (
    SELECT c.*
    FROM cleaned c
    LEFT JOIN bot_users b ON c.user_id = b.user_id
    WHERE b.user_id IS NULL
),

deduped AS (
    SELECT DISTINCT
        event_time, event_type, product_id, category_id,
        category_code, brand, price, user_id, user_session
    FROM no_bots
),

final AS (
    SELECT
        event_time,
        event_type,
        product_id,
        category_id,
        category_code,
        brand,
        price,
        user_id,
        user_session,
        CAST(event_time AS DATE)                AS event_date,
        DATE_TRUNC('month', event_time)         AS event_month,
        EXTRACT(hour FROM event_time)           AS event_hour,
        EXTRACT(dow  FROM event_time)           AS event_dow,
        CASE WHEN EXTRACT(dow FROM event_time)
             IN (0,6) THEN true ELSE false END  AS is_weekend,
        SPLIT_PART(category_code, '.', 1)       AS category_level1,
        SPLIT_PART(category_code, '.', 2)       AS category_level2,
        CASE WHEN event_type = 'view'     THEN 1 ELSE 0 END AS is_view,
        CASE WHEN event_type = 'cart'     THEN 1 ELSE 0 END AS is_cart,
        CASE WHEN event_type = 'purchase' THEN 1 ELSE 0 END AS is_purchase
    FROM deduped
)

SELECT * FROM final
