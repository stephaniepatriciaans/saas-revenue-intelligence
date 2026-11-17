# Data Quality Contract — Draft v1

## Identity
- customer_id must not be null in financial facts.
- customer_id + month_key must be unique.

## Subscription lifecycle
- Paid entitlement must have a valid date range.
- Cancellation flags do not directly imply churn.
- Overlapping transactions require resolution.
- Ambiguous or invalid records must be flagged.

## Financial metrics
- MRR must be nonnegative.
- ARR must equal 12 * MRR.
- Customer churn must be between 0 and 1.
- NRR must be nonnegative when defined.
- Gross revenue churn must be between 0 and 1.

## Reconciliation
- Ending MRR must equal starting MRR
  + new MRR + reactivation MRR
  + expansion MRR - contraction MRR
  - churned MRR.

## Scenarios
- Assumed costs must be labeled.
- Synthetic results must not be mixed
  with observed financial metrics.

## Testing
- Source schema checks
- Null and uniqueness tests
- Business-rule tests
- Financial reconciliation tests
