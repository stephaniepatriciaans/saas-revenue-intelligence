# Phase 3 remaining Jira backlog and interview preparation

## Jira stories (all parent SRIP-3)

1. **Implement Coverage Guardrails**, 3 SP — flag intervals exceeding 450 days, preserve source rows, distinguish valid coverage and paid candidates. DoD: dbt model and tests pass.
2. **Build Dimensions and Transaction Fact**, 3 SP — `dim_month`, `dim_customer`, `dim_plan` (attribute proxy), `fct_transactions`. DoD: source documentation and unique dimension keys.
3. **Build Customer-Month Estimated Coverage Fact**, 5 SP — create customer-month snapshots; classify ambiguous, estimated paid, other coverage, and no-observed-coverage; prevent multiple MRR contributions. DoD: row grain and state/MRR tests pass.
4. **Build MRR Movement and Cohort Models**, 5 SP — create conditional interpretable transitions, churn transitions, and cohort retention with denominators and ambiguous coverage disclosure. DoD: validation tests pass.
5. **Build Monthly SaaS KPI Mart**, 5 SP — estimated run-rate MRR/ARR, conditional customer churn/NRR, segment counts and ambiguity. DoD: arithmetic checks pass; dashboard text explicitly says modeled estimates.
6. **Document Metric Assumptions and Sensitivity**, 3 SP — compare normalization conventions, expiry 366/450/730, cutoff and source coverage, and characterize biases. DoD: documented results and sign-off before any public KPI claim.

## Interview prep — definitions and examples

**1. What was the project problem?**
KKBox's transaction and expiry history is not a clean recurring-revenue ledger. I engineered a tested pipeline with raw, staging, quality classification, ambiguity detection, candidate coverage, and conditional monthly financial estimates.

**2. Why not sum payments for MRR?**
MRR is normalized recurring value at a point in time. Payments include renewals, prepaid amounts and possibly simultaneous events; naive summing overcounts customers or conflates cash receipts with a run-rate.

**3. What's the grain?**
Source transactions: one original row. Day conflicts/overlaps: one customer-date. Customer-month: one customer-month end. KPI mart: one month. Tests enforce grain where applicable.

**4. How did you profile duplicates and conflicts?**
27,942 multi-transaction customer-days, 27,732 with at least one attribute conflict; 192,279 customer-days with potential cross-date coverage overlap among 127,929 customers. These are not confirmed double charges.

**5. Why use a running MAX expiry rather than LAG?**
LAG sees only the immediately prior day; an even earlier row may have a longer expiry. Window MAX catches any earlier potential coverage, while same-day records are aggregated before windowing.

**6. What did you learn from zero-payment events?**
21,448 zero-payment transactions across 16,923 customers; 13,754 customers also have a positive payment in their observed histories; the zero event itself provides no positive-payment evidence.

**7. How do you handle ambiguity?**
Flag the conflict, preserve raw values, and avoid assigning a unique paid contract to multiple active paid candidates. MRR is NULL for ambiguous months; disclose excluded coverage alongside reported metrics.

**8. What makes MRR estimated?**
We don't have KKBox contracts, billing timestamps, entitlement policy, refunds, or cost data. We normalize an eligible positive payment by its stated plan days and explicitly label a 365.25/12 convention as an assumption.

**9. What is ARR?**
12 × a specific month-end MRR estimate, a run rate, not realized annual revenue.

**10. How do you compute NRR?**
Opening cohort's modeled ending MRR / opening MRR, excluding new customers. In this package it's only for consecutive interpretable pairs, so it's a conditional estimate, not a company-wide audited NRR.

**11. How do you define churn?**
A modeled transition from estimated paid coverage to no observed coverage across consecutive month-ends. That's not a verified cancellation and is separate from `is_cancel` and competition `is_churn`.

**12. Why is label leakage a risk?**
Using transactions or listening behavior from after the churn prediction cutoff allows the model to learn the outcome through future data. A label must be joined only to prior features.

**13. What is left censoring?**
Some customers subscribed before the dataset begins. First observed paid month is not necessarily acquisition month; cohort charts must say “first observed estimated paid.”

**14. How did you test your dbt models?**
Generic not-null/unique tests, accepted-value checks, singular count reconciliation, customer-day composite grain, conflict rules, candidate interval bounds, modeled customer-month grain, MRR arithmetic, KPI bounds.

**15. What about gross margin?**
Not observed. Any direct costs would require a separately labeled cost scenario. I would not call a margin number a KKBox financial fact.

**16. If a stakeholder challenges a 9-year overlap, what do you do?**
Surface the raw extreme expiry, apply a clearly labeled candidate duration guardrail, run sensitivity checks, and leave the underlying data unchanged.

**17. What's the next production improvement?**
Obtain authoritative contract and billing event IDs, timestamps, refunds, cancellation-effective dates; verify plan semantics; implement incremental processing and CI; add invoice-level reconciliation.

**18. Explain the dbt dependency graph.**
`source()` declares raw inputs; `ref()` declares dependencies. Our staging rows feed transaction classifications, conflicts and candidate intervals; the monthly fact and marts depend on prior models.

**19. How would you explain the trade-off of strict ambiguity exclusion?**
It lowers false precision and double counting, but can understate paid coverage and introduce selection bias. We present uncertainty counts and compare policy sensitivity.

**20. How do you prevent a flashy but misleading dashboard?**
Show source scope, model-based labels, modeled MRR alongside ambiguity counts and eligible customer coverage, missing-contract caveats, and explicit 'scenario' badges for costs.

## Technical exercises to rehearse

- Write SQL to find duplicate `(customer_id, transaction_date)` keys.
- Derive an interval overlap predicate for `[start, end)`.
- Explain why a left join can increase row counts.
- Implement `lag()` for month-over-month transitions and explain missing first-month values.
- Distinguish numerator/denominator changes when ambiguous states are excluded.
- Explain snapshot-based MRR versus transaction sums with a numerical renewal example.
