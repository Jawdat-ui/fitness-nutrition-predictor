"""Unit tests for strength standards and exercise normalization."""

from __future__ import annotations

import pytest

from fitness_predictor.models import Sex, StrengthLevel, WeightUnit
from fitness_predictor.prediction.strength_standards import (
    format_standards_comparison,
    get_standards_table,
    get_strength_level,
    get_supported_exercises,
    normalize_exercise_name,
)


def test_get_supported_exercises():
    exercises = get_supported_exercises()
    assert len(exercises) >= 5
    assert "Bench Press" in exercises
    assert "Deadlift" in exercises


def test_normalize_exercise_name():
    assert normalize_exercise_name("bench") == "Bench Press"
    assert normalize_exercise_name("OHP") == "Overhead Press"
    assert normalize_exercise_name("DL") == "Deadlift"
    assert normalize_exercise_name("squat") == "Squat"
    assert normalize_exercise_name("unknown exercise") is None


def test_get_strength_level_intermediate():
    # Male, 80 kg bodyweight, 1RM = 100 kg → ratio = 1.25 → Intermediate
    level = get_strength_level("Bench Press", 100, 80, Sex.MALE)
    assert level == StrengthLevel.INTERMEDIATE


def test_get_strength_level_beginner():
    # Male, 80 kg, 1RM = 40 kg → ratio = 0.5 → Beginner
    level = get_strength_level("Bench Press", 40, 80, Sex.MALE)
    assert level == StrengthLevel.BEGINNER


def test_get_strength_level_elite():
    # Male, 80 kg, 1RM = 160 kg → ratio = 2.0 → Elite
    level = get_strength_level("Bench Press", 160, 80, Sex.MALE)
    assert level == StrengthLevel.ELITE


def test_get_strength_level_unsupported():
    with pytest.raises(ValueError):
        get_strength_level("Tricep Kickback", 50, 80, Sex.MALE)


def test_get_standards_table():
    table = get_standards_table("Bench Press", 80, Sex.MALE)
    assert len(table) == 5
    assert "beginner" in table
    assert "elite" in table
    # beginner ratio = 0.50 × 80 = 40
    assert table["beginner"] == pytest.approx(40.0)


def test_format_standards_comparison():
    formatted = format_standards_comparison(
        "Bench Press", 100, 80, Sex.MALE, WeightUnit.KG,
    )
    assert len(formatted) > 0
    assert "Beginner" in formatted
    assert "Elite" in formatted
