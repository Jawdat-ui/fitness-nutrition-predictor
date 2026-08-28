# Fitness & Nutrition Predictor

Fitness & Nutrition Predictor — a modular Python CLI for daily nutrition logging, predictive calorie/macro modeling, one-rep-max calculations, and progress reporting.

## Features
- Daily nutrition logging (calories, protein, carbs, fats) with persistent storage
- Predictive calorie/macro model using Mifflin-St Jeor BMR equation
- One-rep-max calculator using 5 established formulas (Epley, Brzycki, Lombardi, McGlothin, O'Conner)
- Rep percentage table (1-30 reps mapped to % of 1RM)
- Strength level benchmarking (beginner to elite, like strengthlevel.com)
- Daily/weekly reports comparing actual vs. target intake
- 1RM progression tracking over time
- Matplotlib charts for trends

## Quick Start
```bash
git clone https://github.com/YOUR_USERNAME/fitness-nutrition-predictor.git
cd fitness-nutrition-predictor
pip install -r requirements.txt
python main.py
```

## CLI Commands
Show the full list:
- `python main.py` — interactive menu
- `python main.py log nutrition` — log a nutrition entry
- `python main.py log lift` — log a lift entry
- `python main.py predict macros` — show calorie/macro targets
- `python main.py calc 1rm` — 1RM calculator
- `python main.py report daily` — daily report
- `python main.py report weekly` — weekly report
- `python main.py report lifts` — lift progression
- `python main.py profile` — view/update profile

## Project Structure
```text
fitness-nutrition-predictor/
├── README.md
├── requirements.txt
├── setup.py
├── .gitignore
├── main.py                                  # CLI entry point
├── fitness_predictor/
│   ├── __init__.py
│   ├── models.py                            # Pydantic models & enums
│   ├── input/
│   │   ├── __init__.py
│   │   ├── data_entry.py                    # Interactive prompts & validation
│   │   └── biometrics.py                    # Profile management
│   ├── prediction/
│   │   ├── __init__.py
│   │   ├── calorie_model.py                 # BMR, TDEE, macro targets
│   │   ├── one_rep_max.py                   # 5 × 1RM formulas + averaging
│   │   ├── rep_percentage.py                # Rep → % of 1RM table
│   │   └── strength_standards.py            # Strength level benchmarks
│   ├── reporting/
│   │   ├── __init__.py
│   │   ├── summary.py                       # Daily/weekly intake reports
│   │   ├── progression.py                   # 1RM progression over time
│   │   └── charts.py                        # Matplotlib trend charts
│   └── storage/
│       ├── __init__.py
│       ├── base.py                          # StorageBackend Protocol
│       ├── json_storage.py                  # JSON file backend (default)
│       └── csv_storage.py                   # CSV file backend
├── tests/
│   ├── __init__.py
│   ├── test_models.py
│   ├── test_calorie_model.py
│   ├── test_one_rep_max.py
│   ├── test_rep_percentage.py
│   ├── test_strength_standards.py
│   └── test_storage.py
└── data/                                    # Created at runtime
```

## How the Formulas Work

### BMR (Mifflin-St Jeor Equation)
The basal metabolic rate (BMR) represents the number of calories your body needs to maintain basic life-sustaining functions. This app uses the Mifflin-St Jeor equation:
- **Male**: `BMR = (10 × weight in kg) + (6.25 × height in cm) − (5 × age in years) + 5`
- **Female**: `BMR = (10 × weight in kg) + (6.25 × height in cm) − (5 × age in years) − 161`

### TDEE (Total Daily Energy Expenditure)
Calculated by multiplying BMR by an activity multiplier:
| Activity Level | Multiplier |
|---|---|
| Sedentary | 1.2 |
| Lightly Active | 1.375 |
| Moderately Active | 1.55 |
| Very Active | 1.725 |
| Extra Active | 1.9 |

### Goal Adjustment
Based on the user's goal, the TDEE is adjusted to calculate the daily calorie target:
- **Bulk**: +400 kcal
- **Cut**: -400 kcal
- **Maintain**: 0 kcal

### Macro Split
The application uses the following logic to distribute daily calories into macronutrients:
- **Protein**: 1.0 g/lb of body weight when cutting, or 0.8 g/lb when bulking/maintaining.
- **Fats**: 25% of total daily calories.
- **Carbs**: The remaining calories are allocated to carbohydrates.

### One-Rep Max Formulas
The one-rep-max (1RM) calculator estimates the maximum weight you can lift for a single repetition based on the weight lifted (`w`) and reps completed (`r`). It uses 5 formulas:
- **Epley**: `1RM = w × (1 + r/30)`
- **Brzycki**: `1RM = w × 36 / (37 − r)`
- **Lombardi**: `1RM = w × r^0.10`
- **McGlothin**: `1RM = w × 100 / (101.3 − 2.67123 × r)`
- **O'Conner**: `1RM = w × (1 + 0.025 × r)`

The app averages all 5 formulas and flags any individual result that disagrees with the average by more than 5%.

### Repetition Percentage Table
Based on NSCA guidelines and standard rep-percentage charts, this table maps 1-30 reps to a percentage of your 1RM, allowing you to find working weights for specific target rep ranges.

Sample Snippet:
| Reps | % of 1RM |
|------|----------|
| 1 | 100% |
| 2 | 97% |
| 3 | 94% |
| 4 | 92% |
| 5 | 89% |
| 6 | 86% |
| 7 | 83% |
| 8 | 81% |
| 9 | 78% |
| 10 | 75% |

### Strength Standards
The app benchmarks user strength against bodyweight ratios for 5 compound lifts (Bench Press, Squat, Deadlift, Overhead Press, Barbell Row) across 5 levels (Beginner through Elite). These represent approximate population-level standards.

## Running Tests
```bash
pip install pytest
pytest tests/ -v
```

## Architecture Notes
The application features a modular design with clear separation of concerns: `input/`, `prediction/`, `reporting/`, and `storage/`. The storage backend is abstracted, meaning you can easily swap the default JSON storage for a CSV or SQLite implementation. The code is structured efficiently so a web frontend (such as Flask or Streamlit) can be bolted on later without altering the core logic.

## License
MIT License
