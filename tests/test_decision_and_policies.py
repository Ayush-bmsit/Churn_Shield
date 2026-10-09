from pathlib import Path

from backend.ml.decision_support import (
    EMPLOYEE_MONTHLY_AUTHORITY_FCU,
    MAX_DISCOUNT_PERCENT,
    build_decision,
)

POLICY_DIR = Path(__file__).resolve().parents[1] / "data" / "mock_company_policies"
POLICY_FILES = [
    "retention_offer_policy.md",
    "customer_segment_policy.md",
    "finance_and_budget_policy.md",
    "customer_communication_policy.md",
    "contract_and_service_policy.md",
    "retention_escalation_matrix.md",
]


def _base(**overrides):
    features = {
        "Contract": "Month-to-month",
        "tenure": 10,
        "MonthlyCharges": 60,
        "TechSupport": "Yes",
        "InternetService": "DSL",
    }
    features.update(overrides)
    return features


def test_tier_a_within_employee_authority():
    decision = build_decision(_base(), 0.50, decision_threshold=0.40)
    assert decision["offer"]["tier"] == "A"
    assert decision["offer"]["monthly_discount_fcu"] == 3.0
    assert decision["offer"]["approval"] == "employee"
    assert decision["offer"]["monthly_discount_fcu"] <= EMPLOYEE_MONTHLY_AUTHORITY_FCU


def test_tier_c_requires_manager_and_blocks_support_addon():
    decision = build_decision(
        _base(
            tenure=4,
            MonthlyCharges=80,
            InternetService="Fiber optic",
            TechSupport="No",
        ),
        0.91,
        decision_threshold=0.40,
        explanation_ok=True,
    )
    assert decision["offer"]["tier"] == "C"
    assert decision["offer"]["discount_percent"] == MAX_DISCOUNT_PERCENT
    assert decision["offer"]["approval"] == "manager"
    assert decision["support_addon"] is False


def test_missing_shap_does_not_auto_offer_tier_c():
    decision = build_decision(
        _base(tenure=4, MonthlyCharges=80, InternetService="Fiber optic", TechSupport="No"),
        0.91,
        decision_threshold=0.40,
        explanation_ok=False,
    )
    assert decision["offer"]["tier"] != "C"
    assert decision["manual_review"] is True


def test_two_year_contract_has_no_discount():
    decision = build_decision(_base(Contract="Two year"), 0.95, decision_threshold=0.40)
    assert decision["offer"]["eligible"] is False
    assert decision["approval_reason"] == "two_year_contract"


def test_below_threshold_is_not_an_offer():
    decision = build_decision(_base(), 0.20, decision_threshold=0.40)
    assert decision["flagged_for_outreach"] is False
    assert decision["offer"]["eligible"] is False


def test_policy_files_are_synthetic_and_match_the_code_limits():
    for name in POLICY_FILES:
        text = (POLICY_DIR / name).read_text(encoding="utf-8")
        assert "SYNTHETIC DEMONSTRATION DOCUMENT" in text
        assert "fictional" in text.lower()
    offer = (POLICY_DIR / "retention_offer_policy.md").read_text(encoding="utf-8")
    finance = (POLICY_DIR / "finance_and_budget_policy.md").read_text(encoding="utf-8")
    assert "Maximum discount: 15%" in offer
    assert "8 FCU" in finance
    assert "25,000 FCU" in finance
    assert "25 FCU" in finance
    readme = (POLICY_DIR / "README.md").read_text(encoding="utf-8")
    assert "does not search these files" in readme
    assert "SELECT" in readme
