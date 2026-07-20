from datetime import date, datetime
from typing import Literal, Optional

from pydantic import BaseModel, Field


def calculate_age(dob: date) -> int:
    today = date.today()
    age = today.year - dob.year
    if (today.month, today.day) < (dob.month, dob.day):
        age -= 1
    return age


class ProfileCreate(BaseModel):
    user_id: str
    name: str = Field(..., min_length=1, examples=["Soham Mahale"])
    dob: date = Field(..., examples=["2000-01-01"])
    gender: Literal["male", "female", "other"]


class ProfileUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1)
    dob: Optional[date] = None
    gender: Optional[Literal["male", "female", "other"]] = None


class ProfileOut(BaseModel):
    id: str
    user_id: str
    name: str
    dob: date
    gender: str
    age: int
    created_at: datetime
    updated_at: datetime
