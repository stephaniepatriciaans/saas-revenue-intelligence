{{ config(materialized='view') }}

-- Modeled estimates, not observed contractual financials.
-- Conservative reporting policy:
-- If no paid-to-no-coverage exits are observed,
-- suppress published churn/NRR instead of showing
-- apparently conclusive 0% churn and 100% NRR.

with snapshots as (

    select
        month_end,
        count(*) as customers_observed_to_date,

        count(*) filter (
            where modeled_coverage_state = 'estimated_paid_active'
        ) as estimated_paid_customers,

        count(*) filter (
            where modeled_coverage_state = 'ambiguous'
        ) as ambiguous_customer_months,

        count(*) filter (
            where modeled_coverage_state = 'other_coverage_only'
        ) as other_coverage_customer_months,

        count(*) filter (
            where modeled_coverage_state = 'no_observed_coverage'
        ) as no_observed_coverage_customers,

        coalesce(sum(estimated_mrr_twd), 0)
            as included_estimated_mrr_twd

    from {{ ref('fct_customer_month') }}
    group by 1

),

transitions as (

    select
        month_end,

        count(*) filter (
            where is_consecutive
              and prev_state = 'estimated_paid_active'
        ) as opening_paid_customers,

        count(*) filter (
            where is_consecutive
              and prev_state = 'estimated_paid_active'
              and modeled_coverage_state = 'ambiguous'
        ) as paid_to_ambiguous_customers,

        count(*) filter (
            where modeled_paid_to_no_coverage
        ) as modeled_churn_events,

        count(*) filter (
            where is_consecutive
              and prev_state = 'estimated_paid_active'
              and modeled_coverage_state in (
                  'estimated_paid_active',
                  'no_observed_coverage'
              )
        ) as interpretable_opening_paid_customers,

        sum(prior_modeled_mrr) filter (
            where is_consecutive
              and prev_state = 'estimated_paid_active'
              and modeled_coverage_state in (
                  'estimated_paid_active',
                  'no_observed_coverage'
              )
        ) as interpretable_opening_mrr_twd,

        sum(current_modeled_mrr) filter (
            where is_consecutive
              and prev_state = 'estimated_paid_active'
              and modeled_coverage_state in (
                  'estimated_paid_active',
                  'no_observed_coverage'
              )
        ) as interpretable_closing_mrr_twd

    from {{ ref('fct_mrr_movements') }}
    group by 1

),

metrics as (

    select
        s.*,

        12 * s.included_estimated_mrr_twd
            as included_estimated_arr_twd,

        t.opening_paid_customers,
        t.paid_to_ambiguous_customers,
        t.modeled_churn_events,
        t.interpretable_opening_paid_customers,
        t.interpretable_opening_mrr_twd,
        t.interpretable_closing_mrr_twd,

        cast(t.interpretable_opening_paid_customers as double)
            / nullif(t.opening_paid_customers, 0)
            as interpretable_opening_paid_share,

        case
            when coalesce(t.opening_paid_customers, 0) = 0
                then 'no_opening_paid_population'
            when coalesce(t.modeled_churn_events, 0) = 0
                then 'insufficient_exit_evidence'
            else 'observed_exit_transitions_available'
        end as retention_observability_status,

        cast(s.estimated_paid_customers as double)
            / nullif(s.customers_observed_to_date, 0)
            as estimated_paid_classification_share

    from snapshots s
    left join transitions t using (month_end)

)

select
    *,

    case
        when retention_observability_status =
             'observed_exit_transitions_available'
        then cast(modeled_churn_events as double)
            / nullif(interpretable_opening_paid_customers, 0)
    end as conditional_modeled_customer_churn_rate,

    case
        when retention_observability_status =
             'observed_exit_transitions_available'
        then cast(interpretable_closing_mrr_twd as double)
            / nullif(interpretable_opening_mrr_twd, 0)
    end as conditional_estimated_nrr

from metrics
