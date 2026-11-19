select month_end
from {{ ref('mart_monthly_kpis') }}
where included_estimated_mrr_twd < 0
   or included_estimated_arr_twd is distinct from 12 * included_estimated_mrr_twd
   or estimated_paid_customers + ambiguous_customer_months
      + other_coverage_customer_months + no_observed_coverage_customers
       <> customers_observed_to_date
   or conditional_modeled_customer_churn_rate < 0
   or conditional_modeled_customer_churn_rate > 1
   or conditional_estimated_nrr < 0
