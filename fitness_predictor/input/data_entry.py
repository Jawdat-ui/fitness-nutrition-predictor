"""Interactive CLI prompts for data entry with input validation.

All functions use ``input()`` for user interaction and loop until valid
data is provided.
"""

from __future__ import annotations

from datetime import date, datetime

from fitness_predictor.models import LiftLog, NutritionLog, WeightUnit


def prompt_float(
    prompt: str, min_val: float = 0.0, max_val: float | None = None
) -> float:
    """Prompt the user for a float, repeating until a valid value is entered."""
    while True:
        try:
            val = float(input(prompt))
            if val < min_val:
                print(f"  Value must be at least {min_val}.")
                continue
            if max_val is not None and val > max_val:
                print(f"  Value must be at most {max_val}.")
                continue
            return val
        except ValueError:
            print("  Invalid input — please enter a number.")


def prompt_int(
    prompt: str, min_val: int = 0, max_val: int | None = None
) -> int:
    """Prompt the user for an integer, repeating until a valid value is entered."""
    while True:
        try:
            val = int(input(prompt))
            if val < min_val:
                print(f"  Value must be at least {min_val}.")
                continue
            if max_val is not None and val > max_val:
                print(f"  Value must be at most {max_val}.")
                continue
            return val
        except ValueError:
            print("  Invalid input — please enter a whole number.")


def prompt_choice(prompt: str, choices: list[str]) -> str:
    """Display numbered choices and return the user's selection."""
    print(prompt)
    for i, choice in enumerate(choices, 1):
        print(f"  {i}. {choice}")
    while True:
        idx = prompt_int("  Select an option: ", 1, len(choices))
        return choices[idx - 1]


def prompt_date(
    prompt: str = "Date (YYYY-MM-DD or press Enter for today): ",
) -> date:
    """Prompt for a date in ISO format, defaulting to today if blank."""
    while True:
        val = input(prompt).strip()
        if not val:
            return date.today()
        try:
            return datetime.strptime(val, "%Y-%m-%d").date()
        except ValueError:
            print("  Invalid format. Please use YYYY-MM-DD.")


def prompt_nutrition_entry() -> NutritionLog:
    """Interactively collect a nutrition log entry."""
    d = prompt_date()
    calories = prompt_float("Calories: ", min_val=0.0)
    protein = prompt_float("Protein (g): ", min_val=0.0)
    carbs = prompt_float("Carbs (g): ", min_val=0.0)
    fats = prompt_float("Fats (g): ", min_val=0.0)
    notes = input("Notes (optional): ").strip()
    return NutritionLog(
        date=d,
        calories=calories,
        protein_g=protein,
        carbs_g=carbs,
        fats_g=fats,
        notes=notes,
    )


def prompt_lift_entry() -> LiftLog:
    """Interactively collect a lift log entry."""
    d = prompt_date()
    exercise = input("Exercise name: ").strip()
    weight = prompt_float("Weight: ", min_val=0.1)
    reps = prompt_int("Reps: ", min_val=1)
    unit_str = prompt_choice("Unit", [u.value for u in WeightUnit])
    return LiftLog(
        date=d,
        exercise=exercise,
        weight=weight,
        reps=reps,
        unit=WeightUnit(unit_str),
    )


def prompt_date_range() -> tuple[date | None, date | None]:
    """Prompt for optional start/end dates for filtering."""
    start_str = input("Start date (YYYY-MM-DD or Enter for none): ").strip()
    start_date = datetime.strptime(start_str, "%Y-%m-%d").date() if start_str else None
    end_str = input("End date (YYYY-MM-DD or Enter for none): ").strip()
    end_date = datetime.strptime(end_str, "%Y-%m-%d").date() if end_str else None
    return start_date, end_date
