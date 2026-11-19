-- Fails when customer-day grain is violated

select
    customer_id,
    transaction_date,
    count(*) as duplicate_rows

from {{ ref('int_subscription_cross_date_overlaps') }}

group by
    customer_id,
    transaction_date

having count(*) > 1
