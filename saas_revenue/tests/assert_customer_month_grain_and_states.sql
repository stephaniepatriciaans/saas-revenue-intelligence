with checks as (
    select customer_id, month_end
    from {{ ref('fct_customer_month') }}
    group by 1,2 having count(*) > 1
), invalid as (
    select customer_id, month_end
    from {{ ref('fct_customer_month') }}
    where modeled_coverage_state not in (
        'ambiguous','estimated_paid_active','other_coverage_only','no_observed_coverage')
       or (modeled_coverage_state = 'estimated_paid_active'
           and (estimated_mrr_twd is null or estimated_mrr_twd <= 0))
       or (modeled_coverage_state <> 'estimated_paid_active'
           and estimated_mrr_twd is not null)
       or active_eligible_paid_count > active_coverage_candidate_count
)
select * from checks
union all
select * from invalid
