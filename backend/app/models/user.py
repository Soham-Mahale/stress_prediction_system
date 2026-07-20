from datetime import datetime

from pydantic import BaseModel, EmailStr, Field, field_validator


class UserCreate(BaseModel):
    mobile_no: str = Field(..., examples=["7498253835"])
    email: EmailStr
    password: str = Field(..., min_length=8)

    @field_validator("mobile_no")
    @classmethod
    def mobile_no_must_be_10_digits(cls, value: str) -> str:
        if not value.isdigit() or len(value) != 10:
            raise ValueError("mobile_no must be exactly 10 digits")
        return value


class UserOut(BaseModel):
    id: str
    mobile_no: str
    email: EmailStr
    is_active: bool
    created_at: datetime
    updated_at: datetime


class LoginRequest(BaseModel):
    mobile_no: str
    password: str
