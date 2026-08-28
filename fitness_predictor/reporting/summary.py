"""Daily and weekly nutrition summary reports.

Compares actual logged intake against calculated macro targets and shows
compliance metrics.
"""

from __future__ import annotations

from datetime import date, timedelta

from tabulate import tabulate

from fitness_predictor.models import MacroTarget, NutritionLog


def format_macro_breakdown(
    calories: float, protein_g: float, carbs_g: float, fats_g: float
) -> str:
    """One-line compact macro summary."""
    return (
        f"Cal: {calories:.0f} | P: {protein_g:.0f}g | "
        f"C: {carbs_g:.0f}g | F: {fats_g:.0f}g"
    )


def daily_summary(
    log_date: date,
    logs: list[NutritionLog],
    targets: MacroTarget | None = None,
) -> str:
    """Generate a daily intake summary table.

    Args:
        log_date: The date to summarise.
        logs: All nutrition log entries (will be filtered to *log_date*).
        targets: Optional macro targets for comparison columns.

    Returns:
        Formatted text table.
    """
    day_logs = [log for log in logs if log.date == log_date]
    if not day_logs:
        return f"No entries found for {log_date}"

    total_cal = sum(log.calories for log in day_logs)
    total_p = sum(log.protein_g for log in day_logs)
    total_c = sum(log.carbs_g for log in day_logs)
    total_f = sum(log.fats_g for log in day_logs)

    rows: list[list[str]] = []
    headers = ["Metric", "Actual"]

    if targets:
        headers.extend(["Target", "Delta"])
        rows.append(["Calories", f"{total_cal:.0f}", f"{targets.calories:.0f}",
                      f"{total_cal - targets.calories:+.0f}"])
        rows.append(["Protein (g)", f"{total_p:.0f}", f"{targets.protein_g:.0f}",
                      f"{total_p - targets.protein_g:+.0f}"])
        rows.append(["Carbs (g)", f"{total_c:.0f}", f"{targets.carbs_g:.0f}",
                      f"{total_c - targets.carbs_g:+.0f}"])
        rows.append(["Fats (g)", f"{total_f:.0f}", f"{targets.fats_g:.0f}",
                      f"{total_f - targets.fats_g:+.0f}"])
    else:
        rows.append(["Calories", f"{total_cal:.0f}"])
        rows.append(["Protein (g)", f"{total_p:.0f}"])
        rows.append(["Carbs (g)", f"{total_c:.0f}"])
        rows.append(["Fats (g)", f"{total_f:.0f}"])

    title = f"\n  Daily Summary — {log_date}\n"
    return title + tabulate(rows, headers=headers, tablefmt="grid")


def weekly_summary(
    start_date: date,
    logs: list[NutritionLog],
    targets: MacroTarget | None = None,
) -> str:
    """Generate a 7-day nutrition summary with averages and compliance.

    Args:
        start_date: First day of the week to report.
        logs: All nutrition log entries (filtered internally).
        targets: Optional macro targets for compliance calculation.

    Returns:
        Formatted text report.
    """
    end_date = start_date + timedelta(days=6)
    week_logs = [log for log in logs if start_date <= log.date <= end_date]

    header_str = f"\n  Weekly Summary: {start_date} → {end_date}\n\n"
    if not week_logs:
        return header_str + "  No entries found for this week."

    # Aggregate by day
    daily: dict[date, dict[str, float]] = {}
    for log in week_logs:
        if log.date not in daily:
            daily[log.date] = {"cal": 0.0, "p": 0.0, "c": 0.0, "f": 0.0}
        daily[log.date]["cal"] += log.calories
        daily[log.date]["p"] += log.protein_g
        daily[log.date]["c"] += log.carbs_g
        daily[log.date]["f"] += log.fats_g

    # Build day-by-day table
    compliance_days = 0
    rows: list[list[str]] = []
    for i in range(7):
        d = start_date + timedelta(days=i)
        if d in daily:
            dt = daily[d]
            cal, p, c, f = dt["cal"], dt["p"], dt["c"], dt["f"]
            if targets and (targets.calories * 0.9) <= cal <= (targets.calories * 1.1):
                compliance_days += 1
            rows.append([str(d), f"{cal:.0f}", f"{p:.0f}", f"{c:.0f}", f"{f:.0f}"])
        else:
            rows.append([str(d), "—", "—", "—", "—"])

    days_logged = len(daily)
    avg_cal = sum(dt["cal"] for dt in daily.values()) / days_logged if days_logged else 0

    summary_lines = [f"  Days logged: {days_logged}/7"]
    summary_lines.append(f"  Average calories: {avg_cal:.0f}")
    if targets and days_logged:
        pct = compliance_days / days_logged * 100
        summary_lines.append(f"  Target compliance (±10 % cal): {pct:.0f} %")
    summary_lines.append("")

    headers = ["Date", "Calories", "Protein", "Carbs", "Fats"]
    return (
        header_str
        + "\n".join(summary_lines)
        + "\n"
        + tabulate(rows, headers=headers, tablefmt="grid")
    )
