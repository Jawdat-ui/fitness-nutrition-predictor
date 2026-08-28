"""User biometric profile management — create, display, edit, and persist."""

from __future__ import annotations

from typing import Any

from fitness_predictor.models import ActivityLevel, Goal, Sex, UserProfile
from fitness_predictor.input.data_entry import prompt_choice, prompt_float, prompt_int


def prompt_user_profile() -> UserProfile:
    """Interactively collect all UserProfile fields from the user."""
    name = input("Name: ").strip()
    age = prompt_int("Age: ", min_val=1, max_val=120)
    height_cm = prompt_float("Height (cm): ", min_val=1.0)
    weight_kg = prompt_float("Weight (kg): ", min_val=1.0)
    sex_str = prompt_choice("Sex", [s.value for s in Sex])
    activity_str = prompt_choice("Activity Level", [a.value for a in ActivityLevel])
    goal_str = prompt_choice("Goal", [g.value for g in Goal])
    sessions = prompt_int("Training sessions per week: ", min_val=0, max_val=14)
    intensity = prompt_float("Training intensity (0.0–1.0): ", min_val=0.0, max_val=1.0)

    return UserProfile(
        name=name,
        age=age,
        height_cm=height_cm,
        weight_kg=weight_kg,
        sex=Sex(sex_str),
        activity_level=ActivityLevel(activity_str),
        goal=Goal(goal_str),
        training_sessions_per_week=sessions,
        training_intensity=intensity,
    )


def display_profile(profile: UserProfile) -> None:
    """Print the user profile in a readable format."""
    print("  ── User Profile ──")
    print(f"  Name:              {profile.name}")
    print(f"  Age:               {profile.age}")
    print(f"  Height:            {profile.height_cm} cm")
    print(f"  Weight:            {profile.weight_kg} kg ({profile.weight_lb:.1f} lb)")
    print(f"  Sex:               {profile.sex.value}")
    print(f"  Activity Level:    {profile.activity_level.value}")
    print(f"  Goal:              {profile.goal.value}")
    print(f"  Training:          {profile.training_sessions_per_week}×/week "
          f"@ {profile.training_intensity:.0%} intensity")


def prompt_edit_profile(current: UserProfile) -> UserProfile:
    """Edit an existing profile — press Enter on any field to keep the current value."""
    print("  Press Enter to keep the current value.\n")

    def _edit_str(prompt: str, curr: str) -> str:
        val = input(f"  {prompt} [{curr}]: ").strip()
        return val if val else curr

    def _edit_int(prompt: str, curr: int) -> int:
        val = input(f"  {prompt} [{curr}]: ").strip()
        return int(val) if val else curr

    def _edit_float(prompt: str, curr: float) -> float:
        val = input(f"  {prompt} [{curr}]: ").strip()
        return float(val) if val else curr

    name = _edit_str("Name", current.name)
    age = _edit_int("Age", current.age)
    height_cm = _edit_float("Height (cm)", current.height_cm)
    weight_kg = _edit_float("Weight (kg)", current.weight_kg)

    print(f"  Current sex: {current.sex.value}")
    sex_str = prompt_choice("  Sex", [s.value for s in Sex])

    print(f"  Current activity level: {current.activity_level.value}")
    activity_str = prompt_choice("  Activity Level", [a.value for a in ActivityLevel])

    print(f"  Current goal: {current.goal.value}")
    goal_str = prompt_choice("  Goal", [g.value for g in Goal])

    sessions = _edit_int("Training sessions/week", current.training_sessions_per_week)
    intensity = _edit_float("Training intensity (0.0–1.0)", current.training_intensity)

    return UserProfile(
        name=name,
        age=age,
        height_cm=height_cm,
        weight_kg=weight_kg,
        sex=Sex(sex_str),
        activity_level=ActivityLevel(activity_str),
        goal=Goal(goal_str),
        training_sessions_per_week=sessions,
        training_intensity=intensity,
    )


def load_or_create_profile(storage: Any) -> UserProfile:
    """Load an existing profile from storage, or prompt the user to create one."""
    profile = storage.load_profile()
    if profile is None:
        print("No profile found. Let's create one.\n")
        profile = prompt_user_profile()
        storage.save_profile(profile)
    return profile
