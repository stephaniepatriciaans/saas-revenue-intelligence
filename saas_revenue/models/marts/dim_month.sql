{{ config(materialized='view') }}
-- Historical transaction observation window only; not proof of data completeness.
select
    cast(month_start as date) as month_start,
    last_day(cast(month_start as date)) as month_end,
    year(cast(month_start as date)) as report_year,
    month(cast(month_start as date)) as report_month
from generate_series(
    date '2015-01-01', date '2017-03-01', interval 1 month
) as months(month_start)
