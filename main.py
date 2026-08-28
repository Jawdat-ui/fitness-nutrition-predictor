#!/usr/bin/env python3
"""Fitness & Nutrition Predictor — CLI entry point.

Provides both an interactive menu-driven interface and direct argparse
commands for daily nutrition logging, 1RM calculations, macro predictions,
and progress reporting.

Usage:
    python main.py                    # Interactive menu
    python main.py log nutrition      # Log a nutrition entry
    python main.py log lift           # Log a lift entry
    python main.py predict macros     # Show calorie/macro targets
    python main.py calc 1rm           # One-rep-max calculator
    python main.py report daily       # Daily intake report
    python main.py report weekly      # Weekly intake report
    python main.py report lifts       # Lift progression summary
    python main.py profile            # View / update profile
"""

from __future__ import annotations

import argparse
import sys
from datetime import date, timedelta

from fitness_predictor.models import (
    WeightUnit,
    UserProfile,
)
from fitness_predictor.input.biometrics import (
    display_profile,
    load_or_create_profile,
    prompt_edit_profile,
)
from fitness_predictor.input.data_entry import (
    prompt_choice,
    prompt_date,
    prompt_float,
    prompt_int,
    prompt_lift_entry,
    prompt_nutrition_entry,
    prompt_date_range,
)
from fitness_predictor.prediction.calorie_model import calculate_macro_targets
from fitness_predictor.prediction.one_rep_max import calculate_1rm
from fitness_predictor.prediction.rep_percentage import format_rep_table, suggested_working_weight
from fitness_predictor.prediction.strength_standards import (
    format_standards_comparison,
    get_supported_exercises,
    normalize_exercise_name,
)
from fitness_predictor.reporting.summary import daily_summary, weekly_summary
from fitness_predictor.reporting.progression import all_lifts_summary, lift_progression
from fitness_predictor.reporting.charts import (
    plot_nutrition_trend,
    plot_1rm_progression,
    plot_macro_pie,
)
from fitness_predictor.storage.json_storage import JsonStorage


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

BANNER = r"""
 _____ _ _                       _   _       _        _ _   _
|  ___(_) |_ _ __   ___  ___ ___| \ | |_   _| |_ _ __(_) |_(_) ___  _ __
| |_  | | __| '_ \ / _ \/ __/ __|  \| | | | | __| '__| | __| |/ _ \| '_ \
|  _| | | |_| | | |  __/\__ \__ \ |\  | |_| | |_| |  | | |_| | (_) | | | |
|_|   |_|\__|_| |_|\___||___/___/_| \_|\__,_|\__|_|  |_|\__|_|\___/|_| |_|
                 ____               _ _      _
                |  _ \ _ __ ___  __| (_) ___| |_ ___  _ __
                | |_) | '__/ _ \/ _` | |/ __| __/ _ \| '__|
                |  __/| | |  __/ (_| | | (__| || (_) | |
                |_|   |_|  \___|\__,_|_|\___|\__\___/|_|
"""

MENU = """
========== Fitness & Nutrition Predictor ==========
  1. Log Nutrition
  2. Log Lift
  3. View / Edit Past Nutrition Entries
  4. Predict Calorie & Macro Targets
  5. Calculate One-Rep Max
  6. View Reports
  7. View / Update Profile
  8. Generate Charts
  0. Exit
====================================================
"""


def _divider(title: str = "") -> None:
    """Print a section divider."""
    if title:
        print(f"\n{'─' * 20} {title} {'─' * 20}")
    else:
        print(f"\n{'─' * 54}")


# ---------------------------------------------------------------------------
# Menu Actions
# ---------------------------------------------------------------------------

def action_log_nutrition(storage: JsonStorage) -> None:
    """Log a daily nutrition entry."""
    _divider("Log Nutrition")
    entry = prompt_nutrition_entry()
    storage.save_nutrition_log(entry)
    print(f"\n✓ Nutrition entry saved for {entry.date}.")
    print(f"  Calories: {entry.calories:.0f} kcal | "
          f"P: {entry.protein_g:.0f}g | C: {entry.carbs_g:.0f}g | F: {entry.fats_g:.0f}g")


