"""Unit tests for one-rep-max formulas and aggregation."""

from __future__ import annotations

import pytest

from fitness_predictor.models import WeightUnit
from fitness_predictor.prediction.one_rep_max import (
    average_1rm,
    brzycki,
    calculate_1rm,
    calculate_all_1rm,
    epley,
    flag_disagreements,
    lombardi,
    mcglothin,
    oconner,
)


def test_epley():
    # 100 × (1 + 10/30) = 133.33
    assert epley(100, 10) == pytest.approx(133.33, rel=1e-2)


def test_brzycki():
    # 100 × 36 / (37 − 10) = 133.33
    assert brzycki(100, 10) == pytest.approx(133.33, rel=1e-2)


def test_lombardi():
    # 100 × 10^0.10 ≈ 125.89
    assert lombardi(100, 10) == pytest.approx(125.89, rel=1e-2)


def test_mcglothin():
    # 100 × 100 / (101.3 − 26.7123) ≈ 134.00
    assert mcglothin(100, 10) == pytest.approx(134.00, rel=1e-1)


def test_oconner():
    # 100 × (1 + 0.025 × 10) = 125.0
    assert oconner(100, 10) == pytest.approx(125.0)


def test_all_formulas_reps_1():
    """With reps=1, every formula should return the weight itself."""
    for formula in [epley, brzycki, lombardi, mcglothin, oconner]:
        assert formula(200, 1) == 200.0


def test_calculate_all_1rm():
    results = calculate_all_1rm(100, 10)
    assert len(results) == 5
    assert set(results.keys()) == {"epley", "brzycki", "lombardi", "mcglothin", "oconner"}


def test_average_1rm():
    results = calculate_all_1rm(100, 10)
    avg = average_1rm(results)
    expected = sum(results.values()) / 5
    assert avg == pytest.approx(expected)


def test_flag_disagreements():
    results = calculate_all_1rm(100, 10)
    avg = average_1rm(results)
    # Add an artificial outlier
    results["outlier"] = 200.0
    new_avg = average_1rm(results)
    flags = flag_disagreements(results, new_avg)
    assert "outlier" in flags


def test_calculate_1rm_integration():
    result = calculate_1rm(
        weight=225, reps=5, unit=WeightUnit.LB, exercise="Bench Press",
    )
    assert result.exercise == "Bench Press"
    assert result.weight == 225
    assert result.reps == 5
    assert result.unit == WeightUnit.LB
    assert result.average_1rm > 225  # 1RM should exceed the 5-rep weight
    assert result.epley > 0
    assert result.brzycki > 0
