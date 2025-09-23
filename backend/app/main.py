from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

import app.config as config
from app.api.routes import router
from app.api.chat.routes import router as chat_router

from app.database.init import create_all_tables

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",  # Frontend URL
        "http://127.0.0.1:3000",  # Alternative frontend URL
        config.HOST_NAME
    ],
    allow_credentials=False,  # No authentication required
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup") 
def startup_event():
    create_all_tables()

app.include_router(router, prefix="/api")
# app.include_router(auth_router, prefix="/api/auth")  # REMOVED
# app.include_router(user_router, prefix="/api/user")  # REMOVED
app.include_router(chat_router, prefix="/api/chat")
