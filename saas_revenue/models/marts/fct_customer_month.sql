{{ config(materialized='table') }}
-- MODEL-BASED, NOT OBSERVED CONTRACT MRR.
-- Grain: a customer with a recorded transaction x month end, from the first
-- observed transaction month to the last month in the observation window.
-- One eligible active paid record => estimated MRR.
-- Multiple active paid records or active invalid/ambiguous evidence => unknown MRR.
-- No active candidates => no OBSERVED coverage, not verified cancellation.
with customer_first_month as (
    select customer_id, date_trunc('month', min(transaction_date))::date as first_month
    from {{ ref('stg_transactions') }}
    group by 1
),
customer_months as (
    select c.customer_id, m.month_start, m.month_end
    from customer_first_month c
    inner join {{ ref('dim_month') }} m on m.month_start >= c.first_month
),
active_candidates as (
    select
        cm.customer_id, cm.month_end,
        count(t.customer_id) as active_coverage_candidate_count,
        count(t.customer_id) filter (
            where t.is_positive_payment
        ) as active_positive_payment_count,
        count(t.customer_id) filter (
            where t.is_guardrail_paid_candidate
        ) as active_eligible_paid_count,
        count(t.customer_id) filter (
            where t.is_zero_payment
        ) as active_zero_payment_count,
        -- An ambiguous active candidate blocks definitive state classification.
        count(t.customer_id) filter (
            where not t.is_guardrail_coverage_candidate
               or (t.is_positive_payment and not t.is_guardrail_paid_candidate)
        ) as active_unresolved_candidate_count,
        max(case
            when t.is_guardrail_paid_candidate
            then t.actual_amount_paid * 365.25
                 / (12.0 * nullif(t.payment_plan_days, 0))
        end) as single_candidate_normalized_mrr
    from customer_months cm
    left join {{ ref('int_coverage_guardrails') }} t
        on cm.customer_id = t.customer_id
       and t.candidate_start_date <= cm.month_end
       and t.candidate_end_date > cm.month_end
    group by cm.customer_id, cm.month_end
),
classified as (
    select
        customer_id, month_end,
        active_coverage_candidate_count,
        active_positive_payment_count,
        active_eligible_paid_count,
        active_zero_payment_count,
        active_unresolved_candidate_count,
        case
            when active_unresolved_candidate_count > 0
              or active_eligible_paid_count > 1
            then 'ambiguous'
            when active_eligible_paid_count = 1
            then 'estimated_paid_active'
            when active_coverage_candidate_count > 0
            then 'other_coverage_only'
            else 'no_observed_coverage'
        end as modeled_coverage_state,
        case
            when active_unresolved_candidate_count = 0
             and active_eligible_paid_count = 1
            then cast(single_candidate_normalized_mrr as decimal(18, 2))
            else null
        end as estimated_mrr_twd
    from active_candidates
)
select * from classified
