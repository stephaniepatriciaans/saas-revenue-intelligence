-- Fails if customer-day counts or overlap classifications
-- contradict the model's documented rules

with checks as (

    select
        count(*) as customer_days,

        sum(transaction_count) as transaction_rows,

        count(*) filter (
            where overlap_days < 0
        ) as negative_overlap_days,

        count(*) filter (
            where overlap_days is distinct from
                case
                    when prior_max_valid_expiry
                         > transaction_date
                    then date_diff(
                        'day',
                        transaction_date,
                        prior_max_valid_expiry
                    )
                    else 0
                end
        ) as incorrect_overlap_durations,

        count(*) filter (
            where has_prior_coverage_overlap
                is distinct from (
                    prior_max_valid_expiry > transaction_date
                )
        ) as incorrect_overlap_flags,

        count(*) filter (
            where starts_on_prior_expiry
                is distinct from (
                    prior_max_valid_expiry = transaction_date
                )
        ) as incorrect_boundary_flags,

        count(*) filter (
            where valid_coverage_candidate_count
                  > transaction_count
               or paid_billing_candidate_count
                  > transaction_count
               or zero_payment_count
                  > transaction_count
        ) as invalid_daily_counts

    from {{ ref('int_subscription_cross_date_overlaps') }}

),

source_counts as (

    select
        count(*) as source_rows
    from {{ ref('int_subscription_coverage_candidates') }}

)

select *
from checks
cross join source_counts

where
    transaction_rows <> source_rows
    or negative_overlap_days > 0
    or incorrect_overlap_durations > 0
    or incorrect_overlap_flags > 0
    or incorrect_boundary_flags > 0
    or invalid_daily_counts > 0
    or customer_days = 0
