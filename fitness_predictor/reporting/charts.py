from __future__ import annotations
import os
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from datetime import timedelta

from fitness_predictor.models import NutritionLog, LiftLog, MacroTarget

def plot_nutrition_trend(logs: list[NutritionLog], targets: MacroTarget | None = None, days: int = 30, save_path: str | None = None) -> str:
    if not logs:
        return ""
    
    if save_path is None:
        save_path = "data/charts/nutrition_trend.png"
        
    os.makedirs(os.path.dirname(os.path.abspath(save_path)), exist_ok=True)
    
    logs.sort(key=lambda x: x.date)
    end_date = logs[-1].date
    start_date = end_date - timedelta(days=days)
    
    recent_logs = [log for log in logs if log.date >= start_date]
    if not recent_logs:
        return ""
        
    daily_cal = {}
    for log in recent_logs:
        daily_cal[log.date] = daily_cal.get(log.date, 0) + log.calories
        
    dates = sorted(list(daily_cal.keys()))
    calories = [daily_cal[d] for d in dates]
    
    plt.figure(figsize=(10, 6))
    plt.plot(dates, calories, marker='o', label="Calories")
    
    if targets:
        plt.axhline(y=targets.calories, color='r', linestyle='--', label="Target")
        
    plt.title("Nutrition Trend (Calories)")
    plt.xlabel("Date")
    plt.ylabel("Calories")
    plt.xticks(rotation=45)
    plt.legend()
    plt.tight_layout()
    plt.savefig(save_path)
    plt.close()
    
    return save_path

def plot_1rm_progression(exercise: str, lift_logs: list[LiftLog], save_path: str | None = None) -> str:
    if save_path is None:
        save_path = f"data/charts/{exercise}_1rm.png"
        
    os.makedirs(os.path.dirname(os.path.abspath(save_path)), exist_ok=True)
    
    filtered = [log for log in lift_logs if log.exercise.lower() == exercise.lower()]
    if not filtered:
        return ""
        
    filtered.sort(key=lambda x: x.date)
    dates = [log.date for log in filtered]
    orms = [log.estimated_1rm for log in filtered]
    
    plt.figure(figsize=(10, 6))
    plt.plot(dates, orms, marker='o', color='b')
    plt.title(f"{exercise.capitalize()} - Estimated 1RM Progression")
    plt.xlabel("Date")
    plt.ylabel("Estimated 1RM")
    plt.xticks(rotation=45)
    plt.grid(True)
    plt.tight_layout()
    plt.savefig(save_path)
    plt.close()
    
    return save_path

def plot_macro_pie(calories: float, protein_g: float, carbs_g: float, fats_g: float, save_path: str | None = None) -> str:
    if save_path is None:
        save_path = "data/charts/macro_pie.png"
        
    os.makedirs(os.path.dirname(os.path.abspath(save_path)), exist_ok=True)
    
    p_cal = protein_g * 4
    c_cal = carbs_g * 4
    f_cal = fats_g * 9
    
    labels = ['Protein', 'Carbs', 'Fats']
    sizes = [p_cal, c_cal, f_cal]
    colors = ['#ff9999','#66b3ff','#99ff99']
    
    plt.figure(figsize=(8, 8))
    plt.pie(sizes, labels=labels, colors=colors, autopct='%1.1f%%', startangle=90)
    plt.title("Macronutrient Distribution")
    plt.axis('equal')
    plt.tight_layout()
    plt.savefig(save_path)
    plt.close()
    
    return save_path
