{{ config(materialized='view') }}

with source as (

    select *
    from {{ ref('int_transaction_eligibility') }}

),

daily_summary as (

    select
        customer_id,
        transaction_date,

        count(*) as transaction_count,

        count(distinct membership_expire_date)
            as distinct_expiry_dates,

        count(distinct actual_amount_paid)
            as distinct_payment_amounts,

        count(distinct payment_plan_days)
            as distinct_plan_durations,

        count(*) filter (
            where is_positive_payment
        ) as positive_payment_count,

        count(*) filter (
            where is_zero_payment
        ) as zero_payment_count,

        count(*) filter (
            where is_paid_billing_candidate
        ) as paid_billing_candidate_count,

        count(*) filter (
            where has_transaction_anomaly
        ) as anomalous_transaction_count,

        min(membership_expire_date)
            as earliest_recorded_expiry,

        max(membership_expire_date)
            as latest_recorded_expiry

    from source

    group by
        customer_id,
        transaction_date

),

classified as (

    select
        *,

        (transaction_count > 1)
            as has_multiple_transactions,

        (distinct_expiry_dates > 1)
            as has_expiry_conflict,

        (distinct_payment_amounts > 1)
            as has_payment_conflict,

        (distinct_plan_durations > 1)
            as has_plan_duration_conflict,

        (
            positive_payment_count > 0
            and zero_payment_count > 0
        ) as has_mixed_payment_status,

        (
            distinct_expiry_dates > 1
            or distinct_payment_amounts > 1
            or distinct_plan_durations > 1
        ) as has_attribute_conflict

    from daily_summary

)

select *
from classified
