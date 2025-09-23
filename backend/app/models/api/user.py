from pydantic import BaseModel, EmailStr
from typing import List, Optional

class UserCreate(BaseModel):
    email: EmailStr
    name: str

class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    name: Optional[str] = None

class UserResponse(BaseModel):
    id: int
    email: str
    name: str
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    
    class Config:
        from_attributes = True

class UsersListResponse(BaseModel):
    users: List[UserResponse]
    total: int
    page: int
    size: int

