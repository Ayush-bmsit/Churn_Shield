# Implementation report

This report records what was changed and what the notebook run measured on 9 October 2026. Scores below come from `models/training_metrics.json` after `notebooks/01_model_development.ipynb` was executed. They are not targets that the code was adjusted to hit.

## Files created

- `docs/IMPLEMENTATION_PLAN.md`
- `docs/literature_review.md`
- `docs/RESEARCH_GAP_AND_CONTRIBUTION.md`
- `docs/IMPLEMENTATION_REPORT.md`
- `backend/ml/features.py`
- `backend/ml/experiment.py`
- `backend/ml/decision_support.py`
- `notebooks/01_model_development.ipynb` (executed; outputs saved)
- `data/mock_company_policies/` (six synthetic policies plus a README)
- `tests/test_features_and_protocol.py`
- `tests/test_decision_and_policies.py`
- `tests/test_branding.py`
- `tests/test_saved_pipeline.py`

## Files changed

- `backend/ml/preprocessing.py`, `train.py`, `predict.py`, `explain.py`, `retention.py`
- `backend/routes/prediction.py`, `backend/main.py`
- `frontend/app.py`, `frontend/components/ui.py`, and the Streamlit pages
- `requirements.txt`, `README.md`

Authentication, MySQL access, K-Means, batch scoring, and the SELECT-only chatbot were left in place. `backend/ml/train.ipynb` and `backend/ml/preprocessing.ipynb` are still the old one-line cell dumps. The analysis notebook is `notebooks/01_model_development.ipynb`.

## Data checks

The CSV has 7,043 rows and 21 columns. There are 5,174 non-churn and 1,869 churn rows (26.54% churn). Duplicate rows and duplicate `customerID` values: 0.

`TotalCharges` has 11 values that are not numeric. All 11 have tenure 0. They are set to 0 because no bill has accumulated yet. No rows are dropped. `customerID` is not a predictor.

After that cleaning, the interquartile fences for tenure, `MonthlyCharges`, and `TotalCharges` flag 0 rows. Tenure runs from 0 to 72 and monthly charges from 18.25 to 118.75. Nothing was clipped or removed.

Churn is higher for month-to-month contracts (42.71%) than for one-year (11.27%) or two-year (2.83%) contracts. It is higher for fiber (41.89%) than for DSL (18.96%) or no internet (7.40%), and higher for electronic check (45.29%) than for the other payment methods (about 15–19%). Those are group rates, not causes.

## Feature experiment

`tenure_group` uses fixed edges at 0, 12, 24, and 48 months. `optional_service_count` counts `Yes` on six internet add-ons. `No` and `No internet service` count as zero. Phone-line fields are not in the count.

Mean development-set average precision, class-weighted models, engineered minus baseline:

| Model | Baseline | Engineered | Difference |
| --- | ---: | ---: | ---: |
| Logistic regression | 0.6600 | 0.6641 | +0.0041 |
| Random forest | 0.6553 | 0.6569 | +0.0016 |
| XGBoost | 0.6688 | 0.6684 | −0.0004 |
| LightGBM | 0.6667 | 0.6676 | +0.0008 |
| CatBoost | 0.6673 | 0.6678 | +0.0005 |
| Soft vote | 0.6703 | 0.6704 | +0.0001 |

Fold standard deviations on average precision are about 0.015 to 0.030. The differences are smaller than that spread. On this file and these settings, the two extra fields do not show a reliable gain. The result is reported rather than dropped. Logistic regression moves the most, and that move is still smaller than its fold standard deviation (about 0.015 for the engineered class-weighted run).

SMOTE inside training folds did not beat class-weighted logistic regression (engineered 0.6624 versus 0.6641; baseline 0.6583 versus 0.6600). Unweighted LightGBM on the baseline features reached 0.6696, close to the leader, with a lower F1 at the 0.50 cutoff (0.585 versus about 0.63 for the class-weighted boosters). That 0.50 F1 was not used to choose the model.

