from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

import app.config as config
from app.api.routes import router
from app.api.auth.routes import router as auth_router
from app.api.user.routes import router as user_router 
from app.api.chat.routes import router as chat_router
from app.api.lark.routes import router as lark_router

# from app.database.init import create_all_tables

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        config.HOST_NAME
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# @app.on_event("startup") 
# def startup_event():
#     create_all_tables()

app.include_router(router, prefix="/api")
app.include_router(auth_router, prefix="/api/auth")
app.include_router(user_router, prefix="/api/user")
app.include_router(chat_router, prefix="/api/chat")
app.include_router(lark_router, prefix="/api/lark")