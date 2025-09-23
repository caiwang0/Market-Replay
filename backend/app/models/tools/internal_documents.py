from pydantic import BaseModel, EmailStr

class DocumentResult(BaseModel):
    # file_token: str
    # distance: float
    file: str
    link: str
    content: list[dict]