from fastapi import APIRouter

router = APIRouter()

# Health check
@router.post("/ping")
async def ping():
    return "pong"