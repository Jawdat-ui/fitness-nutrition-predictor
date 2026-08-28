"""Strength standards for compound lifts.

Provides bodyweight-ratio benchmarks (à la strengthlevel.com) for five major
compound lifts across five classification tiers: Beginner → Elite.

The ratios are approximate population-level standards compiled from competitive
powerlifting data and general fitness benchmarks.
"""

from __future__ import annotations

from fitness_predictor.models import Sex, StrengthLevel, WeightUnit, LB_PER_KG
from tabulate import tabulate


# ---------------------------------------------------------------------------
# Standards data — ratio of 1RM to bodyweight (in the same unit)
# ---------------------------------------------------------------------------

STRENGTH_STANDARDS: dict[str, dict[str, dict[str, float]]] = {
    "Bench Press": {
        "male":   {"beginner": 0.50, "novice": 0.75, "intermediate": 1.25, "advanced": 1.75, "elite": 2.00},
        "female": {"beginner": 0.25, "novice": 0.50, "intermediate": 0.75, "advanced": 1.00, "elite": 1.50},
    },
    "Squat": {
        "male":   {"beginner": 0.75, "novice": 1.00, "intermediate": 1.50, "advanced": 2.00, "elite": 2.50},
        "female": {"beginner": 0.50, "novice": 0.75, "intermediate": 1.00, "advanced": 1.50, "elite": 2.00},
    },
    "Deadlift": {
        "male":   {"beginner": 1.00, "novice": 1.25, "intermediate": 1.75, "advanced": 2.25, "elite": 3.00},
        "female": {"beginner": 0.50, "novice": 0.75, "intermediate": 1.25, "advanced": 1.75, "elite": 2.50},
    },
    "Overhead Press": {
        "male":   {"beginner": 0.35, "novice": 0.55, "intermediate": 0.80, "advanced": 1.10, "elite": 1.40},
        "female": {"beginner": 0.20, "novice": 0.35, "intermediate": 0.55, "advanced": 0.75, "elite": 1.00},
    },
    "Barbell Row": {
        "male":   {"beginner": 0.40, "novice": 0.60, "intermediate": 0.90, "advanced": 1.20, "elite": 1.60},
        "female": {"beginner": 0.25, "novice": 0.40, "intermediate": 0.65, "advanced": 0.85, "elite": 1.15},
    },
}

# Ordered from highest to lowest for comparison logic
_LEVELS_DESCENDING: list[tuple[str, StrengthLevel]] = [
    ("elite", StrengthLevel.ELITE),
    ("advanced", StrengthLevel.ADVANCED),
    ("intermediate", StrengthLevel.INTERMEDIATE),
    ("novice", StrengthLevel.NOVICE),
    ("beginner", StrengthLevel.BEGINNER),
]

_LEVELS_ASCENDING = list(reversed(_LEVELS_DESCENDING))

# Common exercise aliases (lowercase → canonical name)
_ALIASES: dict[str, str] = {
    "bench": "Bench Press",
    "bench press": "Bench Press",
    "bp": "Bench Press",
    "squat": "Squat",
    "sq": "Squat",
    "back squat": "Squat",
    "deadlift": "Deadlift",
    "dl": "Deadlift",
    "ohp": "Overhead Press",
    "overhead press": "Overhead Press",
    "press": "Overhead Press",
    "shoulder press": "Overhead Press",
    "military press": "Overhead Press",
    "barbell row": "Barbell Row",
    "row": "Barbell Row",
    "bb row": "Barbell Row",
    "bent over row": "Barbell Row",
}


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def get_supported_exercises() -> list[str]:
    """Return canonical names of exercises that have strength standards."""
    return list(STRENGTH_STANDARDS.keys())


def normalize_exercise_name(exercise: str) -> str | None:
    """Map a user-typed exercise name to its canonical form.

    Returns:
        Canonical exercise name, or ``None`` if no match is found.
    """
    return _ALIASES.get(exercise.lower().strip())


def get_strength_level(
    exercise: str, one_rm: float, bodyweight_kg: float, sex: Sex
) -> StrengthLevel:
    """Classify a 1RM against bodyweight-ratio standards.

    The 1RM is expected in the same unit as bodyweight (kg).

    Args:
        exercise: Canonical or aliased exercise name.
        one_rm: Estimated one-rep max in kg.
        bodyweight_kg: User's bodyweight in kg.
        sex: Biological sex.

    Returns:
        The highest StrengthLevel the user meets or exceeds.

    Raises:
        ValueError: If the exercise is not supported.
    """
    norm = normalize_exercise_name(exercise) or exercise
    if norm not in STRENGTH_STANDARDS:
        raise ValueError(f"Exercise '{exercise}' not supported.")

    ratio = one_rm / bodyweight_kg
    sex_key = "male" if sex == Sex.MALE else "female"
    standards = STRENGTH_STANDARDS[norm][sex_key]

    for key, level in _LEVELS_DESCENDING:
        if ratio >= standards[key]:
            return level

    return StrengthLevel.BEGINNER  # below all thresholds


def get_standards_table(
    exercise: str, bodyweight_kg: float, sex: Sex
) -> dict[str, float]:
    """Return the required 1RM (kg) for each strength level.

    Args:
        exercise: Canonical or aliased exercise name.
        bodyweight_kg: User's bodyweight in kg.
        sex: Biological sex.

    Returns:
        Dict mapping level name → required 1RM in kg.

    Raises:
        ValueError: If the exercise is not supported.
    """
    norm = normalize_exercise_name(exercise) or exercise
    if norm not in STRENGTH_STANDARDS:
        raise ValueError(f"Exercise '{exercise}' not supported.")

    sex_key = "male" if sex == Sex.MALE else "female"
    standards = STRENGTH_STANDARDS[norm][sex_key]
    return {level: ratio * bodyweight_kg for level, ratio in standards.items()}


def format_standards_comparison(
    exercise: str,
    one_rm: float,
    bodyweight_kg: float,
    sex: Sex,
    unit: WeightUnit = WeightUnit.LB,
) -> str:
    """Return a formatted text table comparing the user's 1RM against standards.

    Args:
        exercise: Canonical or aliased exercise name.
        one_rm: Estimated 1RM *in kg*.
        bodyweight_kg: User's bodyweight in kg.
        sex: Biological sex.
        unit: Display unit for the table.

    Returns:
        Formatted table string.
    """
    norm = normalize_exercise_name(exercise) or exercise
    if norm not in STRENGTH_STANDARDS:
        return f"Exercise '{exercise}' not supported for strength standards."

    standards_kg = get_standards_table(norm, bodyweight_kg, sex)
    current_level = get_strength_level(norm, one_rm, bodyweight_kg, sex)

    conversion = LB_PER_KG if unit == WeightUnit.LB else 1.0

    rows: list[list[str]] = []
    for key, _level in _LEVELS_ASCENDING:
        req = standards_kg[key] * conversion
        marker = "◀ YOU" if key == current_level.value else ""
        rows.append([key.capitalize(), f"{req:.1f}", marker])

    user_display = one_rm * conversion
    rows.append(["─" * 14, "─" * 10, "─" * 6])
    rows.append(["Your 1RM", f"{user_display:.1f}", current_level.value.upper()])

    headers = ["Level", f"Required ({unit.value})", ""]
    return tabulate(rows, headers=headers, tablefmt="grid")
