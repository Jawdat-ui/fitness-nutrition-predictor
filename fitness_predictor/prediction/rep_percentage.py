from __future__ import annotations
from fitness_predictor.models import WeightUnit
from tabulate import tabulate

REP_PERCENTAGES: dict[int, float] = {
    1: 100.0, 2: 97.0, 3: 94.0, 4: 92.0, 5: 89.0, 6: 86.0, 7: 83.0, 8: 81.0, 9: 78.0, 10: 75.0,
    11: 73.0, 12: 71.0, 13: 70.0, 14: 68.0, 15: 67.0, 16: 65.0, 17: 64.0, 18: 63.0, 19: 61.0, 20: 60.0,
    21: 59.0, 22: 58.0, 23: 57.0, 24: 56.0, 25: 55.0, 26: 54.0, 27: 53.0, 28: 52.0, 29: 51.0, 30: 50.0
}

def get_rep_percentage(reps: int) -> float:
    if reps < 1:
        raise ValueError("Reps must be at least 1")
    if reps > 30:
        return 50.0
    return REP_PERCENTAGES[reps]

def generate_rep_table(one_rm: float, unit: WeightUnit = WeightUnit.LB) -> list[tuple[int, float, float]]:
    return [(r, pct, one_rm * pct / 100.0) for r, pct in REP_PERCENTAGES.items()]

def suggested_working_weight(one_rm: float, target_reps: int) -> float:
    pct = get_rep_percentage(target_reps)
    return one_rm * pct / 100.0

def format_rep_table(one_rm: float, unit: WeightUnit = WeightUnit.LB) -> str:
    table_data = generate_rep_table(one_rm, unit)
    headers = ["Reps", "% of 1RM", f"Weight ({unit.value})"]
    return tabulate(table_data, headers=headers, floatfmt=".1f", tablefmt="grid")
