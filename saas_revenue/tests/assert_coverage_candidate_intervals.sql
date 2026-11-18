-- Fails if a coverage candidate has invalid interval bounds,
-- or if candidate bounds disagree with staged dates

select
    customer_id,
    transaction_date,
    membership_expire_date,
    candidate_start_date,
    candidate_end_date

from {{ ref('int_subscription_coverage_candidates') }}

where
    candidate_start_date is distinct from transaction_date

    or candidate_end_date
        is distinct from membership_expire_date

    or (
        has_candidate_coverage
        and (
            candidate_start_date is null
            or candidate_end_date is null
            or candidate_end_date <= candidate_start_date
        )
    )
