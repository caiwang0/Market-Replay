from pydantic import BaseModel
from typing import Optional

class InvokeRequest(BaseModel):
    query: str
    chat_uuid: Optional[str] = None

class CreateRequest(BaseModel):
    query: str
