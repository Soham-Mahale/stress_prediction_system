from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from motor.motor_asyncio import AsyncIOMotorDatabase

from backend.app.database import get_database
from backend.app.models.assessment import AssessmentCreate, AssessmentOut, FeaturesIn
from backend.app.models.common import to_object_id
from backend.app.tz import IST

router = APIRouter(prefix="/assessments", tags=["assessments"])


def _to_assessment_out(doc: dict) -> AssessmentOut:
    return AssessmentOut(
        id=str(doc["_id"]),
        user_id=str(doc["user_id"]),
        features=FeaturesIn(**doc["features"]),
        stress_score=doc.get("stress_score"),
        stress_level=doc.get("stress_level"),
        model_version=doc.get("model_version"),
        created_at=doc["created_at"],
    )


@router.post("", response_model=AssessmentOut, status_code=201)
async def create_assessment(
    payload: AssessmentCreate, db: AsyncIOMotorDatabase = Depends(get_database)
) -> AssessmentOut:
    user_object_id = to_object_id(payload.user_id, "user_id")

    user_doc = await db["users"].find_one({"_id": user_object_id})
    if not user_doc:
        raise HTTPException(status_code=404, detail="User not found")

    doc = {
        "user_id": user_object_id,
        "features": payload.features.model_dump(),
        "stress_score": None,
        "stress_level": None,
        "model_version": None,
        "interventions_pool_generated": 0,
        "created_at": datetime.now(IST),
    }

    result = await db["stress_assessments"].insert_one(doc)
    doc["_id"] = result.inserted_id
    return _to_assessment_out(doc)


@router.get("/{user_id}", response_model=list[AssessmentOut])
async def get_assessment_history(
    user_id: str, db: AsyncIOMotorDatabase = Depends(get_database)
) -> list[AssessmentOut]:
    user_object_id = to_object_id(user_id, "user_id")

    cursor = db["stress_assessments"].find({"user_id": user_object_id}).sort("created_at", -1)
    docs = await cursor.to_list(length=None)
    return [_to_assessment_out(doc) for doc in docs]
