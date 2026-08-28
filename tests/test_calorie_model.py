"""Unit tests for the calorie/macro prediction model."""

from __future__ import annotations

import pytest

from fitness_predictor.models import ActivityLevel, Goal, Sex, UserProfile
from fitness_predictor.prediction.calorie_model import (
    adjust_for_goal,
    calculate_bmr,
    calculate_macro_targets,
    calculate_tdee,
)


def test_calculate_bmr_male():
    # Male 80 kg, 180 cm, 25 yo → 10×80 + 6.25×180 − 5×25 + 5 = 1805
    assert calculate_bmr(80, 180, 25, Sex.MALE) == pytest.approx(1805.0)


def test_calculate_bmr_female():
    # Female 60 kg, 165 cm, 30 yo → 10×60 + 6.25×165 − 5×30 − 161 = 1320.25
    assert calculate_bmr(60, 165, 30, Sex.FEMALE) == pytest.approx(1320.25)


def test_calculate_tdee_sedentary():
    assert calculate_tdee(2000, ActivityLevel.SEDENTARY) == pytest.approx(2400.0)


def test_calculate_tdee_very_active():
    assert calculate_tdee(2000, ActivityLevel.VERY_ACTIVE) == pytest.approx(3450.0)


def test_adjust_for_goal_bulk():
    assert adjust_for_goal(2500, Goal.BULK, 400) == 2900


def test_adjust_for_goal_cut():
    assert adjust_for_goal(2500, Goal.CUT, 400) == 2100


def test_adjust_for_goal_maintain():
    assert adjust_for_goal(2500, Goal.MAINTAIN, 400) == 2500


def test_calculate_macro_targets_integration():
    profile = UserProfile(
        name="Test", age=25, sex=Sex.MALE, height_cm=180, weight_kg=80,
        activity_level=ActivityLevel.MODERATELY_ACTIVE, goal=Goal.BULK,
    )
    targets = calculate_macro_targets(profile)

    assert targets.bmr is not None and targets.bmr > 0
    assert targets.tdee is not None and targets.tdee > targets.bmr
    assert targets.protein_g > 0
    assert targets.carbs_g > 0
    assert targets.fats_g > 0

    # Verify caloric consistency: P×4 + C×4 + F×9 ≈ total calories
    computed = targets.protein_g * 4 + targets.carbs_g * 4 + targets.fats_g * 9
    assert computed == pytest.approx(targets.calories, abs=5)
