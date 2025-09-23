from fastapi import APIRouter, Request, HTTPException, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

import app.config as config
import app.models.api.auth as AuthModel
import app.api.auth.utils as auth_utils
import app.services.lark as services_lark
import app.services.redis as services_redis
from app.database.init import get_db
from app.database.user import UserDB

router = APIRouter()

# Health check
@router.post("/ping")
async def ping():
    return "pong"

# Routes
@router.get("/session")
def get_session(request: Request, db: Session = Depends(get_db)):
    email = auth_utils.get_email_by_jwt(request.cookies.get("access_token"))
    
    # Get user info from database
    user_db = UserDB(db)
    user = user_db.get_user_by_email(email)
    
    if user:
        return {
            "user": {
                "id": user.id,
                "email": user.email,
                "name": user.name,
                "created_at": user.created_at,
                "updated_at": user.updated_at
            }
        }
    else:
        # User authenticated but not in database (edge case)
        return {"user": {"email": email}}

# Send magic link
@router.post("/magic-link/send")
def send_magic_link(data: AuthModel.TokenRequest):
    # Fetch user data from Lark
    token = services_lark.get_lark_tenant_token()
    lark_user_id = services_lark.get_lark_user_id(
        token=token,
        json={"emails": [data.email]}
    )

    # Send magic link message via Lark
    services_lark.send_lark_magic_link_message(
        lark_user_id=lark_user_id,
        token=token,
        data=data,
        verify_token=auth_utils.generate_login_token(data.email)
    )

# Verify magic link
@router.post("/magic-link/verify")
def verify_magic_link(data: AuthModel.MagicLinkVerifyRequest, db: Session = Depends(get_db)):
    # 1) Lookup the token
    token_redis_key = auth_utils.LOGIN_TOKEN_REDIS_KEY.format(data.email)
    cached = services_redis.get(token_redis_key)

    # If no token left, assume we already verified successfully:
    if not cached:
        raise HTTPException(400, "Verify Token Expired or Not Exist")
    if cached != data.verifyToken:
        raise HTTPException(400, "Invalid Verify Token")

    # 2) Create/Update user in database
    try:
        user_db = UserDB(db)
        user = user_db.get_user_by_email(data.email)
        
        if not user:
            # User doesn't exist, create them
            # Get user info from Lark
            token = services_lark.get_lark_tenant_token()
            user_info = auth_utils.get_lark_user_info(token, data.email)
            
            user = user_db.create_user(
                email=user_info["email"],
                name=user_info["name"]
            )
            print(f"Created new user: {user.email} (ID: {user.id})")
        else:
            # User exists, optionally update their info
            print(f"User already exists: {user.email} (ID: {user.id})")
            
    except Exception as e:
        print(f"Error managing user in database: {e}")
        # Don't fail authentication if database has issues
        # User can still be authenticated, just not saved to DB

    # 3) Create real access JWT
    access_jwt = auth_utils.create_jwt(data.email)
    
    # 4) Return it (or set cookie, as you prefer)
    response = JSONResponse({
        "message": "Logged in",
        "user": {
            "id": user.id if 'user' in locals() else None,
            "email": data.email,
            "name": user.name if 'user' in locals() else None
        }
    })
    response.set_cookie(
        key="access_token",
        value=access_jwt,
        httponly=True,
        secure=False,       # set True in prod (HTTPS)
        samesite="Lax",
        max_age=config.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        path="/"
    )

    # Optionally delete from cache to make it one-time use
    services_redis.delete(token_redis_key)

    return response