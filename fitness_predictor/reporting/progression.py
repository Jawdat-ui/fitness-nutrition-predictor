"""Lift progression tracking and personal records.

Provides text-based tables showing 1RM estimates over time for individual
exercises and a cross-exercise summary of personal records.
"""

from __future__ import annotations

from tabulate import tabulate

from fitness_predictor.models import LiftLog


def lift_progression(exercise: str, lift_logs: list[LiftLog]) -> str:
    """Generate a chronological table of 1RM estimates for an exercise.

    Args:
        exercise: Exercise name (case-insensitive match).
        lift_logs: All lift log entries (filtered internally).

    Returns:
        Formatted text table, or a message if no data found.
    """
    filtered = [
        log for log in lift_logs
        if log.exercise.lower() == exercise.lower()
    ]
    if not filtered:
        return f"No entries found for {exercise}"

    filtered.sort(key=lambda x: x.date)
    rows = []
    for log in filtered:
        est = f"{log.estimated_1rm:.1f}" if log.estimated_1rm is not None else "—"
        rows.append([
            str(log.date),
            f"{log.weight} {log.unit.value}",
            log.reps,
            f"{est} {log.unit.value}",
        ])

    headers = ["Date", "Weight", "Reps", "Est. 1RM"]
    title = f"\n  {exercise} — Progression\n"
    return title + tabulate(rows, headers=headers, tablefmt="grid")


def all_lifts_summary(lift_logs: list[LiftLog]) -> str:
    """Show the best estimated 1RM for every exercise in the logs.

    Args:
        lift_logs: All lift log entries.

    Returns:
        Formatted text table of personal records.
    """
    if not lift_logs:
        return "No lift entries logged yet."

    prs = personal_records(lift_logs)
    rows = []
    for exercise, log in sorted(prs.items()):
        est = f"{log.estimated_1rm:.1f}" if log.estimated_1rm is not None else "—"
        rows.append([
            exercise.title(),
            f"{est} {log.unit.value}",
            str(log.date),
            f"{log.weight} × {log.reps}",
        ])

    headers = ["Exercise", "Best 1RM", "Date", "Weight × Reps"]
    title = "\n  All Lifts — Personal Records\n"
    return title + tabulate(rows, headers=headers, tablefmt="grid")


def personal_records(lift_logs: list[LiftLog]) -> dict[str, LiftLog]:
    """Return the LiftLog with the highest estimated 1RM per exercise.

    Args:
        lift_logs: All lift log entries.

    Returns:
        Dict mapping lowercase exercise name → best LiftLog.
    """
    prs: dict[str, LiftLog] = {}
    for log in lift_logs:
        if log.estimated_1rm is None:
            continue
        ex = log.exercise.lower()
        if ex not in prs or (
            prs[ex].estimated_1rm is not None
            and log.estimated_1rm > prs[ex].estimated_1rm
        ):
            prs[ex] = log
    return prs
