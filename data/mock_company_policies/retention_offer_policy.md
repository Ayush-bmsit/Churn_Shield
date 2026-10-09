# Retention offer policy

| Field | Value |
| --- | --- |
| Status | SYNTHETIC DEMONSTRATION DOCUMENT |
| Company | Northwind Mobile (fictional) |
| Product | ChurnShield demo |
| Version | 1.0 |
| Effective date | 2026-01-15 |
| Scope | Demonstration only. Not a real telecom operator policy and not a regulation. |

## 1. Purpose

This document defines which fictional discounts an employee may recommend after ChurnShield scores a customer. A model score is not an approval. A SHAP factor is not a cause of churn and is not a reason to invent a discount.

## 2. Risk buckets

These buckets are separate from the decision threshold stored with the model.

- Low: predicted churn probability below 0.30.
- Medium: probability from 0.30 through 0.70 inclusive.
- High: probability above 0.70.

A customer is flagged for outreach only when the probability is greater than or equal to the saved decision threshold. Flagging does not by itself make a discount eligible.

## 3. Global limits

- Maximum discount: 15% of MonthlyCharges.
- Maximum offer duration: 3 months.
- The discount ends automatically. It does not change the list price after the stated months.
- No offer may claim that the customer will churn, or that the discount has been proven to prevent churn.

## 4. Offer tiers

Choose the single eligible tier with the highest discount percent. Do not stack tiers.

### 4.1 Tier A

- Discount: 5% of MonthlyCharges for 3 months.
- Eligible when all of the following are true: flagged for outreach; risk is Medium or High; Contract is Month-to-month; tenure is at least 6 months; MonthlyCharges is at least 40.
- Approval: employee when the monthly discount is 8 FCU or less; otherwise a manager.

### 4.2 Tier B

- Discount: 10% of MonthlyCharges for 3 months.
- Eligible when all of the following are true: flagged for outreach; risk is High; Contract is Month-to-month; tenure is at least 3 months; MonthlyCharges is at least 50.
- Approval: employee when the monthly discount is 8 FCU or less; otherwise a manager.

### 4.3 Tier C

- Discount: 15% of MonthlyCharges for 2 months.
- Eligible when all of the following are true: flagged for outreach; risk is High; Contract is Month-to-month; tenure is under 12 months; InternetService is Fiber optic; TechSupport is No; a SHAP explanation was produced for the prediction.
- Approval: manager only.
- If SHAP did not run, do not offer Tier C automatically. Escalate using the retention escalation matrix.

### 4.4 One-year exception

- A one-year contract is not eligible for Tier A, B, or C.
- A manager may approve a 5% discount for 3 months only when the customer is flagged, risk is High, and tenure is at least 6 months.
- An employee cannot approve this exception.

### 4.5 Ineligible cases

- Two-year contract: no price discount.
- Risk bucket Low: no price discount, even if the decision threshold flags the customer.
- Not flagged: no outreach and no discount.
- Any case that matches none of sections 4.1 to 4.4.

## 5. Examples

Eligible. Month-to-month, tenure 10, MonthlyCharges 60, Medium risk, flagged. Tier A applies: 3.00 FCU per month for 3 months. An employee may recommend it. Tier B and Tier C do not apply because the risk is not High.

Eligible. Month-to-month, tenure 4, MonthlyCharges 80, High risk, Fiber optic, TechSupport No, flagged, and SHAP is available. Tier C applies (12.00 FCU per month for 2 months) and needs a manager. Tier B also matches, but the higher percent is Tier C, so only Tier C is recommended.

Ineligible. Two-year contract, High risk, flagged. No discount. A service review may still be recorded under the contract and service policy.

Ineligible. Month-to-month, tenure 2, MonthlyCharges 90, Medium risk, flagged. Tenure is below 6, so Tier A does not apply. Risk is not High, so Tier B and Tier C do not apply. No discount.
