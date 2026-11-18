-- Fails if counts or conflict flags contradict
-- the transaction-day modeling rules

with summary as (

    select
        count(*) as customer_days,
        sum(transaction_count) as source_rows,

        count(*) filter (
            where has_multiple_transactions
        ) as multi_days,

        count(*) filter (
            where has_attribute_conflict
        ) as conflict_days,

        count(*) filter (
            where has_attribute_conflict
              and not has_multiple_transactions
        ) as impossible_conflict_days,

        count(*) filter (
            where has_multiple_transactions
              is distinct from (transaction_count > 1)
        ) as invalid_multiple_flags,

        count(*) filter (
            where has_attribute_conflict is distinct from (
                has_expiry_conflict
                or has_payment_conflict
                or has_plan_duration_conflict
            )
        ) as invalid_attribute_flags,

        count(*) filter (
            where has_expiry_conflict is distinct from (
                distinct_expiry_dates > 1
            )
            or has_payment_conflict is distinct from (
                distinct_payment_amounts > 1
            )
            or has_plan_duration_conflict is distinct from (
                distinct_plan_durations > 1
            )
            or has_mixed_payment_status is distinct from (
                positive_payment_count > 0
                and zero_payment_count > 0
            )
        ) as invalid_detail_flags

    from {{ ref('int_transaction_day_conflicts') }}

),

source_count as (

    select count(*) as raw_rows
    from {{ ref('int_transaction_eligibility') }}

)

select *
from summary
cross join source_count

where
    source_rows <> raw_rows
    or impossible_conflict_days > 0
    or invalid_multiple_flags > 0
    or invalid_attribute_flags > 0
    or invalid_detail_flags > 0
    or customer_days = 0
    or multi_days < conflict_days
