from __future__ import annotations

import json
from datetime import date
from pathlib import Path

from fitness_predictor.models import LiftLog, NutritionLog, UserProfile


class JsonStorage:
    def __init__(self, data_dir: str | Path = 'data') -> None:
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.profile_path = self.data_dir / 'profile.json'
        self.nutrition_logs_path = self.data_dir / 'nutrition_logs.json'
        self.lift_logs_path = self.data_dir / 'lift_logs.json'

    def save_profile(self, profile: UserProfile) -> None:
        with open(self.profile_path, 'w', encoding='utf-8') as f:
            json.dump(profile.model_dump(mode='json'), f, indent=2)

    def load_profile(self) -> UserProfile | None:
        if not self.profile_path.exists():
            return None
        try:
            with open(self.profile_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return UserProfile.model_validate(data)
        except Exception:
            return None

    def _load_all_nutrition_logs(self) -> list[NutritionLog]:
        if not self.nutrition_logs_path.exists():
            return []
        try:
            with open(self.nutrition_logs_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return [NutritionLog.model_validate(item) for item in data]
        except Exception:
            return []

    def _save_all_nutrition_logs(self, logs: list[NutritionLog]) -> None:
        with open(self.nutrition_logs_path, 'w', encoding='utf-8') as f:
            json.dump([log.model_dump(mode='json') for log in logs], f, indent=2)

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
            with open(self.lift_logs_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return [LiftLog.model_validate(item) for item in data]
        except Exception:
            return []

    def _save_all_lift_logs(self, logs: list[LiftLog]) -> None:
        with open(self.lift_logs_path, 'w', encoding='utf-8') as f:
            json.dump([log.model_dump(mode='json') for log in logs], f, indent=2)

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
