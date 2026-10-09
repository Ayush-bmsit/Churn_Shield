import numpy as np
import pandas as pd

from backend.ml.experiment import choose_threshold, split_development_test
from backend.ml.features import (
    OPTIONAL_SERVICE_COLUMNS,
    add_domain_features,
    feature_definitions,
)
from backend.ml.preprocessing import FEATURE_COLUMNS, TARGET_COL, clean_features


def test_total_charges_zero_only_for_new_accounts():
    frame = pd.DataFrame(
        {
            "tenure": [0, 5, 0],
            "TotalCharges": [" ", " ", "29.85"],
            "MonthlyCharges": [29.85, 50, 29.85],
            "SeniorCitizen": [0, 0, 0],
        }
    )
    cleaned = clean_features(frame)
    assert cleaned.loc[0, "TotalCharges"] == 0
    assert pd.isna(cleaned.loc[1, "TotalCharges"])
    assert cleaned.loc[2, "TotalCharges"] == 29.85


def test_optional_service_count_ignores_unavailable_and_phone_lines():
    row = {column: "No internet service" for column in OPTIONAL_SERVICE_COLUMNS}
    row.update({column: "Yes" for column in ("OnlineSecurity", "TechSupport")})
    row["MultipleLines"] = "Yes"
    row["tenure"] = 3
    counted = add_domain_features(pd.DataFrame([row]))
    assert int(counted.loc[0, "optional_service_count"]) == 2
    assert "MultipleLines" not in feature_definitions()["engineered_additions"]["optional_service_count"]["columns"]


def test_tenure_groups_use_fixed_cutoffs():
    frame = pd.DataFrame(
        {
            "tenure": [0, 12, 13, 24, 48, 49],
            **{column: "No" for column in OPTIONAL_SERVICE_COLUMNS},
        }
    )
    grouped = add_domain_features(frame)["tenure_group"].tolist()
    assert grouped == [
        "0 months",
        "1-12 months",
        "13-24 months",
        "13-24 months",
        "25-48 months",
        "49+ months",
    ]


def test_customer_id_and_target_are_not_predictors():
    excluded = set(feature_definitions()["excluded_from_predictors"])
    assert "customerID" in excluded
    assert TARGET_COL in excluded
    assert "customerID" not in FEATURE_COLUMNS
    assert TARGET_COL not in FEATURE_COLUMNS


def test_split_is_stratified_and_disjoint():
    features = pd.DataFrame({"tenure": np.arange(100)})
    target = pd.Series([0] * 75 + [1] * 25)
    x_dev, x_test, y_dev, y_test = split_development_test(features, target)
    assert set(x_dev.index).isdisjoint(set(x_test.index))
    assert len(x_test) == 20
    assert abs(y_test.mean() - 0.25) < 1e-9
    assert abs(y_dev.mean() - 0.25) < 1e-9


def test_threshold_uses_only_the_arrays_it_is_given():
    y_true = np.array([0, 0, 1, 1])
    proba = np.array([0.1, 0.4, 0.6, 0.9])
    chosen = choose_threshold(y_true, proba)["selected"]
    assert chosen["f1"] == 1.0
    assert chosen["threshold"] == 0.41
