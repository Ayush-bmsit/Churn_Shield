# Implementation plan — ChurnShield upgrade

This plan was written after inspecting the local project (the working copy of the telco churn prototype). It is a record of what the code actually did before the upgrade, and of the sequence used to change it. It is not a claim that the new experiments have already succeeded.

## Current implementation (verified before edits)

| Area | What the code does |
| --- | --- |
| Training | `backend/ml/train.py` fits logistic regression, random forest, and XGBoost inside a scikit-learn `Pipeline`. It uses one stratified 80/20 split and selects the model with the highest **test** ROC-AUC. The checked-in `models/training_metrics.json` records logistic regression as that winner. |
| Cleaning | `backend/ml/preprocessing.py` coerces `TotalCharges` with `errors="coerce"` and fills every resulting missing value with 0. Rows that are still missing are dropped in `train.py`. `customerID` is not a model feature. |
| Features | Original numeric and categorical telco columns only. No domain-feature experiment. |
| Inference | `backend/ml/predict.py` loads `models/churn_pipeline.joblib` and does not retrain. The class label uses a fixed 0.50 cutoff. Risk labels use Low &lt; 0.30, Medium 0.30–0.70, High &gt; 0.70. |
| SHAP | `backend/ml/explain.py` uses `LinearExplainer` or `TreeExplainer`. Failures return an error payload and do not invent factors. |
| Segmentation | `backend/ml/segmentation.py` fits K-Means on tenure and charges. Names describe tenure and monthly charges. They do not say “high value”. |
| Retention | `backend/ml/retention.py` returns short rule strings. They are not tied to a policy document. |
| API and UI | FastAPI routes for login, predict, batch predict, customers, analytics, and chat. Streamlit pages call that API. Visible name: “Telco Churn Prototype”. |
| Chatbot | `backend/chatbot/` asks an LLM for SQL, validates a SELECT, and runs it as the read-only database user. RAG is not implemented. |
| Notebooks | `backend/ml/train.ipynb` and `backend/ml/preprocessing.ipynb` are the Python modules split into one-line cells. They are not an analysis notebook. |
| Tests | No test module was present. |
| Data | `data/WA_Fn-UseC_-Telco-Customer-Churn.csv`. |
| Dependencies | FastAPI, Streamlit, scikit-learn, XGBoost, SHAP, MySQL driver. LightGBM, CatBoost, and imbalanced-learn were not required. |

## Deficiencies relative to the requested project

1. Model choice uses the same split that is later treated as the result. Fold variation is not reported. Average precision is not the selection metric.
2. There is no comparison of original features with a documented engineered set.
3. Class imbalance is handled only by class weights or `scale_pos_weight`, with no separate comparison against an unweighted fit or training-fold SMOTE.
4. The operating threshold is fixed at 0.50.
5. There is no executed Jupyter analysis with EDA, missing-value evidence, or outlier decisions.
6. Retention text cannot be traced to a written policy, and there is no mock document set for a later retrieval assistant.
7. The interface is not branded ChurnShield.
8. The three papers are not reviewed in the repository.
9. Automated checks for leakage, feature definitions, and policy consistency do not exist.

## Files to add

- `docs/literature_review.md`
- `docs/RESEARCH_GAP_AND_CONTRIBUTION.md`
- `docs/IMPLEMENTATION_REPORT.md` (after the run, using measured results)
- `backend/ml/features.py`
- `backend/ml/experiment.py`
- `backend/ml/decision_support.py`
- `notebooks/01_model_development.ipynb`
- `data/mock_company_policies/` (six policy files plus a README)
- `tests/` for features, the split protocol, decision rules, branding, and policy files

## Files to change

- `backend/ml/preprocessing.py` — zero-fill `TotalCharges` only where tenure is 0; leave other numeric gaps for a fold-fitted imputer
- `backend/ml/train.py` — call the shared experiment and save one pipeline
- `backend/ml/predict.py` — use the saved decision threshold
- `backend/ml/explain.py` — transform every pipeline step except the classifier and any sampler
- `backend/ml/retention.py` — keep the existing function, backed by the policy rules
- `backend/routes/prediction.py` — return the decision-support payload as well as the existing fields
- `backend/main.py` — API title
- `frontend/app.py`, `frontend/pages/*.py`, `frontend/components/ui.py` — ChurnShield branding and the decision panel
- `requirements.txt` — LightGBM, CatBoost, imbalanced-learn, and notebook execution tools
- `README.md` — product name and the evaluation protocol

## Files left in place

Authentication, MySQL models, analytics, K-Means, the SQL chatbot, Docker files, and the two old notebooks stay. The old notebooks are not a suitable analysis and are not rewritten into a second copy of the training script.

## Implementation sequence

1. Shared feature definitions and leakage-safe pipelines.
2. Cross-validation comparison, development-only threshold choice, one final test evaluation, and artifact save.
3. Decision-support rules aligned with the mock policies.
4. Frontend branding and the prediction screen.
5. Literature and research-gap documents from sources that were actually read.
6. Notebook that loads the CSV, runs EDA, and calls the same experiment code.
7. Tests, then the implementation report from the real run.

## Compatibility risks

- The saved pipeline’s first steps may change. Inference still accepts the same raw columns. An old `churn_pipeline.joblib` must be replaced by rerunning training before the new feature step is assumed.
- `predicted_churn` will follow the saved threshold, which may not be 0.50. Risk buckets stay at 0.30 and 0.70.
- The predict response gains `decision_threshold` and `decision_support`. Existing keys (`churn_probability`, `predicted_churn`, `risk_level`, `explanation`, `recommendations`) remain.
- Batch prediction still returns scores only, so upload behaviour stays the same.
- If CatBoost, LightGBM, or imbalanced-learn cannot be imported, that candidate is skipped and the rest of the comparison still runs.
- The SQL chatbot is unchanged. Policy text is not inserted into SQL prompts.

## How existing behaviour will be checked

- Unit tests for cleaning, engineered features, the absence of `customerID` and `Churn` in predictors, and threshold selection on development probabilities only.
- A smoke check that the saved pipeline scores one raw customer row.
- API field names used by the Streamlit client stay present.
- SHAP errors still return `ok: false` rather than made-up factors.
- Policy files are checked for the synthetic banner and the same numeric limits the code uses.
- The notebook is executed in this environment. Any cell that cannot run is reported, not filled in.