def action_log_lift(storage: JsonStorage, profile: UserProfile | None = None) -> None:
    """Log a lift entry with automatic 1RM estimation."""
    _divider("Log Lift")
    entry = prompt_lift_entry()

    # Calculate 1RM
    nutrition_logs = storage.load_nutrition_logs()
    result = calculate_1rm(
        weight=entry.weight,
        reps=entry.reps,
        unit=entry.unit,
        exercise=entry.exercise,
        profile=profile,
        nutrition_logs=nutrition_logs if nutrition_logs else None,
    )
    entry.estimated_1rm = result.average_1rm
    storage.save_lift_log(entry)

    print(f"\n✓ Lift entry saved: {entry.exercise}")
    print(f"  {entry.weight} {entry.unit.value} × {entry.reps} reps")
    print(f"  Estimated 1RM: {result.average_1rm:.1f} {entry.unit.value}")
    if result.flagged_formulas:
        print(f"  ⚠ Formulas disagreeing by >5%: {', '.join(result.flagged_formulas)}")


def action_view_edit_nutrition(storage: JsonStorage) -> None:
    """View and optionally edit/delete past nutrition entries."""
    _divider("Past Nutrition Entries")
    start, end = prompt_date_range()
    logs = storage.load_nutrition_logs(start_date=start, end_date=end)

    if not logs:
        print("No entries found for the specified date range.")
        return

    from tabulate import tabulate
    rows = []
    for i, log in enumerate(logs, 1):
        rows.append([
            i, log.date, f"{log.calories:.0f}", f"{log.protein_g:.0f}",
            f"{log.carbs_g:.0f}", f"{log.fats_g:.0f}", log.notes or "—",
        ])
    print(tabulate(rows, headers=["#", "Date", "Calories", "Protein(g)",
                                   "Carbs(g)", "Fats(g)", "Notes"],
                   tablefmt="simple"))

    action = prompt_choice(
        "\nAction",
        ["Go back", "Edit an entry", "Delete an entry"],
    )
    if action == "Edit an entry":
        idx = prompt_int("Entry # to edit: ", min_val=1, max_val=len(logs)) - 1
        target_log = logs[idx]
        print(f"\nEditing entry for {target_log.date} — enter new values "
              "(press Enter to keep current):")
        updated = prompt_nutrition_entry()
        if storage.update_nutrition_log(target_log.date, updated):
            print("✓ Entry updated.")
        else:
            print("✗ Could not find the entry to update.")
    elif action == "Delete an entry":
        idx = prompt_int("Entry # to delete: ", min_val=1, max_val=len(logs)) - 1
        target_log = logs[idx]
        if storage.delete_nutrition_log(target_log.date):
            print(f"✓ Entry for {target_log.date} deleted.")
        else:
            print("✗ Could not find the entry to delete.")


def action_predict_macros(storage: JsonStorage, profile: UserProfile) -> None:
    """Calculate and display recommended calorie/macro targets."""
    _divider("Calorie & Macro Targets")
    display_profile(profile)

    targets = calculate_macro_targets(profile)
    print(f"\n  BMR:  {targets.bmr:.0f} kcal")
    print(f"  TDEE: {targets.tdee:.0f} kcal")
    print(f"\n  ── Daily Targets ({profile.goal.value.upper()}) ──")
    print(f"  Calories: {targets.calories:.0f} kcal")
    print(f"  Protein:  {targets.protein_g:.0f} g")
    print(f"  Carbs:    {targets.carbs_g:.0f} g")
    print(f"  Fats:     {targets.fats_g:.0f} g")


