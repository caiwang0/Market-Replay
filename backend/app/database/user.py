from sqlalchemy.orm import Session
from typing import List, Optional
from sqlalchemy.exc import IntegrityError

from app.models.database.user import User as UserDBModel

class UserDB:
    def __init__(self, db: Session):
        self.db = db
    
    def create_user(self, email: str, name: str) -> UserDBModel:
        """Create a new user"""
        try:
            user = UserDBModel(email=email, name=name)
            self.db.add(user)
            self.db.commit()
            self.db.refresh(user)
            return user
        except IntegrityError:
            self.db.rollback()
            raise ValueError(f"User with email {email} already exists")
    
    def get_user_by_id(self, user_id: int) -> Optional[UserDBModel]:
        """Get user by ID"""
        return self.db.query(UserDBModel).filter(UserDBModel.id == user_id).first()
    
    def get_user_by_email(self, email: str) -> Optional[UserDBModel]:
        """Get user by email"""
        return self.db.query(UserDBModel).filter(UserDBModel.email == email).first()
    
    def get_all_users(self, skip: int = 0, limit: int = 100) -> List[UserDBModel]:
        """Get all users with pagination"""
        return self.db.query(UserDBModel).offset(skip).limit(limit).all()
    
    def update_user(self, user_id: int, email: str = None, name: str = None) -> Optional[UserDBModel]:
        """Update user information"""
        user = self.get_user_by_id(user_id)
        if not user:
            return None
            
        try:
            if email and email != user.email:
                # Check if new email already exists
                existing = self.get_user_by_email(email)
                if existing and existing.id != user_id:
                    raise ValueError(f"Email {email} already exists")
                user.email = email
                
            if name:
                user.name = name
                
            self.db.commit()
            self.db.refresh(user)
            return user
        except IntegrityError:
            self.db.rollback()
            raise ValueError(f"Email {email} already exists")
    
    def delete_user(self, user_id: int) -> bool:
        """Delete user by ID"""
        user = self.get_user_by_id(user_id)
        if user:
            self.db.delete(user)
            self.db.commit()
            return True
        return False
    
    def get_users_count(self) -> int:
        """Get total number of users"""
        return self.db.query(UserDBModel).count()