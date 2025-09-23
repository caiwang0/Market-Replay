from pydantic import BaseModel, EmailStr

class TokenRequest(BaseModel):
    email: EmailStr

class MagicLinkVerifyRequest(BaseModel):
    email: EmailStr
    verifyToken: str