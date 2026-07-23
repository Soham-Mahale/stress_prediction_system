from datetime import datetime
from pydantic import BaseModel, Field
from typing import List


class Subtask(BaseModel):
    title: str


class Intervention(BaseModel):
    intervention_id: str
    title: str
    description: str
    subtasks: list[Subtask]


class InterventionPoolCreate(BaseModel):
    user_id: str
    source_assessment_id: str


class InterventionPoolOut(BaseModel):
    source_assessment_id: str
    predicted_stress: str
    interventions: list[Intervention]
    created_at: datetime


# --- LLM-facing schemas ---------------------------------------------------
# Deliberately separate from Intervention/InterventionPoolCreate above: the
# LLM should only ever generate creative content (title/description/
# subtasks). Identity fields (intervention_id, user_id, source_assessment_id)
# are assigned by the app after generation and are never trusted from model
# output - this is what with_structured_output() + these schemas enforce,
# replacing the old eval()-on-raw-text parsing.


class GeneratedIntervention(BaseModel):
    title: str = Field(
        ..., description="Short, actionable name of the intervention, e.g. 'Morning Walk'"
    )
    description: str = Field(
        ...,
        description="1-2 sentence explanation of the intervention and why it helps at this stress level",
    )
    subtasks: list[Subtask] = Field(
        ...,
        min_length=2,
        max_length=5,
        description="2-5 Separate actionable non dependable tasks related to title of this intervention.",
    )


class InterventionPoolLLMResponse(BaseModel):
    main_body: str = Field(
        ..., description="A short, warm, encouraging message introducing the plan to the user"
    )
    interventions: list[GeneratedIntervention] = Field(
        ..., min_length=15, max_length=15, description="Exactly 15 personalized interventions"
    )