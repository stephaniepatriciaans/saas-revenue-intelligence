{{ config(materialized='view') }}

-- Provisional modeling policy: exclusive expiry, and an explicit
-- 450-day maximum plausible interval. This is NOT a KKBox billing rule.
with source as (
    select * from {{ ref('int_subscription_coverage_candidates') }}
),
classified as (
    select
        *,
        case when candidate_end_date > candidate_start_date
             then date_diff('day', candidate_start_date, candidate_end_date)
        end as recorded_coverage_days,
        (candidate_end_date > candidate_start_date
         and date_diff('day', candidate_start_date, candidate_end_date) > 450
        ) as has_extreme_coverage_duration,
        (payment_plan_days > 450) as has_extreme_plan_duration,
        (candidate_start_date < date '2015-01-01'
         or candidate_start_date > date '2017-03-31'
        ) as outside_observed_transaction_window
    from source
),
final as (
    select
        *,
        (has_candidate_coverage
         and not coalesce(has_extreme_coverage_duration, false)
         and not coalesce(has_extreme_plan_duration, false)
         and not coalesce(outside_observed_transaction_window, false)
        ) as is_guardrail_coverage_candidate,
        (is_paid_billing_candidate
         and not coalesce(has_attribute_conflict, false)
         and not coalesce(has_extreme_coverage_duration, false)
         and not coalesce(has_extreme_plan_duration, false)
         and not coalesce(outside_observed_transaction_window, false)
        ) as is_guardrail_paid_candidate
    from classified
)
select * from final
