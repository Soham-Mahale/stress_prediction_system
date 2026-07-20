from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from motor.motor_asyncio import AsyncIOMotorDatabase
from pymongo import ReturnDocument
from pymongo.errors import DuplicateKeyError

from backend.app.database import get_database
from backend.app.models.common import to_object_id
from backend.app.models.profile import ProfileCreate, ProfileOut, ProfileUpdate, calculate_age
from backend.app.tz import IST

router = APIRouter(prefix="/profiles", tags=["profiles"])


def _to_profile_out(doc: dict) -> ProfileOut:
    dob = doc["dob"].date()
    return ProfileOut(
        id=str(doc["_id"]),
        user_id=str(doc["user_id"]),
        name=doc["name"],
        dob=dob,
        gender=doc["gender"],
        age=calculate_age(dob),
        created_at=doc["created_at"],
        updated_at=doc["updated_at"],
    )


@router.post("", response_model=ProfileOut, status_code=201)
async def create_profile(
    payload: ProfileCreate, db: AsyncIOMotorDatabase = Depends(get_database)
) -> ProfileOut:
    user_object_id = to_object_id(payload.user_id, "user_id")

    user_doc = await db["users"].find_one({"_id": user_object_id})
    if not user_doc:
        raise HTTPException(status_code=404, detail="User not found")

    now = datetime.now(IST)
    doc = {
        "user_id": user_object_id,
        "name": payload.name,
        "dob": datetime.combine(payload.dob, datetime.min.time(), tzinfo=IST),
        "gender": payload.gender,
        "created_at": now,
        "updated_at": now,
    }

    try:
        result = await db["profiles"].insert_one(doc)
    except DuplicateKeyError:
        raise HTTPException(status_code=409, detail="A profile already exists for this user")

    doc["_id"] = result.inserted_id
    return _to_profile_out(doc)


@router.get("/{user_id}", response_model=ProfileOut)
async def get_profile(
    user_id: str, db: AsyncIOMotorDatabase = Depends(get_database)
) -> ProfileOut:
    user_object_id = to_object_id(user_id, "user_id")
    doc = await db["profiles"].find_one({"user_id": user_object_id})
    if not doc:
        raise HTTPException(status_code=404, detail="Profile not found")
    return _to_profile_out(doc)


@router.put("/{user_id}", response_model=ProfileOut)
async def update_profile(
    user_id: str,
    payload: ProfileUpdate,
    db: AsyncIOMotorDatabase = Depends(get_database),
) -> ProfileOut:
    user_object_id = to_object_id(user_id, "user_id")

    update_fields = payload.model_dump(exclude_unset=True, exclude_none=True)
    if not update_fields:
        raise HTTPException(status_code=400, detail="No update fields provided")

    if "dob" in update_fields:
        update_fields["dob"] = datetime.combine(
            update_fields["dob"], datetime.min.time(), tzinfo=IST
        )

    update_fields["updated_at"] = datetime.now(IST)

    doc = await db["profiles"].find_one_and_update(
        {"user_id": user_object_id},
        {"$set": update_fields},
        return_document=ReturnDocument.AFTER,
    )
    if not doc:
        raise HTTPException(status_code=404, detail="Profile not found")

    return _to_profile_out(doc)
