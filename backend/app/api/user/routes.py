from fastapi import APIRouter, Request, HTTPException, Depends, Query
from sqlalchemy.orm import Session

import app.api.auth.utils as AuthUtils
import app.models.api.user as UserModel
from app.database.init import get_db
from app.database.user import UserDB

router = APIRouter()

# Health check
@router.post("/ping")
async def ping():
    return "pong"

# # Get current user info
# @router.get("/user")
# def get_current_user(request: Request, db: Session = Depends(get_db)):
#     """Get current authenticated user information"""
#     email = AuthUtils.get_email_by_jwt(request.cookies.get("access_token"))
    
#     user_db = UserDB(db)
#     user = user_db.get_user_by_email(email)
    
#     if not user:
#         raise HTTPException(status_code=404, detail="User not found in database")
    
#     return {
#         "id": user.id,
#         "email": user.email,
#         "name": user.name,
#         "created_at": user.created_at,
#         "updated_at": user.updated_at
#     }

# # CREATE - Add new user
# @router.post("/", response_model=UserModel.UserResponse, status_code=201)
# def create_user(user_data: UserModel.UserCreate, db: Session = Depends(get_db)):
#     """Create a new user"""
#     try:
#         user_db = UserDB(db)
#         user = user_db.create_user(user_data.email, user_data.name)
#         return UserModel.UserResponse(**user.to_dict())
#     except ValueError as e:
#         raise HTTPException(status_code=400, detail=str(e))

# # READ - Get user by ID
# @router.get("/{user_id}", response_model=UserModel.UserResponse)
# def get_user(user_id: int, db: Session = Depends(get_db)):
#     """Get user by ID"""
#     user_db = UserDB(db)
#     user = user_db.get_user_by_id(user_id)
#     if not user:
#         raise HTTPException(status_code=404, detail="User not found")
#     return UserModel.UserResponse(**user.to_dict())

# # READ - Get all users with pagination
# @router.get("/", response_model=UserModel.UsersListResponse)
# def get_users(
#     page: int = Query(1, ge=1, description="Page number"),
#     size: int = Query(10, ge=1, le=100, description="Page size"),
#     db: Session = Depends(get_db)
# ):
#     """Get all users with pagination"""
#     user_db = UserDB(db)
#     skip = (page - 1) * size
#     users = user_db.get_all_users(skip=skip, limit=size)
#     total = user_db.get_users_count()
    
#     return UserModel.UsersListResponse(
#         users=[UserModel.UserResponse(**user.to_dict()) for user in users],
#         total=total,
#         page=page,
#         size=size
#     )

# # READ - Get user by email
# @router.get("/email/{email}", response_model=UserModel.UserResponse)
# def get_user_by_email(email: str, db: Session = Depends(get_db)):
#     """Get user by email"""
#     user_db = UserDB(db)
#     user = user_db.get_user_by_email(email)
#     if not user:
#         raise HTTPException(status_code=404, detail="User not found")
#     return UserModel.UserResponse(**user.to_dict())

# # UPDATE - Update user
# @router.put("/{user_id}", response_model=UserModel.UserResponse)
# def update_user(user_id: int, user_data: UserModel.UserUpdate, db: Session = Depends(get_db)):
#     """Update user information"""
#     if not user_data.email and not user_data.name:
#         raise HTTPException(status_code=400, detail="At least one field must be provided")
    
#     try:
#         user_db = UserDB(db)
#         user = user_db.update_user(
#             user_id, 
#             email=user_data.email, 
#             name=user_data.name
#         )
#         if not user:
#             raise HTTPException(status_code=404, detail="User not found")
#         return UserModel.UserResponse(**user.to_dict())
#     except ValueError as e:
#         raise HTTPException(status_code=400, detail=str(e))

# # DELETE - Delete user
# @router.delete("/{user_id}")
# def delete_user(user_id: int, db: Session = Depends(get_db)):
#     """Delete user by ID"""
#     user_db = UserDB(db)
#     success = user_db.delete_user(user_id)
#     if not success:
#         raise HTTPException(status_code=404, detail="User not found")
#     return {"message": f"User {user_id} deleted successfully"}