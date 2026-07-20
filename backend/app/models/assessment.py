from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

# Field names and ranges mirror the training columns in
# src/components/data_transformation.py so Phase 2 can feed this
# straight into the model without a rename/remap step.


class FeaturesIn(BaseModel):
    anxiety_level: int = Field(..., ge=0, le=21)
    self_esteem: int = Field(..., ge=0, le=30)
    mental_health_history: int = Field(..., ge=0, le=1)
    depression: int = Field(..., ge=0, le=27)
    headache: int = Field(..., ge=0, le=5)
    blood_pressure: int = Field(..., ge=1, le=3)
    sleep_quality: int = Field(..., ge=0, le=5)
    breathing_problem: int = Field(..., ge=0, le=5)
    noise_level: int = Field(..., ge=0, le=5)
    living_conditions: int = Field(..., ge=0, le=5)
    safety: int = Field(..., ge=0, le=5)
    basic_needs: int = Field(..., ge=0, le=5)
    future_career_concerns: int = Field(..., ge=0, le=5)
    social_support: int = Field(..., ge=0, le=3)
    peer_pressure: int = Field(..., ge=0, le=5)
    extracurricular_activities: int = Field(..., ge=0, le=5)
    bullying: int = Field(..., ge=0, le=5)


class AssessmentCreate(BaseModel):
    user_id: str
    features: FeaturesIn


class AssessmentOut(BaseModel):
    id: str
    user_id: str
    features: FeaturesIn
    stress_score: Optional[float] = None
    stress_level: Optional[int] = None
    model_version: Optional[str] = None
    created_at: datetime
