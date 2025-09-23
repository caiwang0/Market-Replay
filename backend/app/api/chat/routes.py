from fastapi import APIRouter, Depends, Request, Query, Body, HTTPException
import json, asyncio
from fastapi import APIRouter, Depends, Request, HTTPException
from fastapi import Query
from fastapi.responses import JSONResponse, StreamingResponse
from sqlalchemy.orm import Session

import app.api.user.utils as User
import app.api.auth.utils as Auth
from app.database.init import get_db
from app.database.chat import ChatDB
import app.models.api.chat as ChatAPIModel
from app.chains.token_stream import token_generator, QueueCallbackHandler
from app.services.openai import generate_chat_title

router = APIRouter()

# Health check
@router.post("/ping")
async def ping():
    return "pong"

@router.post("/invoke")
async def invoke(body_req: ChatAPIModel.InvokeRequest, http_req: Request, db: Session = Depends(get_db)):
    # validate user
    token = Auth.get_jwt_from_cookies(http_req)
    user = User.get_user_by_jwt(token, db)
    
    chat_db = ChatDB(db)
    user_chat = chat_db.get_user_chat_by_chat_uuid(user.id, body_req.chat_uuid)
    if not (user_chat): # create new chat if not exist
        raise HTTPException(status_code=404, detail="Chat not found in database")
    
    queue: asyncio.Queue = asyncio.Queue()
    streamer = QueueCallbackHandler(queue)
    
    # return the streaming response
    return StreamingResponse(
        token_generator(body_req.query, streamer, user_chat.id, user.id, db),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
    )

@router.get("/history")
async def get_chat_history(
    http_req: Request, 
    offset: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=50),
    chat_uuid: str = Query(None),
    db: Session = Depends(get_db)):

    token = Auth.get_jwt_from_cookies(http_req)
    user = User.get_user_by_jwt(token, db)
    messages_slice = []

    chat_db = ChatDB(db)
    user_chat = chat_db.get_user_chat_by_chat_uuid(user.id, chat_uuid)
    if not (user_chat):
        raise HTTPException(status_code=401, detail="Missing token")

    chat_history = chat_db.get_chat_messages(user_chat.id, offset, limit)

    for ch in reversed(chat_history):
        messages_slice.append({
            "question": ch.query,
            "result": json.loads(ch.result),
            "steps": ch.steps,
        })

    return JSONResponse({
        "messages": messages_slice,
        "has_more": len(messages_slice) > 0
    })

@router.post("/create")
async def create_new_chat(
    http_req: Request,
    body_req: ChatAPIModel.CreateRequest,
    db: Session = Depends(get_db),
):
    """
    Create a new chat session for the authenticated user.
    """
    try:
        token = Auth.get_jwt_from_cookies(http_req)
        user = User.get_user_by_jwt(token, db)
        chat_db = ChatDB(db)

        # Create chat first with a placeholder title
        chat = chat_db.create_chat(user.id, title="Untitled Chat")
        # Start async task to generate and update the chat title in the background
        async def update_title():
            try:
                title = await generate_chat_title(body_req.query)
                if title is not None and isinstance(title, str):
                    chat_db.update_chat_title(chat.id, title)
            except Exception as e:
                print(f"Error updating chat title: {e}")
            
        asyncio.create_task(update_title())

        return {"chat_id": chat.id, "chat_uuid": chat.chat_uuid, "title": chat.title, "created_at": chat.created_at.isoformat(), "updated_at": chat.updated_at.isoformat()}
    except Exception as e:
        print(f"Error creating chat: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/lists")
async def get_chat_lists(
    http_req: Request,
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    try:
        token = Auth.get_jwt_from_cookies(http_req)
        user = User.get_user_by_jwt(token, db)
        
        chat_db = ChatDB(db)
        skip = (page - 1) * size
        chats = chat_db.get_user_chats(user.id, skip=skip, limit=size)
        
        return {
            "chats": [
                {
                    "chat_id": chat.id,
                    "chat_uuid": chat.chat_uuid,
                    "title": chat.title,
                    "created_at": chat.created_at,
                    "updated_at": chat.updated_at,
                    # "message_count": chat_db.get_chat_message_count(chat.id)
                }
                for chat in chats
            ],
            "page": page,
            "size": size,
            "user": {
                "id": user.id,
                "email": user.email,
                "name": user.name
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error getting user chats: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

# @router.get("/chat/{chat_id}")
# async def get_chat_detail(
#     chat_id: int,
#     http_req: Request,
#     db: Session = Depends(get_db)
# ):
#     """Get specific chat with all messages for authenticated user"""
#     try:
#         token = Auth.get_jwt_from_cookies(http_req)
#         user = User.get_user_by_jwt(token)

#         chat_db = ChatDB(db)
#         chat = chat_db.get_chat_by_id(chat_id)
        
#         if not chat or chat.user_id != user.id:
#             raise HTTPException(status_code=404, detail="Chat not found or access denied")
        
#         messages = chat_db.get_chat_messages(chat_id)
        
#         return {
#             "id": chat.id,
#             "title": chat.title,
#             "created_at": chat.created_at,
#             "updated_at": chat.updated_at,
#             "messages": [
#                 {
#                     "id": msg.id,
#                     "query": msg.query,
#                     "result": msg.result,
#                     "created_at": msg.created_at,
#                     "steps": msg.steps
#                 }
#                 for msg in messages
#             ],
#             "user": {
#                 "id": user.id,
#                 "email": user.email,
#                 "name": user.name
#             }
#         }
        
#     except HTTPException:
#         raise
#     except Exception as e:
#         print(f"Error getting chat detail: {e}")
#         raise HTTPException(status_code=500, detail="Internal server error")

# @router.delete("/chat/{chat_id}")
# async def delete_chat(
#     chat_id: int,
#     http_req: Request,
#     db: Session = Depends(get_db)
# ):
#     """Delete chat and all its messages for authenticated user"""
#     try:
#         token = Auth.get_jwt_from_cookies(http_req)
#         user = User.get_user_by_jwt(token)
        
#         chat_db = ChatDB(db)
#         chat = chat_db.get_chat_by_id(chat_id)
        
#         if not chat or chat.user_id != user.id:
#             raise HTTPException(status_code=404, detail="Chat not found or access denied")
        
#         success = chat_db.delete_chat(chat_id)
#         if not success:
#             raise HTTPException(status_code=404, detail="Chat not found")
        
#         return {"message": f"Chat {chat_id} deleted successfully"}
        
#     except HTTPException:
#         raise
#     except Exception as e:
#         print(f"Error deleting chat: {e}")
#         raise HTTPException(status_code=500, detail="Internal server error")