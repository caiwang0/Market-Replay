import uuid
import datetime
import app.services.lark as services_lark
from fastapi import Request, HTTPException
from jose import JWTError, jwt

import app.config as config
import app.services.redis as services_redis

LOGIN_TOKEN_REDIS_KEY = "login_token:{}"
LOGIN_TOKEN_TTL_SECONDS = 60 * 30  # 30 minutes

def get_jwt_from_cookies(http_req: Request):
    token = http_req.cookies.get("access_token")
    if not token: 
        raise HTTPException(status_code=401, detail="Missing token")
    
    return token

def get_email_by_jwt(token: str):
    if not token:
        raise HTTPException(status_code=401, detail="Missing token")
    try:
        payload = jwt.decode(token, config.SECRET_KEY, algorithms=[config.ALGORITHM])
        return payload["email"]
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")
    
def create_jwt(email: str):
    expire = datetime.datetime.utcnow() + datetime.timedelta(minutes=config.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode = {"email": email, "exp": expire}
    return jwt.encode(to_encode, config.SECRET_KEY, algorithm=config.ALGORITHM)

def get_lark_user_info(token: str, email: str) -> dict:
    """Get user information from Lark API"""
    try:
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        # First get user ID
        user_id = services_lark.get_lark_user_id(
            token=token,
            json={"emails": [email]}
        )
        
        # Then get user details (you might need to implement this in lark.py)
        # For now, we'll extract name from email or use a default
        name = email.split('@')[0].replace('.', ' ').title()
        
        return {
            "email": email,
            "name": name,
            "lark_user_id": user_id
        }
    except Exception as e:
        print(f"Error getting Lark user info: {e}")
        # Fallback to email-based name
        return {
            "email": email,
            "name": email.split('@')[0].replace('.', ' ').title()
        }
    
def generate_login_token(email: str) -> str:
    token = str(uuid.uuid4())
    key = LOGIN_TOKEN_REDIS_KEY.format(email)

    services_redis.set(key, token, ex=LOGIN_TOKEN_TTL_SECONDS)
    
    return token