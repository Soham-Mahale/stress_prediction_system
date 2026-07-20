from bson import ObjectId
from fastapi import HTTPException


def to_object_id(value: str, field_name: str = "id") -> ObjectId:
    if not ObjectId.is_valid(value):
        raise HTTPException(status_code=400, detail=f"Invalid {field_name}: {value!r}")
    return ObjectId(value)
