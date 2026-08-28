"""One-Rep Max estimation using five established formulas.

Each formula estimates the maximum weight a person can lift for a single
repetition based on a submaximal set (weight × reps).  The app averages
all five estimates and flags any that disagree by more than a configurable
threshold (default 5 %).

References:
    Epley, B. (1985). Poundage Chart. Boyd Epley Workout.
    Brzycki, M. (1993). "Strength Testing — Predicting a One-Rep Max…"
    Lombardi, V.P. (1989). Beginning Weight Training.
    McGlothin, T. (2003). The Ultimate Rep Scheme.
    O'Conner et al. (1989). "A New Approach to Strength Training."
"""

from __future__ import annotations

from fitness_predictor.models import (
    NutritionLog,
    OneRepMaxResult,
    UserProfile,
    WeightUnit,
)


# ---------------------------------------------------------------------------
# Individual formulas
# ---------------------------------------------------------------------------

def epley(weight: float, reps: int) -> float:
    """Epley formula: 1RM = w × (1 + r / 30)."""
    if reps == 1:
        return weight
    return weight * (1 + reps / 30)


def brzycki(weight: float, reps: int) -> float:
    """Brzycki formula: 1RM = w × 36 / (37 − r).

    Capped when reps ≥ 37 to avoid division by zero / negative.
    """
    if reps == 1:
        return weight
    if reps >= 37:
        return weight * 36.0
    return weight * 36.0 / (37 - reps)


def lombardi(weight: float, reps: int) -> float:
    """Lombardi formula: 1RM = w × r^0.10."""
    if reps == 1:
        return weight
    return weight * (reps ** 0.10)


def mcglothin(weight: float, reps: int) -> float:
    """McGlothin formula: 1RM = w × 100 / (101.3 − 2.67123 × r).

    Denominator is capped at 1.0 to prevent extreme values.
    """
    if reps == 1:
        return weight
    denom = 101.3 - 2.67123 * reps
    if denom < 1.0:
        denom = 1.0
    return weight * 100 / denom


def oconner(weight: float, reps: int) -> float:
    """O'Conner formula: 1RM = w × (1 + 0.025 × r)."""
    if reps == 1:
        return weight
    return weight * (1 + 0.025 * reps)


# ---------------------------------------------------------------------------
# Aggregation helpers
# ---------------------------------------------------------------------------

def calculate_all_1rm(weight: float, reps: int) -> dict[str, float]:
    """Run all five 1RM formulas and return results as a dict."""
    return {
        "epley": epley(weight, reps),
        "brzycki": brzycki(weight, reps),
        "lombardi": lombardi(weight, reps),
        "mcglothin": mcglothin(weight, reps),
        "oconner": oconner(weight, reps),
    }


def average_1rm(results: dict[str, float]) -> float:
    """Return the simple average of the formula results."""
    if not results:
        return 0.0
    return sum(results.values()) / len(results)


def flag_disagreements(
    results: dict[str, float], average: float, threshold: float = 0.05
) -> list[str]:
    """Return formula names that deviate from the average by > *threshold* (fraction).

    Args:
        results: Dict of formula-name → estimated 1RM.
        average: The mean 1RM across all formulas.
        threshold: Maximum allowed relative deviation (default 0.05 = 5 %).

    Returns:
        List of formula names that exceed the threshold.
    """
    if average == 0:
        return []
    return [
        name
        for name, val in results.items()
        if abs(val - average) / average > threshold
    ]


# ---------------------------------------------------------------------------
# Biometric / nutrition adjustment
# ---------------------------------------------------------------------------

def adjust_for_biometrics(
    base_1rm: float,
    profile: UserProfile,
    nutrition_logs: list[NutritionLog] | None = None,
) -> float:
    """Apply a small secondary adjustment to the 1RM estimate.

    Rules (intentionally conservative, ±1–3 %):
        • If the average of the last ≤ 7 nutrition logs has calories < 1 500,
          apply a −2 % penalty (under-fuelled lifter).
        • If bodyweight > 100 kg, apply a +1 % bonus (heavier lifters tend to
          have slightly higher absolute strength at a given relative load).

    Args:
        base_1rm: Unadjusted average 1RM.
        profile: User biometric profile.
        nutrition_logs: Recent nutrition entries (newest last).

    Returns:
        Adjusted 1RM.
    """
    factor = 1.0

    if nutrition_logs:
        recent = nutrition_logs[-7:]  # last 7 entries
        avg_cals = sum(log.calories for log in recent) / len(recent)
        if avg_cals < 1500:
            factor -= 0.02

    if profile.weight_kg > 100.0:
        factor += 0.01

    return base_1rm * factor


# ---------------------------------------------------------------------------
# Full pipeline
# ---------------------------------------------------------------------------

def calculate_1rm(
    weight: float,
    reps: int,
    unit: WeightUnit,
    exercise: str,
    profile: UserProfile | None = None,
    nutrition_logs: list[NutritionLog] | None = None,
) -> OneRepMaxResult:
    """Calculate estimated 1RM using all formulas and optionally adjust.

    Args:
        weight: Weight lifted.
        reps: Repetitions performed.
        unit: Weight unit (kg / lb).
        exercise: Exercise name.
        profile: Optional user profile for biometric adjustment.
        nutrition_logs: Optional recent nutrition logs for adjustment.

    Returns:
        Fully-populated OneRepMaxResult.
    """
    results = calculate_all_1rm(weight, reps)
    avg = average_1rm(results)
    flags = flag_disagreements(results, avg)

    adjusted = None
    if profile:
        adjusted = adjust_for_biometrics(avg, profile, nutrition_logs)

    return OneRepMaxResult(
        exercise=exercise,
        weight=weight,
        reps=reps,
        unit=unit,
        epley=results["epley"],
        brzycki=results["brzycki"],
        lombardi=results["lombardi"],
        mcglothin=results["mcglothin"],
        oconner=results["oconner"],
        average_1rm=avg,
        flagged_formulas=flags,
        adjusted_1rm=adjusted,
    )
