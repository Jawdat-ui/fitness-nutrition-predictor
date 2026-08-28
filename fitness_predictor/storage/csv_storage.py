from __future__ import annotations

import csv
import json
from datetime import date
from pathlib import Path

from fitness_predictor.models import LiftLog, NutritionLog, UserProfile


class CsvStorage:
    def __init__(self, data_dir: str | Path = 'data') -> None:
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.profile_path = self.data_dir / 'profile.csv'
        self.nutrition_logs_path = self.data_dir / 'nutrition_logs.csv'
        self.lift_logs_path = self.data_dir / 'lift_logs.csv'

    def save_profile(self, profile: UserProfile) -> None:
        data = profile.model_dump(mode='json')
        with open(self.profile_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=list(data.keys()))
            writer.writeheader()
            writer.writerow({k: (json.dumps(v) if isinstance(v, (list, dict)) else v) for k, v in data.items()})

    def load_profile(self) -> UserProfile | None:
        if not self.profile_path.exists():
            return None
        try:
            with open(self.profile_path, 'r', newline='', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                rows = list(reader)
                if not rows:
                    return None
                data = rows[0]
                # Try to parse JSON fields
                parsed_data = {}
                for k, v in data.items():
                    try:
                        parsed_data[k] = json.loads(v)
                    except (ValueError, TypeError):
                        parsed_data[k] = v
                return UserProfile.model_validate(parsed_data)
        except Exception:
            return None

    def _load_all_nutrition_logs(self) -> list[NutritionLog]:
        if not self.nutrition_logs_path.exists():
            return []
        try:
            logs = []
            with open(self.nutrition_logs_path, 'r', newline='', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    parsed_row = {}
                    for k, v in row.items():
                        try:
                            parsed_row[k] = json.loads(v)
                        except (ValueError, TypeError):
                            parsed_row[k] = v
                    logs.append(NutritionLog.model_validate(parsed_row))
            return logs
        except Exception:
            return []

    def _save_all_nutrition_logs(self, logs: list[NutritionLog]) -> None:
        if not logs:
            if self.nutrition_logs_path.exists():
                self.nutrition_logs_path.unlink()
            return
        
        first_dump = logs[0].model_dump(mode='json')
        with open(self.nutrition_logs_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=list(first_dump.keys()))
            writer.writeheader()
            for log in logs:
                data = log.model_dump(mode='json')
                writer.writerow({k: (json.dumps(v) if isinstance(v, (list, dict)) else v) for k, v in data.items()})

    def save_nutrition_log(self, log: NutritionLog) -> None:
        logs = self._load_all_nutrition_logs()
        logs.append(log)
        self._save_all_nutrition_logs(logs)

    def load_nutrition_logs(self, start_date: date | None = None, end_date: date | None = None) -> list[NutritionLog]:
        logs = self._load_all_nutrition_logs()
        result = []
        for log in logs:
            if start_date and log.date < start_date:
                continue
            if end_date and log.date > end_date:
                continue
            result.append(log)
        return result

    def update_nutrition_log(self, log_date: date, updated: NutritionLog) -> bool:
        logs = self._load_all_nutrition_logs()
        for i, log in enumerate(logs):
            if log.date == log_date:
                logs[i] = updated
                self._save_all_nutrition_logs(logs)
                return True
        return False

    def delete_nutrition_log(self, log_date: date) -> bool:
        logs = self._load_all_nutrition_logs()
        initial_len = len(logs)
        logs = [log for log in logs if log.date != log_date]
        if len(logs) < initial_len:
            self._save_all_nutrition_logs(logs)
            return True
        return False

    def _load_all_lift_logs(self) -> list[LiftLog]:
        if not self.lift_logs_path.exists():
            return []
        try:
            logs = []
            with open(self.lift_logs_path, 'r', newline='', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    parsed_row = {}
                    for k, v in row.items():
                        try:
                            parsed_row[k] = json.loads(v)
                        except (ValueError, TypeError):
                            parsed_row[k] = v
                    logs.append(LiftLog.model_validate(parsed_row))
            return logs
        except Exception:
            return []

    def _save_all_lift_logs(self, logs: list[LiftLog]) -> None:
        if not logs:
            if self.lift_logs_path.exists():
                self.lift_logs_path.unlink()
            return
            
        first_dump = logs[0].model_dump(mode='json')
        with open(self.lift_logs_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=list(first_dump.keys()))
            writer.writeheader()
            for log in logs:
                data = log.model_dump(mode='json')
                writer.writerow({k: (json.dumps(v) if isinstance(v, (list, dict)) else v) for k, v in data.items()})

    def save_lift_log(self, log: LiftLog) -> None:
        logs = self._load_all_lift_logs()
        logs.append(log)
        self._save_all_lift_logs(logs)

    def load_lift_logs(self, exercise: str | None = None, start_date: date | None = None, end_date: date | None = None) -> list[LiftLog]:
        logs = self._load_all_lift_logs()
        result = []
        for log in logs:
            if exercise and log.exercise.lower() != exercise.lower():
                continue
            if start_date and log.date < start_date:
                continue
            if end_date and log.date > end_date:
                continue
            result.append(log)
        return result