def action_calculate_1rm(storage: JsonStorage, profile: UserProfile | None = None) -> None:
    """Full 1RM calculator with rep table and optional strength standards."""
    _divider("One-Rep Max Calculator")

    exercise = input("Exercise name: ").strip()
    weight = prompt_float("Weight lifted: ", min_val=0.1)
    reps = prompt_int("Reps performed: ", min_val=1, max_val=50)
    unit_str = prompt_choice("Unit", ["lb", "kg"])
    unit = WeightUnit.LB if unit_str == "lb" else WeightUnit.KG

    nutrition_logs = storage.load_nutrition_logs()
    result = calculate_1rm(
        weight=weight,
        reps=reps,
        unit=unit,
        exercise=exercise,
        profile=profile,
        nutrition_logs=nutrition_logs if nutrition_logs else None,
    )

    print(f"\n  ── 1RM Estimates for {exercise} ──")
    print(f"  Epley:     {result.epley:.1f} {unit.value}")
    print(f"  Brzycki:   {result.brzycki:.1f} {unit.value}")
    print(f"  Lombardi:  {result.lombardi:.1f} {unit.value}")
    print(f"  McGlothin: {result.mcglothin:.1f} {unit.value}")
    print(f"  O'Conner:  {result.oconner:.1f} {unit.value}")
    print(f"\n  Average 1RM: {result.average_1rm:.1f} {unit.value}")

    if result.adjusted_1rm is not None:
        print(f"  Adjusted 1RM (biometrics): {result.adjusted_1rm:.1f} {unit.value}")

    if result.flagged_formulas:
        print(f"\n  ⚠ Formulas disagreeing by >5%: {', '.join(result.flagged_formulas)}")

    # Rep percentage table
    print(f"\n{format_rep_table(result.average_1rm, unit)}")

    # Suggested working weight
    target = prompt_int("Target reps for working weight (0 to skip): ",
                        min_val=0, max_val=30)
    if target > 0:
        working = suggested_working_weight(result.average_1rm, target)
        print(f"\n  Suggested working weight for {target} reps: "
              f"{working:.1f} {unit.value}")

    # Strength standards comparison
    if profile:
        normalized = normalize_exercise_name(exercise)
        if normalized:
            show_std = prompt_choice("Show strength standards comparison?",
                                     ["Yes", "No"])
            if show_std == "Yes":
                comparison = format_standards_comparison(
                    normalized, result.average_1rm,
                    profile.weight_kg, profile.sex, unit,
                )
                print(f"\n{comparison}")
        else:
            supported = get_supported_exercises()
            print(f"\n  ℹ Strength standards available for: {', '.join(supported)}")


def action_reports(storage: JsonStorage, profile: UserProfile | None = None) -> None:
    """Display daily/weekly reports or lift progression."""
    _divider("Reports")
    choice = prompt_choice(
        "Report type",
        ["Daily nutrition", "Weekly nutrition", "Lift progression", "All lifts summary"],
    )

    targets = None
    if profile:
        from fitness_predictor.prediction.calorie_model import calculate_macro_targets
        targets = calculate_macro_targets(profile)

    if choice == "Daily nutrition":
        report_date = prompt_date("Report date (YYYY-MM-DD or Enter for today): ")
        logs = storage.load_nutrition_logs()
        print(daily_summary(report_date, logs, targets))

    elif choice == "Weekly nutrition":
        start = prompt_date("Week start date (YYYY-MM-DD or Enter for today): ")
        logs = storage.load_nutrition_logs()
        print(weekly_summary(start, logs, targets))

    elif choice == "Lift progression":
        exercise = input("Exercise name: ").strip()
        lift_logs = storage.load_lift_logs(exercise=exercise)
        print(lift_progression(exercise, lift_logs))

    elif choice == "All lifts summary":
        lift_logs = storage.load_lift_logs()
        print(all_lifts_summary(lift_logs))


def action_profile(storage: JsonStorage) -> UserProfile:
    """View or update the user profile."""
    _divider("Profile")
    profile = storage.load_profile()
    if profile:
        display_profile(profile)
        action = prompt_choice("Action", ["Go back", "Edit profile"])
        if action == "Edit profile":
            profile = prompt_edit_profile(profile)
            storage.save_profile(profile)
            print("✓ Profile updated.")
    else:
        print("No profile found. Let's create one.")
        profile = load_or_create_profile(storage)
    return profile


def action_charts(storage: JsonStorage, profile: UserProfile | None = None) -> None:
    """Generate and save trend charts."""
    _divider("Generate Charts")
    choice = prompt_choice(
        "Chart type",
        ["Nutrition trend", "1RM progression", "Macro pie chart"],
    )

    targets = None
    if profile:
        from fitness_predictor.prediction.calorie_model import calculate_macro_targets
        targets = calculate_macro_targets(profile)

    if choice == "Nutrition trend":
        days = prompt_int("Number of days to chart (default 30): ",
                          min_val=1, max_val=365)
        logs = storage.load_nutrition_logs()
        path = plot_nutrition_trend(logs, targets, days=days)
        print(f"✓ Chart saved to: {path}")

    elif choice == "1RM progression":
        exercise = input("Exercise name: ").strip()
        lift_logs = storage.load_lift_logs(exercise=exercise)
        path = plot_1rm_progression(exercise, lift_logs)
        print(f"✓ Chart saved to: {path}")

    elif choice == "Macro pie chart":
        if targets:
            path = plot_macro_pie(
                targets.calories, targets.protein_g,
                targets.carbs_g, targets.fats_g,
            )
            print(f"✓ Chart saved to: {path}")
        else:
            print("⚠ No profile found — cannot calculate macro targets for pie chart.")
            print("  Set up a profile first (option 7).")


# ---------------------------------------------------------------------------
# Interactive Menu Loop
# ---------------------------------------------------------------------------

