select customer_id, month_end
from {{ ref('fct_mrr_movements') }}
where (is_consecutive and current_modeled_mrr is not null
        and prior_modeled_mrr is not null
       and (mrr_increase_twd is distinct from
                greatest(current_modeled_mrr - prior_modeled_mrr, 0)
            or mrr_decrease_twd is distinct from
                greatest(prior_modeled_mrr - current_modeled_mrr, 0)))
   or (not coalesce(is_consecutive, false)
       and (mrr_increase_twd is not null or mrr_decrease_twd is not null))
