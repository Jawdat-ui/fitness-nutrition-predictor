"""Caloric & macronutrient prediction model.

Uses the Mifflin-St Jeor equation for BMR estimation, standard activity
multipliers for TDEE, and evidence-based macro splits.

References:
    Mifflin MD, St Jeor ST, et al. "A new predictive equation for resting
    energy expenditure in healthy individuals." Am J Clin Nutr. 1990.
"""

from __future__ import annotations

from fitness_predictor.models import (
    ActivityLevel,
    Goal,
    MacroTarget,
    Sex,
    UserProfile,
    LB_PER_KG,
)


# ---------------------------------------------------------------------------
# Activity-level multipliers (Harris-Benedict convention)
# ---------------------------------------------------------------------------

ACTIVITY_MULTIPLIERS: dict[ActivityLevel, float] = {
    ActivityLevel.SEDENTARY: 1.2,
    ActivityLevel.LIGHTLY_ACTIVE: 1.375,
    ActivityLevel.MODERATELY_ACTIVE: 1.55,
    ActivityLevel.VERY_ACTIVE: 1.725,
    ActivityLevel.EXTRA_ACTIVE: 1.9,
}


def calculate_bmr(weight_kg: float, height_cm: float, age: int, sex: Sex) -> float:
    """Calculate Basal Metabolic Rate using the Mifflin-St Jeor equation.

    Male:   BMR = 10 × weight(kg) + 6.25 × height(cm) − 5 × age + 5
    Female: BMR = 10 × weight(kg) + 6.25 × height(cm) − 5 × age − 161

    Args:
        weight_kg: Body weight in kilograms.
        height_cm: Height in centimetres.
        age: Age in years.
        sex: Biological sex.

    Returns:
        Estimated BMR in kcal/day.
    """
    base = 10 * weight_kg + 6.25 * height_cm - 5 * age
    return base + 5 if sex == Sex.MALE else base - 161


def calculate_tdee(bmr: float, activity_level: ActivityLevel) -> float:
    """Calculate Total Daily Energy Expenditure.

    TDEE = BMR × activity multiplier.

    Args:
        bmr: Basal Metabolic Rate in kcal/day.
        activity_level: Self-reported activity level.

    Returns:
        Estimated TDEE in kcal/day.
    """
    return bmr * ACTIVITY_MULTIPLIERS.get(activity_level, 1.2)


def adjust_for_goal(tdee: float, goal: Goal, adjustment: float = 400.0) -> float:
    """Adjust TDEE for the user's body-composition goal.

    Args:
        tdee: Total Daily Energy Expenditure.
        goal: Bulk (+), cut (−), or maintain (0).
        adjustment: Surplus/deficit in kcal (default 400).

    Returns:
        Adjusted caloric target in kcal/day.
    """
    if goal == Goal.BULK:
        return tdee + adjustment
    elif goal == Goal.CUT:
        return tdee - adjustment
    return tdee


def adjust_for_training_volume(
    calories: float, sessions_per_week: int, intensity: float
) -> float:
    """Add a small caloric bump for high training volume.

    Extra kcal = sessions × intensity × 50.

    Args:
        calories: Base caloric target.
        sessions_per_week: Resistance-training sessions per week.
        intensity: Subjective intensity (0.0–1.0).

    Returns:
        Calories with training-volume adjustment.
    """
    return calories + sessions_per_week * intensity * 50


def calculate_macro_targets(
    profile: UserProfile, calorie_adjustment: float = 400.0
) -> MacroTarget:
    """Full pipeline: BMR → TDEE → goal adjustment → training adjustment → macro split.

    Macro split logic:
        - Protein: 1.0 g/lb (cutting) or 0.8 g/lb (bulking / maintaining)
        - Fats: 25 % of total calories (÷ 9 for grams)
        - Carbs: remaining calories (÷ 4 for grams)

    Args:
        profile: User biometric profile.
        calorie_adjustment: Surplus/deficit amount in kcal.

    Returns:
        MacroTarget with BMR and TDEE populated.
    """
    bmr = calculate_bmr(profile.weight_kg, profile.height_cm, profile.age, profile.sex)
    tdee = calculate_tdee(bmr, profile.activity_level)
    goal_cals = adjust_for_goal(tdee, profile.goal, calorie_adjustment)
    final_cals = adjust_for_training_volume(
        goal_cals, profile.training_sessions_per_week, profile.training_intensity
    )

    # Protein
    weight_lb = profile.weight_kg * LB_PER_KG
    protein_per_lb = 1.0 if profile.goal == Goal.CUT else 0.8
    protein_g = protein_per_lb * weight_lb
    protein_cals = protein_g * 4

    # Fats (25 % of total)
    fat_cals = final_cals * 0.25
    fat_g = fat_cals / 9

    # Carbs (remainder)
    carb_cals = final_cals - protein_cals - fat_cals
    carb_g = max(carb_cals / 4, 0.0)  # guard against negative

    return MacroTarget(
        calories=final_cals,
        protein_g=protein_g,
        carbs_g=carb_g,
        fats_g=fat_g,
        bmr=bmr,
        tdee=tdee,
    )
