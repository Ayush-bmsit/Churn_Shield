"""Offline training script. Not exposed as an HTTP endpoint.

Runs the shared development-set comparison and writes one pipeline.
The test split is not used to choose the model or the threshold.
"""

from __future__ import annotations

from pathlib import Path

from backend.ml.experiment import run_experiments


def train(csv_path: str | Path | None = None, models_dir: str | Path | None = None) -> dict:
    return run_experiments(csv_path=csv_path, models_dir=models_dir, save=True)


if __name__ == "__main__":
    train()
