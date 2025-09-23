from sqlalchemy.orm import Session
from fastapi import HTTPException

import app.api.auth.utils as Auth
from app.database.user import UserDB
from app.models.database.user import User as UserDBModel

def get_user_by_jwt(jwt_token: str, db: Session) -> UserDBModel:
    try:
        email = Auth.get_email_by_jwt(jwt_token)
        user_db = UserDB(db)
        user = user_db.get_user_by_email(email)
        
        if not user:
            raise HTTPException(status_code=404, detail="User not found in database")
        
        return user
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error getting authenticated user: {e}")
        raise HTTPException(status_code=500, detail="Authentication error")