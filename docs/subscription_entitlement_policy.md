# KKBox Subscription Entitlement Policy

## 1. Purpose

Define the assumptions used to reconstruct subscription
coverage and recurring revenue from KKBox transaction data.

These rules are analytical approximations, not verified
KKBox billing policies.

## 2. Source of Truth

Primary source: stg_transactions

Transaction grain:
One original transaction record.

Reporting currency:
TWD.

Competition churn labels are excluded from financial
subscription and churn calculations.

## 3. Observed Data Quality Findings

- Total transactions: 1,431,009
- Zero-payment transactions: 21,448
- Nonpositive plan durations: 2,218
- Expiry-before-transaction records: 5,106
- Customer-days with multiple transactions: 27,942
- Potential overlap customer-days: 192,279
- Customers with potential overlap: 127,929

These categories may overlap.

## 4. Coverage Versus Revenue

Subscription coverage and paid recurring revenue
are distinct concepts.

A future membership expiry can suggest access,
but does not independently prove positive revenue.

A positive payment can establish billing evidence,
but does not independently prove that a customer was
actively subscribed at every date before expiry.

## 5. Zero-Payment Events

Zero-payment transactions remain in the data.

They do not independently contribute positive MRR.

They may be considered potential coverage evidence,
subject to explicit lifecycle rules.

Do not automatically label them as free trials,
discounts, refunds, or subscription extensions.

## 6. Multiple Transactions and Overlaps

Do not sum transaction amounts directly into MRR.

Do not remove same-day transactions without investigation.

Do not assume that the latest or longest expiry represents
the correct paid contract.

Multiple records may represent legitimate renewals,
plan changes, or other unknown transaction behaviors.

## 7. Invalid or Ambiguous Records

Preserve source records in staging.

Flag nonpositive plan durations, impossible date ordering,
and other anomalies downstream.

Do not silently invent prices, durations, or expiry dates.

## 8. Monthly Reporting

Use month-end subscription snapshots.

Each customer can contribute at most one subscription
state to a given customer-month snapshot.

ARR is twelve times month-end MRR.

Financial churn must be reconstructed from subscription
state transitions, not from the competition is_churn label
or the transaction is_cancel flag alone.

## 9. Revenue Normalization

Use positive payment and valid subscription duration
as candidate evidence for recurring revenue.

Monthly revenue normalization rules must be documented
and tested before implementation.

Do not assume all plans are exactly 30 days.

Do not count overlapping transaction payments as
multiple simultaneous subscriptions without evidence.

## 10. Unresolved Decisions

Before publishing financial metrics:

1. Define transaction precedence for conflicting records.
2. Establish whether expiry dates are inclusive.
3. Define how zero-payment extensions affect paid status.
4. Determine handling for overlapping paid transactions.
5. Establish the valid historical observation window.
6. Specify whether recurring amounts are estimates
   based on payment history or contractual values.
7. Define an explicit anomaly and exclusion policy.

These decisions must be tested and labeled as assumptions.

## 11. Reporting Disclosure

All reconstructed MRR, ARR, retention, and financial churn
metrics will be labeled as estimates based on documented
transaction assumptions.

Costs and margins will be scenario-based assumptions,
not observed KKBox financial data.
