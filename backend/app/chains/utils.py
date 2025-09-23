import json
from langchain.schema import HumanMessage, AIMessage
from langchain_core.messages import BaseMessage
from sqlalchemy.orm import Session

from app.database.chat import ChatDB

def generate_chat_history(user_id: int, chat_id: int, db: Session):
    """Generate chat history from database only (Redis removed)"""
    chat_db = ChatDB(db)
    chat_messages = chat_db.get_chat_messages(chat_id, 0, 20)
    
    chat_history = []
    for cm in reversed(chat_messages):
        human_msg = HumanMessage(content=cm.query)
        ai_msg = AIMessage(content=json.loads(cm.result)["answer"])
        chat_history.extend([human_msg, ai_msg])
    
    return chat_history

def serialize_history_message(message: BaseMessage) -> str:
    return json.dumps({
        "type": message.type,
        "data": message.dict()
    })