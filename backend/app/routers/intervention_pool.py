from datetime import datetime

from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from motor.motor_asyncio import AsyncIOMotorDatabase
from pydantic import ValidationError
from pymongo import ReturnDocument

from backend.app.config import settings
from backend.app.database import get_database
from backend.app.models.assessment import FeaturesIn
from backend.app.models.common import to_object_id
from backend.app.models.intervention_pool import (
    Intervention,
    InterventionPoolCreate,
    InterventionPoolLLMResponse,
    InterventionPoolOut,
)
from backend.app.tz import IST

router = APIRouter(prefix="/intervention_pool", tags=["intervention_pool"])

# Mirrors the trained model's label mapping - see stress_mapping in
# legacy_backend.py.bak and the stress_level column in artifacts/rawdata.csv
# (0=High, 1=Moderate, 2=Low). The old prompt described 1/2/3 as ascending
# severity, which never matched this; kept consistent here.
# STRESS_LABELS = {0: "High", 1: "Moderate", 2: "Low"}

_SYSTEM_PROMPT = """You are a helpful and empathetic mental wellness assistant.
Your goal is to generate supportive, actionable, personalized interventions based on a person's stress assessment.

Stress levels, from most to least severe:
- High: strongly recommend the user also consult a doctor/counsellor alongside the interventions.
- Moderate: recommend the user consider a doctor/counsellor alongside the interventions.
- Low: no clinical referral needed; focus on habit-building and light wellness activities.

Generate exactly 15 personalized interventions tailored to the person's stress level and the specific features that stand out in their assessment (e.g. poor sleep quality, high anxiety, low social support). Each intervention must be realistic, actionable, and something the person can start practicing this week. Break each one down into 2-5 concrete subtasks.

Keep your tone warm and encouraging. Do not name a specific doctor or medication - only recommend seeking professional consultation when appropriate."""


def create_prompt(features: FeaturesIn, stress_level: str) -> list[BaseMessage]:
    """Build the System/Human messages for intervention generation.

    Kept separate from the LLM call itself so the prompt can be unit-tested
    or inspected without hitting the network. The output shape itself is
    enforced by with_structured_output() in generate_interventions() below,
    not by describing the schema in prose here.
    """
    stress_label = stress_level

    human_content = (
        f"The person's predicted stress level is: {stress_label}.\n\n"
        "Here are the assessment features that describe them, on their original scale:\n"
        f"{features.model_dump_json(indent=2)}\n\n"
        "Generate the 15 personalized interventions for this person based on this "
        "stress level and these features."
    )

    return [
        SystemMessage(content=_SYSTEM_PROMPT),
        HumanMessage(content=human_content),
    ]


def get_llm() -> ChatGoogleGenerativeAI:
    return ChatGoogleGenerativeAI(
        model="gemini-2.5-flash",
        temperature=0.6,
        google_api_key=settings.gemini_api_key,
    )


async def generate_interventions(
    features: FeaturesIn, stress_level: str
) -> InterventionPoolLLMResponse:
    """Call the LLM and get back a validated InterventionPoolLLMResponse.

    with_structured_output() makes the model return data matching that
    schema directly (via Gemini's function-calling/JSON mode) - no raw text
    slicing, no eval(). Pydantic still enforces "exactly 15 interventions"
    and the shape of each one; a malformed response raises here instead of
    being silently stored.
    """
    structured_llm = get_llm().with_structured_output(InterventionPoolLLMResponse)
    messages = create_prompt(features, stress_level)

    try:
        return await structured_llm.ainvoke(messages)
    except ValidationError as exc:
        raise HTTPException(
            status_code=502, detail=f"LLM returned an invalid intervention pool: {exc}"
        )
    
@router.post("", response_model=InterventionPoolOut, status_code=201)
async def create_intervention_pool(
    payload: InterventionPoolCreate, db: AsyncIOMotorDatabase = Depends(get_database)
) -> InterventionPoolOut:
    user_object_id = to_object_id(payload.user_id, "user_id")
    assessment_object_id = payload.source_assessment_id

    user_doc = await db["users"].find_one({"_id": user_object_id})
    if not user_doc:
        raise HTTPException(status_code=404, detail="User not found")

    # Atomically: fetch the assessment, confirm it belongs to this user,
    # confirm it's been scored, confirm it hasn't hit the generation cap,
    # AND reserve this attempt by incrementing the counter - all in one
    # round trip. If two requests race, only one can match the $lt filter
    # per increment; the loser gets None back below.
    assessment_doc = await db["stress_assessments"].find_one_and_update(
        {
            "user_id": user_object_id,
            "source_assessment_id": assessment_object_id,
            "stress_level": {"$ne": None},
            "interventions_pool_generated": {"$lt": 2},
        },
        {"$inc": {"interventions_pool_generated": 1}},
        return_document=ReturnDocument.AFTER,
    )

    if assessment_doc is None:
        # Distinguish *why* it didn't match so the error isn't misleading.
        exists = await db["stress_assessments"].find_one(
            {"user_id": user_object_id, "source_assessment_id": assessment_object_id}
        )
        if not exists:
            raise HTTPException(status_code=404, detail="Assessment not found for this user")
        if exists.get("stress_level") is None:
            raise HTTPException(
                status_code=409,
                detail="This assessment has not been scored yet (ML prediction not run) - "
                "cannot generate an intervention pool from it.",
            )
        raise HTTPException(
            status_code=409,
            detail="Cannot generate an intervention pool more than twice for this assessment",
        )

    stress_level = assessment_doc["stress_level"]
    features = FeaturesIn(**assessment_doc["features"])
    llm_response = await generate_interventions(features, stress_level)

    interventions = [
        Intervention(
            intervention_id=str(ObjectId()),
            title=item.title,
            description=item.description,
            subtasks=item.subtasks,
        )
        for item in llm_response.interventions
    ]

    now = datetime.now(IST)
    doc = {
        "user_id": user_object_id,
        "source_assessment_id": assessment_object_id,
        "predicted_stress": stress_level,
        "interventions": [i.model_dump() for i in interventions],
        "created_at": now,
    }

    result = await db["intervention_pools"].insert_one(doc)

    return InterventionPoolOut(
        id=str(result.inserted_id),
        user_id=payload.user_id,
        source_assessment_id=payload.source_assessment_id,
        predicted_stress=doc["predicted_stress"],
        interventions=interventions,
        created_at=now,
    )

