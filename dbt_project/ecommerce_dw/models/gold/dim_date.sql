WITH date_spine AS (
    SELECT UNNEST(
        generate_series(
            DATE '2019-11-01',
            DATE '2019-11-30',
            INTERVAL '1 day'
        )
    )::DATE AS date_day
)

SELECT
    CAST(strftime(date_day, '%Y%m%d') AS INTEGER)  AS date_id,
    date_day,
    EXTRACT(year  FROM date_day)                   AS year,
    EXTRACT(month FROM date_day)                   AS month,
    EXTRACT(day   FROM date_day)                   AS day,
    EXTRACT(dow   FROM date_day)                   AS day_of_week,
    strftime(date_day, '%A')                       AS day_name,
    strftime(date_day, '%B')                       AS month_name,
    CASE WHEN EXTRACT(dow FROM date_day) IN (0,6)
         THEN true ELSE false END                  AS is_weekend
FROM date_spine
