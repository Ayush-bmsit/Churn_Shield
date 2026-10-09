# Research gap and contribution

ChurnShield is a college prototype on the IBM telco customer churn CSV. The questions below are questions to measure. They are not results.

## Literature comparison

| Topic | Poudel et al. 2024 | Asif et al. 2025 | Zerine et al. 2026 | This project |
| --- | --- | --- | --- | --- |
| Full text read here | Abstract and bibliographic record only | Abstract only | Open-access HTML | Not a published paper |
| Dataset as stated by the source | Not in the retrieved abstract | More than 2 million records; drivers include regularity and montant | Kaggle telco link, plus an expanded snapshot the authors count as 8,093 rows and 34 inputs, including technical tickets | Unmodified IBM telco CSV in `data/` |
| Selection protocol as stated | Not verified from the full text | Not stated in the retrieved abstract | Nested cross-validation; PR-AUC for search; F1 threshold on inner validation | Stratified 5-fold average precision on a development set; F1 threshold on out-of-fold development scores; one untouched test evaluation |
| Models | GBM reported at 81% accuracy; other names not verified | Soft vote of XGBoost, CatBoost, and LightGBM | Elastic-net logistic regression, RBF SVC, random forest, XGBoost, multilayer perceptron | Logistic regression, random forest, XGBoost, LightGBM, CatBoost, and a soft vote of the three boosters when those libraries import |
| Explanation | SHAP and scatter plots | LIME and SHAP | SHAP, PDP, and ICE | SHAP on the saved pipeline when the explainer supports it |
| Link from score to a written rule | Not in the retrieved abstract | Not in the retrieved abstract | Narrative recommendations, including ticket-based actions | Deterministic checks against versioned synthetic policy files |

## Research gap

Published churn papers already compare tabular models and explain scores. Two gaps matter for this prototype.

**Evaluation robustness.** The previous ChurnShield code selected a model by the highest ROC-AUC on the same 20% split used as the reported test. That split cannot also be the place where the choice is made. A development-set comparison with shared folds, plus a threshold chosen before the test scores are computed, is the correction. It does not by itself prove a model is best outside this file.

**Prediction-to-action gap.** A SHAP bar does not state whether a discount is allowed, who may approve it, or which sentence of a policy was used. The prototype needs a written rule set and a trace from the recommendation back to that text. Retrieval over those documents is designed and not yet built. The current assistant that writes SQL is a different feature and stays separate.

A third limit is external validity. One telecommunications extract, even with cross-validation, does not establish performance for another operator. This project records that limit. It does not add a second operator file, so it does not claim to remove the limit.

## Research questions

1. Do the documented domain features improve development-set average precision relative to the original predictors, using the same folds and model settings?
2. Does the model preferred by mean cross-validated average precision differ from the model preferred by ROC-AUC on one stratified development split?
3. How do precision, recall, F1, and the number of flagged customers change across decision thresholds on out-of-fold development probabilities?
4. Can the saved score and a SHAP explanation, when one is available, be shown next to a synthetic policy source, an eligibility result, and an approval level without treating the score as a cause?

## Proposed methodology

1. Inspect the CSV before choosing a missing-value rule. Set blank `TotalCharges` to 0 only for tenure 0 if that is what the file shows. Do not drop those rows.
2. Keep `customerID` out of the predictors. Do not remove IQR outliers unless a row is a data error. Extreme bills can be real customers.
3. Split a stratified 20% test set first (`random_state=42`).
4. Compare baseline and engineered features inside pipelines. Imputers and encoders fit on training folds only. SMOTE, if used, sits after preprocessing and runs only while fitting.
5. Rank candidates by mean average precision. Report fold standard deviations and ROC-AUC, and report precision, recall, and F1 at 0.50 as secondary figures.
6. Fit the chosen pipeline on the development set only after the rank is fixed. Choose the threshold by maximum F1 on out-of-fold development probabilities.
7. Score the test set once. Save the pipeline, threshold, feature definitions, and both the cross-validation table and the test metrics.
8. Explain individual scores with SHAP when the saved model allows it. Apply `build_decision` so the screen cites the mock policy section.

Fixed tree settings are used so the comparison stays computable. They are not a claim that a larger search would not change the ranking.

## Expected contribution

A reproducible notebook and a saved pipeline that show, on this dataset:

- whether the two engineered fields help, hurt, or change little under a shared protocol;
- whether a single development split and cross-validation would have picked the same candidate;
- a threshold curve that makes the outreach trade-off explicit;
- a retention screen that keeps the probability, the risk bucket, the explanation, and the policy decision distinct.

The contribution is the evaluation design and the traceable demo. It is not a new algorithm and not a measured retention lift.

## Limitations that remain

- Only the IBM telco extract is used.
- Hyperparameters are fixed, not nested-searched.
- There is no randomised test of discounts, so no claim that an offer retains customers.
- SHAP is not causal.
- The policy files are fictional, and the app does not yet retrieve them. It applies a coded copy of the same rules.
- Contact history, consent, and the live 25,000 FCU budget are not in the database, so those checks are reported as unverified.
- CatBoost is trained on the same one-hot matrix as the other models, not on CatBoost’s native categorical mode. That keeps the preprocessing comparable and does not show what native categorical handling would do.
- If the selected model has no working SHAP explainer, the screen must show the failure. Predictions still come from the saved pipeline.

## Experiments required before each claim

| Claim that would be allowed | Evidence required |
| --- | --- |
| The engineered features improve prediction on this file | Higher mean development average precision for the engineered setup than for the baseline, on the same models and folds, with the fold spread reported |
| Cross-validation and a single split do not choose the same candidate | The diagnostic single-split ranking and the cross-validation ranking, both computed without the test set |
| A threshold other than 0.50 changes the outreach list | The out-of-fold precision, recall, F1, and flagged counts along the threshold curve, and the one threshold that maximises F1 |
| The demo can trace a suggestion to a rule | The prediction payload contains the policy file, the section, the eligibility flag, and the approval level, and the tests match those rules |
| The model works for other operators | Not claimed. It would need data from those operators, which this project does not have |
| A discount reduces churn | Not claimed. It would need outcome data from an intervention, which this project does not have |
