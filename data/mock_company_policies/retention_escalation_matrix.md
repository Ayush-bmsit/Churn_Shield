# Retention escalation matrix

| Field | Value |
| --- | --- |
| Status | SYNTHETIC DEMONSTRATION DOCUMENT |
| Company | Northwind Mobile (fictional) |
| Product | ChurnShield demo |
| Version | 1.0 |
| Effective date | 2026-01-15 |
| Scope | Demonstration only. Not a real telecom operator policy and not a regulation. |

## 1. Purpose

This matrix says who may act. If two documents disagree, use the stricter result: the lower discount, or the higher approval level.

## 2. Employee may handle

- Routine monitoring for a customer who is not flagged, or whose risk bucket is Low.
- A Tier A or Tier B recommendation when the monthly discount is 8 FCU or less and no other rule requires a manager.
- The one-month tech-support add-on in the contract and service policy.
- Checking contact history and consent before any message. If either is unknown, the employee does not send the message.

## 3. Uncertain explanations

If the churn score exists but SHAP returns an error:

- Do not invent feature reasons.
- Do not offer Tier C automatically.
- A High-risk account requires manager review before an offer is treated as final.

## 4. Manager must handle

- Tier C.
- Any one-year contract exception.
- Any monthly discount above 8 FCU, or any amount reduced to the 25 FCU cap.
- A conflict between documents.
- A request to exceed 15% or 3 months. The manager must refuse that request under the current version of the offer policy.
- Any case where no policy passage supports the employee’s proposed action. The action is then unavailable, not approved by default.

## 5. Conflicting-rule example

A High-risk month-to-month fiber customer with no tech support matches Tier C (manager, 15% for 2 months) and also matches the tech-support add-on. The offer policy and the contract policy both say not to stack that add-on with Tier C. Recommend Tier C only, with manager approval. Do not also add the free support month.

## 6. Unavailable information

If a future assistant cannot retrieve a passage that covers the question, it must say the policy information is unavailable and escalate or ask for clarification. It must not fill the gap with a plausible discount.
