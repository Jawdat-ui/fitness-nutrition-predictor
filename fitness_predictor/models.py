"""Core data models for the Fitness & Nutrition Predictor.

Uses Pydantic v2 for runtime validation, serialization, and type safety.
All models are designed for easy JSON serialization and storage.
"""

from __future__ import annotations

from datetime import date, datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field, field_validator


# ---------------------------------------------------------------------------
# Enumerations
# ---------------------------------------------------------------------------

class Sex(str, Enum):
    """Biological sex for BMR calculations."""
    MALE = "male"
    FEMALE = "female"


class ActivityLevel(str, Enum):
    """Physical activity level for TDEE multiplier selection."""
    SEDENTARY = "sedentary"
    LIGHTLY_ACTIVE = "lightly_active"
    MODERATELY_ACTIVE = "moderately_active"
    VERY_ACTIVE = "very_active"
    EXTRA_ACTIVE = "extra_active"


class Goal(str, Enum):
    """Body composition goal determining caloric surplus/deficit."""
    BULK = "bulk"
    CUT = "cut"
    MAINTAIN = "maintain"


class WeightUnit(str, Enum):
    """Unit of measurement for barbell weights."""
    KG = "kg"
    LB = "lb"


class StrengthLevel(str, Enum):
    """Strength classification tiers (à la strengthlevel.com)."""
    BEGINNER = "beginner"
    NOVICE = "novice"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"
    ELITE = "elite"


# ---------------------------------------------------------------------------
# Conversion helpers
# ---------------------------------------------------------------------------

KG_PER_LB: float = 0.453592
LB_PER_KG: float = 2.20462


def to_kg(value: float, unit: WeightUnit) -> float:
    """Convert a weight value to kilograms."""
    return value * KG_PER_LB if unit == WeightUnit.LB else value


def to_lb(value: float, unit: WeightUnit) -> float:
    """Convert a weight value to pounds."""
    return value * LB_PER_KG if unit == WeightUnit.KG else value


# ---------------------------------------------------------------------------
# User Profile
# ---------------------------------------------------------------------------

class UserProfile(BaseModel):
    """Biometric profile used for BMR, TDEE, and strength-standard lookups.

    Attributes:
        name: User's display name.
        age: Age in years (1–120).
        height_cm: Height in centimetres.
        weight_kg: Body weight in kilograms.
        sex: Biological sex (male / female).
        activity_level: Self-reported weekly activity level.
        goal: Current body-composition target (bulk / cut / maintain).
        training_sessions_per_week: Number of resistance-training sessions (0–14).
        training_intensity: Subjective intensity 0.0–1.0 (0 = very light, 1 = max).
    """
    name: str = Field(..., min_length=1, description="User's display name")
    age: int = Field(..., gt=0, le=120, description="Age in years")
    height_cm: float = Field(..., gt=0, description="Height in centimetres")
    weight_kg: float = Field(..., gt=0, description="Body weight in kilograms")
    sex: Sex
    activity_level: ActivityLevel = ActivityLevel.MODERATELY_ACTIVE
    goal: Goal = Goal.MAINTAIN
    training_sessions_per_week: int = Field(
        default=3, ge=0, le=14,
        description="Resistance-training sessions per week",
    )
    training_intensity: float = Field(
        default=0.7, ge=0.0, le=1.0,
        description="Subjective intensity (0.0 = very light, 1.0 = max effort)",
    )

    @property
    def weight_lb(self) -> float:
        """Body weight converted to pounds."""
        return self.weight_kg * LB_PER_KG


# ---------------------------------------------------------------------------
# Nutrition Log
# ---------------------------------------------------------------------------

class NutritionLog(BaseModel):
    """Single daily nutrition entry.

    Attributes:
        date: Calendar date of the entry.
        calories: Total caloric intake (kcal).
        protein_g: Protein intake in grams.
        carbs_g: Carbohydrate intake in grams.
        fats_g: Fat intake in grams.
        notes: Optional free-text notes.
        timestamp: When the entry was created/last modified.
    """
    date: date
    calories: float = Field(..., ge=0, description="Total kcal")
    protein_g: float = Field(..., ge=0, description="Protein in grams")
    carbs_g: float = Field(..., ge=0, description="Carbs in grams")
    fats_g: float = Field(..., ge=0, description="Fats in grams")
    notes: str = ""
    timestamp: datetime = Field(default_factory=datetime.now)

    @field_validator("calories", mode="before")
    @classmethod
    def _calories_reasonable(cls, v: float) -> float:
        if v > 15_000:
            raise ValueError("Calorie value seems unreasonably high (>15 000)")
        return v


# ---------------------------------------------------------------------------
# Lift Log
# ---------------------------------------------------------------------------

class LiftLog(BaseModel):
    """Single lift/exercise entry for 1RM tracking.

    Attributes:
        date: Calendar date of the lift.
        exercise: Name of the exercise (e.g. 'Bench Press').
        weight: Weight lifted (in the specified unit).
        reps: Number of repetitions performed (≥ 1).
        unit: Weight unit (kg or lb).
        estimated_1rm: Calculated estimated one-rep max (populated after prediction).
        timestamp: When the entry was created/last modified.
    """
    date: date
    exercise: str = Field(..., min_length=1, description="Exercise name")
    weight: float = Field(..., gt=0, description="Weight lifted")
    reps: int = Field(..., ge=1, description="Reps performed")
    unit: WeightUnit = WeightUnit.LB
    estimated_1rm: Optional[float] = None
    timestamp: datetime = Field(default_factory=datetime.now)

    @property
    def weight_kg(self) -> float:
        """Weight converted to kilograms."""
        return to_kg(self.weight, self.unit)

    @property
    def weight_lb(self) -> float:
        """Weight converted to pounds."""
        return to_lb(self.weight, self.unit)


# ---------------------------------------------------------------------------
# Prediction Results
# ---------------------------------------------------------------------------

class MacroTarget(BaseModel):
    """Calculated daily caloric and macronutrient targets.

    Attributes:
        calories: Target daily calories (kcal).
        protein_g: Target protein (grams).
        carbs_g: Target carbs (grams).
        fats_g: Target fats (grams).
        bmr: Basal Metabolic Rate used in the calculation.
        tdee: Total Daily Energy Expenditure used in the calculation.
    """
    calories: float = Field(..., ge=0)
    protein_g: float = Field(..., ge=0)
    carbs_g: float = Field(..., ge=0)
    fats_g: float = Field(..., ge=0)
    bmr: Optional[float] = None
    tdee: Optional[float] = None


class OneRepMaxResult(BaseModel):
    """Result of a one-rep-max estimation using multiple formulas.

    Attributes:
        exercise: Name of the exercise.
        weight: Weight used in the set.
        reps: Reps performed in the set.
        unit: Unit of the weight.
        epley: 1RM via Epley formula.
        brzycki: 1RM via Brzycki formula.
        lombardi: 1RM via Lombardi formula.
        mcglothin: 1RM via McGlothin formula.
        oconner: 1RM via O'Conner formula.
        average_1rm: Simple average of all five formulas.
        flagged_formulas: Formulas that disagree with the average by >5 %.
        adjusted_1rm: 1RM after biometric/nutrition adjustment (optional).
        strength_level: Classified strength tier (optional).
    """
    exercise: str
    weight: float
    reps: int
    unit: WeightUnit
    epley: float
    brzycki: float
    lombardi: float
    mcglothin: float
    oconner: float
    average_1rm: float
    flagged_formulas: list[str] = Field(default_factory=list)
    adjusted_1rm: Optional[float] = None
    strength_level: Optional[StrengthLevel] = None