def interactive_menu() -> None:
    """Run the interactive menu-driven interface."""
    print(BANNER)

    storage = JsonStorage()
    profile = storage.load_profile()

    if not profile:
        print("Welcome! Let's set up your profile first.\n")
        profile = load_or_create_profile(storage)

    while True:
        print(MENU)
        try:
            choice = input("Select an option: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye!")
            break

        if choice == "0":
            print("\nGoodbye! Keep pushing those limits 💪")
            break
        elif choice == "1":
            action_log_nutrition(storage)
        elif choice == "2":
            action_log_lift(storage, profile)
        elif choice == "3":
            action_view_edit_nutrition(storage)
        elif choice == "4":
            if profile:
                action_predict_macros(storage, profile)
            else:
                print("⚠ Please set up your profile first (option 7).")
        elif choice == "5":
            action_calculate_1rm(storage, profile)
        elif choice == "6":
            action_reports(storage, profile)
        elif choice == "7":
            profile = action_profile(storage)
        elif choice == "8":
            action_charts(storage, profile)
        else:
            print("Invalid option. Please try again.")


# ---------------------------------------------------------------------------
# Argparse CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    """Build the argparse CLI parser."""
    parser = argparse.ArgumentParser(
        prog="fitness-predictor",
        description="Fitness & Nutrition Predictor — track nutrition and "
                    "predict strength metrics",
    )
    subparsers = parser.add_subparsers(dest="command")

    # log
    log_parser = subparsers.add_parser("log", help="Log nutrition or lift data")
    log_sub = log_parser.add_subparsers(dest="log_type")
    log_sub.add_parser("nutrition", help="Log a nutrition entry")
    log_sub.add_parser("lift", help="Log a lift entry")

    # predict
    pred_parser = subparsers.add_parser("predict", help="Predict targets")
    pred_sub = pred_parser.add_subparsers(dest="pred_type")
    pred_sub.add_parser("macros", help="Show calorie/macro targets")

    # calc
    calc_parser = subparsers.add_parser("calc", help="Calculators")
    calc_sub = calc_parser.add_subparsers(dest="calc_type")
    calc_sub.add_parser("1rm", help="One-rep-max calculator")

    # report
    report_parser = subparsers.add_parser("report", help="View reports")
    report_sub = report_parser.add_subparsers(dest="report_type")
    report_sub.add_parser("daily", help="Daily nutrition report")
    report_sub.add_parser("weekly", help="Weekly nutrition report")
    report_sub.add_parser("lifts", help="Lift progression summary")

    # profile
    subparsers.add_parser("profile", help="View / update profile")

    return parser


def cli_main(args: argparse.Namespace) -> None:
    """Handle argparse-based CLI commands."""
    storage = JsonStorage()
    profile = storage.load_profile()

    if args.command == "log":
        if args.log_type == "nutrition":
            action_log_nutrition(storage)
        elif args.log_type == "lift":
            action_log_lift(storage, profile)
        else:
            print("Usage: fitness-predictor log {nutrition|lift}")

    elif args.command == "predict":
        if args.pred_type == "macros":
            if profile:
                action_predict_macros(storage, profile)
            else:
                print("⚠ No profile found. Run: fitness-predictor profile")
        else:
            print("Usage: fitness-predictor predict macros")

    elif args.command == "calc":
        if args.calc_type == "1rm":
            action_calculate_1rm(storage, profile)
        else:
            print("Usage: fitness-predictor calc 1rm")

    elif args.command == "report":
        if args.report_type == "daily":
            targets = calculate_macro_targets(profile) if profile else None
            report_date = prompt_date()
            logs = storage.load_nutrition_logs()
            print(daily_summary(report_date, logs, targets))
        elif args.report_type == "weekly":
            targets = calculate_macro_targets(profile) if profile else None
            start = prompt_date("Week start date (YYYY-MM-DD or Enter for today): ")
            logs = storage.load_nutrition_logs()
            print(weekly_summary(start, logs, targets))
        elif args.report_type == "lifts":
            lift_logs = storage.load_lift_logs()
            print(all_lifts_summary(lift_logs))
        else:
            print("Usage: fitness-predictor report {daily|weekly|lifts}")

    elif args.command == "profile":
        profile = action_profile(storage)

    else:
        interactive_menu()


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    """Application entry point."""
    parser = build_parser()
    args = parser.parse_args()

    if args.command:
        cli_main(args)
    else:
        interactive_menu()


if __name__ == "__main__":
    main()
