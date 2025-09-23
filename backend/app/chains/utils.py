import json
from langchain.schema import HumanMessage, AIMessage
from langchain_core.messages import BaseMessage
from sqlalchemy.orm import Session

import app.services.redis as services_redis
from app.database.chat import ChatDB

CHAT_HISTORY_REDIS_KEY = "chat_history:{}:{}"
CHAT_HISTORY_MAX_MESSAGES = 20
CHAT_HISTORY_TTL_SECONDS = 60 * 60 * 24 * 1  # 1 day

def generate_chat_history(user_id: int, chat_id: int, db: Session):
    chat_history_key = CHAT_HISTORY_REDIS_KEY.format(user_id, chat_id)
    chat_history = services_redis.get_list(chat_history_key, 0, -1)
    
    # if redis history is empty, fetch from database
    if len(chat_history) == 0:
        chat_db = ChatDB(db)
        chat_messages = chat_db.get_chat_messages(chat_id, 0, 20)
        for cm in reversed(chat_messages):
            human_msg = HumanMessage(content=cm.query)
            ai_msg = AIMessage(content=json.loads(cm.result)["answer"])
            
            chat_history.extend([human_msg, ai_msg])
            services_redis.append_list(chat_history_key, serialize_history_message(human_msg), CHAT_HISTORY_MAX_MESSAGES, CHAT_HISTORY_TTL_SECONDS)
            services_redis.append_list(chat_history_key, serialize_history_message(ai_msg), CHAT_HISTORY_MAX_MESSAGES, CHAT_HISTORY_TTL_SECONDS)
    
    return chat_history

def serialize_history_message(message: BaseMessage) -> str:
    return json.dumps({
        "type": message.type,
        "data": message.dict()
    })