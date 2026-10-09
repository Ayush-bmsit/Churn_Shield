from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_churnshield_appears_on_the_main_screens():
    paths = [
        ROOT / "frontend" / "app.py",
        ROOT / "frontend" / "pages" / "login.py",
        ROOT / "frontend" / "pages" / "customer_prediction.py",
        ROOT / "frontend" / "pages" / "employee_dashboard.py",
        ROOT / "frontend" / "pages" / "manager_dashboard.py",
        ROOT / "README.md",
    ]
    for path in paths:
        assert "ChurnShield" in path.read_text(encoding="utf-8")
