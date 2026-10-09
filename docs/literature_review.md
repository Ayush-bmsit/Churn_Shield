# Literature review

This note summarises three papers that motivate the ChurnShield evaluation design. It separates what each paper states from observations made while reading it. Nothing here is a claim that ChurnShield has already reproduced those papers.

Sources checked on 9 October 2026:

- Paper 1 abstract and bibliographic record from the ScienceDirect page for DOI `10.1016/j.mlwa.2024.100567`, plus the Semantic Scholar record for that DOI. Semantic Scholar marked the article gold open access (CC BY) but returned a null abstract, and the full text was not retrieved in this session.
- Paper 2 abstract as reproduced by CoLab and Mendeley for DOI `10.1016/j.rineng.2025.104629`. Semantic Scholar marked it gold open access (CC BY-NC-ND) and returned a null abstract. The full text was not retrieved in this session.
- Paper 3 full text of the open-access Springer Nature HTML for DOI `10.1007/s44163-026-00983-0` (Discover Artificial Intelligence, volume 6, article 263).

Where the full text was not retrieved, missing items are marked unverified rather than filled in from secondary citations.

## 1. Poudel, Pokharel, and Timilsina (2024)

**Citation.** Sumana Sharma Poudel, Suresh Pokharel, and Mohan Timilsina. “Explaining customer churn prediction in telecom industry using tabular machine learning models.” *Machine Learning with Applications*, volume 17, September 2024, article 100567. DOI: [10.1016/j.mlwa.2024.100567](https://doi.org/10.1016/j.mlwa.2024.100567).

**Research problem (from the abstract).** Customer churn in telecommunications, and the lack of interpretability in earlier classification work that the authors say is needed for decisions.

**Dataset.** Not stated in the retrieved abstract. Size, column list, and whether the file is the IBM telco CSV were **not verified**.

**Preprocessing and feature engineering.** **Not verified.** The retrieved abstract does not describe them.

**Models.** The abstract says various classification models were used and that a gradient boosting machine (GBM) performed best. The names of the other models were **not verified** from the paper. A third-party thesis table that lists extra model names was not used, because it is not the paper.

**Reported findings (from the abstract).** GBM accuracy of 81%. A Wilcoxon signed-rank test is said to confirm a difference; the abstract’s retrieved text says the p-value indicates significant differences but does not print the p-value. The abstract concludes that GBM is better for this churn task and that the visualisations clarify churn factors.

**Explainability (from the abstract).** Local and global explanations using Shapley Additive Explanations plots and scatter plots.

**Limitations stated by the authors.** **Not verified.** The retrieved abstract has no limitations section. This review does not invent any.

**Observations that are not the authors’ claims.** Only the abstract was available here, so the evaluation design (one split versus cross-validation, how the threshold was chosen, and whether the test set was reused) cannot be judged from this reading. The 81% figure is accuracy. Accuracy on an imbalanced churn label is not the same quantity as average precision.

## 2. Asif, Arif, and Mukheimer (2025)

**Citation.** Daniyal Asif, Muhammad Shoaib Arif, and Aiman Mukheimer. “A data-driven approach with explainable artificial intelligence for customer churn prediction in the telecommunications industry.” *Results in Engineering*, June 2025, article 104629. DOI: [10.1016/j.rineng.2025.104629](https://doi.org/10.1016/j.rineng.2025.104629). Author names follow the CoLab record.

**Research problem (from the abstract).** Churn in telecommunications, limited accuracy of traditional models, and limited transparency of black-box models.

**Dataset (from the abstract).** More than 2 million records. The abstract does not call this the IBM telco file. The features it names as important, regularity and montant, are not columns in the IBM CSV used by ChurnShield. The exact row count, source, and class balance were **not verified** beyond “over 2 million records.”

**Preprocessing and features (from the abstract).** Iterative imputation with a Bayesian ridge; scaling described as a sequence of robust, standard, and min-max scaling; Boruta feature selection with a random forest; SMOTE for class imbalance in the training data.

**Models (from the abstract).** A soft-voting ensemble named XAI-Churn TriBoost, combining XGBoost, CatBoost, and LightGBM. The abstract presents this ensemble as the proposed model. It does not, in the text retrieved here, report a full table of the three models trained separately.

**Reported findings (from the abstract).** Accuracy 96.44%, precision 92.82%, recall 87.82%, F1 90.25%. One highlight line in a secondary snippet prints 92.80% precision and 90.24% F1. Those slightly different highlight figures were not treated as a second official result. The body numbers above are the ones used in this review.

**Explainability (from the abstract).** LIME and SHAP. Named drivers: regularity and montant.

**Limitations stated by the authors.** **Not verified.** The retrieved abstract has no limitations section.

**Observations that are not the authors’ claims.** The abstract does not say whether SMOTE, imputation, scaling, and Boruta were fitted only inside training folds. That design point is therefore unknown from this reading, not a finding that the authors leaked information. The dataset is a different problem from the 7,043-row IBM file, so the 96% accuracy is not a benchmark ChurnShield should be expected to match. The abstract does not show that the ensemble beat each base learner under the same protocol; it reports the ensemble’s scores.

## 3. Zerine and colleagues (2026)

**Citation.** Ismoth Zerine, Md Mainul Islam, Mohammad Aman Ullah Khan, Md Asikur Rahman Chy, Abu Saleh Muhammad Saimon, Mia Md. Tofayel Gonee Manik, and Chala Wata. “Explainable churn prediction in telecom with tabular ML five model benchmark and SHAP analysis.” *Discover Artificial Intelligence* 6, article 263 (2026). Published 22 February 2026. DOI: [10.1007/s44163-026-00983-0](https://doi.org/10.1007/s44163-026-00983-0). The full open-access HTML was read. Corresponding author: Chala Wata.

**Research problem (from the paper).** Operators need both an accurate churn score and an explanation that retention staff can connect to actions such as contract changes, ticket handling, and credits. The authors’ questions are which tabular model performs best under their protocol, whether fold-wise differences are stable, which factors drive the score, and how those factors map to interventions.

**Dataset (from the paper).** The data-availability statement links to the Kaggle Telco Customer Churn dataset (`blastchar/telco-customer-churn`). Section 3.1 calls the analytic file an expanded snapshot of 8,093 customers and 34 input features, with 28% churn and 72% non-churn (about 2.57 to 1). The abstract instead says the class ratio is about 2.77 to 1. Blank `TotalCharges` for zero-tenure customers are set to 0. The authors say there are no duplicate customer records. They describe technical-ticket counts that are not part of the preparation below.

**Preprocessing and feature engineering (from the paper).** One-hot encoding, with a dropped reference level for linear and neural models; ordered integers for contract on tree models; median imputation and robust scaling for continuous fields; optional log transform if it helps inner-loop PR-AUC. Engineered fields described in the paper include tenure bins (0–6, 7–12, 13–24, 25–36, above 36), a high-charge flag at the within-fold upper quartile, contract-by-charge and fiber-by-charge interactions, ticket counts capped at five, and a charges-per-tenure proxy. Feature selection (filters, elastic net, permutation importance, recursive elimination, stability selection) is placed inside the inner loop. The paper says this reduced the set to about two dozen features and improved PR-AUC by about two to three points. Those gain figures are the authors’ report; they were not recomputed here.

**Models (from the paper).** Logistic regression with elastic net, RBF support vector classifier, random forest, XGBoost, and a multilayer perceptron. Nested cross-validation: three stratified inner folds for search, five stratified outer folds for evaluation. The search objective is PR-AUC, with ROC-AUC as a tie break. The F1-maximising threshold is chosen on inner validation data. Class weights or a positive-class scale address imbalance. Probabilities may be calibrated with Platt scaling or isotonic regression when that improves PR-AUC.

**Reported findings (from the paper).** Outer-fold means for the multilayer perceptron: accuracy 0.92 ± 0.01, precision 0.88 ± 0.02, recall 0.82 ± 0.02, F1 0.85 ± 0.02, ROC-AUC 0.95 ± 0.01, PR-AUC 0.82 ± 0.02. XGBoost is reported as the strongest non-neural model (accuracy 0.89 ± 0.02, F1 0.69 ± 0.02, PR-AUC 0.74 ± 0.02). One confusion matrix on 704 customers gives 497 true negatives, 153 true positives, 21 false positives, and 33 false negatives. Mean Brier score 0.11 ± 0.01 for the multilayer perceptron. Wilcoxon signed-rank tests on five outer-fold F1 differences versus the multilayer perceptron have two-sided p-values of 0.0625 (logistic regression and SVC), 0.1250 (random forest), and 0.1875 (XGBoost). The authors describe the two-sided results as trend-level and the one-sided tests as meeting 5% only for logistic regression and SVC.

**Explainability (from the paper).** SHAP, partial dependence, and individual conditional expectation. The paper reports lower risk as tenure grows, higher risk from zero to about five technical tickets, and higher risk with high monthly charges, month-to-month contracts, and fiber. Global drivers named in the beeswarm discussion include contract, monthly charges, and tenure. Recommended actions in the paper include contract migration, ticket triage, and credits. The paper also says those actions should be tested with randomised experiments.

**Limitations stated by the authors (section 4.6 and the conclusion).** Results come from a single public dataset and one churn definition, so external validity is uncertain. Churn is behavioural rather than causal. SHAP explains associations, not causes, and actions should be validated prospectively. Ticket counts and charges may contain measurement error. Outreach can create feedback loops and uneven impact. Fairness metrics are not guarantees. The authors recommend privacy controls, opt-out handling, calibration and drift monitoring, audits, and A/B tests. Future work named by the authors includes other datasets and tabular neural architectures.

**Observations that are not the authors’ claims.**

- The paper’s own numbers do not describe one unchanged file. The abstract’s ratio is about 2.77 to 1, while section 3.1 reports 8,093 rows and 28% churn (about 2.57 to 1). The data link points at the public Kaggle telco file. The IBM CSV in this repository is the standard public file; it does not contain 8,093 rows or a technical-ticket column. The ticket effects and the 92% accuracy therefore refer to the authors’ expanded snapshot, not to a result ChurnShield can claim on the unmodified IBM extract.
- The confusion-matrix denominator of 704 customers is about one tenth of 7,043, which is another size that appears in discussion of the public file, and it is not 10% of 8,093. The paper does not explain that difference in the text that was read.
- With five folds, a two-sided Wilcoxon p-value of 0.0625 is the smallest possible non-zero result when one model wins every fold. The authors do report this and call it a trend. A reader should not upgrade that sentence into a claim of two-sided significance at 5%.
- Several business recommendations depend on ticket counts. Those recommendations cannot be copied onto a dataset that does not have tickets.

## What ChurnShield investigates instead

The three papers already study churn models and explanations. ChurnShield does not claim that SHAP, boosting, feature engineering, or churn prediction is new.

The comparison in this repository is narrower and tied to the unmodified IBM CSV:

- A baseline feature set versus two documented additions (`tenure_group` and `optional_service_count`), scored on the same development folds.
- Model choice by mean development-set average precision, with the final test set unused until that choice and the F1 threshold are fixed.
- A deterministic map from the score to synthetic Northwind Mobile rules, with the policy file and section named in the product. That map is a decision-support prototype. It is not evidence that the discount works, and it is not a retrieval system yet.

Cross-validation on this file does not show that a model will work for another operator. Paper 3 states that limitation for its own study. It remains a limitation here.
