{{ config(materialized='view') }}
-- FIRST OBSERVED ESTIMATED-PAID MONTH cohort (left censoring possible).
-- Retention conditional on interpretable states; expose known/ambiguous counts.
with first_paid as (
    select customer_id, min(month_end) as cohort_month_end
    from {{ ref('fct_customer_month') }}
    where modeled_coverage_state = 'estimated_paid_active'
    group by customer_id
),
cohort_months as (
    select
        f.cohort_month_end,
        cm.customer_id, cm.month_end, cm.modeled_coverage_state,
        date_diff('month', date_trunc('month', f.cohort_month_end),
                           date_trunc('month', cm.month_end)) as months_since_cohort
    from {{ ref('fct_customer_month') }} cm
    inner join first_paid f on cm.customer_id = f.customer_id
    where cm.month_end >= f.cohort_month_end
)
select
    cohort_month_end,
    months_since_cohort,
    count(*) as cohort_customers_observed_at_age,
    count(*) filter (where modeled_coverage_state = 'estimated_paid_active')
        as estimated_paid_retained,
    count(*) filter (where modeled_coverage_state in
        ('estimated_paid_active', 'no_observed_coverage')) as interpretable_customers,
    count(*) filter (where modeled_coverage_state = 'ambiguous') as ambiguous_customers,
    cast(count(*) filter (where modeled_coverage_state = 'estimated_paid_active') as double)
        / nullif(count(*) filter (where modeled_coverage_state in
            ('estimated_paid_active', 'no_observed_coverage')), 0)
        as conditional_estimated_retention_rate
from cohort_months
group by 1, 2
