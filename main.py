from fastapi import FastAPI, Path, Query, Response
from pydantic import BaseModel, EmailStr, Field, field_validator
import random
import re
from typing import List, Dict, Any

app=FastAPI()

class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(..., min_length=8)
    full_name: str | None = None
    age: int | None = Field(None, ge=18, le=120)
    is_active: bool = True

    @field_validator('username')
    @classmethod
    def validate_username(cls, v: str) -> str:
        if not re.match(r'^[a-zA-Z0-9]+$', v):
            raise ValueError('только буквы и цифры')
        return v
    @field_validator('password')
    @classmethod
    def validate_password(cls, v: str) -> str:
        if not re.search(r'[0-9]', v) or not re.search(r'[a-zA-Z]', v):
            raise ValueError('минимум 1 буква и 1 цифра')
        return v


@app.post("/user")
def Create_user(user: UserCreate):
    return {**user.model_dump(exclude={"password"}), "id": random.randint(1, 100)}



class ItemCreate(BaseModel):
    name: str = Field(..., min_length=3, max_length=100)
    description: str | None = Field(None, max_length=1000)
    price: float = Field(..., ge=0.01, le=1_000_000)
    tax: float = Field(0, ge=0, le=100)
    tags: List[str] | None = Field(None, max_length=5)
    quantity: int | None = Field(None, ge=0, le=1000)

@app.post("/items")
def Create_item(item: ItemCreate):
    return {**item.model_dump(), "price_after_tax": item.price*(1 - item.tax/100)}


class User(BaseModel):
    name: str
    age: int
    active: bool

class Filters(BaseModel):
    min_age: int | None = Field(None, ge=0, le=150)
    max_age: int | None = Field(None, ge=0, le=150)
    active_only: bool | None = None

class FilterRequest(BaseModel):
    users: List[User] = Field(..., max_items=100)
    filters: Filters

class FilterResponse(BaseModel):
    total_input: int
    filtered_count: int
    filtered_users: List[User]
    applied_filters: Filters

@app.post("/filter-users")
def Filter_users(request: FilterRequest):
    users = request.users
    if request.filters.min_age:
        users = [x for x in users if x.age >= request.filters.min_age]
    if request.filters.max_age:
        users = [x for x in users if x.age <= request.filters.max_age]
    if request.filters.active_only:
        users = [x for x in users if x.active]
    return FilterResponse(total_input=len(request.users), filtered_count=len(users), filtered_users=users, applied_filters=request.filters)


class UserUpdate(BaseModel):
    email: EmailStr
    full_name: str
    age: int = Field(None, ge=18, le=120)
    is_active: bool

@app.put("/users/{user_id}")
def Update_user(user_id: int, user_update: UserUpdate):
    return {"id": user_id, "username": "Anton", **user_update.model_dump()}



