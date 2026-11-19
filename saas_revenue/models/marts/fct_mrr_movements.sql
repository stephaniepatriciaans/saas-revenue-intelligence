{{ config(materialized='view') }}
-- Only consecutive, non-ambiguous measured customer-month pairs.
-- NULL when either side lacks a defensible estimated paid MRR.
with monthly as (
    select
        customer_id, month_end, modeled_coverage_state, estimated_mrr_twd,
        lag(month_end) over (partition by customer_id order by month_end) as prev_month_end,
        lag(modeled_coverage_state) over (
            partition by customer_id order by month_end
        ) as prev_state,
        lag(estimated_mrr_twd) over (
            partition by customer_id order by month_end
        ) as prev_mrr
    from {{ ref('fct_customer_month') }}
),
classified as (
    select *,
        (prev_month_end = last_day(month_end - interval 1 month)) as is_consecutive,
        -- For reporting, no observed coverage has a modeled zero MRR,
        -- but only a transition between complete states is interpretable.
        case
            when modeled_coverage_state = 'estimated_paid_active' then estimated_mrr_twd
            when modeled_coverage_state = 'no_observed_coverage' then 0::decimal(18,2)
        end as current_modeled_mrr,
        case
            when prev_state = 'estimated_paid_active' then prev_mrr
            when prev_state = 'no_observed_coverage' then 0::decimal(18,2)
        end as prior_modeled_mrr
    from monthly
)
select
    customer_id, month_end, prev_month_end, modeled_coverage_state, prev_state,
    current_modeled_mrr, prior_modeled_mrr,
    is_consecutive,
    case when is_consecutive
          and current_modeled_mrr is not null
          and prior_modeled_mrr is not null
         then greatest(current_modeled_mrr - prior_modeled_mrr, 0)
    end as mrr_increase_twd,
    case when is_consecutive
          and current_modeled_mrr is not null
          and prior_modeled_mrr is not null
         then greatest(prior_modeled_mrr - current_modeled_mrr, 0)
    end as mrr_decrease_twd,
    (is_consecutive and prev_state = 'estimated_paid_active'
     and modeled_coverage_state = 'no_observed_coverage')
         as modeled_paid_to_no_coverage,
    (is_consecutive and prev_state = 'no_observed_coverage'
     and modeled_coverage_state = 'estimated_paid_active')
         as modeled_no_coverage_to_paid
from classified
