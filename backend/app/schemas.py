from __future__ import annotations

from datetime import date, datetime
from enum import Enum

from pydantic import BaseModel, EmailStr


class SeniorityLevel(str, Enum):
    INTERN = "Intern"
    JUNIOR = "Junior"
    MEDIM = "Medim"
    SENIOR = "Senior"
    STAFF = "Staff"
    PRINCIPAL = "Principal"
    VP = "VP"
    DIRECTOR = "Director"


class UserBase(BaseModel):
    email: EmailStr


class UserCreate(UserBase):
    password: str
    first_name: str | None = None
    last_name: str | None = None
    birthday: date | None = None
    position: str | None = None
    seniority: SeniorityLevel | None = None


class UserOut(UserBase):
    id: int
    is_active: bool
    is_superuser: bool
    first_name: str | None = None
    last_name: str | None = None
    birthday: date | None = None
    position: str | None = None
    seniority: SeniorityLevel | None = None
    avatar_200_path: str | None = None
    created_at: datetime

    class Config:
        from_attributes = True


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserUpdateSelf(BaseModel):
    first_name: str | None = None
    last_name: str | None = None
    birthday: date | None = None


class UserUpdateAdmin(UserUpdateSelf):
    position: str | None = None
    seniority: SeniorityLevel | None = None
    is_active: bool | None = None
    is_superuser: bool | None = None


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
