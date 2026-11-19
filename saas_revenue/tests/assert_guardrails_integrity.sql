with checks as (
    select count(*) as n,
        count(*) filter (where is_guardrail_paid_candidate
           and (not is_paid_billing_candidate
                or not has_candidate_coverage
                or coalesce(has_extreme_coverage_duration, false)
                or coalesce(has_extreme_plan_duration, false)
                or coalesce(has_attribute_conflict, false)
                or coalesce(outside_observed_transaction_window, false))) as invalid
    from {{ ref('int_coverage_guardrails') }}
), raw as (select count(*) as n from {{ ref('int_subscription_coverage_candidates') }})
select * from checks cross join raw
where checks.n <> raw.n or invalid > 0
