# Mock company policies

These Markdown files are synthetic rules for a fictional operator, Northwind Mobile. They exist so a later retrieval assistant can quote a source. They are not Northwind’s real documents, not IBM’s documents, and not telecom regulations.

ChurnShield already applies the same numeric limits in `backend/ml/decision_support.py`. That code path is deterministic. It does not search these files, and the SQL chatbot does not read them.

## What each file is for

| File | Questions it can answer |
| --- | --- |
| `retention_offer_policy.md` | Which discount tier, if any, matches a contract, tenure, risk bucket, and service mix. What the maximum percent and duration are. |
| `customer_segment_policy.md` | How Low, Medium, and High risk are handled, and that risk is not customer value. |
| `finance_and_budget_policy.md` | The 25,000 FCU monthly budget, the 8 FCU employee limit, and the 25 FCU monthly cap. |
| `customer_communication_policy.md` | How often someone may be contacted, which channel is allowed, and which claims are prohibited. |
| `contract_and_service_policy.md` | When a term change or a one-month tech-support add-on is allowed. |
| `retention_escalation_matrix.md` | Whether an employee can finish the case or a manager must approve it. |

## Future retrieval design

Do not mix this design into the current SQL assistant. That assistant may only run a validated `SELECT`. Policy text and database rows answer different questions and should stay in separate steps.

1. Chunk each file by heading. Keep the document name, version, and section title with every chunk.
2. Embed those chunks in a local index. Rebuilding the index is the only step required when a policy file changes. The churn model does not need retraining.
3. Retrieve a small number of chunks for the employee’s question plus the structured customer fields (contract, tenure, charges, services, probability, risk bucket, decision threshold, and SHAP labels if they exist).
4. Run `build_decision` first. The language model may explain that result in plain language. It may not change the tier, the percent, the duration, or the approval level.
5. The reply must separate three things: the model prediction, the policy passage, and the proposed action. It must cite the file name and section. It must not say that SHAP identified a cause.
6. If no chunk is relevant, the reply says the policy information is unavailable and points the user to a manager. It does not invent a rule.
7. If the live budget or contact history is missing, the reply says those checks are unverified, matching the finance and communication policies.

The model artifact stays in `models/`. Editing a policy file must not change `churn_pipeline.joblib`.
