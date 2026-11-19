{{ config(materialized='view') }}

with source as (

    select *
    from {{ ref('int_subscription_coverage_candidates') }}

),

daily_coverage as (

    select
        customer_id,
        transaction_date,

        count(*) as transaction_count,

        max(candidate_end_date) filter (
            where has_candidate_coverage
        ) as latest_valid_candidate_expiry,

        count(*) filter (
            where has_candidate_coverage
        ) as valid_coverage_candidate_count,

        count(*) filter (
            where is_paid_billing_candidate
        ) as paid_billing_candidate_count,

        count(*) filter (
            where is_zero_payment
        ) as zero_payment_count,

        bool_or(has_attribute_conflict)
            as has_same_day_attribute_conflict

    from source

    group by
        customer_id,
        transaction_date

),

prior_coverage as (

    select
        *,

        max(latest_valid_candidate_expiry) over (
            partition by customer_id
            order by transaction_date
            rows between unbounded preceding
                 and 1 preceding
        ) as prior_max_valid_expiry

    from daily_coverage

),

classified as (

    select
        *,

        (
            prior_max_valid_expiry > transaction_date
        ) as has_prior_coverage_overlap,

        (
            prior_max_valid_expiry = transaction_date
        ) as starts_on_prior_expiry,

        case
            when prior_max_valid_expiry > transaction_date
            then date_diff(
                'day',
                transaction_date,
                prior_max_valid_expiry
            )
            else 0
        end as overlap_days

    from prior_coverage

)

select *
from classified
