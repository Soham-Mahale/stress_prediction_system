from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

from backend.app.config import settings

_client: AsyncIOMotorClient | None = None


def connect() -> None:
    global _client
    _client = AsyncIOMotorClient(settings.mongo_uri)


def disconnect() -> None:
    global _client
    if _client is not None:
        _client.close()
        _client = None


def get_database() -> AsyncIOMotorDatabase:
    if _client is None:
        raise RuntimeError("Database client is not connected")
    return _client[settings.db_name]


async def ensure_indexes() -> None:
    db = get_database()
    await db["users"].create_index("mobile_no", unique=True)
    await db["users"].create_index("email", unique=True)
    await db["profiles"].create_index("user_id", unique=True)
    await db["stress_assessments"].create_index([("user_id", 1), ("created_at", -1)])
    await db["intervention_pools"].create_index("source_assessment_id", unique=True)
    await db["intervention_pools"].create_index([("source_assessment_id", 1), ("created_at", -1)])
