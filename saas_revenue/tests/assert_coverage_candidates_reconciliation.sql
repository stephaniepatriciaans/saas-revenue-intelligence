-- Fails if the candidate model loses or duplicates
-- transaction records or contains unmatched day summaries

with source_count as (

    select count(*) as source_rows
    from {{ ref('int_transaction_eligibility') }}

),

candidate_checks as (

    select
        count(*) as candidate_rows,

        count(*) filter (
            where same_day_transaction_count is null
               or has_multiple_transactions is null
               or has_attribute_conflict is null
               or has_mixed_payment_status is null
        ) as unmatched_day_rows,

        count(*) filter (
            where has_candidate_coverage is distinct from (
                has_valid_date_order
                and has_billing_fields
            )
        ) as invalid_coverage_flags,

        count(*) filter (
            where is_unambiguous_paid_candidate
                is distinct from (
                    is_paid_billing_candidate
                    and not has_attribute_conflict
                )
        ) as invalid_paid_flags

    from {{ ref('int_subscription_coverage_candidates') }}

)

select *
from source_count
cross join candidate_checks

where source_rows <> candidate_rows
   or unmatched_day_rows > 0
   or invalid_coverage_flags > 0
   or invalid_paid_flags > 0
