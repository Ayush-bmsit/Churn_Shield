# Customer segment policy

| Field | Value |
| --- | --- |
| Status | SYNTHETIC DEMONSTRATION DOCUMENT |
| Company | Northwind Mobile (fictional) |
| Product | ChurnShield demo |
| Version | 1.0 |
| Effective date | 2026-01-15 |
| Scope | Demonstration only. Not a real telecom operator policy and not a regulation. |

## 1. Purpose

This document says how Northwind Mobile prioritises a scored customer. Risk is the churn probability bucket. It is not a measure of customer value. The project does not compute lifetime value.

## 2. Risk handling

- High (probability above 0.70) and flagged: place the account on the priority queue and aim to review it within 2 business days.
- Medium (0.30 through 0.70 inclusive) and flagged: review within 7 business days.
- Low (below 0.30): do not place an outbound retention call. Leave the account on routine monitoring.
- Flagged but Low: the decision threshold and the risk bucket disagree. Follow the Low rule. Do not discount.
- Not flagged: do not start outreach, regardless of other attributes.

Tenure below 6 months on a High-risk flagged account is an onboarding case. Complete a service check before discussing price. The offer policy still decides whether a discount exists.

K-Means segment names in the app describe tenure and monthly charges only. They do not change these risk rules and they do not mean the customer is high-value.

## 3. What may inform priority

Employees may read contract, tenure, internet service, tech support, and monthly charges when applying the offer policy. They may read SHAP factors as associations that influenced the score. They may not treat a large SHAP value as proof that changing that field will retain the customer.

## 4. Uncertain cases

If the explanation service returns an error, do not fill in missing factors from memory. High-risk accounts in that state go to a manager before any Tier C offer. See the escalation matrix.
