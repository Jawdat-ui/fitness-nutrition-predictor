"""Unit tests for Pydantic models and conversion helpers."""

from __future__ import annotations

from datetime import date

import pytest
from pydantic import ValidationError

from fitness_predictor.models import (
    ActivityLevel,
    Goal,
    KG_PER_LB,
    LB_PER_KG,
    LiftLog,
    NutritionLog,
    Sex,
    UserProfile,
    WeightUnit,
    to_kg,
    to_lb,
)


# ---------------------------------------------------------------------------
# UserProfile
# ---------------------------------------------------------------------------

def test_user_profile_creation():
    profile = UserProfile(
        name="John", age=25, sex=Sex.MALE, height_cm=180, weight_kg=80,
        activity_level=ActivityLevel.MODERATELY_ACTIVE, goal=Goal.MAINTAIN,
    )
    assert profile.name == "John"
    assert profile.age == 25
    assert profile.weight_kg == 80
    assert profile.height_cm == 180


def test_user_profile_validation():
    # Empty name
    with pytest.raises(ValidationError):
        UserProfile(name="", age=25, sex=Sex.MALE, height_cm=180, weight_kg=80)
    # Negative age
    with pytest.raises(ValidationError):
        UserProfile(name="John", age=-1, sex=Sex.MALE, height_cm=180, weight_kg=80)
    # Zero weight
    with pytest.raises(ValidationError):
        UserProfile(name="John", age=25, sex=Sex.MALE, height_cm=180, weight_kg=0)


def test_user_profile_weight_lb_property():
    profile = UserProfile(
        name="John", age=25, sex=Sex.MALE, height_cm=180, weight_kg=100,
    )
    assert profile.weight_lb == pytest.approx(220.462, rel=1e-3)


# ---------------------------------------------------------------------------
# NutritionLog
# ---------------------------------------------------------------------------

def test_nutrition_log_creation():
    log = NutritionLog(
        date=date.today(), calories=2500, protein_g=150, carbs_g=300, fats_g=80,
    )
    assert log.calories == 2500
    assert log.protein_g == 150


def test_nutrition_log_reject_negative():
    with pytest.raises(ValidationError):
        NutritionLog(
            date=date.today(), calories=-10, protein_g=0, carbs_g=0, fats_g=0,
        )


def test_nutrition_log_reject_extreme():
    with pytest.raises(ValidationError):
        NutritionLog(
            date=date.today(), calories=20000, protein_g=0, carbs_g=0, fats_g=0,
        )


# ---------------------------------------------------------------------------
# LiftLog
# ---------------------------------------------------------------------------

def test_lift_log_creation():
    log = LiftLog(
        date=date.today(), exercise="Bench Press", weight=225, reps=5,
        unit=WeightUnit.LB,
    )
    assert log.exercise == "Bench Press"
    assert log.reps == 5


def test_lift_log_reject_zero_weight():
    with pytest.raises(ValidationError):
        LiftLog(
            date=date.today(), exercise="Bench", weight=0, reps=5,
            unit=WeightUnit.KG,
        )


def test_lift_log_reject_zero_reps():
    with pytest.raises(ValidationError):
        LiftLog(
            date=date.today(), exercise="Bench", weight=100, reps=0,
            unit=WeightUnit.KG,
        )


def test_lift_log_weight_properties():
    log = LiftLog(
        date=date.today(), exercise="Bench", weight=100, reps=1,
        unit=WeightUnit.LB,
    )
    assert log.weight_kg == pytest.approx(45.3592, rel=1e-3)
    assert log.weight_lb == 100.0


# ---------------------------------------------------------------------------
# Conversion helpers
# ---------------------------------------------------------------------------

def test_to_kg():
    assert to_kg(100, WeightUnit.LB) == pytest.approx(45.3592, rel=1e-3)
    assert to_kg(100, WeightUnit.KG) == 100.0


def test_to_lb():
    assert to_lb(100, WeightUnit.KG) == pytest.approx(220.462, rel=1e-3)
    assert to_lb(100, WeightUnit.LB) == 100.0
