from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from motor.motor_asyncio import AsyncIOMotorDatabase
from pymongo.errors import DuplicateKeyError

from backend.app.database import get_database
from backend.app.models.common import to_object_id
from backend.app.models.user import LoginRequest, UserCreate, UserOut
from backend.app.security import hash_password, verify_password
from backend.app.tz import IST

router = APIRouter(prefix="/users", tags=["users"])


def _to_user_out(doc: dict) -> UserOut:
    return UserOut(
        id=str(doc["_id"]),
        mobile_no=doc["mobile_no"],
        email=doc["email"],
        is_active=doc["is_active"],
        created_at=doc["created_at"],
        updated_at=doc["updated_at"],
    )


@router.post("", response_model=UserOut, status_code=201)
async def create_user(
    payload: UserCreate, db: AsyncIOMotorDatabase = Depends(get_database)
) -> UserOut:
    now = datetime.now(IST)
    doc = {
        "mobile_no": payload.mobile_no,
        "email": payload.email,
        "password_hash": hash_password(payload.password),
        "is_active": True,
        "created_at": now,
        "updated_at": now,
    }

    try:
        result = await db["users"].insert_one(doc)
    except DuplicateKeyError:
        raise HTTPException(
            status_code=409, detail="A user with this mobile number or email already exists"
        )

    doc["_id"] = result.inserted_id
    return _to_user_out(doc)


@router.get("/{user_id}", response_model=UserOut)
async def get_user(
    user_id: str, db: AsyncIOMotorDatabase = Depends(get_database)
) -> UserOut:
    object_id = to_object_id(user_id, "user_id")
    doc = await db["users"].find_one({"_id": object_id})
    if not doc:
        raise HTTPException(status_code=404, detail="User not found")
    return _to_user_out(doc)


@router.post("/login", response_model=UserOut)
async def login(
    payload: LoginRequest, db: AsyncIOMotorDatabase = Depends(get_database)
) -> UserOut:
    doc = await db["users"].find_one({"mobile_no": payload.mobile_no})
    if not doc or not verify_password(payload.password, doc["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    return _to_user_out(doc)
