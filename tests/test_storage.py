"""Unit tests for the JSON storage backend."""

from __future__ import annotations

from datetime import date

import pytest

from fitness_predictor.models import (
    ActivityLevel,
    Goal,
    LiftLog,
    NutritionLog,
    Sex,
    UserProfile,
    WeightUnit,
)
from fitness_predictor.storage.json_storage import JsonStorage


@pytest.fixture
def storage(tmp_path):
    """Create a JsonStorage instance backed by a temp directory."""
    return JsonStorage(data_dir=tmp_path)


# ---------------------------------------------------------------------------
# Profile
# ---------------------------------------------------------------------------

def test_profile_round_trip(storage):
    profile = UserProfile(
        name="John", age=25, sex=Sex.MALE, height_cm=180, weight_kg=80,
        activity_level=ActivityLevel.SEDENTARY, goal=Goal.MAINTAIN,
    )
    storage.save_profile(profile)
    loaded = storage.load_profile()
    assert loaded is not None
    assert loaded.name == "John"
    assert loaded.age == 25
    assert loaded.weight_kg == 80


def test_load_empty_profile(storage):
    assert storage.load_profile() is None


# ---------------------------------------------------------------------------
# Nutrition Logs
# ---------------------------------------------------------------------------

def test_nutrition_logs_round_trip(storage):
    log1 = NutritionLog(
        date=date(2023, 1, 1), calories=2000, protein_g=150, carbs_g=200, fats_g=70,
    )
    log2 = NutritionLog(
        date=date(2023, 1, 2), calories=2500, protein_g=180, carbs_g=250, fats_g=80,
    )
    storage.save_nutrition_log(log1)
    storage.save_nutrition_log(log2)

    logs = storage.load_nutrition_logs()
    assert len(logs) == 2
    assert logs[0].calories == 2000
    assert logs[1].calories == 2500


def test_nutrition_log_filtering(storage):
    log1 = NutritionLog(
        date=date(2023, 1, 1), calories=2000, protein_g=150, carbs_g=200, fats_g=70,
    )
    log2 = NutritionLog(
        date=date(2023, 1, 5), calories=2500, protein_g=180, carbs_g=250, fats_g=80,
    )
    storage.save_nutrition_log(log1)
    storage.save_nutrition_log(log2)

    filtered = storage.load_nutrition_logs(
        start_date=date(2023, 1, 2), end_date=date(2023, 1, 10),
    )
    assert len(filtered) == 1
    assert filtered[0].calories == 2500


def test_update_nutrition_log(storage):
    log = NutritionLog(
        date=date(2023, 1, 1), calories=2000, protein_g=150, carbs_g=200, fats_g=70,
    )
    storage.save_nutrition_log(log)

    updated = NutritionLog(
        date=date(2023, 1, 1), calories=2500, protein_g=180, carbs_g=220, fats_g=75,
    )
    assert storage.update_nutrition_log(date(2023, 1, 1), updated) is True

    logs = storage.load_nutrition_logs()
    assert len(logs) == 1
    assert logs[0].calories == 2500


def test_delete_nutrition_log(storage):
    log = NutritionLog(
        date=date(2023, 1, 1), calories=2000, protein_g=150, carbs_g=200, fats_g=70,
    )
    storage.save_nutrition_log(log)
    assert storage.delete_nutrition_log(date(2023, 1, 1)) is True

    logs = storage.load_nutrition_logs()
    assert len(logs) == 0


# ---------------------------------------------------------------------------
# Lift Logs
# ---------------------------------------------------------------------------

def test_lift_logs_round_trip(storage):
    log = LiftLog(
        date=date.today(), exercise="Bench Press", weight=225, reps=5,
        unit=WeightUnit.LB,
    )
    storage.save_lift_log(log)

    logs = storage.load_lift_logs()
    assert len(logs) == 1
    assert logs[0].exercise == "Bench Press"
    assert logs[0].weight == 225


def test_load_empty_logs(storage):
    assert storage.load_nutrition_logs() == []
    assert storage.load_lift_logs() == []
