-- Fails if customer_id + transaction_date
-- appears more than once.

select
    customer_id,
    transaction_date,
    count(*) as duplicate_rows

from {{ ref('int_transaction_day_conflicts') }}

group by
    customer_id,
    transaction_date

having count(*) > 1