## What was selected, and how that differs from the old rule

Selection rule: highest mean average precision over five stratified development folds. The 20% test set was not used for that choice or for the threshold.

Selected pipeline: engineered features, soft vote of XGBoost, CatBoost, and LightGBM, class weighting. Mean average precision 0.6704 ± 0.0233. Mean ROC-AUC 0.8494.

The margin over the baseline soft vote is 0.0001. That is not evidence the ensemble or the extra features are clearly better. The pre-stated rule still saves the top row. A larger nested search was not run. Tree models used 80 rounds, depth 4, so another setting could reorder these near-ties.

A single stratified 80/20 split of the development set, ranked by ROC-AUC and not used for selection, put engineered CatBoost first (holdout ROC-AUC 0.8531). Cross-validation and that one split do not choose the same candidate. That is the concrete answer to the robustness question on this file. It does not mean cross-validation will transfer to another operator.

The old project chose the highest ROC-AUC on the test split itself. That number is no longer the selection rule. The test metrics below were computed once, after the choice.

## Threshold and test result

The threshold maximises F1 on out-of-fold development probabilities. The chosen value is 0.55, not 0.50.

On those out-of-fold scores: precision 0.558, recall 0.757, F1 0.643, 2,028 of 5,634 development customers flagged (36.0%). Confusion matrix [[3243, 896], [363, 1132]].

Untouched test set (1,409 customers), same threshold: average precision 0.667, ROC-AUC 0.847, precision 0.541, recall 0.757, F1 0.631, balanced accuracy 0.762, Brier score 0.161. Confusion matrix [[795, 240], [91, 283]]. 523 customers flagged (37.1%).

Risk buckets stay at 0.30 and 0.70 and are not this threshold.

## Explainability and decisions

SHAP has no TreeExplainer for `VotingClassifier`. The app averages TreeExplainer values from the three members and says so in the method string. That average is not a single joint SHAP decomposition of the soft-vote probability. The note on the payload says the values are not causes.

The prediction screen shows the probability, the saved-threshold class, the risk bucket, the factors, and a decision built from the synthetic Northwind Mobile rules: offer tier or no offer, approval level, and the policy file and section. The SQL chatbot does not read those files. Retrieval is specified in `data/mock_company_policies/README.md` and is not implemented.

## What this does and does not address

Addressed in the prototype: model choice is no longer the test-set ROC-AUC; feature setups share folds; the threshold is chosen before the test look; recommendations cite a written rule and do not treat SHAP as causal.

Still unresolved: one public dataset only; no nested hyperparameter search; no measurement of whether a discount changes churn; no live budget, consent, or contact log; policy retrieval is not built; CatBoost uses the shared one-hot pipeline rather than native categories.

## What was tested

`python -m pytest tests -q`: 15 passed. The run checks the tenure-0 charge rule, the service count, the disjoint stratified split, threshold selection on the arrays it is given, the offer rules, the synthetic banner and the 15% / 8 FCU / 25,000 FCU limits, the ChurnShield label, scoring one raw row with the saved pipeline, and a non-empty SHAP factor list or a clear error.

The notebook was executed with `nbclient` and its outputs were written back. The first execution showed the VotingClassifier SHAP error. After the member-average explainer was added, the notebook was executed again. The second run is the one stored.

The Streamlit screens were not clicked in a browser. That needs the FastAPI process and MySQL, which were not started in this session.

## How to run it

From the project root, with the packages in `requirements.txt` installed:

```bash
python -m pytest tests -q
python -m backend.ml.train
```

The notebook needs a Jupyter kernel and reruns the same training:

```bash
python -m nbclient --timeout=2400 notebooks/01_model_development.ipynb
```

Application processes, unchanged from the existing Docker or local setup:

```bash
uvicorn backend.main:app --reload
streamlit run frontend/app.py
```

Training overwrites `models/churn_pipeline.joblib`, `models/shap_background.npy`, and `models/training_metrics.json`. Inference loads those files. It does not fit a new model per request.
