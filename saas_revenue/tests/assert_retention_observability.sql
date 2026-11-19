select
    month_end,
    retention_observability_status,
    modeled_churn_events,
    conditional_estimated_nrr,
    conditional_modeled_customer_churn_rate
from {{ ref('mart_monthly_kpis') }}

where (
    retention_observability_status =
        'insufficient_exit_evidence'
    and (
        conditional_estimated_nrr is not null
        or conditional_modeled_customer_churn_rate is not null
    )
)
or (
    retention_observability_status =
        'observed_exit_transitions_available'
    and coalesce(modeled_churn_events, 0) = 0
)
or (
    interpretable_opening_paid_share < 0
    or interpretable_opening_paid_share > 1
)
